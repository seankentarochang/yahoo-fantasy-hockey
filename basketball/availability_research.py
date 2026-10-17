"""Comparison-only workload models, including players who leave the league."""
import hashlib
import math
import random
import statistics

import numpy as np

from . import empirical, value_board
from .backtest import digest
from .config import ROOT, path, read_json, write_json
from .empirical_draft import anchored_order, score_roster, simulate, summarize
from .ranking_library import checked_board
from .strategy_lab import key, nbc_data

ALPHAS = (.1, 1, 10, 100)
TRAIN = tuple(range(2020, 2024))
VALIDATION = 2024
TEST = (2025, 2026)
PROTOCOL = ROOT.parent / "docs/BASKETBALL_AVAILABILITY_PROTOCOL.md"
DEPENDENCIES = ("availability_research.py", "value_board.py", "empirical.py", "empirical_draft.py",
                "planner.py", "source_backtest.py", "ranking_library.py", "config.py",
                "strategy_lab.py", "backtest.py", "model.py", "research_board.py")


def fingerprint(manifest):
    return {"data_sha256": digest(manifest), "numpy_version": np.__version__,
            "protocol_sha256": hashlib.sha256(PROTOCOL.read_text(encoding="utf-8").encode()).hexdigest(),
            "code_sha256": {name: hashlib.sha256((ROOT/name).read_text(encoding="utf-8").encode()).hexdigest()
                            for name in DEPENDENCIES}}


def debut(store, pid, year):
    return min(y for y, players in store.seasons.items() if y < year and pid in players)


def features(store, pid, year):
    first = debut(store, pid, year)
    result = []
    for lag in (1, 2, 3):
        row = store.seasons.get(year-lag, {}).get(pid)
        result.extend([row["game_share"] if row else 0,
                       row["minutes"]/row["games"]/48 if row else 0,
                       int(row is not None), int(year-lag >= first)])
    return result + [min(3, year-first)/3]


def candidates(store, year):
    prior = set().union(*(store.seasons.get(year-lag, {}) for lag in (1, 2)))
    return sorted(pid for pid in prior if sum(store.seasons.get(year-lag, {}).get(pid, {}).get("games", 0)
                                              for lag in (1, 2)) >= 20)


def no_floor_games(store, pid, year):
    first = debut(store, pid, year)
    values = [(w, store.seasons.get(year-lag, {}).get(pid, {}).get("game_share", 0))
              for lag, w in ((1, .8), (2, .2)) if year-lag >= first]
    return 82*sum(w*share for w, share in values)/sum(w for w, _ in values)


def fit(store, years, alpha):
    rows = [(year, pid) for year in years for pid in candidates(store, year)]
    if not rows:
        raise ValueError("No availability training candidates")
    x = np.asarray([features(store, pid, year) for year, pid in rows])
    # No target-season row is a zero label, never a reason to drop a player.
    y = np.asarray([store.seasons[year].get(pid, {}).get("game_share", 0) for year, pid in rows])
    mean, scale = x.mean(axis=0), x.std(axis=0)
    scale[scale < 1e-9] = 1
    design = np.column_stack([np.ones(len(x)), (x-mean)/scale])
    penalty = np.eye(design.shape[1])*alpha
    penalty[0, 0] = 0
    coef = np.linalg.solve(design.T@design+penalty, design.T@y)
    return {"training_years": list(years), "training_samples": len(rows),
            "zero_target_samples": int(sum(y == 0)), "alpha": alpha,
            "mean": mean.tolist(), "scale": scale.tolist(), "coefficients": coef.tolist()}


def predict(model, values):
    x = np.r_[1, (np.asarray(values)-model["mean"])/model["scale"]]
    return 82*float(np.clip(x@np.asarray(model["coefficients"]), 0, 1))


def errors(values):
    return {"players": len(values), "mae_games": statistics.mean(abs(v) for v in values),
            "rmse_games": math.sqrt(statistics.mean(v*v for v in values)),
            "bias_games": statistics.mean(values)} if values else None


