"""Comparison-only NHL-style historical projections and positional value."""
from functools import lru_cache
import hashlib
import math
import random
from urllib.parse import urlparse

from . import empirical
from .backtest import digest, input_model
from .config import ROOT, active_slots, instant, path, read_json, roster_size, write_json
from .empirical_draft import anchored_order, score_roster, simulate, summarize
from .planner import assign, legal_roster
from .ranking_library import checked_board
from .research_data import FIELDS
from .source_backtest import preferences, primary_sources
from .strategy_lab import key

YEARS = (2019, 2023, 2024, 2025, 2026)
POSITIONS = ("PG", "SG", "SF", "PF", "C")
PARAMETERS = {"version":1,"production_weights":[.65,.35],"games_weights":[.8,.2],
              "minimum_history_games":20,"small_sample_games":60,"established_games":100,
              "established_floor":60,"other_floor":40,"games_cap":80}


def projection(store, nba_id, year, scoring):
    rows=[(i,store.seasons.get(year-i-1,{}).get(nba_id)) for i in range(2)]
    rows=[(i,row) for i,row in rows if row and row["games"]>0]
    games=sum(r["games"] for _,r in rows)
    if games < PARAMETERS["minimum_history_games"]:
        return None
    weights=PARAMETERS["production_weights"]
    denominator=sum(weights[i]*r["games"] for i,r in rows)
    regression=(.85+.15*games/60) if games<60 else 1
    stats={k:regression*sum(weights[i]*r["stats"][k] for i,r in rows)/denominator for k in FIELDS}
    weights=PARAMETERS["games_weights"]
    forecast=sum(weights[i]*r["games"] for i,r in rows)/sum(weights[i] for i,_ in rows)
    floor=PARAMETERS["established_floor"] if games>=PARAMETERS["established_games"] else PARAMETERS["other_floor"]
    forecast=min(PARAMETERS["games_cap"],max(floor,forecast))
    fpg=empirical.points(stats,scoring)
    return {"per_game":stats,"fpg":fpg,"games":forecast,"season_points":fpg*forecast,
            "history_games":games,"small_sample_multiplier":regression,
            "missing_latest_season":not any(i==0 for i,_ in rows)}


def replacement_depth(cfg):
    allocation={p:0.0 for p in POSITIONS}
    for slot,count in cfg["slots"].items():
        if slot=="IR":continue
        positions=([slot] if slot in POSITIONS else ["PG","SG"] if slot=="G" else
                   ["SF","PF"] if slot=="F" else list(POSITIONS) if slot in {"UTIL","BE"} else None)
        if positions is None:
            raise ValueError("Unsupported slot for positional replacement allocation")
        for position in positions:allocation[position]+=count/len(positions)
    return {p:max(1,math.ceil(n*cfg["teams"]-1e-9)) for p,n in allocation.items()}


def replacement_levels(rows, cfg):
    depth=replacement_depth(cfg)
    result={}
    for position in POSITIONS:
        group=sorted((r for r in rows if r["primary"]==position),key=lambda r:(-r["season_points"],r["id"]))
        if group:
            chosen=group[min(depth[position],len(group))-1]
            result[position]={"points":chosen["season_points"],"depth":depth[position],
                              "actual_depth":min(depth[position],len(group)),"player_id":chosen["id"]}
    return result


def attach_value(rows, levels):
    for row in rows:
        if row["primary"] not in levels:
            raise ValueError("No modeled replacement baseline for a player's primary position")
        row["replacement_points"]=levels[row["primary"]]["points"]
        row["vor"]=row["season_points"]-row["replacement_points"]


