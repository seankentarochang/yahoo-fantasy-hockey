"""Comparison-only forecasts from prior statistics, forward projections and research.

This module has no draft transport, credentials, live-source selector or scheduler.
"""
from concurrent.futures import ThreadPoolExecutor
from collections import Counter
from datetime import datetime
from html.parser import HTMLParser
import hashlib
import json
import math
from pathlib import Path
import re
import statistics
import urllib.request

from . import bans
from .availability import SITE, Sources, fresh
from .backtest import BASE, digest, get_json, parse_totals
from .config import ROOT, instant, now, path, read_json, write_json
from .draft_advisor import orders
from .injury_returns import catalog
from .model import Model
from .strategy_lab import key

HASHTAG = "https://hashtagbasketball.com/fantasy-basketball-projections"
BREF = "https://www.basketball-reference.com/friv/projections.cgi?year={season}"
FANTASYPROS = "https://www.fantasypros.com/nba/projections/overall.php"
DARKO = "https://www.darko.app/projections"
PARAMETERS = {"history_weights": [0.6, 0.3, 0.1], "history_cap": 0.65,
              "changed_role_cap": 0.35, "prior_minutes": 750, "forward_games_weight": 0.75,
              "season_games": 82, "version": 2}
STATS = ("PTS", "FGM", "FGA", "FTM", "FTA", "3PM", "REB", "AST", "STL", "BLK", "TO")


class PublicTable(HTMLParser):
    """Read the public table, ignoring the duplicate mobile player-name link."""
    def __init__(self, text):
        super().__init__()
        self.rows, self.row, self.cell = [], None, None
        self.text = []
        self.skip_anchor = False
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "tr": self.row = []
        if tag in {"td", "th"} and self.row is not None: self.cell = []
        if tag == "a" and "HyperLinkShort" in attrs.get("id", ""): self.skip_anchor = True

    def handle_data(self, text):
        self.text.append(text)
        if self.cell is not None and not self.skip_anchor: self.cell.append(text)

    def handle_endtag(self, tag):
        if tag == "a": self.skip_anchor = False
        if tag in {"td", "th"} and self.cell is not None:
            self.row.append(" ".join("".join(self.cell).split()))
            self.cell = None
        if tag == "tr" and self.row is not None:
            self.rows.append(self.row)
            self.row = None


def line_valid(stats, games, minutes):
    if (type(games) not in (int,float) or type(minutes) not in (int,float)
            or not all(k in stats for k in STATS) or not all(type(stats[k]) in (int, float) and math.isfinite(stats[k]) and stats[k] >= 0 for k in STATS)
            or not math.isfinite(games) or not 0 < games <= 82 or not math.isfinite(minutes) or not 0 < minutes <= 48):
        return False
    return (stats["FGM"] <= stats["FGA"] and stats["FTM"] <= stats["FTA"] and stats["3PM"] <= stats["FGM"]
            and abs(stats["PTS"]-(2*stats["FGM"]+stats["3PM"]+stats["FTM"])) <= 0.6)


def public_projections(text, season):
    if f"{season-1}-{str(season)[-2:]}" not in text:
        raise ValueError("Hashtag preview is for a different season")
    page = PublicTable(text)
    updated = set(re.findall(r"Updated:\s*(\d{1,2} [A-Za-z]+ \d{4})", " ".join(page.text)))
    if len(updated) != 1:
        raise ValueError("Hashtag preview has no publication/update date")
    header = ["R#", "PLAYER", "ADP", "POS", "TEAM", "GP", "MPG", "FG%", "FT%", "3PM", "PTS", "TREB", "AST", "STL", "BLK", "TO", "TOTAL"]
    if header not in page.rows:
        raise ValueError("Hashtag projection header changed")
    rows, seen = [], set()
    for row in page.rows:
        if row == header:
            continue
        if not row or not re.match(r"^\d", row[0]):
            continue
        if len(row) != len(header):
            raise ValueError("Hashtag public projection columns changed")
        raw = dict(zip(header, row))
        if key(raw["PLAYER"]) in seen:
            raise ValueError("Duplicate public projection identity")
        seen.add(key(raw["PLAYER"]))
        shooting = [re.search(r"\(([\d.]+)/([\d.]+)\)", raw[c]) for c in ("FG%", "FT%")]
        if not all(shooting):
            raise ValueError("Shooting attempts are missing; never infer them from rounded percentages")
        stats = {k: float(raw[c]) for k,c in (("PTS","PTS"),("3PM","3PM"),("REB","TREB"),("AST","AST"),("STL","STL"),("BLK","BLK"),("TO","TO"))}
        stats.update(FGM=float(shooting[0][1]), FGA=float(shooting[0][2]), FTM=float(shooting[1][1]), FTA=float(shooting[1][2]))
        games, minutes = float(raw["GP"]), float(raw["MPG"])
        if not line_valid(stats, games, minutes):
            raise ValueError("Invalid complete public projection line")
        rows.append({"name":raw["PLAYER"], "team":raw["TEAM"], "games":games, "minutes":minutes, "stats":stats})
    if len(rows) != 30:
        raise ValueError("Expected the 30-row public preview; review coverage changes explicitly")
    return rows, updated.pop()


