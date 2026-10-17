"""Learn statistical production from prior game logs; no live-draft integration."""
import csv
import hashlib
import io
import math
from pathlib import Path
import statistics

import numpy as np

from .backtest import digest
from .config import ROOT, path, read_json, write_json
from .research_data import FIELDS, audit
from .strategy_lab import key

ALPHAS = (0.1, 1, 10, 100)
TRAIN = (2020, 2021, 2022, 2023)
VALIDATION = 2024
TEST = (2025, 2026)
WEIGHTS = (0.6, 0.3, 0.1)
RATE_FIELDS = ("2PA", "3PA", "FTA", "REB", "AST", "STL", "BLK", "TO")
COMPONENTS = RATE_FIELDS + ("2P%", "3P%", "FT%")


def load_seasons(cfg):
    root = path(cfg, "research-datasets")
    manifest = read_json(root / "manifest.json")
    if not manifest:
        raise ValueError("Collect the public historical game logs first")
    seasons = {}
    for record in manifest["seasons"]:
        year = record["year"]
        target = (root / record["file"]).resolve()
        if not target.is_relative_to(root.resolve()):
            raise ValueError("Historical data path escapes the research directory")
        data = target.read_bytes()
        if hashlib.sha256(data).hexdigest() != record["sha256"]:
            raise ValueError("Historical game-log hash changed")
        checked = audit(data, year)
        if any(checked[k] != record[k] for k in ("played_rows", "games", "teams")):
            raise ValueError("Historical audit does not match its manifest")
        players, team_games = {}, {}
        for raw in csv.DictReader(io.StringIO(data.decode("utf-8-sig"))):
            if raw["season_type_id"] != "2" or not raw["game_id"].startswith("002"):
                continue
            team_games.setdefault(raw["team_id"], set()).add(raw["game_id"])
            if not raw["minutes"]:
                continue
            text = raw["minutes"]
            minutes = sum(float(x) / (60 ** i) for i, x in enumerate(text.split(":")))
            pid = raw["person_id"]
            row = players.setdefault(pid, {"id":pid, "name":raw["first_name"] + " " + raw["family_name"],
                    "minutes":0, "games":0, "stats":{k:0 for k in (*FIELDS, "3PA")}, "teams":{}})
            row["minutes"] += minutes
            row["games"] += 1
            row["teams"][raw["team_id"]] = row["teams"].get(raw["team_id"], 0) + 1
            for stat, column in FIELDS.items():
                row["stats"][stat] += float(raw[column])
            row["stats"]["3PA"] += float(raw["three_pointers_attempted"])
        for row in players.values():
            denominator = sum(len(team_games[t]) * n for t,n in row["teams"].items()) / row["games"]
            row["game_share"] = min(1, row["games"] / denominator)
        seasons[year] = players
    if not set(range(2017, 2027)) <= set(seasons):
        raise ValueError("This registered experiment needs all ending seasons 2017–2026")
    return Store(seasons), manifest


def components(row, prior, shrink=False):
    if not row or not row["minutes"]:
        return list(prior)
    s = row["stats"]
    values = {**s, "2PA":s["FGA"]-s["3PA"], "2PM":s["FGM"]-s["3PM"]}
    if values["2PA"] < 0 or values["2PM"] < 0:
        raise ValueError("Invalid two-point decomposition")
    minutes = row["minutes"]
    strength = 500 if shrink else 0
    result = [(values[k] + prior[i]*strength) / (minutes+strength) for i,k in enumerate(RATE_FIELDS)]
    strength = 50 if shrink else 0
    for index, made, attempted in ((8,"2PM","2PA"),(9,"3PM","3PA"),(10,"FTM","FTA")):
        result.append((values[made] + strength*prior[index]) / (values[attempted]+strength)
                      if values[attempted]+strength else prior[index])
    return result


def box_score(values):
    """Derive coherent expected counts rather than separately forecasting PTS."""
    if len(values) != 11 or any(not math.isfinite(float(x)) for x in values):
        raise ValueError("Invalid empirical statistical components")
    rates = {k:max(0, float(v)) for k,v in zip(RATE_FIELDS,values[:8])}
    p2,p3,pft = [min(1,max(0,float(v))) for v in values[8:]]
    two, three, free = rates["2PA"]*p2, rates["3PA"]*p3, rates["FTA"]*pft
    return {"PTS":2*two+3*three+free, "FGM":two+three, "FGA":rates["2PA"]+rates["3PA"],
            "FTM":free, "FTA":rates["FTA"], "3PM":three,
            **{k:rates[k] for k in ("REB","AST","STL","BLK","TO")}}


