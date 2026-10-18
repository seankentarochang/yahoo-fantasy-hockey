"""Close-rank positional scarcity within the existing expert timing tier."""
from . import availability, drafting
from .config import active_slots, roster_size


def coverage(players, slots, weights):
    """Distinct-player slot matching; flexible eligibility never counts twice."""
    masks = {0}
    for player in players:
        masks |= {mask | (1 << i) for mask in tuple(masks) for i, slot in enumerate(slots)
                  if not mask & (1 << i) and slot in player['eligible']}
    return max(sum(w for i, w in enumerate(weights) if mask & (1 << i)) for mask in masks)


def verified_choice(model, candidates):
    best, checks = availability.verified_choice(model, candidates)
    policy = model.cfg['draft'].get('balance')
    if not policy:
        return best, checks
    if policy != {'rank_gap': 3, 'start_round': 2, 'lookahead': 32}:
        raise ValueError('Unknown positional balance policy')
    picks = drafting.state(model)['picks']
    mine = [model.by_id[p['player']] for p in picks if p['team'] == model.cfg['team_id']]
    # Preserve the opening elite choice; rank proximity is not equal value.
    if len(mine) < policy['start_round']-1 or len(mine)+1 >= roster_size(model.cfg):
        return best, checks
    ranks = best.get('published_expert_ranks', {})
    if len(ranks) != 1 or type(next(iter(ranks.values()))) is not int:
        return best, checks
    source, rank = next(iter(ranks.items()))
    near = [p for p in candidates if p.get('timing_tier') == best.get('timing_tier')
            and type(p.get('published_expert_ranks', {}).get(source)) is int
            and rank <= p['published_expert_ranks'][source] <= rank+policy['rank_gap']]
    slots = [s for s in active_slots(model.cfg) if s != 'UTIL']
    future = [model.by_id[p['id']] for p in candidates
              if p.get('timing_tier') == 'likely_available_next_turn'][:policy['lookahead']]
    supply = {s: sum(s in p['eligible'] for p in future) for s in slots}
    weights = [1/(1+supply[s]) for s in slots]
    before = coverage(mine, slots, weights)
    gains = {p['id']: coverage(mine+[model.by_id[p['id']]], slots, weights)-before for p in near}
    base_gain = gains[best['id']]
    alternatives = sorted((p for p in near if gains[p['id']] > base_gain+1e-12),
                          key=lambda p: (-round(gains[p['id']], 12), p['quality_order']))
    selected = best
    for candidate in alternatives:
        result = availability.check(model.cfg, model.by_id[candidate['id']])
        checks.append(result)
        if result['allowed']:
            selected = candidate
            break
    return {**selected, 'balance': {'best_expert_id': best['id'], 'changed': selected['id'] != best['id'],
                                   'rank_gap_limit': policy['rank_gap'], 'future_supply': supply,
                                   'coverage_gain': gains[selected['id']],
                                   'reason': 'Prefer scarce unfilled starter positions within three expert ranks and the same timing tier'}}, checks
