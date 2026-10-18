# RotoWire timing and position-scarcity mock results

Keep the scheduled **RotoWire board with the existing ESPN-rank next-pick timing**. None of the tested refinements earns promotion. Wider timing windows secure more RotoWire targets and improve the board's own rank metric, but reduce ESPN's projected roster points. The positional rule gives inconsistent gains and can pass over an early star for position coverage.

These are **2,112 completed forward draft simulations**, not drafts in ESPN rooms or historical season outcomes. Six policies use the same 352 field/slot/seed settings, covering all 16 possible positions. No live policy, API execution rule or scheduled automation changed.

## Paired results

The main comparison pools 320 noisy settings per policy: ten seeds at each of 16 slots in each of two opponent fields. Percentages are the mean within-setting change versus the current policy. Starting-nine points/game assumes those players are available; it does not model daily schedules or weekly wins.

| Policy | RotoWire ordinal-sum improvement | ESPN projected season points | Projected starting-nine points/game | Deferred target lost before next turn |
| --- | ---: | ---: | ---: | ---: |
| Current timing | 0 | Baseline | Baseline | 18.13% |
| Timing window +4 players | +18.41 | -0.74% | -0.69% | 10.09% |
| Timing window +8 players | +24.05 | -1.13% | -0.94% | 4.92% |
| Position scarcity within 3 RotoWire ranks | +2.62 | -0.19% | -0.17% | 26.64% |
| +4 window and position scarcity | +20.88 | -1.01% | -0.93% | 23.73% |
| Best available RotoWire, ignoring timing | +23.50 | -2.03% | -1.64% | No deferrals |

Positive ordinal-sum improvement means the roster is ranked better by the completed RotoWire preference order. This is a board-aligned metric, not an independent quality judgment. ESPN completes RotoWire's unpublished tail. No selected player lacked an ESPN projection.

The current policy averages 26,016.5 projected season points and 302.70 starting-nine points/game. The +4 window averages 25,823.6 and 300.56; the +8 window averages 25,722.5 and 299.80. These forecasts disagree with the RotoWire-order metric, so the experiment does not establish which roster would actually perform better.

Deferred-target loss is conditional on each policy's own decisions: the current policy deferred 1,175 targets, +4 deferred 892 and +8 deferred 630. These percentages have different denominators and are not calibrated probabilities of a player surviving. Wider windows both change which targets we pass and reduce the number of passes.

## Opponent and slot sensitivity

| Opponent field | Settings per policy | +4 season points | +8 season points | Scarcity season points | Combined season points | Greedy season points |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Deterministic ESPN rank | 16 | -0.61% | -0.97% | +0.06% | -1.05% | -2.04% |
| Deterministic ADP-led | 16 | -0.81% | -1.06% | -0.12% | -1.06% | -1.98% |
| Typical: 80% ADP / 20% rank | 160 | -0.79% | -1.12% | -0.30% | -1.23% | -2.08% |
| Loose: 60% ADP / 40% rank | 160 | -0.69% | -1.14% | -0.09% | -0.80% | -1.97% |

Against the noisy fields, neither buffer improved mean projected season points at any of the 16 slots. Scarcity improved that proxy at six slots, with slot means ranging from -1.35% to +0.54%; the combined policy improved it at one slot. Each slot has only 20 noisy settings, so this does not justify selecting a special rule after discovering our draft position.

Scarcity reduced late coverage pressure from 0.181 to 0.116 selections per draft; combining it with +4 reduced that to 0.084. Pressure means rounds 9–12 where the number of unfilled starter slots equals the remaining roster selections. Every final roster still covered all nine starters under every policy. The coverage benefit did not translate into a consistent projected-points gain.

## Fixed example: slot 8, typical field, seed 0

This example was selected in the implementation before evaluation, rather than chosen for its results. The +4 policy matches the current roster throughout; the combined policy matches scarcity throughout. All six full examples and player IDs are in the [aggregate JSON](basketball_timing_lab_results.json).

