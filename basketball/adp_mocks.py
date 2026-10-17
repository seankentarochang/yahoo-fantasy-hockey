"""Forward ADP rehearsals. No credentials, draft room or execution transport."""
from collections import Counter
from datetime import date
from functools import lru_cache
import hashlib
import json
import math
import random
import urllib.request

from . import bans
from .backtest import digest
from .config import ROOT, active_slots, instant, now, path, read_json, roster_size, write_json
from .draft_advisor import orders
from .espn import player
from .injury_returns import estimate
from .model import Model
from .planner import assign, legal_roster

FIELDS = {"adp": (1.0, 0), "typical": (0.8, 8), "loose": (0.6, 16)}
ADP_TAIL = 130
PROTOCOL = ROOT.parent / "docs/BASKETBALL_ADP_MOCKS_PROTOCOL.md"


def valid_adp(value):
    return type(value) in (int, float) and math.isfinite(value) and 0 < value < 999


def market_value(p):
    return float(p["adp"]) if valid_adp(p.get("adp")) and p["adp"] < ADP_TAIL else float(p["draft_rank"])


def preference_sigma(demand, sigma):
    return min(sigma, 0.25 * demand)


def collect(cfg):
    """Read only the public season player endpoint, with complete pagination."""
    root = path(cfg, "research-adp-mocks")
    url = f"https://lm-api-reads.fantasy.espn.com/apis/v3/games/fba/seasons/{cfg['season']}/players?view=kona_player_info"
    rows, captures = [], []
    for offset in range(0, 20000, 2000):
        filters = {"limit": 2000, "offset": offset,
                   "sortDraftRanks": {"sortPriority": 1, "sortAsc": True, "value": "STANDARD"},
                   "filterStatsForExternalIds": {"value": [cfg["season"]]},
                   "filterStatsForSourceIds": {"value": [1]}, "filterStatsForSplitTypeIds": {"value": [0]}}
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json",
                                                  "x-fantasy-filter": json.dumps(filters)})
        with urllib.request.urlopen(req, timeout=40) as response:
            raw = response.read()
        page = json.loads(raw)
        if not isinstance(page, list):
            raise ValueError("Unexpected ESPN player page")
        filename = f"players-{offset}-{hashlib.sha256(raw).hexdigest()[:12]}.raw"
        root.mkdir(parents=True, exist_ok=True)
        (root / filename).write_bytes(raw)
        captures.append({"file": filename, "sha256": hashlib.sha256(raw).hexdigest(), "filters": filters})
        rows.extend(page)
        if len(page) < 2000:
            break
    else:
        raise ValueError("ESPN pagination did not finish")
    if len({int(p["id"]) for p in rows}) != len(rows):
        raise ValueError("Repeated ESPN page or player identity")
    result = {"season": cfg["season"], "captured_at": now(cfg).isoformat(), "url": url,
              "captures": captures, "players": rows}
    write_json(root / "market.json", result)
    write_json(root / "market-lock.json", {"sha256": digest(result)})
    return {"players": len(rows), "pages": len(captures), "sha256": digest(result)}


def first_round(cfg, p, injury, draft_at):
    """Mirror injury price windows using the rehearsal date, without draft files."""
    if p.get("status") == "SUSPENSION":
        return None
    records = injury.get("injuries", []) if injury else []
    if injury and (injury.get("out_for_season") or any(
            r.get("designation") == "OFS" or "susp" in str(r.get("status", "")).lower()
            or "susp" in str(r.get("designation", "")).lower() for r in records)):
        return None
    if not records and p.get("status") == "ACTIVE":
        return 1
    result = estimate(records, draft_at)
    days = result["days_out"]
    policy = cfg["draft"]["injury_policy"]
    if days is None or days < 0 or date.fromisoformat(result["expected_return"]) > date.fromisoformat(policy["season_end"]):
        return None
    if days <= policy["early_days"]:
        return 1
    if days <= policy["middle_days"]:
        return policy["early_rounds"] + 1
    return policy["late_round"]


