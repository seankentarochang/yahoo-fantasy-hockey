"""Injury-aware box-score/minutes forecasts, evaluated before draft selection."""
from collections import defaultdict
import hashlib
import math
import statistics

import numpy as np

from . import empirical, injury_history, injury_research, value_board
from .backtest import digest
from .config import ROOT, path, read_json, write_json

TRAIN = (2020, 2021)
VALIDATION = 2022
TEST = (2023, 2024, 2025)
ALPHAS = (.1, 1, 10, 100)
POLICIES = {"statistical": (False, False), "injury_availability": (False, True),
            "injury_production": (True, False), "injury_full": (True, True)}
PROTOCOL = ROOT.parent/"docs/BASKETBALL_INJURY_SCORING_PROTOCOL.md"
FILES = ("injury_scoring.py", *injury_research.FILES)


def locked_games(cfg, manifest, injuries):
    root = path(cfg, "research-injury")
    selection = read_json(root/"selection.json", {})
    evidence = read_json(root/"decisions.json", {})
    if (not selection or not evidence
            or digest(selection) != read_json(root/"selection-lock.json", {}).get("sha256")
            or digest(evidence) != read_json(root/"decisions-lock.json", {}).get("sha256")
            or evidence.get("selection_sha256") != digest(selection)):
        raise ValueError("Run and lock the injury-history experiment first")
    fingerprints = injury_research.fingerprints(manifest, injuries)
    if any(selection.get(k) != v or evidence.get(k) != v for k, v in fingerprints.items()):
        raise ValueError("Injury-history inputs, source, code or protocol changed")
    expected = {k: cfg[k] for k in ("teams", "slots", "position_limits", "scoring")}
    if selection.get("scoring") != cfg["scoring"] or evidence.get("config") != expected:
        raise ValueError("Frozen games experiment configuration changed")
    return evidence


class Production:
    def __init__(self, store, history, scoring):
        self.store, self.scoring = store, scoring
        self.research = injury_research.Research(store, history, scoring)
        self._samples = {}

    def features(self, pid, year, injury=False):
        row = self.research.frame(year)[pid]
        return self.store.features(pid, year) + (row["injury"]["features"] if injury else [])

    def samples(self, year):
        if year not in self._samples:
            candidates = self.research.frame(year)
            self._samples[year] = [(pid, components, target) for pid, _, components, target in self.store.samples(year)
                                   if pid in candidates]
        return self._samples[year]

    def fit(self, years, alpha, injury, target):
        if target not in {"rates", "minutes"}:
            raise ValueError("Unknown scoring model component")
        rows = [(year, pid, components, actual) for year in years for pid, components, actual in self.samples(year)]
        if not rows:
            raise ValueError("No conditional production training samples")
        x = np.asarray([self.features(pid, year, injury) for year, pid, _, _ in rows])
        y = np.asarray([components if target == "rates" else actual["minutes"]/actual["games"]/48
                        for _, _, components, actual in rows])
        weights = np.asarray([max(.25, min(1, self.store.prior_minutes(pid, year)/2000)) for year, pid, _, _ in rows])
        mean = np.average(x, axis=0, weights=weights)
        scale = np.sqrt(np.average((x-mean)**2, axis=0, weights=weights))
        scale[scale < 1e-9] = 1
        design = np.column_stack([np.ones(len(x)), (x-mean)/scale])
        penalty = np.eye(design.shape[1])*alpha
        penalty[0, 0] = 0
        weighted_target = y*weights[:, None] if y.ndim == 2 else y*weights
        coef = np.linalg.solve(design.T@(design*weights[:, None])+penalty, design.T@weighted_target)
        return {"target": target, "injury": injury, "alpha": alpha, "training_years": list(years),
                "training_samples": len(rows), "mean": mean.tolist(), "scale": scale.tolist(),
                "coefficients": coef.tolist()}

    def predict(self, model, pid, year):
        if max(model["training_years"]) >= year:
            raise ValueError("Production training overlaps its forecast season")
        x = np.r_[1, (np.asarray(self.features(pid, year, model["injury"]))-model["mean"])/model["scale"]]
        value = x@np.asarray(model["coefficients"])
        return empirical.box_score(value) if model["target"] == "rates" else 48*float(np.clip(value, 0, 1))


