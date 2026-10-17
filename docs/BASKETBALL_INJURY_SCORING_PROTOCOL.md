# Injury-aware statistical scoring experiment, version 1

Specified October 17, 2026 before fitting or evaluating the new scoring models.
The prior injury experiment predicted season totals directly; this experiment
applies injury history to the empirical box-score and minutes models. Previously
studied years are exploratory tests, not fresh independent holdouts. Keep frozen
experiments and the live expert strategy unchanged; use the existing research PR.

## Inputs and population

Reuse verified NBA game logs, the pinned injury transaction archive and its
censored features, and the verified preseason ESPN universes. Injury history is
available through May 13, 2025; full tests are ending seasons 2023,2024,2025 only.
Injury observations use the same October 1 cutoff preceding each season. Missing
later coverage is not health and must fail explicitly.

Candidates are players with >=20 NBA games in the prior two seasons, matching
the preceding injury experiment. All candidates stay in season-output evaluation,
including zero target appearances. Report all candidates and the matched preseason
ESPN top 100 separately. Unknown/unmodeled rookies are outside this statistical
cohort; this is not a claim about complete rookie or draft-board accuracy.

## Apply injury history to the scoring model

Use the existing 42-feature empirical production representation: three lags of
eight per-minute attempt/count rates, three shooting percentages, minutes/game,
opportunity share and presence. Keep its 500-minute/50-attempt feature shrinkage,
coherent box-score reconstruction and prior-minutes observation weights unchanged.
The injury variant appends the 26 frozen injury-history features. Neither version
uses a flat 9% injury penalty inferred from descriptive group differences.

Fit ridge to eight per-minute volume rates plus 2P%,3P%,FT%, reconstructing all
11 league-scored box statistics. Separately fit minutes/game from the same base
or augmented features. Both fit on the identical intersection of known candidates
with >=150 prior-three-year minutes and >=100 target minutes. This conditional
training cohort estimates production while playing; it does not remove absent
players from season-total scoring. Predict rates/minutes for every known candidate.
Bound volume rates nonnegative, percentages [0,1], minutes [0,48]. Preserve the
league's scoring algebra even if a resulting fantasy score is negative.

Train on 2020–2021 and select penalties from 0.1,1,10,100 on 2022, separately for
base/injury rate and minutes models. Rate selection minimizes fantasy-scoring
RMSE at a common 30 minutes under this league's weights; minutes selection uses
minutes/game RMSE. Ties select the smaller penalty. Freeze selection before
2023–2025 evaluation. Expand training through year-1 for each test year.

Reuse the preceding injury experiment's locked base/injury games predictions
for the same candidates and years. Verify its selection/decision hashes, source
hashes, protocol and implementation fingerprints, scoring and forecast config.
No new games fitting or parameter selection occurs here.

## Fixed comparisons

1. Base statistical rates + base minutes + base expected games.
2. Availability-only injury adjustment: base rates/minutes + injury games.
3. Production-only injury adjustment: injury rates/minutes + base games.
4. Full injury model: injury rates/minutes + injury games.
5. Frozen NHL-style FPG and games as a comparator.

Per-game projection is reconstructed per-minute stats times predicted minutes;
season projection is that FPG times predicted games. Hold component models fixed
between the four combinations. No actual target minutes or games are supplied
to a practical forecast. Do not use current expert forward forecasts without
equivalent historical captures. No live ranking or transport selector changes.

## Scoring prediction evaluation

Hash-lock selected penalties, fitted coefficients, input/source/code/protocol
identities and every candidate's component/stat/point predictions before joining
test-year outcomes for evaluation. Reuse ending years 2023–2025 only.

Primary metric: season fantasy-point MAE/RMSE/bias on all candidates including
zero-game outcomes, with the same 82-opportunity normalization as the previous
games experiment. Also report matched ESPN top-100 season errors. Per-game
MAE/RMSE/bias use a common cohort with >=1 actual appearance; a >=20-appearance
cohort is a stability diagnostic. These conditional metrics do not replace
the unconditional season-total test. Report minutes/game error and each of
the 11 per-game stat errors; scoring at a common 30-minute workload is an
additional conditional rate diagnostic, not an actual-minute forecast.

Show paired per-year differences versus the base statistical model and pooled
errors, without treating repeated players as independent seasons. Include
cohort counts, zero-game counts and explicit comparison-only/coverage limits.
No draft simulation, weekly H2H or deployment claims follow from forecast error
alone. No model/policy changes after test results unless correcting a documented
implementation defect and rerunning all affected comparisons.
