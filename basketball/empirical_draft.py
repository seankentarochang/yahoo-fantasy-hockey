"""Paired historical draft comparisons using locked statistical rate forecasts."""
from functools import lru_cache
import hashlib
from pathlib import Path
import random
import statistics

from . import empirical
from .backtest import digest, input_model
from .config import ROOT, active_slots, path, read_json, roster_size, write_json
from .planner import assign, legal_roster
from .ranking_library import checked_board
from .source_backtest import preferences, primary_sources
from .strategy_lab import key


def anchored_order(market, scores):
    """Keep unmodeled players at their market slots, never invent rookie rates."""
    modeled = iter(sorted(scores,key=lambda pid:(-scores[pid],pid)))
    return [next(modeled) if pid in scores else pid for pid in market]


def choose(order, legal, roster, gone, market, opponent_picks=None):
    urgent = None
    if opponent_picks is not None:
        remaining = [pid for pid in market if pid not in gone]
        urgent = set(remaining[:opponent_picks])
    if urgent:
        selected = next((pid for pid in order if pid in urgent and pid not in gone and legal(tuple(sorted(roster)),pid)),None)
        if selected is not None:
            return selected
    return next((pid for pid in order if pid not in gone and legal(tuple(sorted(roster)),pid)),None)


def simulate(model, target, order, opponents, market, legal, timing=False):
    rosters = {team:[] for team in range(1,model.cfg["teams"]+1)}
    sequence = [team for rnd in range(roster_size(model.cfg))
                for team in (range(1,model.cfg["teams"]+1) if rnd%2==0 else range(model.cfg["teams"],0,-1))]
    our_picks = [i for i,team in enumerate(sequence,1) if team==target]
    gone, trace = set(), []
    for pick,team in enumerate(sequence,1):
        queue = order if team==target else opponents[team]
        next_turn = next((p for p in our_picks if p>pick),None) if team==target else None
        gap = next_turn-pick-1 if timing and next_turn is not None else None
        pid = choose(queue,legal,rosters[team],gone,market,gap)
        if pid is None:
            raise ValueError("No legal historical draft choice")
        rosters[team].append(pid); gone.add(pid)
        if team==target:
            trace.append({"pick":pick,"id":pid,"opponent_picks_to_next":gap})
    for roster in rosters.values():
        players=[model.by_id[pid] for pid in roster]
        if not legal_roster(players,model.cfg) or len(assign(players,active_slots(model.cfg)))!=len(active_slots(model.cfg)):
            raise ValueError("Historical draft produced an invalid roster")
    if len(gone)!=len(sequence):
        raise ValueError("Historical draft duplicated a player")
    return rosters[target],trace


def prepare_year(cfg,store,year,rate_model,library):
    pack=read_json(library/f"input-{year}.json")
    inventory=read_json(ROOT.parent/"docs/basketball_data_inventory.json")
    registered=next(p["input_sha256"] for p in inventory["historical_inputs"] if p["season"]==year)
    if digest(pack)!=registered:
        raise ValueError("Historical preseason input changed from its registered inventory")
    for source in pack["sources"]:
        board=read_json(library/"boards"/(source["id"]+".json"))
        checked_board(library,board)
        if board["status"]!="preseason" or board["source"]["format"]!="points" or board["sha256"]!=source["sha256"]:
            raise ValueError("Historical expert board is not verified preseason points data")
    model=input_model(cfg,pack)
    published,_,_=preferences(model,pack)
    market=published["espn"]["order"]
    names=store.identities(year)
    production,totals,prior,mapping={},{},{},{}
    for pid in market:
        nba=names.get(key(model.by_id[pid]["name"]))
        if nba:
            mapping[pid]=nba
            previous=store.seasons[year-1].get(nba)
            if previous:
                prior[pid]=empirical.points(previous["stats"],cfg["scoring"])
        if not nba or store.prior_minutes(nba,year)<150:
            continue
        workload=store.workload(nba,year)
        if workload is None:
            continue
        mpg,games=workload
        rate=empirical.points(empirical.predict(rate_model,store.features(nba,year)),cfg["scoring"])
        production[pid]=rate*mpg
        totals[pid]=production[pid]*games
    policies={"espn":market,"prior_total":anchored_order(market,prior),
              "learned_per_game":anchored_order(market,production),"learned_total":anchored_order(market,totals),
              "learned_next_turn":anchored_order(market,totals)}
    for family,source in primary_sources(pack).items():
        if family!="ESPN":policies[family]=published["source:"+source]["order"]

    @lru_cache(maxsize=200000)
    def legal(roster,pid):
        players=[model.by_id[p] for p in (*roster,pid)]
        left=roster_size(model.cfg)-len(players)
        return legal_roster(players,model.cfg) and len(active_slots(model.cfg))-len(assign(players,active_slots(model.cfg)))<=left
    return {"model":model,"pack_sha256":digest(pack),"market":market,"policies":policies,
            "mapping":mapping,"modeled":set(totals),"legal":legal}


