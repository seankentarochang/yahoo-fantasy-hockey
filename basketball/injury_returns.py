"""Sourced return estimates and draft-price rules; never a medical clearance."""
from datetime import date

from .config import instant, now, path, read_json, write_json


def estimate(records, at):
    dates = []
    for record in records:
        value = record.get("return_date")
        if not value:
            continue
        try:
            dates.append(date.fromisoformat(value) if len(value) == 10 else instant(value).date())
        except (ValueError, TypeError):
            return {"expected_return": None, "days_out": None, "certainty": "invalid provider estimate"}
    # Take the latest structured date if profile, roster and report disagree.
    expected = max(dates) if dates else None
    if any(not r.get("return_date") and (r.get("description") or r.get("designation")) for r in records):
        return {"expected_return": None, "days_out": None, "certainty": "an injury has no published return date"}
    days = (expected-at.date()).days if expected else None
    if days is not None and days < 0:
        return {"expected_return": expected.isoformat(), "days_out": days, "certainty": "overdue estimate; needs an update"}
    return {"expected_return": expected.isoformat() if expected else None, "days_out": days,
            "certainty": "provider estimate; not a guaranteed return" if expected else "no published return date"}


def catalog(cfg, refresh=False, sources=None):
    from .availability import SITE, Sources, athlete_id, fresh, injury_record
    sources = sources or Sources(cfg)
    at = now(cfg)
    report = sources.get(SITE+"injuries", refresh)
    if (report.get("status") != "success" or report.get("season", {}).get("year") != cfg["season"]
            or not fresh(report.get("timestamp"), at) or not isinstance(report.get("injuries"), list)):
        raise ValueError("Current injury report season/freshness/coverage is unverified")
    grouped = {}
    for group in report["injuries"]:
        if not isinstance(group.get("injuries"), list):
            raise ValueError("Incomplete injury team record")
        for row in group["injuries"]:
            athlete = row.get("athlete", {})
            pid = athlete_id(athlete)
            entry = grouped.setdefault(pid, {"id": pid, "name": athlete.get("displayName", str(pid)), "injuries": []})
            entry["injuries"].append(injury_record(row))
    rows = [{**entry, **estimate(entry["injuries"], at),
             "out_for_season": any(r.get("designation") == "OFS" for r in entry["injuries"])} for entry in grouped.values()]
    result = {"season": cfg["season"], "checked_at": at.isoformat(), "source_as_of": report["timestamp"],
              "source": SITE+"injuries", "players": sorted(rows, key=lambda r: (r["expected_return"] or "9999", r["name"]))}
    write_json(path(cfg, "injury-returns.json"), result)
    markdown = ["# Expected injury returns", "", "Checked: " + result["checked_at"], "",
                "Provider estimates can change. Notes may describe a broader return window than the structured date. "
                "An estimate does not guarantee a return or override a season-out designation or a ban.", "",
                "| Player | Estimated return | Status | Provider note |", "|---|---|---|---|"]
    for r in result["players"]:
        notes = " / ".join(dict.fromkeys(i["description"] for i in r["injuries"] if i["description"]))
        status = "Out for season — blocked" if r["out_for_season"] else " / ".join(dict.fromkeys(i["status"] or "Unknown" for i in r["injuries"]))
        markdown.append("| " + " | ".join(str(x).replace("|", "/").replace("\n", " ") for x in
                                           (r["name"], r["expected_return"] or "Unknown", status, notes)) + " |")
    markdown += ["", "Source: " + result["source"], ""]
    path(cfg, "injury-returns.md").write_text("\n".join(markdown), encoding="utf-8")
    return result


def assess(cfg, records):
    """No injured-player count limit. Longer absences require a later price."""
    policy = cfg.get("draft", {}).get("injury_policy")
    if not policy:
        return None
    for key in ("early_rounds", "early_days", "middle_days", "late_round"):
        if type(policy.get(key)) is not int or policy[key] < 0:
            raise ValueError("Invalid draft injury policy")
    if policy["early_rounds"] >= policy["late_round"] or policy["early_days"] > policy["middle_days"]:
        raise ValueError("Invalid draft injury round windows")
    season_end = date.fromisoformat(policy["season_end"])
    if season_end.year != cfg["season"]:
        raise ValueError("Injury policy season end does not match the draft season")
    at = now(cfg)
    result = estimate(records, at)
    picks = read_json(path(cfg, "draft.json"), {"picks": []})["picks"]
    round_number = 1+sum(p["team"] == cfg["team_id"] for p in picks)
    days = result["days_out"]
    latest_news = [instant(r["published_at"]) for r in records if r.get("published_at")]
    if any(t > at for t in latest_news):
        raise ValueError("Injury record is dated in the future")
    allowed = days is not None and days >= 0 and date.fromisoformat(result["expected_return"]) <= season_end
    if allowed:
        if round_number <= policy["early_rounds"]:
            allowed = days <= policy["early_days"]
        elif round_number < policy["late_round"]:
            allowed = days <= policy["middle_days"]
        else:
            allowed = date.fromisoformat(result["expected_return"]) <= season_end
    return {**result, "round": round_number, "allowed": allowed, "policy": policy,
            "reason": "Known absence fits this draft round" if allowed else "Return estimate is unknown, overdue, or too distant for this draft round"}
