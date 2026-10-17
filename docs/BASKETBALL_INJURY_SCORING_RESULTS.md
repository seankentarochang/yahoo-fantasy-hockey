# Injury history applied to statistical scoring forecasts

Adding injury history to the box-score/minutes model did not improve the full
forecast. Its pooled season-point MAE worsens 0.6% overall and 4.5% among preseason
top-100 players. Keep the base statistical model as the experimental control and
the expert board as the live draft source. No live scoring or drafting policy
was changed.

This differs from the prior injury experiment's direct season-total regression:
it predicts statistical rates, minutes and games separately, reconstructs box
scores and applies the league's actual fantasy scoring. The
[protocol](BASKETBALL_INJURY_SCORING_PROTOCOL.md) was committed at `e66b69e` before
fitting. Previously studied seasons are exploratory comparisons, not fresh
independent holdouts. No parameters were retuned after evaluating these results.

## Forecast construction

Base and injury versions learn eight volume rates plus 2P%,3P%,FT% from the same
42 prior-statistic features. The injury version adds the 26 frozen injury-history
features. Separate base/injury regressions predict minutes/game. Reconstruct
consistent makes, attempts, points and the other league statistics, then:

`predicted fantasy points/game = scoring weights × projected per-game box stats`

`predicted season points = predicted fantasy points/game × predicted games`

Weights: PTS +1, FGM +2, FGA -1, FTM +1, FTA -1, 3PM +1, REB +1, AST +2,
STL +3, BLK +3, TO -2. No blanket 9% injury discount is applied. Use projected
minutes, never actual target minutes, in a practical forecast.

Train on ending seasons 2020–2021, select on 2022 and refit through year-1 for
each 2023–2025 test. Both rate models select ridge penalty 100; both minutes
models select 10. Rate selection minimizes league-scoring RMSE at a standard
30-minute workload, while minutes selection minimizes minutes/game RMSE.
Rates/minutes fit on the same conditional cohort with >=150 prior minutes and
>=100 target minutes. The unconditional season evaluation retains absent players.

Expected games are reused exactly from the preceding locked injury experiment:
base and injury forecasts are not refit here. This isolates the contribution of
production changes, availability changes, and their combination.

## Prediction accuracy

Three test seasons: 2022–23, 2023–24, 2024–25. The broad known-player cohort has
1,611 player-seasons, including 351 zero-appearance outcomes. It requires at
least 20 games in the prior two seasons and does not cover unmodeled rookies.
The matched preseason ESPN top-100 cohort has 294 player-seasons. Counts include
repeated players; they are not independent observations or independent seasons.

MAE means average absolute prediction error; lower is better. Season points and
games are normalized to 82 team opportunities, as in the games model.

| Forecast | All: season-point MAE | Top 100: season-point MAE | Top 100: fantasy PPG MAE |
|---|---:|---:|---:|
| Base statistical rates/minutes/games | 386.46 | 567.19 | 4.33 |
| Injury availability only | 386.59 | 581.22 | 4.33 |
| Injury production only | 386.12 | 571.44 | 4.47 |
| Full injury adjustment | 388.94 | 592.54 | 4.47 |
| Fixed NHL-style comparison | 444.38 | 528.20 | 4.21 |

The production-only variant is almost neutral overall (-0.34 season-point MAE,
about 0.09% better), and worse for the top 100 (+4.25). The full version raises
top-100 season error by 25.35 points and PPG error by 0.13. These small or negative
gains do not justify promoting the injury model.

The NHL-style comparison has better top-100 error here but worse broad-cohort
season error. That is a forecast comparison on this cohort, not evidence that
its draft strategy wins. **None of these three seasons' matched top-100 players
has a zero-game outcome.** This test cannot validate avoiding the later season's
catastrophic unavailable-player selections, for which injury coverage is missing.

Year-by-year season-point errors, with paired changes (full minus base):

