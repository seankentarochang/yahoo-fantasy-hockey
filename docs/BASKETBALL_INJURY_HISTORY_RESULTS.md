# Injury history and future fantasy output

Past injury history is associated with future availability among fantasy-relevant
players. Explicit injury features add only small, inconsistent predictive gains
beyond prior games, minutes and production in this experiment. They do not yet
justify a blanket injury-history penalty or a change to the live expert strategy.

The [protocol](BASKETBALL_INJURY_HISTORY_PROTOCOL.md) was committed at `c4826fb`
before new associations, fitting or evaluation. Three test seasons were examined
previously for other strategies: these are exploratory tests, not fresh holdouts.
No parameters were retuned after seeing the following results.

## Quantified association

Pool the 2022–23, 2023–24 and 2024–25 preseason ESPN top-100 intersections with
players having at least 20 NBA games in the prior two seasons. Injury features
use only records before October 1 preceding each season. The flag below means
at least one report episode mentioning surgery, tear/rupture, fracture or
dislocation in the prior three years. It is a broad text flag, not a clinical
severity assessment.

Games and season points are normalized to 82 team opportunities.

| Prior three-year history | Player-seasons | Mean next-season games | Under 50 games | Mean season fantasy points | Mean prior projected FPG |
|---|---:|---:|---:|---:|---:|
| No flagged episode | 211 | 64.84 | 11.37% | 2,361 | 35.78 |
| At least one flagged episode | 83 | 61.10 | 18.07% | 2,152 | 35.95 |

The flagged group averages 3.75 fewer games and about 9% less season output,
despite similar prior scoring rates. The under-50-game difference is 6.70
percentage points. These are observational associations; the small samples,
repeated players across seasons, age/role differences and reporting coverage
prevent interpreting them as a causal penalty for an individual player.

Among top-100 players with 1–2 documented episodes, next games average 68.36
(25 player-seasons), versus 63.52 for 3–5 episodes (60) and 62.63 for 6+ (201).
Only eight top-100 player-seasons have no recorded episode; their 80.63-game
average is too small a group to use as a healthy-player baseline.

The full NBA cohort demonstrates the confounding problem: players with *more*
recorded episodes average more next-season games because they are more often
established players. The zero-episode group has mean prior FPG 10.75 versus
25.03 in the 6+ group. Missing injury records do not prove good health, and a raw
injury count cannot safely determine a draft discount.

## Prediction tests

Use the same prior games/minutes/presence/tenure controls for both versions.
The injury version adds three-year report episodes, observed calendar absence
days, body groups, same-body recurrences, severe-report flags, recency and
unresolved reports. Rest and illness are separate. Returns after the feature
cutoff cannot shorten a historical absence. Calendar intervals are merged to
avoid counting overlapping injuries twice.

Train on ending seasons 2020–2021, select penalties on 2022 RMSE, and refit on
2020 through year-1 for each 2023–2025 test. Selected penalties: base games 10,
injury games 100, base output 1, injury output 1. All models retain zero target
outcomes; none conditions on the player appearing in the target year.

Games MAE on paired NBA candidates (lower is better):

| Season | Candidates | Without explicit injury history | With injury history | Top-100 without | Top-100 with |
|---|---:|---:|---:|---:|---:|
| 2022–23 | 538 | 17.71 | 18.12 | 12.26 | 13.24 |
| 2023–24 | 531 | 15.60 | 15.41 | 12.13 | 12.80 |
| 2024–25 | 542 | 16.47 | 16.34 | 12.05 | 11.78 |

The explicit history slightly helps two broad-cohort seasons and hurts one.
It hurts top-100 games accuracy in two of three years. Most availability signal
may already be represented by prior workload; this test does not establish a
reliable incremental gain from the injury details.

Also learn total season fantasy output directly, rather than assuming injury
can change only games. Both versions include prior production, workload and
production-by-availability interactions. The direct model estimates joint season
output; it does not separately identify a per-game medical recovery effect.

| Season | Output MAE without injury features | With injury features |
|---|---:|---:|
| 2022–23 | 386.09 points | 390.14 |
| 2023–24 | 368.27 | 364.89 |
| 2024–25 | 373.36 | 380.28 |