def bref_projections(text, season):
    """Read only the explicitly projected per-36 lines, never historical rows."""
    if f"{season-1}-{str(season)[-2:]} Simple Projection System" not in text:
        raise ValueError("Basketball Reference projection season is unverified")
    page = PublicTable(text)
    header = ["Rk", "Player", "Type", "FG", "FGA", "3P", "3PA", "FT", "FTA", "ORB", "TRB", "AST", "STL", "BLK", "TOV", "PF", "PTS", "FG%", "3P%", "FT%"]
    if header not in page.rows:
        raise ValueError("Basketball Reference projection columns changed")
    rows, seen = [], set()
    for row in page.rows:
        if len(row) < 3 or row[2] != "Projected":
            continue
        if len(row) != len(header):
            raise ValueError("Malformed Basketball Reference projected row")
        raw = dict(zip(header, row))
        stats = {k:float(raw[c]) for k,c in (("PTS","PTS"),("FGM","FG"),("FGA","FGA"),("FTM","FT"),("FTA","FTA"),("3PM","3P"),("REB","TRB"),("AST","AST"),("STL","STL"),("BLK","BLK"),("TO","TOV"))}
        if not line_valid(stats,82,36) or key(raw["Player"]) in seen:
            raise ValueError("Invalid or duplicate Basketball Reference projection")
        seen.add(key(raw["Player"]))
        rows.append({"name":raw["Player"],"rates":{k:v/36 for k,v in stats.items()}})
    if len(rows) < 400:
        raise ValueError("Basketball Reference projection coverage is incomplete")
    return rows


def fantasypros_opportunities(text, season):
    if f"{season-1}-{str(season)[-2:]} Projections" not in text:
        raise ValueError("FantasyPros projection season is unverified")
    page = PublicTable(text)
    header = ["Player","PTS","REB","AST","BLK","STL","FG%","FT%","3PM","GP","MIN","TO"]
    if header not in page.rows:
        raise ValueError("FantasyPros projection columns changed")
    dates = set(re.findall(r"Consensus last updated\s+([A-Za-z]+ \d{1,2}, \d{4})", " ".join(page.text)))
    if len(dates) != 1:
        raise ValueError("FantasyPros projection date is unverified")
    rows, seen = [], set()
    for row in page.rows:
        if len(row) != len(header) or row == header:
            continue
        match = re.fullmatch(r"(.+?)\s+\(([A-Z]+) - [^)]+\)(?:\s+\w+)?",row[0])
        if not match:
            raise ValueError("FantasyPros projection identity is unverified")
        games, total_minutes = float(row[9].replace(",","")),float(row[10].replace(",",""))
        if not (math.isfinite(games) and 0 < games <= 82 and math.isfinite(total_minutes) and 0 < total_minutes/games <= 48):
            raise ValueError("Invalid FantasyPros playing-time forecast")
        if key(match[1]) in seen:
            raise ValueError("Duplicate FantasyPros identity")
        seen.add(key(match[1]))
        rows.append({"name":match[1],"team":match[2],"games":games,"minutes":total_minutes/games})
    if len(rows) < 200:
        raise ValueError("FantasyPros public projection coverage is incomplete")
    return rows, dates.pop()


