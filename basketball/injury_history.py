"""Pinned historical injury transactions; features are censored at forecast time."""
from collections import Counter, defaultdict
from datetime import date, timedelta
import hashlib
import json
import re
import urllib.request

from .config import path, read_json, write_json
from .strategy_lab import key

COMMIT = "217ce05b967b201d1b7a474f20b4a6cab273de66"
URL = f"https://raw.githubusercontent.com/JaseZiv/NBA_data/{COMMIT}/raw-data/nba-injuries/nba_injuries.json"
SHA256 = "94a6338ed0c4645115f5e4efe567909e381a14f9e7c379dd5e6aaf34876c25cd"
COVERAGE_END = date(2025, 5, 13)
GROUPS = ("knee", "ankle", "achilles", "foot", "hip_groin", "hamstring", "leg", "back",
          "upper", "head_neck", "other")
PATTERNS = (r"knee|\bacl\b|\bmcl\b|\bpcl\b|menisc", r"ankle", r"achill+es", r"foot|feet|toe|plantar",
            r"hip|groin|adductor", r"hamstring", r"calf|thigh|quadricep|shin|tibia|fibula|patella|leg",
            r"back|lumbar|spinal|spine", r"shoulder|arm|elbow|hand|wrist|finger|thumb|pectoral",
            r"head|neck|concuss|eye|nose|jaw|face|migraine")
SEVERE = re.compile(r"surgery|surgical|fractur|dislocat|ruptur|torn|\btear\b", re.I)
FEATURE_NAMES = tuple(f"lag{lag}_{name}" for lag in (1, 2, 3) for name in ("episodes", "days_fraction", "severe")) + tuple(
    "body_"+g for g in GROUPS) + ("same_body_recurrences", "recentness", "unresolved_age", "unresolved_severe",
                                 "illness_reports", "rest_reports")


def classify(note):
    text = note.lower()
    if re.search(r"coach|personal|suspend|disciplin|g.league|not with team|bereave", text):
        return None
    if re.search(r"\brest\b", text):
        return "rest"
    if re.search(r"illness|\bflu\b|covid|health and safety|virus|infection|gastro|respirator", text):
        return "illness"
    # Achilles must precede broad lower-leg/foot terms.
    if re.search(PATTERNS[2], text):
        return "achilles"
    for group, pattern in zip(GROUPS, PATTERNS):
        if re.search(pattern, text):
            return group
    return "other" if re.search(r"injur|sore|sprain|strain|fractur|surgery|surgical|torn|ruptur|"
                               r"bruis|contus|pain|tendinitis|tendonitis|abdom|\bribs?\b|chest|blood clot", text) else None


def resolve(name, identities):
    # Accept alias variants only when all matching variants point to one ID.
    variants = [name] + re.sub(r"\([^)]*\)", "", name).split("/")
    ids = {identities[key(v)] for v in variants if key(v) in identities}
    return next(iter(ids)) if len(ids) == 1 else None


def union_days(intervals, start, end):
    spans = sorted((max(a, start), min(b, end)) for a, b in intervals if a < end and b > start)
    total, last = 0, start
    for left, right in spans:
        if right > max(left, last):
            total += (right-max(left, last)).days
        last = max(last, right)
    return total


