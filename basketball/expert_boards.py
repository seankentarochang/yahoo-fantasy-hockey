"""Historical expert points boards, coverage controls and paired draft tests."""
from datetime import datetime, timezone
import hashlib
import html
import json
import random
import re
import statistics
import urllib.parse
import urllib.request

from . import empirical, value_board
from .backtest import digest
from .config import ROOT, instant, path, read_json, write_json
from .empirical_draft import score_roster, simulate
from .ranking_library import CUTOFFS, Page, dates, resolve_name, validate_rows
from .strategy_lab import key

YEARS = (2023, 2024, 2025, 2026)
PROTOCOL = ROOT.parent/"docs/BASKETBALL_EXPERT_BOARDS_PROTOCOL.md"
SCRIPT = "https://cdn.fantasypros.com/js/fp-widget-2.0.js?v=1"
YAHOO_ARTICLE = "https://sports.yahoo.com/2023-24-fantasy-basketball-draft-rankings-points-leagues-220930771.html"
FANTRAX = "https://www.fantraxhq.com/2024-25-fantasy-basketball-points-league-rankings-top-200/"
ROTOBALLER = "https://www.rotoballer.com/fantasy-basketball-rankings-points-leagues-2023-2024/1214219"
FILES = ("expert_boards.py", "empirical_draft.py", "empirical.py", "value_board.py", "ranking_library.py",
         "source_backtest.py", "planner.py", "backtest.py", "model.py", "strategy_lab.py", "config.py")
ALIASES = {"cameronthomas": "Cam Thomas", "xaviertillmansr": "Xavier Tillman"}


def yahoo_url(year):
    params = {"callback": "FPW.rankingsCB", "position": "ALL", "sport": "NBA", "year": year-1,
              "week": 0, "experts": "show", "id": 1663, "type": "ST", "scoring": "PTS", "filters": 3793, "widget": "ST"}
    return "https://partners.fantasypros.com/api/v1/consensus-rankings.php?"+urllib.parse.urlencode(params)


def cutoff(year):
    return instant(CUTOFFS[year]+"T00:00:00-04:00")


def yahoo_board(text, year):
    if not text.strip().startswith("FPW.rankingsCB(") or not text.strip().endswith((");", ")")):
        raise ValueError("Unexpected Yahoo widget payload")
    data = json.loads(text[text.find("(")+1:text.rfind(")")])
    if (data.get("sport") != "NBA" or str(data.get("year")) != str(year-1) or str(data.get("week")) != "0"
            or data.get("scoring") != "PTS" or data.get("ranking_type_name") != "draft"
            or data.get("type") != "Draft - Points" or data.get("total_experts") != 1
            or data.get("expert_names") != {"3793": "Dan Titus"}):
        raise ValueError("Unverified Yahoo season, format or individual expert")
    updated = datetime.fromtimestamp(data["last_updated_ts"], timezone.utc)
    published = datetime.fromisoformat(data["expert_pub"]["3793"]).replace(tzinfo=timezone.utc)
    evidence = {"datePublished": published.isoformat(), "dateModified": updated.isoformat()}
    if max(updated, published) >= cutoff(year):
        return [], evidence, "Widget updated after the frozen preseason cutoff"
    rows = []
    for player in data["players"]:
        rank = int(player["experts"]["3793"])
        if rank != int(player["rank_ecr"]):
            raise ValueError("Single-expert widget has conflicting ranks")
        rows.append({"rank": rank, "name": player["player_name"], "positions": []})
    return validate_rows(rows, {"count": data["count"]}), evidence, None


def static_board(text, kind):
    evidence = dates(text)
    page = Page(text)
    if kind == "fantrax":
        if not page.titles or "2024-25 Fantasy Basketball Points League Rankings" not in page.titles[0]:
            raise ValueError("Unexpected Fantrax title")
        rows = [{"rank": int(rank), "name": html.unescape(name).strip(), "positions": []}
                for rank, name in re.findall(r"(\d+)\.\s*<strong>\s*([^<]+)</strong>", text)]
        count = 200
    elif kind == "rotoballer":
        if not page.titles or not re.search(r"Points League|Points Leagues", page.titles[0], re.I):
            raise ValueError("Unverified RotoBaller points format")
        rows = [{"rank": int(cells[0]), "name": cells[1], "positions": []}
                for table in page.tables if table and table[0] == ["RANK", "PLAYER", "TEAM", "POS"] for cells in table[1:]]
        count = 50
    else:
        raise ValueError("Unknown static ranking adapter")
    return validate_rows(rows, {"count": count}), evidence