def darko_audit(text):
    """Parse public export inputs as data; never execute publisher JavaScript."""
    match = re.search(r'players:(\[\{nba_id:.*?\}\]),asOf:"(\d{4}-\d{2}-\d{2})"',text,re.S)
    if not match:
        raise ValueError("DARKO public projection data format changed")
    data = re.sub(r'([{,])(\w+):',r'\1"\2":',match[1])
    data = re.sub(r'(:|,)(-?)\.(\d)',r'\g<1>\g<2>0.\3',data)
    rows = json.loads(data)
    if len(rows) < 400 or len({p["nba_id"] for p in rows}) != len(rows):
        raise ValueError("DARKO projection coverage/identities are incomplete")
    problems=[]
    for p in rows:
        if p["x_fg3a_100"] > p["x_fga_100"]:
            problems.append({"name":p["player_name"],"reason":"Projected 3PA exceeds FGA"})
    return {"as_of":match[2],"players":rows,"quality_issues":problems,"used_in_model":False,
            "reason":"Stale playing time/rosters; separately estimated box-score components need further validation"}


def verify_public_date(value, fmt, captured):
    day = datetime.strptime(value,fmt).date()
    age = (instant(captured).date()-day).days
    if not 0 <= age <= 30:
        raise ValueError("Current forward projection publication date is stale or in the future")


def match_outside(rows, inputs, team_required):
    identities={}
    for player in inputs["snapshot"]["players"]:
        identities.setdefault(key(player["name"]),[]).append(player["id"])
    def abbreviation(value):
        value={"was":"wsh","uth":"utah","uta":"utah","nor":"no"}.get(value.lower(),value.lower())
        return bans.TEAM_ALIASES.get(value,value)
    matched, unmatched = {}, []
    for row in rows:
        candidates=identities.get(key(row["name"]),[])
        roster=inputs["rosters"].get(str(candidates[0])) if len(candidates)==1 else None
        if roster and (not team_required or abbreviation(row["team"])==abbreviation(roster["abbreviation"])):
            matched[candidates[0]]=row
        else:
            unmatched.append(row["name"])
    return matched,unmatched


def history(raw, year):
    result = parse_totals(raw, year)
    general = next(c["names"] for c in raw["categories"] if c["name"] == "general")
    minute_index = general.index("minutes")
    for row in raw["athletes"]:
        pid = int(row["athlete"]["id"])
        values = next(c["values"] for c in row["categories"] if c["name"] == "general")
        minutes = float(values[minute_index])
        if not math.isfinite(minutes) or minutes < 0:
            raise ValueError("Invalid historical minutes")
        result[pid].update(minutes=minutes, team=str(row["athlete"].get("teamId", "")))
    return result


def fetch_bytes(url):
    req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0", "Cache-Control":"no-cache"})
    with urllib.request.urlopen(req, timeout=20) as response:
        if response.geturl() != url:
            raise ValueError("Research source redirected; inspect its identity first")
        return response.read()


