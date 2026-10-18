# Injury-history prediction experiment, version 1

Specified October 17, 2026 before new injury associations, model fits or outcome
evaluation. Earlier NBA draft outcomes have been studied, so this is exploratory
and not an independent holdout. Keep prior experiments frozen and the live expert
draft strategy unchanged. Extend the existing research worktree and pull request.

## Injury data and time boundaries

Use the public JaseZiv/NBA_data Pro Sports Transactions archive, pinned to commit
217ce05b967b201d1b7a474f20b4a6cab273de66, raw JSON SHA-256
94a6338ed0c4645115f5e4efe567909e381a14f9e7c379dd5e6aaf34876c25cd.
It contains 73,306 transaction rows and ends May 13, 2025. Its dates describe
historical events, not independently archived publication timestamps. Preserve
source bytes, reject changed hashes, and expose coverage explicitly.

Use October 1 of the calendar year preceding each ending season as the injury
feature cutoff. Include only events strictly before that date. Full historical
preseason evaluations are possible through ending season 2025; refuse later
forecasts with this archive. Never silently treat the missing later period as
healthy. The archive's reported range is not proof of complete capture of every
injury. Current roster verification/injury-return research remains separate.

Resolve transaction names to unique NBA IDs using only identities observed before
the forecast season. Strip parenthesized alternate names and split explicit
slash aliases, accepting only one resulting NBA identity. Record unmatched and
ambiguous names; do not join on target rosters. Ignore pre-2011 transactions and
approximate-date rows. Coach-only and nonmedical transactions are not injuries.
Separate illness and rest from musculoskeletal injury; generic IL placements
without a medical description do not establish an injury diagnosis.

Build conservative report episodes: coalesce same-body reports within 14 days
unless a recorded activation/return separates them. These are documentation
episodes, not proven independent injuries or actual missed games. Retain a
severe flag for surgery, rupture/torn tendon/ligament, fracture or dislocation.
Achilles spelling variants count together. A recorded activation/return ends
all currently documented absences, as an explicit approximation. Without a
recorded return, censor elapsed days at the feature cutoff; never use a later
return to compute a pre-draft duration. Merge overlapping observed intervals
when calculating absence days. Those are calendar days, not games missed.

## Predictors and controls

Use candidates with >=20 NBA games in the prior two seasons, including zero
target-season appearances. Base games predictors match the preceding availability
experiment (three lags of normalized games, minutes/game, presence, post-debut
indicators and observed tenure). Keep the NHL-style per-game production baseline.

Injury features: episode counts, observed absence-day fractions and severe-event
counts in each of the prior three 365-day windows; three-year body-group counts
and same-body recurrence counts; recency; unresolved-report age and severe
unresolved-report flag; and separate illness/rest report counts. Body groups:
knee, ankle, Achilles, foot, hip/groin, hamstring, other leg, back, upper body,
head/neck, other medical. Features are computed from the censored snapshot only.
No manual player-specific adjustments or parameters based on outcomes.

Compare games-only and injury-augmented ridge models. Also compare direct season
fantasy-output models with and without injury features. Direct-output base adds
the NHL FPG estimate, prior two FPGs and three FPG-by-games-share interactions,
so injury output gains are tested beyond prior production and workload. Predict
normalized season fantasy points directly, retaining zeros for absent players;
do not filter on target minutes. Bound games to [0,82] and season points at zero.
This learns associations involving injury, role and league exit, not causal
medical effects. Direct output does not independently identify a per-game injury
penalty or a medical recovery forecast.

Train ending seasons 2020–2021, select ridge penalty from 0.1,1,10,100 using 2022
RMSE, separately for each model/target. Freeze selection before 2023–2025 tests.
Refit on all 2020 through year-1 for each forecast. Report paired games/output
MAE, RMSE and bias on all candidates and the preseason ESPN top 100 intersection.
Also report next-season games, under-50-game frequency and season output by
predeclared prior three-year episode bins 0,1–2,3–5,6+, and severe-history status.
These groups are descriptive associations, not randomized comparisons.

## Draft test and evidence

Use verified historical preseason packs for 2023,2024,2025; all 16 slots and
seeds -1,0,1; and the exact previous ESPN-based opponent orders. Rerun ESPN and
available expert controls. Test VOR from base games, injury games, base direct
output and injury direct output, each with and without next-turn timing. The
production model, modeled candidate pool and primary-position replacement
definition stay fixed; recompute replacement points for each policy. Unmodeled
players keep ESPN ordinal slots. Legal roster/position rules stay unchanged.

Lock source/data/protocol/implementation hashes, selected penalties, coefficients,
predictions and draft selections before joining target outcomes for scoring.
Report full-roster season fantasy points and zero-game picks; these are not
weekly H2H wins. Overlapping drafts are not independent seasons. Do not promote
a new live strategy based on these exploratory results alone.