def prepare(cfg):
    root = path(cfg, "research-adp-mocks")
    market = read_json(root / "market.json")
    inputs = read_json(path(cfg, "research-board/inputs.json"))
    manifest = read_json(path(cfg, "research-board/manifest.json"))
    if (not market or digest(market) != read_json(root / "market-lock.json", {}).get("sha256")
            or not inputs or digest(inputs) != manifest["inputs_sha256"]):
        raise ValueError("Current mock input hashes do not match")
    for capture in market["captures"]:
        file = (root / capture["file"]).resolve()
        if not file.is_relative_to(root.resolve()) or hashlib.sha256(file.read_bytes()).hexdigest() != capture["sha256"]:
            raise ValueError("ADP source capture changed")
    for stamp in (market["captured_at"], inputs["as_of"], inputs["injuries"]["checked_at"], inputs["injuries"]["source_as_of"]):
        if not 0 <= (now(cfg) - instant(stamp)).total_seconds() <= 86400:
            raise ValueError("Current mock evidence is future-dated or older than 24 hours")
    if market["season"] != cfg["season"] or inputs["season"] != cfg["season"] or cfg["format"] != "points":
        raise ValueError("Current mock season or scoring format mismatch")
    snapshot = {**inputs["snapshot"], "players": [player(p) for p in market["players"]], "fetched_at": market["captured_at"]}
    model = Model(cfg, snapshot)
    quality, ranked, published, details = orders(model, "consensus", path(cfg, "ranking-library"))
    injuries = {p["id"]: p for p in inputs["injuries"]["players"]}
    pool, rounds, excluded = [], {}, []
    draft_at = instant(cfg["draft"]["date"])
    for pid in ranked:
        p, roster = model.by_id[pid], inputs["rosters"].get(str(pid))
        allowed_round = first_round(cfg, p, injuries.get(pid), draft_at)
        if (p.get("active") is not True or not roster or roster["status"] != "active"
                or p["team"] != roster["team"] or allowed_round is None):
            excluded.append({"id": pid, "name": p["name"], "reason": "Unverified/inactive roster, team conflict, suspension or unknown/OFS injury"})
            continue
        pool.append(pid)
        rounds[pid] = allowed_round
    if len(pool) < cfg["teams"] * roster_size(cfg):
        raise ValueError("Insufficient verified draft pool")
    own_bans = {pid for pid in pool if bans.reason(cfg, model.by_id[pid], current_team=inputs["rosters"][str(pid)]["team"])}
    return {"model": model, "pool": pool, "quality": [pid for pid in quality if pid in rounds],
            "market": sorted(pool, key=lambda pid: (market_value(model.by_id[pid]), model.by_id[pid]["draft_rank"], pid)),
            "rounds": rounds, "bans": own_bans, "excluded": excluded, "sources": details, "published": published,
            "inputs_sha256": digest(inputs), "market_sha256": digest(market), "market_capture": market["captured_at"],
            "roster_injury_capture": inputs["as_of"],
            "adp_fallback_ids": [pid for pid in pool if not valid_adp(model.by_id[pid].get("adp")) or model.by_id[pid]["adp"] >= ADP_TAIL]}


def opponents(data, field, seed):
    adp_share, sigma = FIELDS[field]
    model, pool = data["model"], data["pool"]
    result = {}
    for team in range(1, model.cfg["teams"] + 1):
        rng = random.Random(f"adp-rehearsal-v1:{field}:{seed}:{team}")
        follows_adp = rng.random() < adp_share
        scores = {}
        for pid in sorted(pool):
            demand = market_value(model.by_id[pid]) if follows_adp else model.by_id[pid]["draft_rank"]
            scores[pid] = demand + (rng.gauss(0, preference_sigma(demand, sigma)) if sigma else 0)
        result[team] = sorted(pool, key=lambda pid: (scores[pid], pid))
    return result


def simulate(data, slot, field, seed):
    model, cfg = data["model"], data["model"].cfg
    teams, size = cfg["teams"], roster_size(cfg)
    rosters = {t: [] for t in range(1, teams + 1)}
    sequence = [t for r in range(size) for t in (range(1, teams + 1) if r % 2 == 0 else range(teams, 0, -1))]
    turns = [i for i, team in enumerate(sequence, 1) if team == slot]
    queues = opponents(data, field, seed)
    gone, trace, log = set(), [], []
    active = active_slots(cfg)

    @lru_cache(maxsize=4096)
    def legal(roster, pid):
        ps = [model.by_id[p] for p in (*roster, pid)]
        return legal_roster(ps, cfg) and len(active) - len(assign(ps, active)) <= size - len(ps)

    for pick, team in enumerate(sequence, 1):
        rnd = (pick - 1) // teams + 1
        own = team == slot
        queue = data["quality"] if own else queues[team]
        available = [pid for pid in queue if pid not in gone and data["rounds"][pid] <= rnd
                     and (not own or pid not in data["bans"])]
        next_pick = next((p for p in turns if p > pick), None) if own else None
        urgent = set()
        if own and next_pick is not None and next_pick > pick + 1:
            # Banned/round-ineligible players still consume opponents' market demand.
            remaining = [pid for pid in data["market"] if pid not in gone]
            urgent = set(remaining[:next_pick - pick - 1])
        choices = [pid for pid in available if pid in urgent] if urgent else []
        candidate = next((pid for pid in choices if legal(tuple(rosters[team]), pid)), None)
        if candidate is None:
            candidate = next((pid for pid in available if legal(tuple(rosters[team]), pid)), None)
        if candidate is None:
            raise ValueError(f"No legal mock selection at pick {pick}")
        if own:
            trace.append({"round": rnd, "pick": pick, "id": candidate, "next_pick": next_pick,
                          "available": available, "demand_window": sorted(urgent)})
        rosters[team].append(candidate)
        gone.add(candidate)
        log.append({"pick": pick, "team": team, "id": candidate})
    if len(gone) != teams * size:
        raise ValueError("Duplicate or missing mock picks")
    for team, roster in rosters.items():
        ps = [model.by_id[pid] for pid in roster]
        if not legal_roster(ps, cfg) or len(assign(ps, active)) != len(active):
            raise ValueError("Mock failed final roster coverage")
        if team == slot and set(roster) & data["bans"]:
            raise ValueError("Mock selected a banned player")
    return {"field": field, "slot": slot, "seed": seed, "roster": rosters[slot], "trace": trace, "picks": log}