def collect(cfg):
    if cfg["format"] != "points" or cfg["season"] != 2027:
        raise ValueError("Research board is explicitly for this 2026-27 points league")
    root = path(cfg, "research-board")
    root.mkdir(parents=True, exist_ok=True)
    captured, records = now(cfg).isoformat(), []

    def capture(name, data, url):
        data = data if isinstance(data, bytes) else json.dumps(data, ensure_ascii=False).encode()
        filename = "captures/"+name+"-"+hashlib.sha256(data).hexdigest()[:12]+".raw"
        target = root/filename
        target.parent.mkdir(exist_ok=True)
        if target.exists() and target.read_bytes() != data:
            raise ValueError("Research capture identity collision")
        target.write_bytes(data)
        records.append({"name":name,"file":filename,"url":url,"sha256":hashlib.sha256(data).hexdigest(),"captured_at":captured})

    snapshot = read_json(path(cfg,"snapshot.json"))
    if not snapshot or snapshot.get("season") != cfg["season"]:
        raise ValueError("A current ESPN-normalized snapshot is required")
    if not 0 <= (now(cfg)-instant(snapshot["fetched_at"])).total_seconds() <= 86400:
        raise ValueError("Refresh the comparison snapshot; it is older than 24 hours")
    capture("snapshot", snapshot, "local saved ESPN league snapshot (no authentication data)")
    histories = {}
    for year in range(cfg["season"]-3,cfg["season"]):
        url = f"{BASE}?season={year}&seasontype=2&limit=1000&isqualified=false"
        raw = get_json(url,root/"raw"/f"totals-{year}.json")
        histories[str(year)] = history(raw,year)
        capture(f"stats-{year}",raw,url)
    raw = fetch_bytes(HASHTAG)
    preview, updated = public_projections(raw.decode("utf-8-sig"),cfg["season"])
    verify_public_date(updated,"%d %B %Y",captured)
    capture("hashtag",raw,HASHTAG)
    url = BREF.format(season=cfg["season"])
    raw = fetch_bytes(url)
    bref = bref_projections(raw.decode("utf-8-sig"),cfg["season"])
    capture("basketball-reference",raw,url)
    raw = fetch_bytes(FANTASYPROS)
    opportunities, fp_updated = fantasypros_opportunities(raw.decode("utf-8-sig"),cfg["season"])
    verify_public_date(fp_updated,"%b %d, %Y",captured)
    capture("fantasypros",raw,FANTASYPROS)
    raw = fetch_bytes(DARKO)
    darko = darko_audit(raw.decode("utf-8-sig"))
    capture("darko",raw,DARKO)
    sources = Sources(cfg)
    teams = sources.get(SITE+"teams?limit=100",refresh=True)
    entries = [r["team"] for s in teams["sports"] for l in s["leagues"] for r in l["teams"]]
    if len(entries) != 30 or len({t["id"] for t in entries}) != 30:
        raise ValueError("NBA team catalog is incomplete")
    capture("teams",teams,SITE+"teams?limit=100")

    def roster(team):
        url = SITE+f"teams/{team['id']}/roster"
        raw = sources.get(url,refresh=True)
        if (raw.get("season",{}).get("year") != cfg["season"] or str(raw.get("team",{}).get("id")) != str(team["id"])
                or not fresh(raw.get("timestamp"),now(cfg)) or not isinstance(raw.get("athletes"),list)):
            raise ValueError("Public NBA roster identity/season/freshness is unverified")
        return team,raw,url

    rosters = {}
    with ThreadPoolExecutor(max_workers=5) as executor:
        for team,raw,url in executor.map(roster,entries):
            capture("roster-"+str(team["id"]),raw,url)
            for athlete in raw["athletes"]:
                pid = str(athlete["id"])
                if pid in rosters:
                    raise ValueError("Player appears on multiple current NBA rosters")
                rosters[pid] = {"team":str(team["id"]),"team_name":team["displayName"],"abbreviation":team["abbreviation"],
                                "status":(athlete.get("status") or {}).get("type")}
    injuries = catalog(cfg,refresh=True,sources=sources)
    capture("injuries",injuries,injuries["source"])
    context = read_json(ROOT/"research_context.json")
    if context["season"] != cfg["season"]:
        raise ValueError("Role research belongs to a different season")
    for i,note in enumerate(context["team_role_changes"]):
        raw = fetch_bytes(note["source"])
        if b"2026-27 Season Preview" not in raw:
            raise ValueError("Role research source has an unexpected season/title")
        capture(f"role-{i}",raw,note["source"])
    capture("role-context",context,"basketball/research_context.json; sourced research interpretations")
    _,_,published,details = orders(Model(cfg,snapshot),"rotowire",path(cfg,"ranking-library"))
    inputs = {"season":cfg["season"],"as_of":captured,"scoring":cfg["scoring"],"snapshot":snapshot,"history":histories,
              "public_projections":preview,"public_updated":updated,"rosters":rosters,"injuries":injuries,"context":context,
              "bref_projections":bref,"fantasypros_opportunities":opportunities,"fantasypros_updated":fp_updated,"darko":darko,
              "comparison_ranks":published["rotowire"],"comparison_sources":details,"bans":bans.listing(cfg)}
    # Normalize numeric mapping keys before hashing so a saved/reloaded pack is
    # exactly the same input, including its deterministic key ordering.
    inputs = json.loads(json.dumps(inputs))
    capture("inputs",inputs,"normalized comparison-only inputs")
    manifest = {"version":2,"parameters":PARAMETERS,"as_of":captured,"records":records,"inputs_sha256":digest(inputs)}
    write_json(root/"inputs.json",inputs)
    write_json(root/"manifest.json",manifest)
    return {"captured_sources":len(records),"public_projection_rows":len(preview),"bref_rows":len(bref),"fantasypros_rows":len(opportunities),"darko_rows":len(darko["players"]),"public_roster_players":len(rosters),
            "injured_players":len(injuries["players"]),"inputs_sha256":manifest["inputs_sha256"],"comparison_only":True}