def points(stats, scoring):
    if any(value and k not in stats for k,value in scoring.items()):
        raise ValueError("Unsupported empirical scoring component")
    return sum(stats.get(k,0)*value for k,value in scoring.items())


class Store:
    def __init__(self, seasons):
        self.seasons = seasons
        self._priors = {}

    def prior(self, year):
        if year not in self._priors:
            rows = list(self.seasons[year-1].values())
            aggregate = {"minutes":sum(r["minutes"] for r in rows),
                         "stats":{k:sum(r["stats"][k] for r in rows) for k in (*FIELDS,"3PA")}}
            self._priors[year] = components(aggregate, [0]*8+[.5,.35,.75])
        return self._priors[year]

    def previous(self, pid, year):
        return [(w,self.seasons.get(year-i,{}).get(pid)) for i,w in enumerate(WEIGHTS,1)]

    def prior_minutes(self, pid, year):
        return sum(r["minutes"] for _,r in self.previous(pid,year) if r)

    def features(self, pid, year):
        prior = self.prior(year)
        values = []
        for _,row in self.previous(pid,year):
            values.extend(components(row,prior,shrink=True))
            values.extend([row["minutes"]/row["games"] if row and row["games"] else 0,
                           row["game_share"] if row else 0, int(row is not None)])
        return values

    def samples(self, year):
        # Candidate identity comes from earlier years, never the target roster.
        candidates = set().union(*(self.seasons.get(year-i,{}) for i in range(1,4)))
        for pid in sorted(candidates):
            target = self.seasons[year].get(pid)
            if self.prior_minutes(pid,year) >= 150 and target and target["minutes"] >= 100:
                yield pid,self.features(pid,year),components(target,self.prior(year)),target

    def baseline(self, pid, year, method):
        rows = [(w,r) for w,r in self.previous(pid,year) if r and r["minutes"] > 0]
        if method == "last_season":
            row = self.seasons[year-1].get(pid)
            return ({k:v/row["minutes"] for k,v in row["stats"].items() if k in FIELDS}
                    if row and row["minutes"] else None)
        minutes = sum(w*r["minutes"] for w,r in rows)
        return {k:sum(w*r["stats"][k] for w,r in rows)/minutes for k in FIELDS} if minutes else None

    def workload(self, pid, year):
        rows = [(w,r) for w,r in self.previous(pid,year) if r and r["minutes"] > 0]
        if not rows:
            return None
        mpg = sum(w*r["minutes"]/r["games"] for w,r in rows)/sum(w for w,_ in rows)
        debut = min(y for y,players in self.seasons.items() if y < year and pid in players)
        share = [(w,r["game_share"] if r else 0) for i,(w,r) in enumerate(self.previous(pid,year),1) if year-i >= debut]
        games = 82*sum(w*value for w,value in share)/sum(w for w,_ in share)
        return min(48,mpg),min(82,games)

    def identities(self, year):
        result = {}
        for y in sorted(y for y in self.seasons if y < year):
            for pid,row in self.seasons[y].items():
                result.setdefault(key(row["name"]),set()).add(pid)
        return {name:next(iter(ids)) for name,ids in result.items() if len(ids)==1}


def fit(store, years, alpha):
    rows = [(year,*sample) for year in years for sample in store.samples(year)]
    if not rows:
        raise ValueError("No eligible historical training samples")
    x = np.asarray([r[2] for r in rows],dtype=float)
    y = np.asarray([r[3] for r in rows],dtype=float)
    weights = np.asarray([max(.25,min(1,store.prior_minutes(r[1],r[0])/2000)) for r in rows])
    mean = np.average(x,axis=0,weights=weights)
    scale = np.sqrt(np.average((x-mean)**2,axis=0,weights=weights))
    scale[scale < 1e-9] = 1
    design = np.column_stack([np.ones(len(x)),(x-mean)/scale])
    penalty = np.eye(design.shape[1])*alpha
    penalty[0,0] = 0
    coef = np.linalg.solve(design.T @ (design*weights[:,None])+penalty, design.T @ (y*weights[:,None]))
    return {"training_years":list(years),"training_samples":len(rows),"alpha":alpha,
            "mean":mean.tolist(),"scale":scale.tolist(),"coefficients":coef.tolist()}


