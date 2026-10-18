"""Paired, comparison-only RotoWire timing and core-position scarcity mocks."""
from collections import defaultdict
from functools import lru_cache
import hashlib
import statistics

from . import adp_mocks
from .backtest import digest
from .config import ROOT, active_slots, path, read_json, roster_size, write_json
from .draft_advisor import orders
from .planner import assign, legal_roster

CORE = ("PG", "SG", "SF", "PF", "C")
POLICIES = {"greedy": (None, False), "current": (0, False), "buffer4": (4, False),
            "buffer8": (8, False), "scarcity3": (0, True), "buffer4_scarcity3": (4, True)}
PROTOCOL = ROOT.parent / "docs/BASKETBALL_TIMING_LAB_PROTOCOL.md"
FILES = ("timing_lab.py", "adp_mocks.py", "draft_advisor.py", "draft_timing.py", "model.py", "planner.py",
         "espn.py", "config.py", "injury_returns.py", "bans.py", "ranking_library.py", "live_rankings.py")


def weighted_coverage(players, weights):
    """Exact matching of distinct players to distinct core slots, at most 32 masks."""
    possible = {0}
    for player in players:
        expanded = set(possible)
        for mask in possible:
            for i, slot in enumerate(CORE):
                if not mask & (1 << i) and slot in player["eligible"]:
                    expanded.add(mask | (1 << i))
        possible = expanded
    return max(sum(weights[i] for i in range(len(CORE)) if mask & (1 << i)) for mask in possible)


def prepare(cfg):
    data = adp_mocks.prepare(cfg)
    quality, market, published, details = orders(data["model"], "rotowire", path(cfg, "ranking-library"))
    model = data["model"]
    active = active_slots(cfg)

    @lru_cache(maxsize=200000)
    def legal(roster, pid):
        ps = [model.by_id[p] for p in (*roster, pid)]
        return legal_roster(ps, cfg) and len(active) - len(assign(ps, active)) <= roster_size(cfg) - len(ps)

    return {**data, "quality": [pid for pid in quality if pid in data["rounds"]],
            "quality_rank": {pid: i+1 for i, pid in enumerate(quality)}, "espn_market": market,
            "rw_ranks": published["rotowire"], "sources": details, "legal": legal}


def choose(data, roster, gone, rnd, gap, policy):
    buffer, scarcity = POLICIES[policy]
    legal = data["legal"]
    available = [pid for pid in data["quality"] if pid not in gone and pid not in data["bans"]
                 and data["rounds"][pid] <= rnd]
    roster_key = tuple(sorted(roster))
    best_available = next((pid for pid in available if legal(roster_key, pid)), None)
    if best_available is None:
        raise ValueError("No legal timing-lab selection")
    remaining = [pid for pid in data["espn_market"] if pid not in gone]
    positions = {pid: i+1 for i, pid in enumerate(remaining)}
    base_window = gap+1 if gap is not None and gap > 0 else None
    window = base_window + buffer if base_window is not None and buffer is not None else None
    urgent = set(remaining[:window]) if window is not None else set()
    tier = [pid for pid in available if pid in urgent]
    best = next((pid for pid in tier if legal(roster_key, pid)), None)
    if best is None:
        tier, best = available, best_available
    candidate, gain, supply = best, 0, {}
    if scarcity and gap is not None and best in data["rw_ranks"]:
        near = [pid for pid in tier if pid in data["rw_ranks"]
                and data["rw_ranks"][pid] <= data["rw_ranks"][best]+3 and legal(roster_key, pid)]
        survivors = [pid for pid in data["quality"] if pid not in gone and pid not in data["bans"]
                     and positions[pid] > (base_window or 1) and data["rounds"][pid] <= rnd+1][:32]
        supply = {slot: sum(slot in data["model"].by_id[pid]["eligible"] for pid in survivors) for slot in CORE}
        weights = tuple(1/(1+supply[slot]) for slot in CORE)
        before = weighted_coverage([data["model"].by_id[pid] for pid in roster], weights)
        gains = {pid: weighted_coverage([data["model"].by_id[p] for p in (*roster, pid)], weights)-before for pid in near}
        candidate = max(near, key=lambda pid: (round(gains[pid], 12), -data["quality_rank"][pid]))
        gain = gains[candidate]
    return candidate, {"best_available": best_available, "best_in_tier": best, "market_position": positions[candidate],
                       "base_window": base_window, "window": window, "scarcity_changed": candidate != best,
                       "scarcity_gain": gain, "future_core_supply": supply,
                       "buffered_reach": bool(base_window is not None and positions[candidate] > base_window)}