def metrics(errors):
    return {"players": len(errors), "mae": statistics.mean(abs(x) for x in errors),
            "rmse": math.sqrt(statistics.mean(x*x for x in errors)), "bias": statistics.mean(errors)} if errors else None


def validate_component(production, model, year):
    errors = []
    for pid, _, target in production.samples(year):
        prediction = production.predict(model, pid, year)
        if model["target"] == "rates":
            actual = empirical.points(target["stats"], production.scoring)/target["minutes"]
            errors.append(30*(empirical.points(prediction, production.scoring)-actual))
        else:
            errors.append(prediction-target["minutes"]/target["games"])
    return metrics(errors)


def select(production):
    selections, results = {}, {}
    for injury in (False, True):
        for target in ("rates", "minutes"):
            name = ("injury_" if injury else "base_")+target
            scores = {str(a): validate_component(production, production.fit(TRAIN, a, injury, target), VALIDATION)
                      for a in ALPHAS}
            selections[name] = min(ALPHAS, key=lambda a: (scores[str(a)]["rmse"], a))
            results[name] = scores
    return {"training_years": list(TRAIN), "validation_year": VALIDATION, "selected": selections, "metrics": results}


def score_line(rates, minutes, games, scoring):
    if (not math.isfinite(minutes) or not 0 <= minutes <= 48
            or not math.isfinite(games) or not 0 <= games <= 82):
        raise ValueError("Invalid projected workload")
    per_game = {k: v*minutes for k, v in rates.items()}
    fpg = empirical.points(per_game, scoring)
    return {"per_minute": rates, "per_game": per_game, "minutes": minutes, "games": games,
            "fpg": fpg, "season_points": fpg*games}


def forecast(production, year, selected, prior):
    candidates = production.research.frame(year)
    locked = prior["forecasts"][str(year)]
    if any(set(locked[name]) != set(candidates) for name in ("base_games", "injury_games")):
        raise ValueError("Frozen games candidates differ from the scoring cohort")
    models = {}
    for injury in (False, True):
        for target in ("rates", "minutes"):
            name = ("injury_" if injury else "base_")+target
            models[name] = production.fit(range(2020, year), selected[name], injury, target)
    predictions = {name: {} for name in (*POLICIES, "nhl_fixed")}
    for pid, row in candidates.items():
        rates = {injury: production.predict(models[("injury_" if injury else "base_")+"rates"], pid, year)
                 for injury in (False, True)}
        minutes = {injury: production.predict(models[("injury_" if injury else "base_")+"minutes"], pid, year)
                   for injury in (False, True)}
        for name, (production_injury, games_injury) in POLICIES.items():
            games = locked["injury_games" if games_injury else "base_games"][pid]["games"]
            predictions[name][pid] = score_line(rates[production_injury], minutes[production_injury], games, production.scoring)
        baseline = row["projection"]
        predictions["nhl_fixed"][pid] = {**{k: baseline[k] for k in ("per_game", "fpg", "games", "season_points")},
                                          "minutes": None, "per_minute": None}
    return models, predictions


def collect_errors(production, predictions, year, cohort=None):
    result = {}
    for name, rows in predictions.items():
        errors = defaultdict(list)
        counts = {"candidates": 0, "zero_games": 0, "played": 0, "played20": 0, "rate_diagnostic": 0}
        for pid, prediction in rows.items():
            if cohort is not None and pid not in cohort:
                continue
            counts["candidates"] += 1
            actual = production.store.seasons[year].get(pid)
            normalized = production.research.actual(pid, year)
            errors["season_points"].append(prediction["season_points"]-normalized["points"])
            errors["games"].append(prediction["games"]-normalized["games"])
            if not actual:
                counts["zero_games"] += 1
                errors["zero_game_projected_points"].append(prediction["season_points"])
                continue
            counts["played"] += 1
            fpg = empirical.points(actual["stats"], production.scoring)/actual["games"]
            errors["per_game"].append(prediction["fpg"]-fpg)
            if actual["games"] >= 20:
                counts["played20"] += 1
                errors["per_game_20plus"].append(prediction["fpg"]-fpg)
            if prediction["minutes"] is not None:
                errors["minutes"].append(prediction["minutes"]-actual["minutes"]/actual["games"])
            for field in empirical.FIELDS:
                errors["stat_"+field].append(prediction["per_game"][field]-actual["stats"][field]/actual["games"])
            if prediction["per_minute"] is not None and actual["minutes"] >= 100:
                counts["rate_diagnostic"] += 1
                actual_rate = empirical.points(actual["stats"], production.scoring)/actual["minutes"]
                errors["rate_at30"].append(30*(empirical.points(prediction["per_minute"], production.scoring)-actual_rate))
        result[name] = {"counts": counts, "errors": dict(errors)}
    return result


