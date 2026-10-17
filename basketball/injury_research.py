"""Chronological injury-history ablations; no live draft integration."""
from collections import defaultdict
import hashlib
import math
import random
import statistics

import numpy as np

from . import availability_research, empirical, injury_history, value_board
from .backtest import digest
from .config import ROOT, path, read_json, write_json
from .empirical_draft import anchored_order, score_roster, simulate, summarize

TRAIN = (2020, 2021)
VALIDATION = 2022
TEST = (2023, 2024, 2025)
ALPHAS = (.1, 1, 10, 100)
KINDS = ("base_games", "injury_games", "base_output", "injury_output")
PROTOCOL = ROOT.parent/"docs/BASKETBALL_INJURY_HISTORY_PROTOCOL.md"
FILES = ("injury_research.py", "injury_history.py", *availability_research.DEPENDENCIES)


class Research:
    def __init__(self, store, history, scoring):
        self.store, self.history, self.scoring = store, history, scoring
        self.cache = {}

    def frame(self, year):
        if year not in self.cache:
            rows = {}
            for pid in availability_research.candidates(self.store, year):
                projection = value_board.projection(self.store, pid, year, self.scoring)
                base = availability_research.features(self.store, pid, year)
                prior = [self.store.seasons.get(year-lag, {}).get(pid) for lag in (1, 2, 3)]
                fpg = [empirical.points(r["stats"], self.scoring)/r["games"] if r else 0 for r in prior]
                production = [projection["fpg"]/100, fpg[0]/100, fpg[1]/100]
                production += [projection["fpg"]*(r["game_share"] if r else 0)/100 for r in prior]
                rows[pid] = {"base": base, "output": base+production,
                             "injury": self.history.summary(self.store, pid, year), "projection": projection}
            self.cache[year] = rows
        return self.cache[year]

    def features(self, row, kind):
        values = row["output"] if kind.endswith("output") else row["base"]
        return values+row["injury"]["features"] if kind.startswith("injury") else values

    def actual(self, pid, year):
        row = self.store.seasons[year].get(pid)
        if not row:
            return {"games": 0, "points": 0}
        games = 82*row["game_share"]
        return {"games": games, "points": empirical.points(row["stats"], self.scoring)*games/row["games"]}

    def fit(self, years, alpha, kind):
        rows = [(year, pid, row) for year in years for pid, row in self.frame(year).items()]
        x = np.asarray([self.features(row, kind) for _, _, row in rows])
        target, scale_y = ("points", 1000) if kind.endswith("output") else ("games", 82)
        y = np.asarray([self.actual(pid, year)[target]/scale_y for year, pid, _ in rows])
        mean, scale = x.mean(axis=0), x.std(axis=0)
        scale[scale < 1e-9] = 1
        design = np.column_stack([np.ones(len(x)), (x-mean)/scale])
        penalty = np.eye(design.shape[1])*alpha
        penalty[0, 0] = 0
        coef = np.linalg.solve(design.T@design+penalty, design.T@y)
        return {"kind": kind, "alpha": alpha, "training_years": list(years), "training_samples": len(rows),
                "zero_target_samples": int(sum(y == 0)), "mean": mean.tolist(), "scale": scale.tolist(),
                "coefficients": coef.tolist(), "target": target, "target_scale": scale_y}

    def predict(self, model, row):
        x = np.r_[1, (np.asarray(self.features(row, model["kind"]))-model["mean"])/model["scale"]]
        value = float(x@np.asarray(model["coefficients"]))
        if model["target"] == "games":
            games = 82*min(1, max(0, value))
            return {"games": games, "points": games*row["projection"]["fpg"]}
        return {"games": None, "points": max(0, value*1000)}


def metrics(values):
    return {"players": len(values), "mae": statistics.mean(abs(x) for x in values),
            "rmse": math.sqrt(statistics.mean(x*x for x in values)), "bias": statistics.mean(values)} if values else None