def predict(model, features):
    design = np.r_[1,(np.asarray(features)-model["mean"])/model["scale"]]
    return box_score(design @ np.asarray(model["coefficients"]))


def evaluate_rates(store, model, year, scoring):
    errors = {"learned":[],"last_season":[],"three_year":[]}
    for pid,features,_,target in store.samples(year):
        actual = points(target["stats"],scoring)/target["minutes"]
        predictions = {"learned":predict(model,features),
                       **{name:store.baseline(pid,year,name) for name in ("last_season","three_year")}}
        # Use identical paired cohorts for every comparator.
        if any(value is None for value in predictions.values()):
            continue
        for name,stats in predictions.items():
            errors[name].append(30*(points(stats,scoring)-actual))
    if not errors["learned"]:
        raise ValueError("No comparable production evaluation cohort")
    return {name:{"players":len(values),"mae_at_30_minutes":statistics.mean(abs(x) for x in values),
                  "rmse_at_30_minutes":math.sqrt(statistics.mean(x*x for x in values)),
                  "mean_error_at_30_minutes":statistics.mean(values)} for name,values in errors.items()}


def locked_selection(cfg, manifest):
    root=path(cfg,"research-empirical")
    selection=read_json(root/"selection.json")
    lock=read_json(root/"selection-lock.json",{})
    if (not selection or lock.get("sha256")!=digest(selection) or selection["data_sha256"]!=digest(manifest)
            or selection["scoring"]!=cfg["scoring"]
            or selection["implementation_sha256"]!=hashlib.sha256(Path(__file__).read_text(encoding="utf-8").encode()).hexdigest()
            or selection["protocol_sha256"]!=hashlib.sha256((ROOT.parent/"docs/BASKETBALL_EMPIRICAL_PROTOCOL.md").read_text(encoding="utf-8").encode()).hexdigest()):
        raise ValueError("Empirical selection, data, scoring, implementation or protocol changed; refit explicitly")
    return selection


def experiment(cfg):
    store,manifest = load_seasons(cfg)
    root = path(cfg,"research-empirical")
    root.mkdir(parents=True,exist_ok=True)
    candidates = {}
    for alpha in ALPHAS:
        model = fit(store,TRAIN,alpha)
        candidates[str(alpha)] = evaluate_rates(store,model,VALIDATION,cfg["scoring"])
    alpha = min(ALPHAS,key=lambda a:(candidates[str(a)]["learned"]["mae_at_30_minutes"],a))
    selection = {"alpha":alpha,"training_years":list(TRAIN),"validation_year":VALIDATION,
                 "candidates":candidates,"data_sha256":digest(manifest),"scoring":cfg["scoring"],
                 "implementation_sha256":hashlib.sha256(Path(__file__).read_text(encoding="utf-8").encode()).hexdigest(),
                 "protocol_sha256":hashlib.sha256((ROOT.parent/"docs/BASKETBALL_EMPIRICAL_PROTOCOL.md").read_text(encoding="utf-8").encode()).hexdigest(),
                 "numpy_version":np.__version__}
    # Selection is written and hashed before evaluating later target seasons.
    write_json(root/"selection.json",selection)
    write_json(root/"selection-lock.json",{"sha256":digest(selection)})
    results = {}
    for year in TEST:
        model = fit(store,range(2020,year),alpha)
        results[str(year)] = {"model":model,"metrics":evaluate_rates(store,model,year,cfg["scoring"])}
    report = {"version":1,"selection_sha256":digest(selection),"selected_alpha":alpha,"test_years":results,
              "metric":"Conditional production error at a common 30-minute workload; not full draft performance",
              "fresh_independent_holdout":False,"comparison_only":True}
    write_json(root/"rate-backtest.json",report)
    current = fit(store,range(2020,cfg["season"]),alpha)
    saved={**current,"data_sha256":digest(manifest),"selection_sha256":digest(selection)}
    write_json(root/"model.json",saved)
    write_json(root/"model-lock.json",{"sha256":digest(saved)})
    return {"selected_alpha":alpha,"validation":candidates[str(alpha)],
            "test":{year:r["metrics"] for year,r in results.items()},"current_training_samples":current["training_samples"]}