def evaluate(store, model, year):
    groups = {name: {"all": [], "zero": [], "nonzero": []}
              for name in ("nhl_floor", "no_floor", "learned")}
    for pid in candidates(store, year):
        actual = 82*store.seasons[year].get(pid, {}).get("game_share", 0)
        old = value_board.projection(store, pid, year, {})
        forecasts = {"nhl_floor": old["games"], "no_floor": no_floor_games(store, pid, year),
                     "learned": predict(model, features(store, pid, year))}
        for name, forecast in forecasts.items():
            error = forecast-actual
            groups[name]["all"].append(error)
            groups[name]["nonzero" if actual else "zero"].append(error)
    return {name: {group: errors(values) for group, values in split.items()} for name, split in groups.items()}


def forecast_games(forecast):
    if "G" in forecast:
        games = forecast["G"]
    elif forecast.get("FP/G", 0) > 0 and "FP" in forecast:
        games = forecast["FP"]/forecast["FP/G"]
    else:
        return None
    if not math.isfinite(games) or not 0 <= games <= 82.2:
        raise ValueError("Invalid dated games projection")
    return min(82, games)


def dated_games(library, year):
    records = {}
    evidence = []
    ids = ("rotoworld-2025", "rotowire-2025") if year == 2025 else ("rotowire-2026",)
    for source_id in ids:
        board = read_json(library/"boards"/(source_id+".json"))
        checked_board(library, board)
        if board["status"] != "preseason" or board["source"]["season"] != year:
            raise ValueError("Games forecast is not eligible preseason data")
        evidence.append({"id": source_id, "sha256": board["sha256"], "dates": board["date_evidence"],
                         "url": board["source"]["url"]})
        family = board["source"]["family"]
        if source_id == "rotoworld-2025":
            import pdfplumber
            with pdfplumber.open(library/"raw"/(source_id+".pdf")) as pdf:
                projections, _ = nbc_data(pdf)
            rows = [(name, p["GP"]) for name, p in projections.items()]
        else:
            rows = [(key(r["name"]), forecast_games(r.get("forecast", {}))) for r in board["rows"]]
        seen = set()
        for name, games in rows:
            if name in seen:
                raise ValueError("Ambiguous dated forecast name")
            seen.add(name)
            if games is not None:
                if not math.isfinite(games) or not 0 <= games <= 82:
                    raise ValueError("Invalid dated games projection")
                records.setdefault(name, {})[family] = games
    return {name: {"games": statistics.mean(rows.values()), "sources": rows}
            for name, rows in records.items()}, evidence


def order_for(data, rows, cfg):
    levels = value_board.replacement_levels(rows, cfg)
    value_board.attach_value(rows, levels)
    return anchored_order(data["market"], {r["id"]: r["vor"] for r in rows}), levels


def with_games(row, games):
    return {**row, "games": games, "season_points": row["fpg"]*games}


def prepare(cfg, store, year, model):
    library = path(cfg, "ranking-library")
    data = value_board.prepare(cfg, store, year, library)
    outside, evidence = dated_games(library, year)
    forecasts = []
    for row in data["projections"]:
        pid, nba = row["id"], data["mapping"][row["id"]]
        source = outside.get(key(data["model"].by_id[pid]["name"]))
        forecasts.append({**row, "no_floor_games": no_floor_games(store, nba, year),
                          "learned_games": predict(model, features(store, nba, year)), "dated": source})
    policies = {k: v for k, v in data["policies"].items() if k != "nhl_total"}
    pools = {}
    for name, field, covered in (("no_floor_vor", "no_floor_games", False),
                                 ("availability_vor", "learned_games", False),
                                 ("coverage_guard_vor", "learned_games", True),
                                 ("dated_games_vor", "dated", True)):
        rows = [with_games(r, r["dated"]["games"] if field == "dated" else r[field])
                for r in forecasts if not covered or r["dated"] is not None]
        if not rows:
            raise ValueError("No usable availability projections")
        policies[name], pools[name] = order_for(data, rows, cfg)
    policies["availability_next_turn"] = policies["availability_vor"]
    policies["dated_games_next_turn"] = policies["dated_games_vor"]
    return {**data, "policies": policies, "forecasts": forecasts, "source_evidence": evidence,
            "replacement_pools": pools, "dated_coverage": sum(r["dated"] is not None for r in forecasts)}


