"""Defer expert targets the ESPN market expects to survive our next turn."""
from .config import roster_size
from .drafting import snake_picks, state


def window(model, slot=None):
    picks = state(model)["picks"]
    if sorted(p["pick"] for p in picks) != list(range(1, len(picks)+1)) or len({p["player"] for p in picks}) != len(picks):
        raise ValueError("Timing requires unique, consecutive authoritative picks")
    current = len(picks)+1
    order = model.snapshot.get("settings", {}).get("draftSettings", {}).get("pickOrder", [])
    slot = order.index(model.cfg["team_id"])+1 if model.cfg["team_id"] in order else slot or model.cfg["draft"].get("slot")
    if type(slot) is not int or not 1 <= slot <= model.cfg["teams"]:
        raise ValueError("Timing requires our confirmed snake draft slot")
    turns = snake_picks(model.cfg["teams"], slot, roster_size(model.cfg))
    turn = next((p for p in turns if p >= current), None)
    following = next((p for p in turns if turn is not None and p > turn), None)
    if turn is not None and sum(p["team"] == model.cfg["team_id"] for p in picks) != turns.index(turn):
        raise ValueError("Our selections disagree with the confirmed snake slot")
    return {"pick": turn, "next_pick": following, "current_pick": current}


def prioritize(model, players, slot=None):
    timing = window(model, slot)
    following = timing["next_pick"]
    if following is None:
        return players, [], {**timing, "reason": "Final team pick: take best eligible expert player"}
    gap = following-timing["pick"]-1
    if gap == 0:
        return players, [], {**timing, "opponent_picks": 0, "reason": "Consecutive team picks: take best expert first"}
    gone = {p["player"] for p in state(model)["picks"]}
    # Opponents do not share our bans, position needs or injury preferences.
    market = sorted((p for p in model.players if p["id"] not in gone and p["owner"] in (0, model.cfg["team_id"])
                     and type(p.get("draft_rank")) is int and 0 < p["draft_rank"] < 999),
                    key=lambda p: (p["draft_rank"], p["id"]))
    positions = {p["id"]: i+1 for i, p in enumerate(market)}
    # Include our own selection in the demand window: taking another urgent
    # player shifts the next player into the opponents' intervening picks.
    urgent_ids = {p["id"] for p in market[:gap+1]}
    urgent, deferred = [], []
    for p in players:
        rank = p.get("espn_rank")
        if type(rank) is not int or not 0 < rank < 999:
            raise ValueError("Timing requires a valid ESPN STANDARD rank")
        row = dict(p, remaining_market_position=positions.get(p["id"]))
        (urgent if p["id"] in urgent_ids else deferred).append(row)
    # Deferred players are retained as a second tier. Only after every urgent
    # legal player fails availability do we use this tier, never on expert rank
    # alone. A final pick has no reason to defer anyone.
    return urgent, deferred, {**timing, "opponent_picks": gap, "market_window": gap+1,
                             "reason": "Prefer expert players inside the remaining ESPN demand window before our next turn",
                             "note": "ESPN rank is a market heuristic, not a calibrated survival probability"}
