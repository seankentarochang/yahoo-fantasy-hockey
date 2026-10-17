"""Public game-level data downloads and audits, isolated from live draft data."""
import csv
import hashlib
import io
import math
import urllib.request
from concurrent.futures import ThreadPoolExecutor

from .config import now, path, read_json, write_json

RELEASE = "https://github.com/sportsdataverse/sportsdataverse-data/releases/tag/nba_stats_player_boxscores"
DOWNLOAD = "https://github.com/sportsdataverse/sportsdataverse-data/releases/download/nba_stats_player_boxscores/player_boxscores_{year}.csv"
FIELDS = {"PTS":"points","FGM":"field_goals_made","FGA":"field_goals_attempted",
          "FTM":"free_throws_made","FTA":"free_throws_attempted","3PM":"three_pointers_made",
          "REB":"rebounds_total","AST":"assists","STL":"steals","BLK":"blocks","TO":"turnovers"}


def audit(data, year):
    """Keep all original rows; audit only regular-season outcomes for research."""
    reader = csv.DictReader(io.StringIO(data.decode("utf-8-sig")))
    required = set(FIELDS.values()) | {"season","season_type_id","game_id","person_id","team_id","minutes","comment"}
    if not required <= set(reader.fieldnames or []):
        raise ValueError("Game log schema is missing required identifiers/statistics")
    seen, games, players, teams = set(), set(), set(), set()
    counts = {"rows":0,"regular_season_rows":0,"played_rows":0,"dnp_rows":0,"unclassified_zero_stat_rows":0,
              "excluded_other_game_types":0,"minute_second_rollovers":0}
    for row in reader:
        counts["rows"] += 1
        if row["season"] != str(year):
            raise ValueError("Game log contains a different ending season")
        identity = (row["game_id"],row["person_id"])
        if not all(identity) or identity in seen:
            raise ValueError("Missing or duplicate player/game identity")
        seen.add(identity)
        if row["season_type_id"] != "2" or not row["game_id"].startswith("002"):
            counts["excluded_other_game_types"] += 1
            continue
        counts["regular_season_rows"] += 1
        games.add(row["game_id"]); teams.add(row["team_id"])
        if not row["minutes"] and row["comment"]:
            counts["dnp_rows"] += 1
            continue
        if not row["minutes"] and all(row[c] in {"0","0.0"} for c in FIELDS.values()):
            # An untagged all-zero line does not prove a played appearance or
            # a particular absence reason. Keep it separate from known DNPs.
            counts["unclassified_zero_stat_rows"] += 1
            continue
        minute_text = row["minutes"]
        if ":" in minute_text:
            minutes, seconds = minute_text.split(":")
            # Some legacy exports round :59.99 up to :60 without carrying the
            # minute. Preserve the raw CSV and explicitly count this conversion.
            if not 0 <= float(seconds) <= 60:
                raise ValueError("Invalid game clock seconds")
            if float(seconds)==60: counts["minute_second_rollovers"] += 1
            minutes = float(minutes)+float(seconds)/60
        else:
            minutes = float(minute_text)
        stats = {k:float(row[v]) for k,v in FIELDS.items()}
        if (not math.isfinite(minutes) or not 0 <= minutes <= 80
                or any(not math.isfinite(v) or v < 0 or not v.is_integer() for v in stats.values())
                or stats["FGM"] > stats["FGA"] or stats["FTM"] > stats["FTA"]
                or stats["3PM"] > stats["FGM"]
                or stats["PTS"] != 2*stats["FGM"]+stats["3PM"]+stats["FTM"]):
            raise ValueError("Invalid complete game box score")
        counts["played_rows"] += 1
        players.add(row["person_id"])
    if not counts["played_rows"]:
        raise ValueError("No usable regular-season game observations")
    return {**counts,"games":len(games),"players":len(players),"teams":len(teams),
            "id_system":"NBA (not ESPN)","season_convention":"ending year",
            "forecast_data":False,"preseason_capture_proven":False}


def collect(cfg, years):
    years=sorted(set(years))
    if not years or any(type(y) is not int or not 1997 <= y < cfg["season"] for y in years):
        raise ValueError("Choose completed ending seasons from 1997 through last season")
    root=path(cfg,"research-datasets")
    root.mkdir(exist_ok=True,parents=True)
    previous=read_json(root/"manifest.json",{}).get("seasons",[])
    records={r["year"]:r for r in previous}

    def download(year):
        target=root/f"player_boxscores_{year}.csv"
        existing=records.get(year)
        data=target.read_bytes() if target.exists() else None
        if data is not None and existing and hashlib.sha256(data).hexdigest()!=existing["sha256"]:
            raise ValueError("Cached historical dataset hash changed")
        url=DOWNLOAD.format(year=year)
        if data is None:
            with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"BasketballPersonalResearch/1.0"}),timeout=45) as response:
                data=response.read()
        summary=audit(data,year)
        expected_teams=30 if year>=2005 else 29
        if summary["teams"] != expected_teams:
            raise ValueError("Historical season does not cover all NBA teams for its year")
        sha=hashlib.sha256(data).hexdigest()
        if not target.exists():
            temporary=target.with_suffix(".csv.tmp")
            temporary.write_bytes(data); temporary.replace(target)
        return {"year":year,"file":target.name,"url":url,"bytes":len(data),"sha256":sha,
                "captured_at":existing["captured_at"] if existing else now(cfg).isoformat(),**summary}

    with ThreadPoolExecutor(max_workers=3) as executor:
        for record in executor.map(download,years):
            records[record["year"]]=record
    manifest={"source":RELEASE,"seasons":[records[y] for y in sorted(records)],
              "notes":"Historical outcomes only; historical rankings/forecasts need separately dated preseason snapshots. Source code licenses do not imply unrestricted rights to NBA data."}
    write_json(root/"manifest.json",manifest)
    return {"seasons":len(records),"years":sorted(records),"regular_season_played_rows":sum(r["played_rows"] for r in records.values()),
            "games":sum(r["games"] for r in records.values()),"manifest":str(root/"manifest.json")}
