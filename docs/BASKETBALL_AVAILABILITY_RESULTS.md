# Availability normalization: results and limits

The games-floor bias can be corrected, but historical availability alone does
not solve injury-aware drafting. Keep the expert board as the live draft source.
This comparison adds a learned statistical fallback and gives dated forward
games forecasts priority over backward-looking games estimates.

The [protocol](BASKETBALL_AVAILABILITY_PROTOCOL.md) was committed at `f99d9de`
before fitting. Target seasons have been examined previously; these are
exploratory comparisons rather than fresh independent holdouts. Parameters were
not retuned after the following results.

## What changed

- Keep the NHL-style per-game production forecast fixed. Estimate games separately.
- Normalize past games by actual team-season opportunities, handling shortened
  seasons. Count absent seasons after observed debut as zero availability.
- Remove the 40/60-game floors. Train expected next-season workload on prior
  players including those who never return, rather than conditioning on survival.
- Give one vote per publisher to dated forward games forecasts where available.
  These replace the historical estimate; do not multiply two injury discounts.
- For the current comparison, apply the existing sourced return-date opportunity
  cap with `min(expected games, remaining opportunities)`. Unknown or overdue
  returns stay flagged. Current roster verification and bans stay in force.

The regression estimates unconditional NBA workload, combining health, role,
retirement and league-exit effects. It is not a medical injury probability.
Standardized ridge uses only the three prior seasons' opportunity shares,
minutes/game, presence, post-debut indicators and observed tenure. Penalty 10
was selected by 2024 games RMSE after training on 2020–2023; each later year
uses an expanding fit ending before the forecast year.

## Availability forecast accuracy

Errors are measured on the same paired candidates within each season: prior
two-season NBA games >=20, without a target-season survival filter. Normalize
outcomes to 82 opportunities. There are 542 candidates in 2024–25, including
118 zero-game outcomes; 558 in 2025–26, including 121 zero-game outcomes.
This broad NBA cohort includes players outside the fantasy draft pool.

| Season | Old floors MAE | No-floor MAE | Learned MAE | Old bias | Learned bias |
|---|---:|---:|---:|---:|---:|
| 2024–25 | 22.68 games | 18.15 | 16.47 | +16.07 | -0.59 |
| 2025–26 | 23.91 games | 19.33 | 17.85 | +15.78 | -0.12 |

The learned model lowers mean absolute error by 27.4% and 25.3% versus the
original floors. For players who played zero games, expected games fall from
44.88 to 16.60 and from 46.09 to 17.75. Among players who did appear, the learned
forecast underpredicts by roughly five games on average. Near-zero overall bias
does not imply accurate predictions for every player or for early-round stars.

For example, entering 2025–26 the learned model still forecasts 68.7 games for
Jayson Tatum, 65.1 for Tyrese Haliburton and 61.4 for Damian Lillard. Historical
regular-season workloads cannot reveal subsequent injuries; removing floors
does not supply that missing preseason information.

## Draft results

Run 1,008 legal 16-team, 12-round scenarios: all 16 slots, three fixed opponent
seeds, two seasons and the applicable controls/strategies. That is 96 paired
settings, not 1,008 independent samples. Production, eligibility, opponent orders
and positional replacement method are held fixed; replacement point levels are
recomputed for each declared projection pool. Repeated ESPN and expert/legacy
controls match the preceding value experiment exactly.

Mean paired change in actual full-season points of drafted rosters versus ESPN:

| Policy | 2024–25 | 2025–26 |
|---|---:|---:|
| Old NHL VOR | -7.94% | -48.35% |
| No-floor VOR | -9.80% | -42.19% |
| Learned availability VOR | -12.84% | -46.69% |
| Learned availability + next-turn timing | -12.25% | -9.28% |
| Covered-subset guard + learned games | -4.46% | -11.37% |
| Dated preseason games VOR | -5.69% | +0.80% |
| Dated preseason games + next-turn timing | -5.68% | +2.86% |
| RotoWire expert board | -0.05% | +8.99% |

The source policies reorder only players covered by dated games forecasts;
uncovered players keep their ESPN ordinal slots. Missing coverage is **unknown**,
never interpreted as zero games or a diagnosis. The covered-subset guard has
the same eligibility and replacement pool but uses learned games. This control
shows the 2025–26 improvement comes from both coverage restraint and better GP
forecasts. Source GP itself helps in 2025–26 and hurts in 2024–25 versus that guard.

Coverage is 272 of 488 statistically modeled fantasy players in 2024–25 and
99 of 501 in 2025–26. Sources are the verified preseason Rotoworld 2024–25 PDF
profile GP plus RotoWire 2024–25 G, and RotoWire 2025–26 total FP divided by FP/G.
The last is approximate because published points are rounded. Each publisher
gets one contribution per player; publisher forecasts may still share inputs.
Retrospective captures have publisher dates, not independent archive timestamps.

In 2025–26 zero-game picks average 3.77 per roster for old VOR, 4.00 for learned
VOR, 0.25 for the coverage guard, 0.21 for dated games plus timing, 0.56 for ESPN
and 0.04 for the expert board. Better broad-population games calibration did
not, by itself, fix catastrophic early-round selections.

## Current comparison

The exported board contains 317 players, all with at least one current forward
games forecast; 12 personal bans remain excluded from personal ranks. ESPN,
Hashtag and FantasyPros GP are averaged where matched; the previous 25%
historical-GP blend is removed. The learned fallback trains on 3,713 historical
player-seasons, including 813 zero-appearance target seasons. No statistical
fallback was needed for games in this current input universe.

This can raise projections for a player with credible recovery expectations:
historical-only games should not permanently punish someone returning after a
lost season. For Jimmy Butler, the input forecasts are ESPN 39 and FantasyPros
44 games. Their mean is 41.5; the sourced return-date opportunity cap is 50, so
the result stays 41.5 rather than subtracting the injury absence again. That
example describes the captured source estimates, not a guaranteed return date.

The board still uses the fixed NHL-style production forecast and approximate
primary-position VOR. Its full current injury-aware pipeline has not been
validated by the historical GP-only tests. This work does not promote it over
the expert board, change the scheduled real draft, or claim weekly H2H results.

## Reproduction and evidence

After collecting the already documented public datasets and ranking packs:

```text
python -m basketball research availability-backtest
python -m basketball research availability-rank
python -m unittest discover -s tests -p test_basketball_availability_research.py
```

Twelve targeted backend tests cover missing-season/debut handling, shortened
seasons, zero-outcome training, temporal isolation, bounded predictions,
unknown source coverage, source deduplication/validation, anchored fallback
slots, evidence invalidation, comparison-only routing and the current
forward-games/return-cap/ban integration. All pass.

Generated inputs, fitted models and draft choices are hash-locked before joining
target outcomes for draft scoring. The committed aggregate evidence is
[basketball_availability_results.json](basketball_availability_results.json).
Large raw captures and local per-draft receipts stay ignored.

Decision SHA-256:
`5715ca26b568cbf64731008204c74247b29d65b278172f6a60a0c475702901f0`.

Local reports: `basketball/data/research-availability/backtest.json`,
`rankings.json` and `rankings.md`. Sources:
[Rotoworld PDF](https://nbcsports.brightspotcdn.com/03/10/b09f526442aab7ad4db7ba3584ed/rotoworld-2024-25-fantasy-basketball-kit.pdf),
[RotoWire 2024](https://www.rotowire.com/basketball/article/fantasy-basketball-points-league-rankings-2024-projections-85939),
[RotoWire 2025](https://www.rotowire.com/basketball/article/fantasy-basketball-points-league-rankings-2025-26-nba-projections-95771).