def score_roster(roster,model,store,year,mapping):
    # Outcome identity joins occur only after draft selections have been locked.
    names={}
    for nba,row in store.seasons[year].items():
        names.setdefault(key(row["name"]),set()).add(nba)
    total,games=0,[]
    for pid in roster:
        nba=mapping.get(pid)
        if nba is None:
            ids=names.get(key(model.by_id[pid]["name"]),set())
            nba=next(iter(ids)) if len(ids)==1 else None
        actual=store.seasons[year].get(nba)
        total+=empirical.points(actual["stats"],model.cfg["scoring"]) if actual else 0
        games.append(actual["games"] if actual else 0)
    return {"total_points":total,"zero_games":sum(g==0 for g in games),"under_25_games":sum(g<25 for g in games)}


def summarize(rows):
    by_year={}
    for year in sorted({r["season"] for r in rows}):
        pairs={}
        for row in rows:
            if row["season"]==year:pairs.setdefault((row["seed"],row["slot"]),{})[row["policy"]]=row
        summary={}
        for policy in sorted({r["policy"] for r in rows if r["season"]==year}):
            values=[case[policy] for case in pairs.values()]
            differences=[case[policy]["total_points"]-case["espn"]["total_points"] for case in pairs.values()]
            gains=[100*delta/case["espn"]["total_points"] for delta,case in zip(differences,pairs.values())]
            summary[policy]={"drafts":len(values),"mean_total_points":statistics.mean(v["total_points"] for v in values),
                "mean_gain_pct_vs_espn":statistics.mean(gains),"paired_win_rate":statistics.mean(d>0 for d in differences),
                "paired_tie_rate":statistics.mean(d==0 for d in differences),
                "mean_modeled_pick_share":statistics.mean(v["modeled_pick_share"] for v in values),
                "mean_zero_games":statistics.mean(v["zero_games"] for v in values)}
        by_year[str(year)]=summary
    return by_year


def run(cfg):
    store,manifest=empirical.load_seasons(cfg)
    root=path(cfg,"research-empirical"); library=path(cfg,"ranking-library")
    selection=empirical.locked_selection(cfg,manifest)
    prepared,decisions={},[]
    for year in empirical.TEST:
        rate_model=empirical.fit(store,range(2020,year),selection["alpha"])
        data=prepare_year(cfg,store,year,rate_model,library);prepared[year]=data
        ordinal={pid:i for i,pid in enumerate(data["market"])}
        for seed in (-1,0,1):
            opponents={}
            for team in range(1,cfg["teams"]+1):
                rng=random.Random(f"empirical-v1:{year}:{seed}:{team}")
                noise={pid:rng.gauss(0,12) if seed>=0 else 0 for pid in data["market"]}
                opponents[team]=sorted(data["market"],key=lambda pid:(ordinal[pid]+noise[pid],pid))
            for slot in range(1,cfg["teams"]+1):
                for policy,order in data["policies"].items():
                    roster,trace=simulate(data["model"],slot,order,opponents,data["market"],data["legal"],policy=="learned_next_turn")
                    decisions.append({"season":year,"seed":seed,"slot":slot,"policy":policy,"roster":roster,"trace":trace,
                                      "modeled_pick_share":sum(pid in data["modeled"] for pid in roster)/len(roster)})
            print(f"Completed {year}, opponent seed {seed}: {len(decisions)} draft scenarios",flush=True)
    evidence={"version":1,"selection_sha256":digest(selection),"data_sha256":digest(manifest),
              "preseason_inputs":{str(y):p["pack_sha256"] for y,p in prepared.items()},
              "code_sha256":{name:hashlib.sha256((ROOT/name).read_text(encoding="utf-8").encode()).hexdigest()
                             for name in ("empirical.py","empirical_draft.py","planner.py","source_backtest.py","ranking_library.py","config.py","strategy_lab.py","backtest.py","model.py")},
              "config":{k:cfg[k] for k in ("teams","slots","position_limits","scoring")},"decisions":decisions}
    write_json(root/"draft-decisions.json",evidence)
    write_json(root/"draft-decisions-lock.json",{"sha256":digest(evidence)})
    locked=read_json(root/"draft-decisions.json")
    if digest(locked)!=read_json(root/"draft-decisions-lock.json")["sha256"]:
        raise ValueError("Draft choices changed before outcome scoring")
    results=[]
    for row in locked["decisions"]:
        data=prepared[row["season"]]
        results.append({**{k:v for k,v in row.items() if k not in {"roster","trace"}},
                        **score_roster(row["roster"],data["model"],store,row["season"],data["mapping"])})
    report={"version":1,"decision_sha256":digest(locked),"summaries":summarize(results),"cases":results,
            "metric":"Actual drafted-roster season points, not weekly H2H wins",
            "independent_holdout":False,"comparison_only":True}
    write_json(root/"draft-backtest.json",report)
    return {"draft_scenarios":len(results),"summaries":report["summaries"],"decisions_sha256":report["decision_sha256"]}
