# RotoWire timing buffers and positional tiebreakers

Comparison-only forward mock simulations. No ESPN room is joined, no credentials are loaded and no live strategy, draft execution module or automation changes. The real draft remains RotoWire plus its current ESPN-rank next-turn window.

Use the existing hash-locked October 17, 2026 evening public ESPN fantasy player capture, selected October 16 RotoWire points board and verified research roster/injury evidence. Reject evidence older than 24 hours. Reuse `adp_mocks.prepare` for the 352 active, roster-verified candidate pool, injury round gates and our bans. Replace its consensus preference order with RotoWire's published order and ESPN completion for its unpublished tail. Keep current league scoring, 16 teams, 12 rounds, nine starters and primary-center maximum four.

## Policies, fixed before evaluation

1. `greedy`: best legal, policy-eligible RotoWire player available.
2. `current`: current production-style timing. For N opponents' selections until our next pick, prioritize the best eligible RotoWire player in the first N+1 remaining ESPN STANDARD-ranked players. Include our current choice in this window, matching `draft_timing.prioritize`. Use the deferred tier only if no urgent legal, injury-eligible candidate exists.
3. `buffer4`: current window plus four market players.
4. `buffer8`: current window plus eight market players.
5. `scarcity3`: current window, with the positional tiebreaker below.
6. `buffer4_scarcity3`: four-player buffer plus that tiebreaker.

Final and consecutive selections follow best-available RotoWire, with no timing buffer. Scarcity may break near ties on consecutive selections, but is disabled on the final selection. Every policy keeps the same hard legality, remaining-starter-coverage, ban and injury rules. No projected points are used for our decisions.

The tiebreaker may choose only among legal players no more than three **published RotoWire rank spots** behind the best player in the chosen urgency tier. Unpublished tail ranks do not create artificial tiers. Forecast which players survive using only the remaining ESPN order beyond the unbuffered N+1 window, not the actual opponent queues or future simulated picks. Among that pool, retain the best 32 RotoWire-ordered players eligible at our following round. For each core starting position PG/SG/SF/PF/C, weight scarcity as 1/(1+number of those 32 players eligible there). Use exact weighted matching of the current roster to the five distinct core slots, handling multi-position players without counting one player twice. Prefer the candidate with the largest marginal weighted coverage, breaking ties by RotoWire order. Full nine-slot coverage remains a separate hard legality requirement. This fixed heuristic does not claim to estimate positional point value or calibrated survival probabilities.

## Opponents and pairing

All 16 snake positions; fields: deterministic ESPN rank, deterministic ADP-led with the existing rank fallback at ADP >=130, typical (80% ADP followers / 20% rank followers, noise scale <=8), and loose (60% / 40%, scale <=16). Reuse the earlier stable seeded preference generator and the same opponent queues across policies and positions. Ten seeds per noisy field; one deterministic seed per control. Total 16*(10+10+1+1)*6 = 2,112 full drafts across 352 paired settings. These are dependent scenarios, not independent seasons or observed human choices.

For baseline fidelity, timing demand includes all 411 valid ESPN-ranked identities, including our banned targets and players that our separate availability gate excludes. Opponents select from the same active 352-player candidate pool as earlier forward simulations, with identical roster and injury constraints; they do not share our bans. This mismatch can make the live-style timing estimate conservative; buffer effects cannot be attributed exclusively to opponent reaches. Report a separate deterministic ESPN-rank field to expose sensitivity to actual market behavior.

## Outcomes and integrity

Lock all choices and full 192-pick logs before calculating aggregate metrics. Hash protocol, code, selected source, inputs and decisions. Do not change policies or choose a winning cutoff after seeing outputs; label any later diagnostics explicitly.

Metrics: completed RotoWire preference ordinal (with disclosed ESPN tail), captured ESPN-projected full-roster season points, the sum of projected fantasy points/game for the best legal starting nine, projection coverage, early primary-center count, late coverage pressure, and the fraction of deferred best legal RotoWire targets selected by opponents before our next turn. Quality/projection metrics are proxies, not future results. Missing projections contribute zero and their counts must be shown. The scoring model's same-day values are used only after choices are locked.

Late coverage pressure counts rounds 9–12 where missing starter slots equal the remaining roster selections before our pick. Deferred-target loss is conditional on our actual simulated choices; different policies need not have the same denominator. A buffered reach means our selection lies beyond the unbuffered demand window, not beyond an absolute ADP or ESPN-rank cutoff. Every full draft must have 192 unique positive player IDs, legal team rosters, full nine-slot coverage and no personal bans on our team.

Compare each policy with `current` in exactly the same field/slot/seed, with means, win/tie shares and slot-level summaries. Show actual complete representative examples and aggregate evidence. A lower rank score is better by that board; an increased projection proxy alone does not justify changing the scheduled strategy. Report material tradeoffs and field dependence.