def forecast(player, inputs, public=None, bref=None, opportunities=None):
    """A fixed numeric model. Comparison ranks and draft order are not features."""
    pid, season = player["id"], inputs["season"]
    forward, flags = [], []
    for split in player.get("splits",[]):
        stats = split.get("stats",{})
        if split.get("season") != season or split.get("source") != 1 or not stats.get("GP") or not stats.get("MIN"):
            continue
        gp, mpg = stats["GP"],stats["MIN"]/stats["GP"]
        pg = {k:stats[k]/gp for k in STATS if k in stats}
        if line_valid(pg,gp,mpg):forward.append({"family":"ESPN","stats":pg,"minutes":mpg,"games":gp})
    if len(forward) > 1:
        raise ValueError("Ambiguous current ESPN statistical projection")
    if public:
        if not line_valid(public["stats"],public["games"],public["minutes"]):
            raise ValueError("Invalid outside projection")
        forward.append({**public,"family":"Hashtag"})
    if not forward:
        return None
    histories = [(season-i,w,inputs["history"].get(str(season-i),{}).get(str(pid))) for i,w in enumerate(PARAMETERS["history_weights"],1)]
    minutes = sum(w*p["minutes"] for _,w,p in histories if p and p["minutes"]>0)
    historical = {k:sum(w*p["stats"][k] for _,w,p in histories if p and p["minutes"]>0)/minutes for k in STATS} if minutes else {}
    current = inputs["rosters"][str(pid)]
    recent = next((p for _,_,p in histories if p),None)
    changed_team = recent is not None and recent["team"] != current["team"]
    contexts = [n for n in inputs["context"]["team_role_changes"] if n["team"] == current["team"]]
    cap = PARAMETERS["changed_role_cap"] if changed_team or contexts else PARAMETERS["history_cap"]
    weight = min(cap,minutes/(minutes+PARAMETERS["prior_minutes"]))
    rates=[{"family":p["family"],"rates":{k:p["stats"][k]/p["minutes"] for k in STATS}} for p in forward]
    if bref:
        if set(bref["rates"]) != set(STATS) or not line_valid({k:v*36 for k,v in bref["rates"].items()},82,36):
            raise ValueError("Invalid Basketball Reference per-minute forecast")
        rates.append({**bref,"family":"Basketball Reference"})
    playing_time=[{"family":p["family"],"minutes":p["minutes"],"games":p["games"]} for p in forward]
    if opportunities:
        if not (0 < opportunities["games"] <= 82 and 0 < opportunities["minutes"] <= 48):
            raise ValueError("Invalid outside playing-time forecast")
        playing_time.append({**opportunities,"family":"FantasyPros"})
    mpg = statistics.mean(p["minutes"] for p in playing_time)
    rate = {k:statistics.mean(p["rates"][k] for p in rates) for k in STATS}
    per_game = {k:mpg*(weight*historical.get(k,0)+(1-weight)*rate[k]) for k in STATS}
    expected_games = statistics.mean(p["games"] for p in playing_time)
    debut = min((y for y,_,p in histories if p),default=season)
    durable = [(w,p["stats"]["GP"] if p else 0) for y,w,p in histories if y>=debut]
    historical_games = sum(w*gp for w,gp in durable)/sum(w for w,_ in durable) if durable else None
    if historical_games is not None:
        expected_games = PARAMETERS["forward_games_weight"]*expected_games+(1-PARAMETERS["forward_games_weight"])*historical_games
    expected_games = min(PARAMETERS["season_games"],expected_games)
    injury = next((p for p in inputs["injuries"]["players"] if p["id"]==pid),None)
    injury_cap = None
    if injury:
        if injury["out_for_season"]:
            return None
        if injury.get("days_out") is not None and injury["days_out"]>=0:
            schedule = inputs["snapshot"].get("games",{}).get(current["team"],[])
            dates = {g["id"]:g["date"] for g in schedule if not g.get("cancelled")}
            if dates:
                unknown = max(0,82-len(dates))
                injury_cap = sum(day>=injury["expected_return"] for day in dates.values())+unknown
                expected_games = min(expected_games,injury_cap)
                if unknown: flags.append(f"{unknown} schedule opportunities unassigned")
            else:
                flags.append("No schedule to bound injury absence")
        else:
            flags.append("Unknown or overdue injury return")
    if not minutes:flags.append("Projection-only; no NBA statistical history")
    if len(rates)==1:flags.append("Only ESPN forward statistical rates available")
    if changed_team:flags.append("Changed team; current role given greater weight")
    if contexts:flags.append("Researched role change; current projections given greater weight")
    if minutes and minutes<750:flags.append("Limited historical minutes")
    if len(rates)>1:
        scores=[sum(p["rates"][k]*mpg*inputs["scoring"].get(k,0) for k in STATS) for p in rates]
        disagreement=max(scores)-min(scores)
        if disagreement>5:flags.append("Forward sources differ by >5 fantasy points/game")
    else:disagreement=None
    if expected_games <= 0:
        return None
    if not line_valid(per_game,expected_games,mpg):
        raise ValueError("Forecast generated an invalid stat line")
    fpg=sum(per_game[k]*inputs["scoring"].get(k,0) for k in STATS)
    return {"id":pid,"name":player["name"],"team":current["team_name"],"eligible":player["eligible"],
            "per_game":per_game,"minutes":mpg,"games":expected_games,"fpg":fpg,"season_points":fpg*expected_games,
            "history_weight":weight,"weighted_history_minutes":minutes,"historical_games":historical_games,
            "forward_sources":[p["family"] for p in rates],"playing_time_sources":[p["family"] for p in playing_time],"source_disagreement_fpg":disagreement,
            "injury":injury,"injury_opportunity_cap":injury_cap,"research":contexts,"flags":flags,
            "espn_rank":player.get("draft_rank"),"rotowire_rank":inputs["comparison_ranks"].get(str(pid)),
            "ban":bans.reason({"_data":"unused"},player,current["team"],policy=inputs["bans"])}