def evaluate(research, predictions, year, cohort=None):
    result = {}
    for name, rows in predictions.items():
        errors = defaultdict(list)
        for pid, prediction in rows.items():
            if cohort is not None and pid not in cohort:
                continue
            actual = research.actual(pid, year)
            for target in ("games", "points"):
                if prediction[target] is not None:
                    errors[target].append(prediction[target]-actual[target])
        result[name] = {k: metrics(v) for k, v in errors.items()}
    return result


def select(research):
    scores, selected = {}, {}
    for kind in KINDS:
        candidates = {}
        for alpha in ALPHAS:
            model = research.fit(TRAIN, alpha, kind)
            predictions = {kind: {pid: research.predict(model, row) for pid, row in research.frame(VALIDATION).items()}}
            candidates[str(alpha)] = evaluate(research, predictions, VALIDATION)[kind]
        target = "points" if kind.endswith("output") else "games"
        selected[kind] = min(ALPHAS, key=lambda a: (candidates[str(a)][target]["rmse"], a))
        scores[kind] = candidates
    return {"training_years": list(TRAIN), "validation_year": VALIDATION, "selected": selected, "metrics": scores}


def forecast(research, year, models):
    predictions = {name: {pid: research.predict(model, row) for pid, row in research.frame(year).items()}
                   for name, model in models.items()}
    predictions["nhl_fixed"] = {pid: {"games": row["projection"]["games"], "points": row["projection"]["season_points"]}
                                for pid, row in research.frame(year).items()}
    return predictions


def prepare(cfg, research, year, predictions):
    data = value_board.prepare(cfg, research.store, year, path(cfg, "ranking-library"))
    policies = {k: v for k, v in data["policies"].items() if not k.startswith("nhl_")}
    for kind in KINDS:
        rows = [{**row, "season_points": predictions[kind][data["mapping"][row["id"]]]["points"]}
                for row in data["projections"]]
        levels = value_board.replacement_levels(rows, cfg)
        value_board.attach_value(rows, levels)
        order = anchored_order(data["market"], {r["id"]: r["vor"] for r in rows})
        policies[kind] = order
        policies[kind+"_next_turn"] = order
    return {**data, "policies": policies}


def associations(research, years, top_cohorts):
    groups = defaultdict(list)
    for year in years:
        for pid, row in research.frame(year).items():
            history = row["injury"]
            count = history["episodes"]
            group = "0" if count == 0 else "1–2" if count <= 2 else "3–5" if count <= 5 else "6+"
            actual = research.actual(pid, year)
            result = {**actual, "prior_fpg": row["projection"]["fpg"]}
            for cohort in ("all", "espn_top100"):
                if cohort == "espn_top100" and pid not in top_cohorts[year]:
                    continue
                groups[(cohort, "episode_count", group)].append(result)
                groups[(cohort, "severe_history", str(history["severe"]))].append(result)
    return [{"cohort": k[0], "feature": k[1], "group": k[2], "player_seasons": len(rows),
             "mean_next_games": statistics.mean(r["games"] for r in rows),
             "under50_frequency": statistics.mean(r["games"] < 50 for r in rows),
             "mean_next_points": statistics.mean(r["points"] for r in rows),
             "mean_prior_fpg": statistics.mean(r["prior_fpg"] for r in rows)} for k, rows in sorted(groups.items())]


def fingerprints(manifest, injuries):
    return {"data_sha256": digest(manifest), "injury_manifest": injuries, "numpy_version": np.__version__,
            "protocol_sha256": hashlib.sha256(PROTOCOL.read_text(encoding="utf-8").encode()).hexdigest(),
            "code_sha256": {file: hashlib.sha256((ROOT/file).read_text(encoding="utf-8").encode()).hexdigest() for file in FILES}}