def adjustments(year, as_of, file=None):
    policy=read_json(file or ROOT/"value_adjustments.json")
    if not policy or policy.get("version")!=1 or not isinstance(policy.get("players"),list):
        raise ValueError("Invalid value-board adjustment policy")
    if policy.get("season")!=year:
        return {}  # Current research never leaks into a historical draft.
    result={}
    allowed={"id","games","fpg_multiplier","source","observed_at","note"}
    for row in policy["players"]:
        if (not isinstance(row,dict) or set(row)-allowed or type(row.get("id")) is not int
                or row["id"]<=0 or row["id"] in result or not row.get("note")
                or urlparse(row.get("source","")).scheme not in {"http","https"}
                or not urlparse(row.get("source","")).netloc or not row.get("observed_at")):
            raise ValueError("Adjustment requires a unique ESPN ID, source, observation time and note")
        observed=instant(row["observed_at"])
        if observed.tzinfo is None:
            raise ValueError("Adjustment observation must include its timezone")
        if observed>instant(as_of):
            raise ValueError("Adjustment observation is later than the ranking cutoff")
        for field,high in (("games",82),("fpg_multiplier",float("inf"))):
            if field in row and (type(row[field]) not in (int,float) or not math.isfinite(row[field]) or not 0<=row[field]<=high):
                raise ValueError("Invalid adjustment games or scoring multiplier")
        result[row["id"]]=row
    return result


def apply_adjustment(row, adjustment=None, injury_cap=None):
    result=dict(row)
    if adjustment:
        multiplier=adjustment.get("fpg_multiplier",1)
        result["per_game"]={k:v*multiplier for k,v in row["per_game"].items()}
        result["fpg"]=row["fpg"]*multiplier
        result["games"]=adjustment.get("games",row["games"])
    if injury_cap is not None:result["games"]=min(result["games"],injury_cap)
    result["season_points"]=result["fpg"]*result["games"]
    result["adjustment"]=adjustment
    return result


def prepare(cfg, store, year, library):
    pack=read_json(library/f"input-{year}.json")
    inventory=read_json(ROOT.parent/"docs/basketball_data_inventory.json")
    expected=next(r["input_sha256"] for r in inventory["historical_inputs"] if r["season"]==year)
    if digest(pack)!=expected:raise ValueError("Historical preseason pack changed")
    for source in pack["sources"]:
        board=read_json(library/"boards"/(source["id"]+".json"))
        checked_board(library,board)
        if board["status"]!="preseason" or board["source"]["format"]!="points" or board["sha256"]!=source["sha256"]:
            raise ValueError("Historical source is not verified preseason points data")
    model=input_model(cfg,pack)
    published,_,_=preferences(model,pack)
    market=published["espn"]["order"]
    names=store.identities(year)
    rows,mapping=[],{}
    for pid in market:
        nba=names.get(key(model.by_id[pid]["name"]))
        if nba:mapping[pid]=nba
        projected=projection(store,nba,year,cfg["scoring"]) if nba else None
        if projected:rows.append({"id":pid,"primary":model.by_id[pid]["primary"],**projected})
    levels=replacement_levels(rows,cfg)
    attach_value(rows,levels)
    policies={"espn":market,
              "nhl_total":anchored_order(market,{p["id"]:p["season_points"] for p in rows}),
              "nhl_vor":anchored_order(market,{p["id"]:p["vor"] for p in rows}),
              "nhl_vor_next_turn":anchored_order(market,{p["id"]:p["vor"] for p in rows})}
    for family,source in primary_sources(pack).items():
        if family!="ESPN":policies[family]=published["source:"+source]["order"]

    @lru_cache(maxsize=200000)
    def legal(roster,pid):
        players=[model.by_id[p] for p in (*roster,pid)]
        left=roster_size(model.cfg)-len(players)
        return legal_roster(players,model.cfg) and len(active_slots(model.cfg))-len(assign(players,active_slots(model.cfg)))<=left
    return {"model":model,"market":market,"policies":policies,"mapping":mapping,
            "modeled":{r["id"] for r in rows},"replacement":levels,"projections":rows,
            "input_sha256":digest(pack),"legal":legal}