| Season | All: base | All: full injury | Change | Top 100: base | Top 100: full injury | Change |
|---|---:|---:|---:|---:|---:|---:|
| 2022–23 | 404.61 | 413.52 | +8.91 | 572.31 | 631.79 | +59.49 |
| 2023–24 | 366.72 | 368.98 | +2.25 | 554.02 | 578.94 | +24.92 |
| 2024–25 | 387.77 | 384.12 | -3.65 | 575.04 | 567.02 | -8.03 |

The full adjustment improves one season and worsens two, including the top-100
subset. Pooled top-100 season bias is -163.28 for the base model and -196.10 for
the full model: the adjustment makes an existing tendency to underpredict
strong players worse.

## Separate scoring rates from minutes

Per-game metrics condition on actual participation; they do not drop absent
players from the season-total test. Across 1,260 played player-seasons, PPG MAE
is 4.58 base versus 4.60 injury. Across the 1,128 with >=20 appearances, it is
4.31 versus 4.33. The absence of improvement is not just an artifact of a few
one-game samples.

| Conditional diagnostic | All: base | All: injury production | Top 100: base | Top 100: injury production |
|---|---:|---:|---:|---:|
| Minutes/game MAE | 4.17 | 4.20 | 2.36 | 2.47 |
| Fantasy scoring MAE at common 30 minutes | 2.93 | 2.94 | 2.79 | 2.82 |

The common-minute diagnostic uses actual minutes only to express observed
scoring rate for evaluation. Practical predictions use predicted minutes.
Neither the learned rates nor minutes improve overall when injury features
are added. The common-30-minute cohort has 1,188 player-seasons with >=100 actual
minutes; all 294 top-100 cases qualify.

Top-100 per-game box-stat MAE:

| Statistic | Base | Injury production |
|---|---:|---:|
| NBA points | 2.811 | 2.869 |
| FGM | 1.020 | 1.037 |
| FGA | 1.957 | 1.976 |
| FTM | 0.729 | 0.739 |
| FTA | 0.868 | 0.874 |
| 3PM | 0.390 | 0.403 |
| Rebounds | 0.818 | 0.830 |
| Assists | 0.770 | 0.797 |
| Steals | 0.185 | 0.185 |
| Blocks | 0.164 | 0.168 |
| Turnovers | 0.363 | 0.367 |

This supports retaining the unadjusted statistical control while keeping current
injury/return information as a separate input. It does not establish that injury
history is unimportant; it fails to establish useful incremental accuracy from
this feature set and archive beyond prior workload and production.

## Coverage, evidence and reproduction

The pinned injury archive ends May 13, 2025. Full pre-draft history is unavailable
for ending season 2026 or current 2027. This experiment neither fills that gap
with healthy labels nor exports current player forecasts from stale history.
Transaction episodes, body groups and returns are approximations; event dates
come from retrospective records, not independently archived pre-draft captures.
The prior report's age/role/reporting confounding limits still apply.

```text
python -m basketball research injury-scoring-backtest
python -m unittest discover -s tests -p test_basketball_injury_scoring.py
```

Eleven targeted backend tests pass for scoring algebra, workload bounds, feature
augmentation, matched training cohorts, future-data isolation, training cutoff,
zero-outcome versus conditional evaluation, component isolation, locked evidence,
pooled counts and comparison-only routing/coverage. Selection and forecast locks
verify. Every candidate's expected games matches its prior frozen prediction,
and every forecast's fantasy points reconcile with its stat line and league weights.

Local models and individual forecasts are under the ignored
`basketball/data/research-injury-scoring/` directory. The committed
[aggregate evidence](basketball_injury_scoring_results.json) includes annual/pooled
metrics, paired changes, per-stat MAE, source and implementation identities.
No new draft simulations or weekly H2H claims are made by this experiment.

Prediction SHA-256:
`b33561c5d1d3c5e330563cf4f0330e2539a1417fa55176ebdbf9f200ac84211c`.