def summarize(data, cases):
    def describe(pid):
        p = data["model"].by_id[pid]
        return {"id": pid, "name": p["name"], "position": p["primary"], "adp": p.get("adp"),
                "espn_rank": p["draft_rank"], "first_allowed_round": data["rounds"][pid],
                "demand_score": market_value(p),
                "demand_basis": "ESPN ADP" if valid_adp(p.get("adp")) and p["adp"] < ADP_TAIL else "ESPN rank fallback",
                "expert_ranks": {s: ranks.get(pid) for s, ranks in data["published"].items()}}
    result = []
    for field, slot in ((f, s) for f in FIELDS for s in sorted({c["slot"] for c in cases})):
        rows = [c for c in cases if c["field"] == field and c["slot"] == slot]
        by_round = []
        for r in range(roster_size(data["model"].cfg)):
            counts = Counter(c["trace"][r]["id"] for c in rows)
            available = Counter(pid for c in rows for pid in c["trace"][r]["available"])
            by_round.append({"round": r + 1, "pick": rows[0]["trace"][r]["pick"],
                             "choices": [{**describe(pid), "count": n, "selection_share": n / len(rows),
                                          "available_share": available[pid] / len(rows)} for pid, n in counts.most_common()],
                             "availability": [{**describe(pid), "share": n / len(rows)} for pid, n in available.most_common()]})
        representative = max(rows, key=lambda c: (sum(next(p["count"] for p in by_round[r]["choices"] if p["id"] == t["id"])
                                                     for r, t in enumerate(c["trace"])), -c["seed"]))
        result.append({"field": field, "slot": slot, "drafts": len(rows), "unique_draft_logs": len({digest(c["picks"]) for c in rows}),
                       "rounds": by_round, "representative_seed": representative["seed"],
                       "representative": [{**describe(t["id"]), "round": t["round"], "pick": t["pick"]} for t in representative["trace"]]})
    return result


def run(cfg, slot=None, count=25, refresh=False):
    if (slot is not None and (type(slot) is not int or not 1 <= slot <= cfg["teams"])) or type(count) is not int or not 1 <= count <= 1000:
        raise ValueError("Valid draft slot and 1–1000 seeds per field required")
    if cfg["draft"]["type"] != "snake":
        raise ValueError("ADP mock requires a snake draft")
    if refresh:
        collect(cfg)
    data = prepare(cfg)
    cases = []
    slots = list(range(1, cfg["teams"] + 1)) if slot is None else [slot]
    for field in FIELDS:
        for position in slots:
            for seed in range(count):
                cases.append(simulate(data, position, field, seed))
            print(f"Completed {count} {field} rehearsals at slot {position}", flush=True)
    report = {"version": 2, "comparison_only": True, "season": cfg["season"], "slot": slot,
              "slots": slots, "seeds_per_slot_field": count,
              "teams": cfg["teams"], "rounds": roster_size(cfg), "draft_date": cfg["draft"]["date"],
              "captured_at": data["market_capture"], "roster_injury_capture": data["roster_injury_capture"],
              "market_sha256": data["market_sha256"], "inputs_sha256": data["inputs_sha256"],
              "protocol_sha256": hashlib.sha256(PROTOCOL.read_bytes()).hexdigest(),
              "code_sha256": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in
                              ("adp_mocks.py", "draft_advisor.py", "model.py", "planner.py", "espn.py", "config.py", "injury_returns.py", "bans.py")},
              "config": {k: cfg[k] for k in ("teams", "slots", "position_limits", "scoring", "draft")},
              "ban_policy": bans.listing(cfg), "pool": len(data["pool"]), "own_banned_ids": sorted(data["bans"]),
              "adp_fallback_ids": data["adp_fallback_ids"], "excluded": data["excluded"], "sources": data["sources"],
              "fields": FIELDS, "adp_rank_fallback_threshold": ADP_TAIL,
              "noise_scale": "min(field_sigma, 0.25 * demand_score)", "summary": summarize(data, cases), "cases": cases,
              "note": "Frequencies are conditional on simulated draft paths and assumed preference noise, not calibrated player survival probabilities. The ADP-led field with ESPN tail repeats deterministically."}
    root = path(cfg, "research-adp-mocks")
    write_json(root / "mocks.json", report)
    write_json(root / "mocks-lock.json", {"sha256": digest(report)})
    return {"drafts": len(cases), "slots": slots, "report": str(root / "mocks.json"), "sha256": digest(report)}
