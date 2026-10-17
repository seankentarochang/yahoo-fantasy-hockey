# Data-trained rankings and new-data backtests — October 17, 2026

The learned model improves on last-season-only production forecasts, but does not reliably beat a three-year production average. Its draft strategies fail in 2025–26. These results do not support replacing the current expert strategy.

## What was built

- Ten ending seasons (2017–2026), with 255,085 regular-season player appearances.
- Learned eight volume rates and three shooting percentages; derive makes and points coherently. No expert ranks are production features.
- Training targets 2020–2023; validation 2024 selected ridge alpha 10 from 0.1, 1, 10 and 100. Expanding fits test 2025 and 2026, never using the target season to fit that forecast.
- Final 2026–27 model refits through 2026 on 2,745 player-season observations. Current board: 317 eligible players, 303 with learned production, 14 with a visibly marked existing-comparison fallback because NBA history is insufficient.
- Current games/minutes and injury caps are outside workload assumptions, distinct from learned production. Historical draft tests lack an equivalent dated injury-news feed, which is a substantial limitation.

## Conditional production accuracy

MAE in fantasy points at a fixed 30-minute workload; lower is better. All methods use the same paired veteran cohort with prior NBA history and at least 100 target-year minutes. Players with zero or very few target minutes are excluded from this rate metric, but remain included in draft scoring.

| Season | Players | Last season | Three-year average | Learned model |
|---|---:|---:|---:|---:|
| 2024–25 | 396 | 2.988 | 2.908 | 2.938 |
| 2025–26 | 397 | 3.136 | 2.953 | 2.932 |

Against last season, the learned model reduces error by 1.7% in 2024–25 and 6.5% in 2025–26. Against the three-year average, it is 1.0% worse and 0.7% better respectively. This is a small, inconsistent gain over the stronger simple baseline, not evidence of a decisive forecasting advantage.

## Draft comparisons

624 completed legal draft scenarios, each with 16 teams and 12 rounds: 48 scenarios per policy per season, covering all draft slots and three fixed opponent seeds. There are 96 paired slot/seed settings, not 624 independent historical seasons. Seven policies are available in 2024–25 and six in 2025–26. Opponents use dated preseason ESPN ranks with fixed optional noise.

The table gives the mean paired percentage difference in actual full-season points of the 12 drafted players versus ESPN. It does not measure weekly H2H wins, starters-only production, streaming or playoff success.

| Policy | 2024–25 gain vs ESPN | Paired win rate | 2025–26 gain vs ESPN | Paired win rate |
|---|---:|---:|---:|---:|
| ESPN baseline | +0.00% | 0.0% | +0.00% | 0.0% |
| Prior-season totals | -5.92% | 22.9% | -50.03% | 0.0% |
| Learned rates × historical minutes | -8.00% | 14.6% | -56.60% | 0.0% |
| Learned rates × historical minutes/games | +2.58% | 60.4% | -54.84% | 0.0% |
| Learned totals + next-pick timing | +5.23% | 66.7% | -16.87% | 10.4% |
| RotoWire primary board | -0.05% | 52.1% | +8.99% | 77.1% |
| NBC / Rotoworld board | -0.40% | 43.8% | Unavailable | — |

## Why the statistical draft failed

A production model can estimate what a player does on the floor without knowing whether he will be on the floor. Historical games/minutes alone badly mishandled the long absences in 2025–26. The unrestricted learned-total policy averaged 4.06 zero-game players per roster that year, versus 0.56 for ESPN and 0.04 for RotoWire. Next-pick timing reduced the model to 1.02 zero-game players but still lost 16.87% on roster points.

One deterministic 2025–26 run at slot 15 selected Jayson Tatum at 15, Tyrese Haliburton at 47, Damian Lillard at 50, Kyrie Irving at 82 and Fred VanVleet at 111 under the learned-total strategy. Those selections were made from earlier statistical history, without dated preseason injury news. This demonstrates a failed availability assumption, not proof that the production model is useful for real drafting.

The current comparison board does apply current sourced injury caps and current roster verification, and does not recreate this historical retired-player universe. However, these historical draft tests do not validate that complete current pipeline. Historical injury/rotation snapshots would be needed for that claim. Do not label the current board deployment-ready.

## Current statistical top 20

Main rank is expected season points; per-game rank separates production from the workload/availability assumptions. Rankings are comparison-only, with personal bans preserved.

| Rank | Player | Fpts/game | Expected games | Per-game rank | RotoWire |
|---:|---|---:|---:|---:|---:|
| 1 | Nikola Jokic | 62.7 | 71.7 | 1 | 1 |
| 2 | Shai Gilgeous-Alexander | 51.8 | 73.8 | 4 | 3 |
| 3 | Luka Doncic | 55.1 | 67.6 | 2 | 5 |
| 4 | Victor Wembanyama | 53.5 | 66.3 | 3 | 2 |
| 5 | Cade Cunningham | 48.8 | 69.2 | 6 | 6 |
| 6 | Giannis Antetokounmpo | 51.2 | 64.5 | 5 | 4 |
| 7 | Donovan Mitchell | 45.5 | 71.7 | 8 | 19 |
| 8 | Jalen Johnson | 45.9 | 69.7 | 7 | 10 |
| 9 | Scottie Barnes | 42.1 | 75.1 | 15 | 16 |
| 10 | Tyrese Maxey | 45.0 | 70.2 | 10 | 15 |
| 11 | Jamal Murray | 43.3 | 71.8 | 12 | 24 |
| 12 | Anthony Edwards | 42.8 | 72.3 | 14 | 8 |
| 13 | Alperen Sengun | 42.1 | 73.2 | 16 | 9 |
| 14 | LaMelo Ball | 45.2 | 67.8 | 9 | 50 |
| 15 | Jalen Brunson | 41.9 | 73.0 | 20 | 20 |
| 16 | Amen Thompson | 39.9 | 76.6 | 28 | 18 |
| 17 | Kevin Durant | 42.0 | 72.5 | 19 | 29 |
| 18 | Devin Booker | 42.0 | 70.7 | 18 | 21 |
| 19 | James Harden | 40.4 | 73.5 | 24 | 35 |
| 20 | Derrick White | 38.1 | 77.2 | 38 | 47 |

## Reproducibility and limits

- Selection hash: `ef701feabe55bc8f981e7b03a4ecef5b7b4d6d748d4ea3698892a8dda7efd105`.
- Locked draft evidence: `a72200b67102dcb88a78da1febd7b0eb46e5422e62c7ad3aaaf97c1bf78dcc8e`.
- Complete aggregate metrics, source/implementation hashes and dated preseason input hashes: `basketball_empirical_results.json` beside this report.
- Local full current board: `basketball/data/research-empirical/rankings.md`; full forecasts and provenance: `rankings.json`.
- 22 focused backend tests pass across research and empirical modules, including chronological isolation, valid box-score identities, locked inputs, bans, injury caps, next-pick timing, paired cohorts, and zero-game outcome handling.
- The evaluated years have been examined in earlier experiments; these are chronological out-of-training evaluations, not freshly untouched independent holdouts. Overlapping draft scenarios cannot establish a tight confidence interval from the scenario count alone.
- Historical injury/rotation news, weekly lineups, replacement players and waivers are not modeled by the draft experiment. No parameters were retuned after viewing the test results.

Reproduce from captured local inputs:

```text
python -m basketball research fit
python -m basketball research backtest
python -m basketball research rank
python -m unittest discover -s tests -p test_basketball_empirical.py -v
```

The scheduled real draft and its expert source, injury policy, bans and API transport remain unchanged.