def experiment(cfg):
    store, manifest = empirical.load_seasons(cfg)
    history, injuries = injury_history.load(cfg)
    research = Research(store, history, cfg["scoring"])
    root = path(cfg, "research-injury")
    selection = {**select(research), **fingerprints(manifest, injuries), "scoring": cfg["scoring"]}
    write_json(root/"selection.json", selection)
    write_json(root/"selection-lock.json", {"sha256": digest(selection)})
    prepared, forecasts, models, decisions = {}, {}, {}, []
    for year in TEST:
        models[str(year)] = fitted = {kind: research.fit(range(2020, year), selection["selected"][kind], kind) for kind in KINDS}
        forecasts[year] = forecast(research, year, fitted)
        prepared[year] = data = prepare(cfg, research, year, forecasts[year])
        ordinal = {pid: i for i, pid in enumerate(data["market"])}
        for seed in (-1, 0, 1):
            opponents = {}
            for team in range(1, cfg["teams"]+1):
                rng = random.Random(f"empirical-v1:{year}:{seed}:{team}")
                noise = {pid: rng.gauss(0, 12) if seed >= 0 else 0 for pid in data["market"]}
                opponents[team] = sorted(data["market"], key=lambda pid: (ordinal[pid]+noise[pid], pid))
            for slot in range(1, cfg["teams"]+1):
                for policy, order in data["policies"].items():
                    roster, trace = simulate(data["model"], slot, order, opponents, data["market"], data["legal"],
                                             policy.endswith("next_turn"))
                    decisions.append({"season": year, "seed": seed, "slot": slot, "policy": policy,
                                      "roster": roster, "trace": trace,
                                      "modeled_pick_share": sum(pid in data["modeled"] for pid in roster)/len(roster)})
            print(f"Completed injury-history comparison: {year}, seed {seed}", flush=True)
    evidence = {**fingerprints(manifest, injuries), "selection_sha256": digest(selection), "models": models,
                "feature_names": injury_history.FEATURE_NAMES, "forecasts": forecasts,
                "preseason_inputs": {str(y): d["input_sha256"] for y, d in prepared.items()},
                "config": {k: cfg[k] for k in ("teams", "slots", "position_limits", "scoring")}, "decisions": decisions}
    write_json(root/"decisions.json", evidence)
    write_json(root/"decisions-lock.json", {"sha256": digest(evidence)})
    locked = read_json(root/"decisions.json")
    if digest(locked) != read_json(root/"decisions-lock.json")["sha256"]:
        raise ValueError("Injury model evidence changed")
    results = []
    for row in locked["decisions"]:
        data = prepared[row["season"]]
        results.append({**{k: v for k, v in row.items() if k not in {"roster", "trace"}},
                        **score_roster(row["roster"], data["model"], store, row["season"], data["mapping"])})
    top = {year: {data["mapping"][pid] for pid in data["market"][:100] if pid in data["mapping"]}
           for year, data in prepared.items()}
    prior = read_json(path(cfg, "research-value/backtest.json"))
    if prior:
        prior_cases = {(r["season"], r["seed"], r["slot"], r["policy"]): r["total_points"] for r in prior["cases"]}
        for row in results:
            identity = tuple(row[k] for k in ("season", "seed", "slot", "policy"))
            if identity in prior_cases and prior_cases[identity] != row["total_points"]:
                raise ValueError("Repeated historical control differs")
    report = {"version": 1, "comparison_only": True, "independent_holdout": False,
              "selection_sha256": digest(selection), "decision_sha256": digest(locked),
              "selected": selection["selected"], "summaries": summarize(results), "cases": results,
              "prediction_metrics": {str(y): {"all": evaluate(research, forecasts[y], y),
                                             "espn_top100": evaluate(research, forecasts[y], y, top[y])} for y in TEST},
              "associations": associations(research, TEST, top),
              "injury_audit": {str(y): history.snapshot(store, y)[2] for y in range(2020, 2026)},
              "feature_coverage": {str(y): {"candidates": len(research.frame(y)),
                                            "with_prior_episodes": sum(r["injury"]["episodes"] > 0 for r in research.frame(y).values())}
                                   for y in TEST}, "archive_coverage_end": injuries["coverage_end"]}
    write_json(root/"backtest.json", report)
    return {k: v for k, v in report.items() if k not in {"cases", "associations", "injury_audit"}}