def current_board(cfg):
    from .research_board import build
    build(cfg)  # Validate immutable input pack/captures before using opportunities.
    base = read_json(path(cfg,"research-board/rankings.json"))
    store,manifest = load_seasons(cfg)
    root = path(cfg,"research-empirical")
    model = read_json(root/"model.json")
    if not model or model["data_sha256"] != digest(manifest) or model["training_years"] != list(range(2020,cfg["season"])):
        raise ValueError("Fit the registered current statistical model first")
    selection = locked_selection(cfg,manifest)
    if (digest(selection) != model["selection_sha256"] or read_json(root/"model-lock.json",{}).get("sha256") != digest(model)):
        raise ValueError("Empirical model selection changed")
    identities = store.identities(cfg["season"])
    rows=[]
    for source in base["rows"]:
        row={k:source[k] for k in ("id","name","team","eligible","minutes","games","injury","injury_opportunity_cap",
                                  "ban","espn_rank","rotowire_rank","playing_time_sources","per_game","fpg","season_points")}
        nba=identities.get(key(row["name"]))
        if nba and store.prior_minutes(nba,cfg["season"]) >= 150:
            rates=predict(model,store.features(nba,cfg["season"]))
            row.update(per_game={k:v*row["minutes"] for k,v in rates.items()},nba_id=nba,
                       production_basis="Learned NBA game-log model",model_fallback=False)
            row["fpg"]=points(row["per_game"],cfg["scoring"])
            row["season_points"]=row["fpg"]*row["games"]
        else:
            row.update(nba_id=nba,production_basis="Existing comparison forecast; insufficient NBA history",model_fallback=True)
        row["comparison_model_rank"]=source["rank"]
        rows.append(row)
    rows.sort(key=lambda r:(-r["season_points"],r["id"]))
    pg={r["id"]:i for i,r in enumerate(sorted(rows,key=lambda r:(-r["fpg"],r["id"])),1)}
    personal=0
    for rank,row in enumerate(rows,1):
        row.update(rank=rank,per_game_rank=pg[row["id"]])
        if not row["ban"]:personal+=1
        row["personal_rank"]=None if row["ban"] else personal
    report={"version":1,"as_of":base["as_of"],"comparison_only":True,"model":model,"rows":rows,
            "rate_backtest":read_json(root/"rate-backtest.json"),"base_input_sha256":base["inputs_sha256"],
            "modeled_players":sum(not r["model_fallback"] for r in rows),"fallback_players":sum(r["model_fallback"] for r in rows)}
    write_json(root/"rankings.json",report)
    lines=["# Our data-trained basketball rankings","", "As of: "+report["as_of"],"",
           "Production is learned from historical NBA game logs. Games/minutes use current outside workload estimates and sourced injury caps. "
           "Rank is expected season points under your scoring; per-game rank is separate. This is comparison only and does not change live drafting. "
           "Totals omit replacement players and weekly lineup scheduling.","",
           f"Learned model: {report['modeled_players']} players. Clearly marked outside-projection fallback: {report['fallback_players']} players.","",
           "| Rank | Player | Team | Fpts/game | Games | Season pts | Per-game rank | RotoWire | ESPN | Notes |",
           "|---:|---|---|---:|---:|---:|---:|---:|---:|---|"]
    for row in rows:
        notes=[row["ban"]] if row["ban"] else []
        if row["injury"]:notes.append("Return estimate: "+(row["injury"]["expected_return"] or "unknown"))
        if row["model_fallback"]:notes.append(row["production_basis"])
        lines.append(f"| {row['rank']} | {row['name']} | {row['team']} | {row['fpg']:.1f} | {row['games']:.1f} | {row['season_points']:.0f} | {row['per_game_rank']} | {row['rotowire_rank'] or '—'} | {row['espn_rank'] or '—'} | {'; '.join(notes)} |")
    (root/"rankings.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    return {"ranked":len(rows),"modeled":report["modeled_players"],"fallbacks":report["fallback_players"],"board":str(root/"rankings.md")}
