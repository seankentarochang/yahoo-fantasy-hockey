# Availability normalization experiment, version 1

Specified October 17, 2026 before fitting or evaluating the new availability
models. Earlier draft outcomes have already been examined, so all results are
exploratory, not a fresh independent holdout. This changes comparison research
only; the scheduled expert draft strategy stays unchanged.

## Separate production from availability

Hold the NHL-style per-game production forecast and legal-roster simulator
fixed. Replace only games, recomputing the same primary-position replacement
levels. Normalize historical games by actual team-season opportunities from
the audited logs, including shortened seasons. An absent season after a player's
first observed appearance is zero availability; years before debut are not
evidence of missed games. Remove all games floors.

The mechanical control uses the same 0.8/0.2 recent/older weights on opportunity
shares, excluding pre-debut years, multiplied by 82. The learned alternative is
ridge regression of next-season opportunity share, clipped to [0,1], using three
lags of share, minutes/game divided by 48, presence, and post-debut indicator,
plus observed tenure capped at three years. The candidate cohort is known from
prior years, with at least 20 games in the preceding two seasons, matching the
fixed production model. Include candidates with no target-season appearance as
zero outcomes, including retirement/league-exit risk; never filter on target
minutes or survival. This predicts expected workload, not a medical diagnosis.

Train on ending seasons 2020–2023; choose ridge penalty from 0.1,1,10,100 by
2024 mean squared opportunity-share error (ties choose smaller). Lock selection
before evaluating 2025 and 2026. For each test year refit on 2020 through year-1;
the current model trains through 2026. Report games MAE, RMSE, bias, and separate
zero-game and nonzero-game errors. Do not select parameters by draft returns.

## Known preseason information and coverage

Past games cannot foresee a new offseason injury. Add a separate, explicit
source-based experiment using already captured, verified preseason forecasts:
Rotoworld 2024–25 PDF profile GP, RotoWire 2024–25 G, and RotoWire 2025–26 total
FP divided by FP/G (rounded values imply approximate GP). Average publishers
once each where they overlap; do not count two RotoWire tables as independent.
Validate source hashes, preseason status and season. Match only unique names.
Missing coverage is unknown, never zero games. Source snapshots were collected
retrospectively and have publisher dates, not independent archival timestamps.

For the source policy, rerank only modeled players with a dated GP forecast;
all others retain their preseason ESPN ordinal slots. To distinguish coverage
guardrails from improved games estimates, also run a learned-games policy with
exactly that same covered subset and the same replacement pool. Source GP
replaces the learned games forecast, rather than multiplying two injury
discounts. Historical experiments have no separately reconstructed injury news.

## Paired draft comparisons

For 2025 and 2026 use all 16 slots and seeds -1,0,1 with the exact prior ESPN
opponent construction. Compare mechanical no-floor VOR, learned VOR, learned VOR
with next-turn timing, coverage-guard learned VOR, dated-source GP VOR and its
next-turn variant. Rerun ESPN, fixed NHL VOR and its next-turn variant, and all
available expert controls. Coverage-guard and dated-source VOR replacement pools
contain exactly their covered modeled players. Other variants use all modeled
players. Fallback players remain anchored; no target observations establish
identity, eligibility, forecasts, or draft choices.

Lock all forecasts, fitted models, source/data/protocol/implementation hashes
and draft selections before joining target-year outcomes for draft scoring.
Report paired roster-season points versus ESPN and zero-game selections. A
season is an independent year; 48 overlapping drafts are not 48 seasons. No
weekly H2H, waiver, or streaming performance is claimed.

## Current comparison

Export both learned historical games and forward-source games for the verified
current comparison universe. Use available ESPN/Hashtag/FantasyPros GP forecasts
(one vote each), without the legacy 25% historical-games blend; use learned games
only when no forward estimate exists. Apply the existing sourced injury-return
opportunity cap as a minimum with expected games, not a second subtraction.
Unknown/overdue return estimates remain visibly flagged. Current verified active
rosters, season-out exclusions and personal bans remain in force. This full
current injury-aware pipeline is not historically validated by the GP-only test.