| Overall pick | Current timing | +8 window | Scarcity |
| --- | --- | --- | --- |
| 8 | Giannis Antetokounmpo | Giannis Antetokounmpo | Cooper Flagg |
| 25 | Bam Adebayo | Paolo Banchero | Bam Adebayo |
| 40 | Paolo Banchero | Stephon Castle | Paolo Banchero |
| 57 | Donovan Clingan | Matas Buzelis | Donovan Clingan |
| 72 | Matas Buzelis | Donovan Clingan | Matas Buzelis |
| 89 | Derik Queen | Derik Queen | Derik Queen |
| 104 | Cedric Coward | Cedric Coward | Cedric Coward |
| 121 | Nic Claxton | Nic Claxton | Nic Claxton |
| 136 | Davion Mitchell | Day'Ron Sharpe | Davion Mitchell |
| 153 | Rui Hachimura | Rui Hachimura | Rui Hachimura |
| 168 | Collin Murray-Boyles | Collin Murray-Boyles | Collin Murray-Boyles |
| 185 | Ajay Mitchell | Ajay Mitchell | Ajay Mitchell |

The scarcity rule chooses Flagg (published RotoWire rank 7) over Giannis (rank 4) at pick 8. The rule permits this because the gap is three ordinal ranks and Flagg improves weighted core-position coverage. That is a concrete reason to reject this formulation: a small rank gap does not establish similar player value. We did not retune its threshold after seeing this result.

## Method and limits

- The [protocol](BASKETBALL_TIMING_LAB_PROTOCOL.md) was committed before evaluation. Choices were locked before calculating scores. The current policy uses the first N+1 remaining ESPN-ranked players when N opponent selections remain before our next turn. Buffers expand that window by four or eight players. Final/consecutive picks do not get a timing buffer.
- Scarcity only considers legal players within three published RotoWire ranks of the best player in the selected urgency tier. It estimates future supply from ESPN order, then exactly matches distinct core slots to current players. It does not inspect actual future opponent choices or use projected points for selection.
- Sources are the selected October 16 RotoWire points board, the October 17 ESPN public fantasy capture (19:08 Eastern), and verified research roster/injury evidence (17:36 Eastern). All inputs were under 24 hours old at execution. The market capture contains 3,228 unique identities and 411 valid ESPN STANDARD ranks; the candidate pool contains 352 verified active players, including 193 published RotoWire matches.
- Opponents draft from the 352 candidates; timing demand includes all 411 ranked identities, matching the live timing module. Unavailable or personally banned players can therefore make timing conservative. Buffer effects cannot be attributed exclusively to opponents reaching. Opponents do not inherit our personal bans.
- The ADP-led fields retain the previously disclosed ESPN-rank fallback at ADP >=130. Noise scales are assumptions, not calibrated human behavior. Paired queues are shared across policies. These overlapping scenarios are not independent seasons.
- All policies use identical roster legality, full starter coverage, center cap, personal bans and sourced injury windows. Injury gates allow returns within 14 days in rounds 1–4, within 42 days in rounds 5–8, and known returns before the season end from round 9. There is no injured-player count limit.
- All 12 assets count toward season-point forecasts; the starting-nine metric optimizes nine eligible starters by projected points/game. Neither models streaming, opponent matchup scores, weekly schedules, playoffs or realized injuries. ESPN forecast values may align with its market rankings; their advantage here is not proof of superior actual-season results.

## Verification and reproduction

Fourteen focused backend tests passed. All 2,112 complete logs were checked for 192 unique selections, legal final rosters, full starter coverage and our bans. All 4,224 baseline selections were independently replayed through the production `draft_timing.prioritize` path and matched. A performance optimization preserved 54 complete decision logs exactly before the final experiment.

Run `python -m basketball research timing-mocks` with the pinned local captures and selected source to reproduce the fixed grid. The evidence-age guard rejects stale captures rather than silently treating them as current. Large local logs are ignored under `basketball/data/research-timing/`; portable metadata, summaries, per-slot results and all six representative rosters are in [the aggregate evidence](basketball_timing_lab_results.json).

Locked decision SHA-256: `0c4fffec97445efa7e139d879d247c9ffa6cd5870053f37cc1a188698345989a`.