def simulate(data, slot, field, seed, policy, queues=None):
    model, legal = data["model"], data["legal"]
    cfg, size = model.cfg, roster_size(model.cfg)
    sequence = [t for r in range(size) for t in (range(1, cfg["teams"]+1) if r % 2 == 0 else range(cfg["teams"], 0, -1))]
    turns = [i for i, t in enumerate(sequence, 1) if t == slot]
    queues = queues or opponent_queues(data, field, seed)
    rosters, gone, picks, trace = {t: [] for t in range(1, cfg["teams"]+1)}, set(), [], []
    for pick, team in enumerate(sequence, 1):
        rnd = (pick-1)//cfg["teams"]+1
        if team == slot:
            following = next((p for p in turns if p > pick), None)
            pid, decision = choose(data, rosters[team], gone, rnd, None if following is None else following-pick-1, policy)
            missing = len(active_slots(cfg))-len(assign([model.by_id[p] for p in rosters[team]], active_slots(cfg)))
            trace.append({"pick": pick, "round": rnd, "id": pid, "next_pick": following, **decision,
                          "late_coverage_pressure": rnd >= 9 and missing == size-len(rosters[team])})
        else:
            pid = next((p for p in queues[team] if p not in gone and data["rounds"][p] <= rnd
                        and legal(tuple(sorted(rosters[team])), p)), None)
            if pid is None:
                raise ValueError("No legal opponent selection")
        rosters[team].append(pid)
        gone.add(pid)
        picks.append({"pick": pick, "team": team, "id": pid})
    if len(gone) != len(sequence):
        raise ValueError("Mock duplicated a player")
    for team, roster in rosters.items():
        players = [model.by_id[pid] for pid in roster]
        if not legal_roster(players, cfg) or len(assign(players, active_slots(cfg))) != len(active_slots(cfg)):
            raise ValueError("Mock roster legality or coverage failed")
        if team == slot and set(roster) & data["bans"]:
            raise ValueError("Mock selected a personal ban")
    return {"field": field, "seed": seed, "slot": slot, "policy": policy, "roster": rosters[slot], "trace": trace, "picks": picks}


def opponent_queues(data, field, seed):
    if field == "espn":
        pool = set(data["pool"])
        order = [pid for pid in data["espn_market"] if pid in pool]
        return {t: order for t in range(1, data["model"].cfg["teams"]+1)}
    return adp_mocks.opponents(data, field, seed)


def evaluate(data, case):
    model, roster = data["model"], case["roster"]
    players = [model.by_id[pid] for pid in roster]
    starters = assign(players, active_slots(model.cfg), {p["id"]: p["fpg"] for p in players})
    picked_at = {p["id"]: p["pick"] for p in case["picks"]}
    deferred = [t for t in case["trace"] if t["next_pick"] is not None and t["best_available"] != t["id"]]
    return {"rank_score": sum(data["quality_rank"][pid] for pid in roster),
            "projected_season_points": sum(p["ros"] for p in players),
            "starter_fpg_sum": sum(model.by_id[pid]["fpg"] for pid in starters),
            "missing_projections": sum(not p["ranked"] for p in players),
            "published_rw_picks": sum(pid in data["rw_ranks"] for pid in roster),
            "deferred_targets": len(deferred), "deferred_lost": sum(picked_at.get(t["best_available"], float("inf")) < t["next_pick"] for t in deferred),
            "buffered_reaches": sum(t["buffered_reach"] for t in case["trace"]),
            "scarcity_changes": sum(t["scarcity_changed"] for t in case["trace"]),
            "late_coverage_pressure": sum(t["late_coverage_pressure"] for t in case["trace"]),
            "centers_first6": sum(model.by_id[t["id"]]["primary"] == "C" for t in case["trace"][:6])}