def build(cfg):
    root=path(cfg,"research-board")
    manifest,inputs=read_json(root/"manifest.json"),read_json(root/"inputs.json")
    if not manifest or not inputs or manifest["parameters"]!=PARAMETERS or digest(inputs)!=manifest["inputs_sha256"]:
        raise ValueError("Missing or changed research inputs/parameters; collect explicitly")
    if inputs["season"]!=cfg["season"] or inputs["scoring"]!=cfg["scoring"]:
        raise ValueError("Research inputs belong to different scoring/season")
    if any(value and name not in STATS for name,value in inputs["scoring"].items()):
        raise ValueError("Research model does not support all configured scoring components")
    for record in manifest["records"]:
        file=(root/record["file"]).resolve()
        if not file.is_relative_to(root.resolve()) or hashlib.sha256(file.read_bytes()).hexdigest()!=record["sha256"]:
            raise ValueError("Research source capture changed")
    public,unmatched=match_outside(inputs["public_projections"],inputs,True)
    bref,bref_unmatched=match_outside(inputs["bref_projections"],inputs,False)
    opportunities,fp_unmatched=match_outside(inputs["fantasypros_opportunities"],inputs,True)
    rows,excluded=[],[]
    for player in inputs["snapshot"]["players"]:
        roster=inputs["rosters"].get(str(player["id"]))
        if player.get("active") is False or not roster or roster["status"]!="active":
            excluded.append({"id":player["id"],"name":player["name"],"reason":"Not verified active on a current NBA roster"});continue
        row=forecast(player,inputs,public.get(player["id"]),bref.get(player["id"]),opportunities.get(player["id"]))
        if row is None:
            excluded.append({"id":player["id"],"name":player["name"],"reason":"No complete current projection, or out for season"});continue
        rows.append(row)
    rows.sort(key=lambda p:(-p["season_points"],p["id"]))
    pg={p["id"]:i+1 for i,p in enumerate(sorted(rows,key=lambda p:(-p["fpg"],p["id"])))}
    personal=0
    for i,row in enumerate(rows,1):
        row.update(rank=i,per_game_rank=pg[row["id"]])
        if not row["ban"]:personal+=1
        row["personal_rank"]=None if row["ban"] else personal
    report={"version":2,"comparison_only":True,"as_of":inputs["as_of"],"parameters":PARAMETERS,"inputs_sha256":manifest["inputs_sha256"],
            "ranked_players":len(rows),"outside_projection_matches":len(public),"unmatched_outside_projections":unmatched,
            "bref_matches":len(bref),"unmatched_bref":bref_unmatched,"fantasypros_matches":len(opportunities),"unmatched_fantasypros":fp_unmatched,
            "darko_audit":{k:v for k,v in inputs["darko"].items() if k!="players"},
            "statistical_source_coverage":dict(Counter(s for p in rows for s in p["forward_sources"])),
            "playing_time_source_coverage":dict(Counter(s for p in rows for s in p["playing_time_sources"])),
            "rows":rows,"excluded":excluded,"performance_validated":False}
    write_json(root/"rankings.json",report)
    export(root,report)
    return {k:v for k,v in report.items() if k not in {"rows","excluded"}}