class History:
    def __init__(self, rows, coverage_end=COVERAGE_END):
        self.rows = rows
        self.coverage_end = coverage_end
        self.cache = {}

    def snapshot(self, store, year):
        cutoff = date(year-1, 10, 1)
        if cutoff > self.coverage_end:
            raise ValueError("Injury archive ends before this forecast cutoff; missing coverage is not health")
        if year in self.cache:
            return self.cache[year]
        identities = store.identities(year)
        events, seen, audit = defaultdict(list), set(), Counter()
        for row in self.rows:
            day = date.fromisoformat(row["Date"])
            if not date(2011, 1, 1) <= day < cutoff:
                continue
            if "date approximate" in row["Notes"].lower():
                audit["approximate_date_excluded"] += 1
                continue
            kind = classify(row["Notes"])
            for field, action in (("Acquired", "return"), ("Relinquished", kind)):
                if not row[field] or action is None:
                    continue
                if action == "return" and not re.search(r"activat|returned|cleared", row["Notes"], re.I):
                    continue
                if "coach" in row["Notes"].lower():
                    continue
                pid = resolve(row[field], identities)
                if pid is None:
                    audit["unmatched_or_ambiguous"] += 1
                    continue
                event = (pid, day, action, bool(SEVERE.search(row["Notes"])))
                if event in seen:
                    audit["duplicate_events"] += 1
                    continue
                seen.add(event)
                events[pid].append(event[1:])
                audit["matched_"+action] += 1
        snapshots = {}
        for pid, values in events.items():
            episodes, other = [], []
            for day, kind, severe in sorted(values, key=lambda e: (e[0], e[1] != "return", e[1])):
                if kind == "return":
                    for ep in episodes:
                        if ep["end"] is None:
                            ep["end"] = day
                elif kind in {"illness", "rest"}:
                    other.append((day, kind))
                else:
                    old = next((e for e in reversed(episodes) if e["body"] == kind and e["end"] is None
                                and (day-e["last"]).days <= 14), None)
                    if old:
                        old["last"] = day
                        old["severe"] |= severe
                    else:
                        episodes.append({"start": day, "last": day, "end": None, "body": kind, "severe": severe})
            snapshots[pid] = (episodes, other)
        self.cache[year] = (cutoff, snapshots, dict(audit))
        return self.cache[year]

    def summary(self, store, pid, year):
        cutoff, snapshots, _ = self.snapshot(store, year)
        episodes, other = snapshots.get(pid, ([], []))
        recent = [e for e in episodes if cutoff-timedelta(days=1095) <= e["start"] < cutoff]
        intervals = [(e["start"], e["end"] or cutoff) for e in episodes]
        values = []
        for lag in (1, 2, 3):
            start, end = cutoff-timedelta(days=365*lag), cutoff-timedelta(days=365*(lag-1))
            subset = [e for e in recent if start <= e["start"] < end]
            values.extend([len(subset)/10, union_days(intervals, start, end)/365,
                           sum(e["severe"] for e in subset)/5])
        bodies = Counter(e["body"] for e in recent)
        pending = [e for e in episodes if e["end"] is None]
        recurrence = sum(max(0, n-1) for n in bodies.values())
        values.extend(bodies[g]/10 for g in GROUPS)
        values.extend([recurrence/10, max((1-(cutoff-e["start"]).days/1095 for e in recent), default=0),
                       min(1095, max(((cutoff-e["start"]).days for e in pending), default=0))/1095,
                       int(any(e["severe"] for e in pending))])
        values.extend(sum(k == kind and (cutoff-day).days <= 1095 for day, k in other)/10
                      for kind in ("illness", "rest"))
        return {"features": values, "episodes": len(recent), "severe": any(e["severe"] for e in recent),
                "recurrences": recurrence, "observed_days": union_days(intervals, cutoff-timedelta(days=1095), cutoff)}


def load(cfg):
    root = path(cfg, "research-injury")
    file = root/"transactions.json"
    if not file.exists():
        with urllib.request.urlopen(urllib.request.Request(URL, headers={"User-Agent": "BasketballResearch/1.0"}), timeout=45) as response:
            raw = response.read()
    else:
        raw = file.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SHA256:
        raise ValueError("Historical injury archive hash changed")
    rows = json.loads(raw)
    required = {"Date", "Team", "Acquired", "Relinquished", "Notes"}
    if len(rows) != 73306 or any(set(r) != required or any(not isinstance(v, str) for v in r.values()) for r in rows):
        raise ValueError("Historical injury schema/count changed")
    dates = [date.fromisoformat(r["Date"]) for r in rows]
    if max(dates) != COVERAGE_END:
        raise ValueError("Historical injury archive coverage changed")
    if not file.exists():
        root.mkdir(parents=True, exist_ok=True)
        file.write_bytes(raw)
    manifest = {"url": URL, "commit": COMMIT, "sha256": SHA256, "rows": len(rows), "coverage_end": str(COVERAGE_END),
                "earliest_accepted_date": "2011-01-01", "independently_timestamped": False,
                "source": "Pro Sports Transactions archive mirrored by JaseZiv/NBA_data"}
    write_json(root/"manifest.json", manifest)
    return History(rows), manifest