def summaries(results):
    baseline = {(r["field"], r["slot"], r["seed"]): r for r in results if r["policy"] == "current"}
    groups, slots = defaultdict(list), defaultdict(list)
    for row in results:
        base = baseline[row["field"], row["slot"], row["seed"]]
        row = {**row, "rank_gain": base["rank_score"]-row["rank_score"],
               "season_gain_pct": 100*(row["projected_season_points"]/base["projected_season_points"]-1) if base["projected_season_points"] else None,
               "starter_gain_pct": 100*(row["starter_fpg_sum"]/base["starter_fpg_sum"]-1) if base["starter_fpg_sum"] else None}
        groups[row["field"], row["policy"]].append(row)
        if row["field"] in {"typical", "loose"}:
            groups["noisy", row["policy"]].append(row)
            slots[row["slot"], row["policy"]].append(row)

    def aggregate(rows):
        deferred = sum(r["deferred_targets"] for r in rows)
        result = {"drafts": len(rows), "mean_rank_gain_vs_current": statistics.mean(r["rank_gain"] for r in rows),
                  "rank_win_share": statistics.mean(r["rank_gain"] > 0 for r in rows),
                  "rank_tie_share": statistics.mean(r["rank_gain"] == 0 for r in rows),
                  "projected_season_gain_pct_vs_current": statistics.mean(r["season_gain_pct"] for r in rows if r["season_gain_pct"] is not None),
                  "projected_starter_gain_pct_vs_current": statistics.mean(r["starter_gain_pct"] for r in rows if r["starter_gain_pct"] is not None),
                  "deferred_target_loss_share": sum(r["deferred_lost"] for r in rows)/deferred if deferred else None,
                  "deferred_target_count": deferred}
        for name in ("rank_score", "projected_season_points", "starter_fpg_sum", "missing_projections", "published_rw_picks",
                     "buffered_reaches", "scarcity_changes", "late_coverage_pressure", "centers_first6"):
            result["mean_"+name] = statistics.mean(r[name] for r in rows)
        return result
    return ([{"field": f, "policy": p, **aggregate(rows)} for (f, p), rows in sorted(groups.items())],
            [{"slot": s, "policy": p, **aggregate(rows)} for (s, p), rows in sorted(slots.items())])


def run(cfg):
    data = prepare(cfg)
    cases, fields = [], {"espn": [0], "adp": [0], "typical": list(range(10)), "loose": list(range(10))}
    for field, seeds in fields.items():
        for seed in seeds:
            queues = opponent_queues(data, field, seed)
            for slot in range(1, cfg["teams"]+1):
                for policy in POLICIES:
                    cases.append(simulate(data, slot, field, seed, policy, queues))
            print(f"Timing lab: {field}, seed {seed}; {len(cases)} full drafts", flush=True)
    evidence = {"version": 1, "comparison_only": True, "live_espn_rooms": 0, "fields": fields,
                "protocol_sha256": hashlib.sha256(PROTOCOL.read_bytes()).hexdigest(),
                "code_sha256": {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in FILES},
                "market_sha256": data["market_sha256"], "inputs_sha256": data["inputs_sha256"],
                "market_capture": data["market_capture"], "roster_injury_capture": data["roster_injury_capture"],
                "config": {k: cfg[k] for k in ("teams", "slots", "position_limits", "scoring", "draft")},
                "ban_policy": read_json(path(cfg, "draft-bans.json")), "sources": data["sources"],
                "policies": POLICIES, "candidate_pool": len(data["pool"]), "demand_pool": len(data["espn_market"]),
                "quality_order": data["quality"], "espn_order": data["espn_market"], "cases": cases}
    root = path(cfg, "research-timing")
    write_json(root/"decisions.json", evidence)
    write_json(root/"decisions-lock.json", {"sha256": digest(evidence)})
    locked = read_json(root/"decisions.json")
    if digest(locked) != read_json(root/"decisions-lock.json")["sha256"]:
        raise ValueError("Timing-lab decisions changed before scoring")
    results = [{**{k: c[k] for k in ("field", "seed", "slot", "policy")}, **evaluate(data, c)} for c in locked["cases"]]
    summary, by_slot = summaries(results)
    examples = [{"policy": c["policy"], "slot": c["slot"], "field": c["field"], "seed": c["seed"],
                 "roster": [{"pick": t["pick"], "id": t["id"], "name": data["model"].by_id[t["id"]]["name"],
                             "rw_rank": data["rw_ranks"].get(t["id"]), "espn_rank": data["model"].by_id[t["id"]]["draft_rank"]} for t in c["trace"]]}
                for c in locked["cases"] if c["slot"] == 8 and c["field"] == "typical" and c["seed"] == 0]
    report = {**{k: v for k, v in evidence.items() if k not in {"cases", "quality_order", "espn_order"}},
              "decision_sha256": digest(locked), "summary": summary, "by_slot": by_slot, "examples": examples, "cases": results,
              "note": "Forward rank/projection proxies, not actual outcomes or independent seasons. No live change."}
    write_json(root/"results.json", report)
    write_json(ROOT.parent/"docs/basketball_timing_lab_results.json", {k: v for k, v in report.items() if k != "cases"})
    return {"drafts": len(cases), "paired_settings": len(cases)//len(POLICIES), "decision_sha256": digest(locked)}