def experiment(cfg):
    store, manifest = empirical.load_seasons(cfg)
    root = path(cfg, "research-availability")
    candidates_metrics = {}
    for alpha in ALPHAS:
        candidates_metrics[str(alpha)] = evaluate(store, fit(store, TRAIN, alpha), VALIDATION)
    alpha = min(ALPHAS, key=lambda a: (candidates_metrics[str(a)]["learned"]["all"]["rmse_games"], a))
    selection = {**fingerprint(manifest), "selected_alpha": alpha, "validation": candidates_metrics,
                 "training_years": list(TRAIN), "validation_year": VALIDATION}
    write_json(root/"selection.json", selection)
    write_json(root/"selection-lock.json", {"sha256": digest(selection)})
    prepared, models, decisions = {}, {}, []
    for year in TEST:
        models[str(year)] = model = fit(store, range(2020, year), alpha)
        prepared[year] = data = prepare(cfg, store, year, model)
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
            print(f"Completed availability comparison: {year}, seed {seed}", flush=True)
    evidence = {**fingerprint(manifest), "selection_sha256": digest(selection), "models": models,
                "preseason": {str(y): {k: d[k] for k in ("input_sha256", "forecasts", "source_evidence",
                                                         "replacement_pools", "dated_coverage")} for y, d in prepared.items()},
                "config": {k: cfg[k] for k in ("teams", "slots", "position_limits", "scoring")},
                "decisions": decisions}
    write_json(root/"decisions.json", evidence)
    write_json(root/"decisions-lock.json", {"sha256": digest(evidence)})
    locked = read_json(root/"decisions.json")
    if digest(locked) != read_json(root/"decisions-lock.json")["sha256"]:
        raise ValueError("Availability draft evidence changed")
    results = []
    for row in locked["decisions"]:
        data = prepared[row["season"]]
        results.append({**{k: v for k, v in row.items() if k not in {"roster", "trace"}},
                        **score_roster(row["roster"], data["model"], store, row["season"], data["mapping"])})
    report = {"version": 1, "comparison_only": True, "independent_holdout": False,
              "decision_sha256": digest(locked), "selection_sha256": digest(selection),
              "selected_alpha": alpha, "summaries": summarize(results), "cases": results,
              "games_metrics": {str(y): evaluate(store, models[str(y)], y) for y in TEST},
              "coverage": {str(y): {"modeled": len(d["forecasts"]), "dated": d["dated_coverage"]}
                           for y, d in prepared.items()}}
    write_json(root/"backtest.json", report)
    current = {**fit(store, range(2020, cfg["season"]), alpha), **fingerprint(manifest),
               "selection_sha256": digest(selection), "target_season": cfg["season"]}
    write_json(root/"model.json", current)
    write_json(root/"model-lock.json", {"sha256": digest(current)})
    return {k: v for k, v in report.items() if k != "cases"}


def locked_model(cfg, manifest):
    root = path(cfg, "research-availability")
    model = read_json(root/"model.json", {})
    selection = read_json(root/"selection.json", {})
    if (not model or digest(model) != read_json(root/"model-lock.json", {}).get("sha256")
            or digest(selection) != read_json(root/"selection-lock.json", {}).get("sha256")
            or model.get("selection_sha256") != digest(selection)
            or model.get("target_season") != cfg["season"]
            or any(model.get(k) != v or selection.get(k) != v for k, v in fingerprint(manifest).items())):
        raise ValueError("Availability evidence changed; rerun the comparison explicitly")
    return model


def forward_games(player, public=None, opportunities=None, season=None):
    sources = {}
    for split in player.get("splits", []):
        if split.get("season") == season and split.get("source") == 1 and "GP" in split.get("stats", {}):
            if "ESPN" in sources:
                raise ValueError("Ambiguous forward games projection")
            sources["ESPN"] = split["stats"]["GP"]
    for family, row in (("Hashtag", public), ("FantasyPros", opportunities)):
        if row:
            sources[family] = row["games"]
    if any(type(v) not in (int, float) or not math.isfinite(v) or not 0 <= v <= 82 for v in sources.values()):
        raise ValueError("Invalid forward games projection")
    return sources