Output accuracy improves in one of three years. Target games and points in these
prediction tables are normalized to 82 team opportunities. Full per-year RMSE,
bias and top-100 output metrics are in the aggregate JSON evidence.

## Draft comparisons

Run 1,440 legal 16-team, 12-round draft scenarios over 144 paired settings:
all 16 slots, three opponent seeds and three seasons. Eight new policies compare
base/injury games forecasts and base/injury direct output, each with/without
next-turn timing. The same NHL production forecast, modeled pool, primary-position
VOR method, eligibility, roster checks and ESPN opponent construction are used.
Unmodeled players retain their ESPN ordinal slots. Repeated ESPN/expert controls
match the preceding value experiment exactly.

Mean paired roster-season point change versus ESPN:

| Policy | 2022–23 | 2023–24 | 2024–25 |
|---|---:|---:|---:|
| Base games | +0.03% | -12.97% | -12.84% |
| Injury games | -0.36% | -5.19% | -13.20% |
| Base games + timing | +1.87% | -6.01% | -12.25% |
| Injury games + timing | +0.68% | +0.46% | -12.55% |
| Base direct output | -17.07% | -11.74% | -18.72% |
| Injury direct output | -13.21% | -5.77% | -18.76% |
| Base direct output + timing | -8.59% | -4.18% | -15.34% |
| Injury direct output + timing | +0.25% | -4.16% | -15.24% |
| RotoWire expert | +0.66% | unavailable | -0.05% |

Injury features improve direct-output draft results in two years and slightly
worsen the third; that version still loses to ESPN in every year. The games-based
comparison improves in one year and worsens in two. This supports further research,
not deployment. Draft metrics are actual season points of all roster assets,
not weekly H2H wins, and overlapping scenarios are not independent seasons.

## Dataset and limitations

The public [JaseZiv archive](https://github.com/JaseZiv/NBA_data) mirrors Pro Sports
Transactions and contains 73,306 transaction rows, including returns and noninjury
events. Source bytes are pinned to commit
`217ce05b967b201d1b7a474f20b4a6cab273de66` and SHA-256
`94a6338ed0c4645115f5e4efe567909e381a14f9e7c379dd5e6aaf34876c25cd`.
Use dated events from 2011 onward, excluding approximate-date rows, matching
unique NBA identities known before each target season. Preserve unmatched and
ambiguous counts. The full-history audit includes unmatched pre-2017 players
outside the game-log identity window; it is not a recent-window match rate.

At least one prior-three-year episode is matched for 472 of 538 candidates in
2022–23, 457 of 531 in 2023–24 and 482 of 542 in 2024–25. These counts are not
proof of complete injury coverage. Reporting frequency changes over time; for
example, matched rest reports do not increase in the later archive years.
Episode merging and activation-to-return assumptions are approximations.
Repeated chronic reports can resemble recurrence, and an unrecorded return can
inflate a censored interval. The data is not a clinical diagnosis dataset.

**The archive ends May 13, 2025.** It cannot support complete 2025–26 or current
2026–27 preseason injury features. Forecasting those cutoffs fails explicitly;
the missing period is never treated as healthy. A fresh, complete injury history
is needed before applying this model to current players. Existing current
injury-return checks remain separate and the scheduled expert strategy is intact.
Historical event dates are retrospective records, not independently timestamped
pre-draft captures. No 2025–26 result is presented for this injury-history model.

## Reproduction and validation

```text
python -m basketball research injury-backtest
python -m unittest discover -s tests -p test_basketball_injury_history.py
```

Twelve targeted backend tests pass: medical/rest/illness classification and
Achilles spelling; conservative alias joins; cutoff censoring; repeated-report
merging; same-body recurrence after return; interval overlap; approximate-date
exclusion; coverage failure; zero target outcomes; future-data isolation;
prediction bounds/short-season normalization; corrupt archive rejection; and
comparison-only command routing. Some tests cover multiple related conditions.

Selection and draft evidence locks verify. Raw data, coefficients, forecast
receipts and individual draft selections stay in the ignored
`basketball/data/research-injury/` directory. The committed aggregate evidence is
[basketball_injury_history_results.json](basketball_injury_history_results.json).

Decision SHA-256:
`b52e88ee664ae8b38d717924873ab4338c0eb2d4dad575d13758eb500d22905c`.