def backtest(cfg):
    store,manifest=empirical.load_seasons(cfg)
    root=path(cfg,"research-value");root.mkdir(parents=True,exist_ok=True)
    prepared,decisions={},[]
    for year in YEARS:
        data=prepare(cfg,store,year,path(cfg,"ranking-library"));prepared[year]=data
        ordinal={pid:i for i,pid in enumerate(data["market"])}
        for seed in (-1,0,1):
            opponents={}
            for team in range(1,cfg["teams"]+1):
                rng=random.Random(f"empirical-v1:{year}:{seed}:{team}")
                noise={pid:rng.gauss(0,12) if seed>=0 else 0 for pid in data["market"]}
                opponents[team]=sorted(data["market"],key=lambda pid:(ordinal[pid]+noise[pid],pid))
            for slot in range(1,cfg["teams"]+1):
                for policy,order in data["policies"].items():
                    roster,trace=simulate(data["model"],slot,order,opponents,data["market"],data["legal"],policy=="nhl_vor_next_turn")
                    decisions.append({"season":year,"seed":seed,"slot":slot,"policy":policy,"roster":roster,"trace":trace,
                                      "modeled_pick_share":sum(pid in data["modeled"] for pid in roster)/len(roster)})
            print(f"Completed {year}, opponent seed {seed}: {len(decisions)} scenarios",flush=True)
    files=("value_board.py","empirical.py","empirical_draft.py","planner.py","source_backtest.py","ranking_library.py","config.py","strategy_lab.py","backtest.py","model.py")
    evidence={"version":1,"parameters":PARAMETERS,"data_sha256":digest(manifest),
              "protocol_sha256":hashlib.sha256((ROOT.parent/"docs/BASKETBALL_VALUE_PROTOCOL.md").read_text(encoding="utf-8").encode()).hexdigest(),
              "code_sha256":{name:hashlib.sha256((ROOT/name).read_text(encoding="utf-8").encode()).hexdigest() for name in files},
              "preseason_inputs":{str(y):d["input_sha256"] for y,d in prepared.items()},
              "replacement":{str(y):d["replacement"] for y,d in prepared.items()},
              "projections":{str(y):d["projections"] for y,d in prepared.items()},
              "config":{k:cfg[k] for k in ("teams","slots","position_limits","scoring")},"decisions":decisions}
    write_json(root/"decisions.json",evidence)
    write_json(root/"decisions-lock.json",{"sha256":digest(evidence)})
    locked=read_json(root/"decisions.json")
    if digest(locked)!=read_json(root/"decisions-lock.json")["sha256"]:raise ValueError("Draft decisions changed")
    results=[]
    for row in locked["decisions"]:
        data=prepared[row["season"]]
        results.append({**{k:v for k,v in row.items() if k not in {"roster","trace"}},
                        **score_roster(row["roster"],data["model"],store,row["season"],data["mapping"])})
    prior=read_json(path(cfg,"research-empirical/draft-backtest.json"))
    comparisons=None
    if prior:
        baseline={(r["season"],r["seed"],r["slot"]):r["total_points"] for r in results if r["policy"]=="espn"}
        for row in prior["cases"]:
            if row["policy"]=="espn" and baseline[(row["season"],row["seed"],row["slot"])]!=row["total_points"]:
                raise ValueError("Paired ESPN baseline differs from the earlier experiment")
        previous_evidence=read_json(path(cfg,"research-empirical/draft-decisions.json"))
        previous_lock=read_json(path(cfg,"research-empirical/draft-decisions-lock.json"))
        if (digest(previous_evidence)!=previous_lock["sha256"] or prior["decision_sha256"]!=previous_lock["sha256"]
                or previous_evidence["data_sha256"]!=digest(manifest) or prior["summaries"]!=summarize(prior["cases"])):
            raise ValueError("Previous empirical comparison is not locked")
        comparisons={y:{k:v for k,v in rows.items() if k.startswith("learned_")} for y,rows in prior["summaries"].items()}
    report={"version":1,"decision_sha256":digest(locked),"summaries":summarize(results),"cases":results,
            "earlier_empirical":comparisons,"comparison_only":True,"independent_holdout":False,
            "metric":"Actual season fantasy points of drafted rosters, not weekly H2H wins"}
    write_json(root/"backtest.json",report)
    return {"scenarios":len(results),"summaries":report["summaries"],"decision_sha256":report["decision_sha256"]}