def current(cfg):
    from .research_board import build, match_outside
    build(cfg)
    base = read_json(path(cfg, "research-board/rankings.json"))
    inputs = read_json(path(cfg, "research-board/inputs.json"))
    store, manifest = empirical.load_seasons(cfg)
    model = locked_model(cfg, manifest)
    public, _ = match_outside(inputs["public_projections"], inputs, True)
    opportunities, _ = match_outside(inputs["fantasypros_opportunities"], inputs, True)
    players = {p["id"]: p for p in inputs["snapshot"]["players"]}
    names = store.identities(cfg["season"])
    rows, excluded = [], []
    for source in base["rows"]:
        pid = source["id"]
        nba = names.get(key(source["name"]))
        production = value_board.projection(store, nba, cfg["season"], cfg["scoring"]) if nba else None
        statistical_games = predict(model, features(store, nba, cfg["season"])) if production else None
        forecasts = forward_games(players[pid], public.get(pid), opportunities.get(pid), cfg["season"])
        games = statistics.mean(forecasts.values()) if forecasts else statistical_games
        if games is None:
            raise ValueError("No forward or modeled availability forecast")
        cap = source["injury_opportunity_cap"]
        if cap is not None:
            games = min(games, cap)
        if games <= 0:
            excluded.append({"id": pid, "name": source["name"], "reason": "Zero expected games"})
            continue
        old = production or {k: source[k] for k in ("fpg", "per_game", "games", "season_points")}
        rows.append({**{k: source[k] for k in ("id", "name", "team", "eligible", "injury", "ban",
                                               "espn_rank", "rotowire_rank", "flags")},
                     **with_games(old, games), "primary": players[pid]["primary"], "model_fallback": production is None,
                     "learned_games": statistical_games, "forward_games": forecasts,
                     "old_floor_games": production["games"] if production else None,
                     "injury_opportunity_cap": cap})
    levels = value_board.replacement_levels([r for r in rows if not r["model_fallback"]], cfg)
    value_board.attach_value(rows, levels)
    rows.sort(key=lambda r: (-r["vor"], r["id"]))
    personal = 0
    for rank, row in enumerate(rows, 1):
        row["rank"] = rank
        if not row["ban"]:
            personal += 1
        row["personal_rank"] = None if row["ban"] else personal
    report = {"version": 1, "comparison_only": True, "as_of": base["as_of"], "model_sha256": digest(model),
              "inputs_sha256": base["inputs_sha256"], "replacement": levels, "rows": rows, "excluded": excluded}
    root = path(cfg, "research-availability")
    write_json(root/"rankings.json", report)
    lines = ["# Availability-normalized board — comparison only", "", "As of: "+base["as_of"], "",
             "Fixed NHL-style production; forward GP replaces historical games, with sourced return-date caps. "
             "Learned GP is the fallback. Unknown returns remain flagged. No live strategy changes.", "",
             "| Rank | Player | Fpts/game | GP | Learned GP | Old floor GP | Sources | Notes |",
             "|---:|---|---:|---:|---:|---:|---|---|"]
    for r in rows:
        learned = f"{r['learned_games']:.1f}" if r["learned_games"] is not None else "—"
        old = f"{r['old_floor_games']:.1f}" if r["old_floor_games"] is not None else "—"
        notes = ([r["ban"]] if r["ban"] else []) + r["flags"]
        if r["injury"]:
            notes.append("Return: "+(r["injury"]["expected_return"] or "unknown"))
        if r["model_fallback"]:
            notes.append("Existing comparison production fallback")
        lines.append(f"| {r['rank']} | {r['name']} | {r['fpg']:.1f} | {r['games']:.1f} | {learned} | {old} | "
                     f"{', '.join(r['forward_games']) or 'Learned historical'} | {'; '.join(notes)} |")
    (root/"rankings.md").write_text("\n".join(lines)+"\n", encoding="utf-8")
    return {"ranked": len(rows), "board": str(root/"rankings.md"), "comparison_only": True}