def collect(cfg):
    root = path(cfg, "research-experts")
    captures = root/"captures"
    previous = read_json(root/"catalog.json", {})
    expected = {r["file"]: r["sha256"] for r in previous.get("captures", [])}
    records = []

    def capture(name, url):
        file = captures/name
        if file.exists():
            raw = file.read_bytes()
            if name in expected and hashlib.sha256(raw).hexdigest() != expected[name]:
                raise ValueError("Expert source bytes changed")
        else:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=40) as response:
                raw = response.read()
            captures.mkdir(parents=True, exist_ok=True)
            file.write_bytes(raw)
        records.append({"file": name, "url": url, "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)})
        return raw.decode("utf-8-sig")

    sources = []
    for kind, year, url in (("rotoballer", 2024, ROTOBALLER), ("fantrax", 2025, FANTRAX)):
        text = capture(f"{kind}-{year}.html", url)
        rows, evidence = static_board(text, kind)
        if any(instant(stamp) >= cutoff(year) for stamp in evidence.values()):
            raise ValueError("Static expert board was updated after its preseason cutoff")
        sources.append({"id": f"{kind}-{year}", "season": year, "family": "RotoBaller" if kind == "rotoballer" else "FantraxHQ",
                        "format": "points", "basis": "published expert order", "status": "preseason", "url": url,
                        "date_evidence": evidence, "capture": f"{kind}-{year}.html", "rows": rows})
    article = capture("yahoo-2024.html", YAHOO_ARTICLE)
    script = capture("fantasypros-widget.js", SCRIPT)
    if "consensus-rankings.php" not in script or "partners.fantasypros.com" not in script:
        raise ValueError("Published widget no longer identifies the public ranking endpoint")
    embed = re.search(r"https://partners\.fantasypros\.com/external/widget/fp-widget\.php\?[^\"]+", article)
    if not embed:
        raise ValueError("Yahoo article does not contain its ranking-widget provenance")
    embed_url = html.unescape(embed[0].rstrip("\\").replace("\\u0026", "&"))
    widget = capture("yahoo-2024-widget.html", embed_url)
    if 'data-year="2023"' not in widget or 'data-filters="3793"' not in widget:
        raise ValueError("Yahoo widget identity changed")
    for year in YEARS:
        name = f"yahoo-{year}-ranks.jsonp"
        text = capture(name, yahoo_url(year))
        rows, evidence, rejected = yahoo_board(text, year)
        sources.append({"id": f"yahoo-{year}", "season": year, "family": "Yahoo", "format": "points",
                        "basis": "published expert order", "status": "diagnostic" if rejected else "preseason",
                        "note": rejected, "url": yahoo_url(year), "date_evidence": evidence, "capture": name, "rows": rows})
    catalog = {"version": 1, "sources": sources, "captures": records,
               "note": "Retrospective publisher-dated captures; no independent archival timestamp. Dynamic player metadata is excluded."}
    write_json(root/"catalog.json", catalog)
    write_json(root/"catalog-lock.json", {"sha256": digest(catalog)})
    return {"accepted": [s["id"] for s in sources if s["status"] == "preseason"],
            "diagnostic": [s["id"] for s in sources if s["status"] != "preseason"]}


def locked_catalog(cfg):
    root = path(cfg, "research-experts")
    catalog = read_json(root/"catalog.json", {})
    if not catalog or digest(catalog) != read_json(root/"catalog-lock.json", {}).get("sha256"):
        raise ValueError("Collect and lock expert source captures first")
    for row in catalog["captures"]:
        file = (root/"captures"/row["file"]).resolve()
        if not file.is_relative_to((root/"captures").resolve()) or hashlib.sha256(file.read_bytes()).hexdigest() != row["sha256"]:
            raise ValueError("Expert capture changed or escapes its directory")
    return catalog


def complete(market, ranks):
    ordinal = {pid: i for i, pid in enumerate(market)}
    return sorted(market, key=lambda pid: (pid not in ranks, ranks.get(pid, ordinal[pid]), ordinal[pid], pid))


def primary_sources(sources):
    result = {}
    for row in sources:
        stamp = max(instant(v) for v in row["date_evidence"].values())
        priority = (row["basis"] != "projected points per game", stamp, row["id"])
        if row["family"] not in result or priority > result[row["family"]][0]:
            result[row["family"]] = priority, row["id"]
    return {family: value[1] for family, value in result.items()}


def policies_for(market, ranks, sources, depth):
    boards = {source: {pid: rank for pid, rank in values.items() if depth is None or rank <= depth}
              for source, values in ranks.items()}
    orders = {source: complete(market, values) for source, values in boards.items()}
    primary = primary_sources(sources)
    ordinal = {source: {pid: i for i, pid in enumerate(orders[source])} for source in primary.values()}
    espn_rank = {pid: i for i, pid in enumerate(market)}
    consensus = sorted(market, key=lambda pid: (sum(order[pid] for order in ordinal.values()), espn_rank[pid], pid))
    policies = {"espn": {"order": market, "sources": [primary["ESPN"]], "timing": False,
                         "coverage": set(boards[primary["ESPN"]])}}
    for source in sources:
        sid = source["id"]
        if source["family"] == "ESPN":
            continue
        for timing in (False, True):
            policies[sid+("_next_turn" if timing else "")] = {"order": orders[sid], "sources": [sid],
                                                               "timing": timing, "coverage": set(boards[sid])}
    coverage = set.intersection(*(set(boards[s]) for s in primary.values()))
    for timing in (False, True):
        policies["consensus"+("_next_turn" if timing else "")] = {
            "order": consensus, "sources": sorted(primary.values()), "timing": timing, "coverage": coverage}
    return policies


def prepare(cfg, store, year, catalog):
    data = value_board.prepare(cfg, store, year, path(cfg, "ranking-library"))
    pack = read_json(path(cfg, f"ranking-library/input-{year}.json"))
    ranks = {sid: {int(pid): rank for pid, rank in values.items()} for sid, values in pack["ranking_boards"].items()}
    sources = []
    for row in pack["sources"]:
        board = read_json(path(cfg, "ranking-library/boards/"+row["id"]+".json"))
        sources.append({**row, "published_rows": len(board["rows"]), "matched_rows": len(ranks[row["id"]]), "unmatched": []})
    identities, prior = {}, {}
    for player in data["model"].players:
        identities.setdefault(key(player["name"]), set()).add(player["id"])
        if any(s["source"] == 0 and s["season"] < year and s["stats"].get("GP", 0) > 0 for s in player["splits"]):
            prior.setdefault(key(player["name"]), set()).add(player["id"])
    for source in catalog["sources"]:
        if source["season"] != year or source["status"] != "preseason":
            continue
        matched, unmatched = {}, []
        for row in source["rows"]:
            pid = resolve_name(ALIASES.get(key(row["name"]), row["name"]), identities, prior)
            if pid is None:
                unmatched.append({"name": row["name"], "rank": row["rank"]})
            elif pid in matched:
                raise ValueError("Multiple expert names resolve to the same ESPN identity")
            else:
                matched[pid] = row["rank"]
        ranks[source["id"]] = matched
        sources.append({**{k: v for k, v in source.items() if k != "rows"}, "published_rows": len(source["rows"]),
                        "matched_rows": len(matched), "unmatched": unmatched})
    extras = set().union(*(set(r) for r in ranks.values()))-set(data["market"])
    def prior_points(pid):
        stats = next((s["stats"] for s in data["model"].by_id[pid]["splits"] if s["source"] == 0 and s["season"] == year-1), {})
        return sum(stats.get(k, 0)*w for k, w in cfg["scoring"].items())
    market = data["market"]+sorted(extras, key=lambda pid: (-prior_points(pid), pid))
    names = store.identities(year)
    mapping = {pid: names[key(p["name"])] for pid, p in data["model"].by_id.items() if key(p["name"]) in names}
    return {**data, "market": market, "mapping": mapping, "sources": sources, "ranks": ranks, "added_players": sorted(extras)}


def summaries(results):
    baseline = {(r["season"], r["field"], r["depth"], r["seed"], r["slot"]): r["total_points"]
                for r in results if r["policy"] == "espn"}
    groups = {}
    for row in results:
        base = baseline[tuple(row[k] for k in ("season", "field", "depth", "seed", "slot"))]
        delta = 100*(row["total_points"]/base-1)
        identity = tuple(row[k] for k in ("season", "field", "depth", "policy"))
        groups.setdefault(identity, []).append({**row, "gain": delta, "win": row["total_points"] > base,
                                               "tie": row["total_points"] == base})
    return [{**dict(zip(("season", "field", "depth", "policy"), identity)), "drafts": len(rows),
             "mean_gain_pct_vs_espn": statistics.mean(r["gain"] for r in rows),
             "paired_win_rate": statistics.mean(r["win"] for r in rows), "paired_tie_rate": statistics.mean(r["tie"] for r in rows),
             "mean_points": statistics.mean(r["total_points"] for r in rows), "mean_zero_games": statistics.mean(r["zero_games"] for r in rows),
             "mean_covered_pick_share": statistics.mean(r["covered_pick_share"] for r in rows)}
            for identity, rows in sorted(groups.items())]


def experiment(cfg):
    catalog = locked_catalog(cfg)
    store, manifest = empirical.load_seasons(cfg)
    root = path(cfg, "research-experts")
    prepared, decisions, orders = {}, [], {}
    for year in YEARS:
        data = prepared[year] = prepare(cfg, store, year, catalog)
        full = policies_for(data["market"], data["ranks"], data["sources"], None)
        fields = {"espn": data["market"]}
        if year == 2025:
            fields["consensus"] = full["consensus"]["order"]
        for depth in ("full", "top50"):
            policies = policies_for(data["market"], data["ranks"], data["sources"], None if depth == "full" else 50)
            orders[f"{year}:{depth}"] = {name: {**policy, "coverage": sorted(policy["coverage"])} for name, policy in policies.items()}
            for field, field_order in fields.items():
                ordinal = {pid: i for i, pid in enumerate(field_order)}
                for seed in (-1, 0, 1):
                    opponents = {}
                    for team in range(1, cfg["teams"]+1):
                        rng = random.Random(f"empirical-v1:{year}:{seed}:{team}")
                        noise = {pid: rng.gauss(0, 12) if seed >= 0 else 0 for pid in data["market"]}
                        opponents[team] = sorted(field_order, key=lambda pid: (ordinal[pid]+noise[pid], pid))
                    for slot in range(1, cfg["teams"]+1):
                        for policy, spec in policies.items():
                            roster, trace = simulate(data["model"], slot, spec["order"], opponents, data["market"], data["legal"], spec["timing"])
                            decisions.append({"season": year, "field": field, "depth": depth, "seed": seed, "slot": slot,
                                              "policy": policy, "roster": roster, "trace": trace,
                                              "covered_pick_share": sum(pid in spec["coverage"] for pid in roster)/len(roster)})
                    print(f"Expert boards: {year}, {depth}, {field}, seed {seed}; {len(decisions)} scenarios", flush=True)
    evidence = {"version": 1, "catalog_sha256": digest(catalog), "data_sha256": digest(manifest),
                "protocol_sha256": hashlib.sha256(PROTOCOL.read_text(encoding="utf-8").encode()).hexdigest(),
                "code_sha256": {name: hashlib.sha256((ROOT/name).read_text(encoding="utf-8").encode()).hexdigest() for name in FILES},
                "config": {k: cfg[k] for k in ("teams", "slots", "position_limits", "scoring")}, "orders": orders,
                "preseason": {str(y): {"input_sha256": d["input_sha256"], "sources": d["sources"], "market": d["market"],
                                        "added_players": d["added_players"]} for y, d in prepared.items()}, "decisions": decisions}
    write_json(root/"decisions.json", evidence)
    write_json(root/"decisions-lock.json", {"sha256": digest(evidence)})
    locked = read_json(root/"decisions.json")
    if digest(locked) != read_json(root/"decisions-lock.json")["sha256"]:
        raise ValueError("Expert draft decisions changed")
    results = []
    for row in locked["decisions"]:
        data = prepared[row["season"]]
        results.append({**{k: v for k, v in row.items() if k not in {"roster", "trace"}},
                        **score_roster(row["roster"], data["model"], store, row["season"], data["mapping"])})
    prior = read_json(path(cfg, "research-value/backtest.json"))
    if prior:
        old = {(r["season"], r["seed"], r["slot"]): r["total_points"] for r in prior["cases"] if r["policy"] == "espn"}
        for row in results:
            if row["policy"] == "espn" and row["field"] == "espn" and not prepared[row["season"]]["added_players"]:
                if old[(row["season"], row["seed"], row["slot"])] != row["total_points"]:
                    raise ValueError("Repeated ESPN control differs")
    report = {"version": 1, "comparison_only": True, "independent_holdout": False, "decision_sha256": digest(locked),
              "catalog_sha256": digest(catalog), "summary": summaries(results), "cases": results,
              "sources": {str(y): d["sources"] for y, d in prepared.items()},
              "added_players": {str(y): d["added_players"] for y, d in prepared.items()}}
    write_json(root/"backtest.json", report)
    return {"scenarios": len(results), "summaries": len(report["summary"]), "decision_sha256": report["decision_sha256"]}