def current(cfg):
    from .research_board import build
    build(cfg)
    base=read_json(path(cfg,"research-board/rankings.json"))
    inputs=read_json(path(cfg,"research-board/inputs.json"))
    store,manifest=empirical.load_seasons(cfg)
    policy=adjustments(cfg["season"],base["as_of"])
    names=store.identities(cfg["season"])
    players={p["id"]:p for p in inputs["snapshot"]["players"]}
    rows,excluded=[],[]
    for source in base["rows"]:
        pid=source["id"]
        nba=names.get(key(source["name"]))
        forecast=projection(store,nba,cfg["season"],cfg["scoring"]) if nba else None
        fallback=forecast is None
        if fallback:forecast={k:source[k] for k in ("per_game","fpg","games","season_points")}
        forecast=apply_adjustment(forecast,policy.get(pid),source["injury_opportunity_cap"])
        row={**forecast,**{k:source[k] for k in ("id","name","team","eligible","injury","ban","espn_rank","rotowire_rank")},
             "primary":players[pid]["primary"],"nba_id":nba,"model_fallback":fallback}
        if row["games"]<=0:excluded.append({"id":pid,"name":row["name"],"reason":"Zero expected games"});continue
        rows.append(row)
    if set(policy)-{r["id"] for r in base["rows"]}:raise ValueError("Adjustment player is outside the verified current universe")
    levels=replacement_levels([r for r in rows if not r["model_fallback"]],cfg)
    attach_value(rows,levels)
    rows.sort(key=lambda r:(-r["vor"],r["id"]))
    personal=0
    for rank,row in enumerate(rows,1):
        row["rank"]=rank
        if not row["ban"]:personal+=1
        row["personal_rank"]=None if row["ban"] else personal
    root=path(cfg,"research-value")
    report={"version":1,"as_of":base["as_of"],"parameters":PARAMETERS,"comparison_only":True,
            "base_input_sha256":base["inputs_sha256"],"data_sha256":digest(manifest),"adjustments":list(policy.values()),
            "replacement":levels,"modeled_players":sum(not r["model_fallback"] for r in rows),"rows":rows,"excluded":excluded}
    write_json(root/"rankings.json",report)
    lines=["# NHL-style basketball value board — comparison only","","As of: "+report["as_of"],"",
           "Two-season historical production, projected games and primary-position value over replacement. "
           "Current sourced injury caps and explicit sourced adjustments can change games. Team labels alone do not change production. "
           "This is not the live draft source; historical tests do not validate the full current injury-aware pipeline.","",
           "| Rank | Player | Pos | Fpts/game | Games | Season pts | VOR | RotoWire | ESPN | Notes |",
           "|---:|---|---|---:|---:|---:|---:|---:|---:|---|"]
    for row in rows:
        notes=[row["ban"]] if row["ban"] else []
        if row["model_fallback"]:notes.append("Existing comparison forecast; fewer than 20 historical games or unmatched")
        if row.get("missing_latest_season"):notes.append("Missing latest historical season; older production carried")
        if row["injury"]:notes.append("Return estimate: "+(row["injury"]["expected_return"] or "unknown"))
        if row["adjustment"]:notes.append(row["adjustment"]["note"])
        lines.append(f"| {row['rank']} | {row['name']} | {row['primary']} | {row['fpg']:.1f} | {row['games']:.1f} | {row['season_points']:.0f} | {row['vor']:.0f} | {row['rotowire_rank'] or '—'} | {row['espn_rank'] or '—'} | {'; '.join(notes)} |")
    lines += ["","## Replacement baselines",""]
    lines += [f"- {p}: rank {r['actual_depth']} (target depth {r['depth']}), {r['points']:.1f} expected season points." for p,r in levels.items()]
    (root/"rankings.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    return {"ranked":len(rows),"modeled":report["modeled_players"],"fallbacks":len(rows)-report["modeled_players"],"board":str(root/"rankings.md")}