def summarize(errors):
    return {name: {"counts": row["counts"], "metrics": {target: metrics(values) for target, values in row["errors"].items()}}
            for name, row in errors.items()}


def pooled(by_year):
    combined = {}
    for policies in by_year.values():
        for name, row in policies.items():
            result = combined.setdefault(name, {"counts": defaultdict(int), "errors": defaultdict(list)})
            for k, v in row["counts"].items():
                result["counts"][k] += v
            for k, values in row["errors"].items():
                result["errors"][k].extend(values)
    return summarize(combined)


def fingerprints(manifest, injuries):
    return {"data_sha256": digest(manifest), "injury_manifest": injuries, "numpy_version": np.__version__,
            "protocol_sha256": hashlib.sha256(PROTOCOL.read_text(encoding="utf-8").encode()).hexdigest(),
            "code_sha256": {file: hashlib.sha256((ROOT/file).read_text(encoding="utf-8").encode()).hexdigest() for file in FILES}}


def experiment(cfg):
    store, manifest = empirical.load_seasons(cfg)
    history, injuries = injury_history.load(cfg)
    prior = locked_games(cfg, manifest, injuries)
    production = Production(store, history, cfg["scoring"])
    root = path(cfg, "research-injury-scoring")
    selection = {**select(production), **fingerprints(manifest, injuries), "scoring": cfg["scoring"],
                 "games_evidence_sha256": digest(prior)}
    write_json(root/"selection.json", selection)
    write_json(root/"selection-lock.json", {"sha256": digest(selection)})
    forecasts, models, preseason, top = {}, {}, {}, {}
    for year in TEST:
        models[str(year)], forecasts[str(year)] = forecast(production, year, selection["selected"], prior)
        data = value_board.prepare(cfg, store, year, path(cfg, "ranking-library"))
        top[year] = {data["mapping"][pid] for pid in data["market"][:100] if pid in data["mapping"]}
        preseason[str(year)] = data["input_sha256"]
        print(f"Locked scoring inputs prepared for {year}: {len(production.research.frame(year))} candidates", flush=True)
    evidence = {**fingerprints(manifest, injuries), "selection_sha256": digest(selection),
                "games_evidence_sha256": digest(prior), "scoring": cfg["scoring"], "models": models,
                "preseason_inputs": preseason, "top100_ids": {str(y): sorted(pids) for y, pids in top.items()},
                "predictions": forecasts}
    write_json(root/"predictions.json", evidence)
    write_json(root/"predictions-lock.json", {"sha256": digest(evidence)})
    locked = read_json(root/"predictions.json")
    if digest(locked) != read_json(root/"predictions-lock.json")["sha256"]:
        raise ValueError("Scoring predictions changed before evaluation")
    all_errors = {str(y): collect_errors(production, locked["predictions"][str(y)], y) for y in TEST}
    top_errors = {str(y): collect_errors(production, locked["predictions"][str(y)], y, top[y]) for y in TEST}
    report = {"version": 1, "comparison_only": True, "independent_holdout": False,
              "selected": selection["selected"], "selection_sha256": digest(selection), "prediction_sha256": digest(locked),
              "games_evidence_sha256": digest(prior), "scoring": cfg["scoring"],
              "annual": {y: {"all": summarize(rows), "espn_top100": summarize(top_errors[y])} for y, rows in all_errors.items()},
              "pooled": {"all": pooled(all_errors), "espn_top100": pooled(top_errors)},
              "injury_coverage_end": injuries["coverage_end"],
              "metrics_note": "Season points include zero appearances; per-game/rate errors condition on played games. No draft or H2H result."}
    write_json(root/"backtest.json", report)
    return {k: v for k, v in report.items() if k != "annual"}