def export(root, report):
    lines=["# Our statistical basketball rankings — comparison only","", "As of: "+report["as_of"],"",
           "Forecasts use your exact scoring. Main rank is expected season points; per-game rank is separate. "
           "These forecasts are not performance-validated and do not control the automatic draft. "
           "Totals omit replacement players, weekly lineup constraints and waivers. Bans are marked rather than changing analytical ranks.","",
           f"Ranked players: {report['ranked_players']}. Source identity matches before eligibility filtering: Basketball Reference {report['bref_matches']}; FantasyPros playing time {report['fantasypros_matches']}; Hashtag {report['outside_projection_matches']} (30-row preview). DARKO is captured for inspection, excluded from the model because its playing time/rosters are stale.", "",
           "Statistics coverage on the ranked board: "+str(report["statistical_source_coverage"])+". Playing-time coverage: "+str(report["playing_time_source_coverage"])+".","",
           "Basketball Reference's historical inputs overlap our historical rate estimate; publisher counts are not independent votes. Expert-board differences below are descriptive, not evidence of improved accuracy. Expected games are uncertain; the durability formula can over-penalize a one-off injury.","",
           "| Ours | Player | Fpts/game | Games | Season pts | Per-game rank | RotoWire | ESPN | Notes |",
           "|---:|---|---:|---:|---:|---:|---:|---:|---|"]
    for p in report["rows"]:
        notes=[p["ban"]] if p["ban"] else []
        if p["injury"]:notes.append("Return estimate: "+(p["injury"]["expected_return"] or "unknown"))
        notes+=p["flags"]
        notes.append("Rates: "+", ".join(p["forward_sources"]))
        lines.append(f"| {p['rank']} | {p['name']} | {p['fpg']:.1f} | {p['games']:.1f} | {p['season_points']:.0f} | {p['per_game_rank']} | {p['rotowire_rank'] or '—'} | {p['espn_rank'] or '—'} | {'; '.join(notes)} |")
    lines += ["", "## Research context", ""]
    context={r["source"]:r["note"] for p in report["rows"] for r in p["research"]}
    lines += [f"- [{note}]({url})" for url,note in context.items()]
    lines += ["", "Source provenance and complete stat lines are retained in manifest.json, inputs.json and rankings.json beside this report.",""]
    (root/"rankings.md").write_text("\n".join(lines),encoding="utf-8")
