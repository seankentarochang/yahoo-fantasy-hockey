# Statistical rate model and chronological backtest, version 1

Specified before fitting or evaluating this experiment, October 17, 2026.
This extends the comparison research; it does not change automatic drafting.

## Production model

Use the ten captured SportsDataverse ending seasons 2017–2026. Verify their
hashes and aggregate only regular-season played rows; preserve the source audit.
Use NBA player IDs within the data. Match ESPN identities only by unique
normalized names found before the forecast year, with explicit unmatched cases.

Learn next-season per-minute production using a standardized ridge regression.
Features are three lagged seasons of two-point attempts/minute, three-point
attempts/minute, free-throw attempts/minute, rebounds/minute, assists/minute,
steals/minute, blocks/minute, turnovers/minute, two-point percentage, three-point
percentage, free-throw percentage, minutes/game, games as a share of team games,
and history-presence indicators. Shrink input rates toward the preceding season's
league rates with 500 minutes of prior strength and shooting percentages with 50
attempts. Missing lag seasons have prior rates and zero opportunity/presence.

Predict the eight production rates and three shooting percentages. Clip negative
rates to zero and percentages to [0,1]. Derive makes and points from attempts and
percentages so the forecast respects the box-score identities. Current minutes
and games remain separately identified assumptions from the comparison input
pack, including its sourced injury caps. Rookies/players with fewer than 150
minutes in the preceding three seasons use the existing forward forecast and
are explicitly labeled outside-model fallbacks. Expert ranks are never production
features. No age, tracking, defensive matchup or coaching effect is claimed.

## Rate evaluation

Train on target ending seasons 2020–2023, validate on 2024, then evaluate on
2025 and 2026. Ridge alpha candidates: 0.1, 1, 10, 100. Select alpha by validation
mean absolute fantasy-points/minute error, not by test-year draft outcomes.
Each sample needs 150 prior three-year minutes and 100 target-season minutes.
Training weight is max(0.25, min(1, prior_minutes / 2000)). Evaluate against
last-season actual rates and a 6/3/1 weighted historical-rate baseline. Report
errors at a common 30-minute workload. This is a conditional production test:
it does not predict whether somebody plays or establish preseason roster accuracy.
Refit expanding training years for each test year without using that target
year's outcomes. Refit through 2026 only after reporting the historical tests.

## Draft evaluation

Use the already verified, dated preseason input packs for 2025 and 2026 and the
same legal 16-team, 12-round league configuration. Compare ESPN order, prior-season
total points, learned production times historical minutes, learned production
times historical minutes and games, and the latter with next-pick market timing.
Also compare each available primary non-ESPN expert board. Opponents follow the
preseason ESPN board, with fixed ordinal Gaussian noise of 0 or 12 spots under
three seeds (-1, 0, 1). Run all 16 draft slots, paired across policies.

Historical workload estimates use 6/3/1 weighted minutes/game across played
prior seasons and a 6/3/1 weighted games/team-games share (missing seasons after
first observed debut contribute zero). Forecast 82 opportunities; short historical
seasons use their observed team-game denominator. This workload assumption is
separate from the rate-model evaluation and deliberately lacks historical injury
news. Players without usable statistical history keep their ESPN positions in
the policy order while modeled veterans reorder within the remaining positions.
Report fallback coverage on actual picks. This is not a pure model for rookies.

Next-pick timing considers the actual remaining ESPN market order and number of
opponent selections before our next pick. Prefer the highest model-ranked legal
candidate in that market window; if the window contains no legal choice, use the
highest legal model candidate. At the last pick, the timing restriction ends.

Lock selections before joining each target year's NBA outcomes for draft scoring.
Primary metric is the sum of drafted players' actual season fantasy points.
Report paired differences and win/tie rates by year. This measures roster assets,
not weekly H2H wins: it excludes lineup scheduling, replacement players, waivers,
trades and playoff timing. Current personal bans do not apply retroactively.

The years were studied in earlier experiments, so these are chronological
out-of-training evaluations for this model, not newly untouched independent
holdouts. Draft scenarios share players and seasons and are not independent
statistical samples. Do not claim a universal optimal strategy from two years.
Do not retune after observing test results in this version.
