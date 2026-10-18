# Comparison-only statistical ranking model, version 2

Version 1 was specified October 17, 2026 before its provisional rankings. Version
2 is specified before generating revised rankings, following the user's request
to find better free datasets. Changes concern source coverage, not outcome-driven
parameter tuning. The user
explicitly requested building and comparing first. This model is not an automatic
draft source and must not change the scheduled draft or its selected board.

## Inputs

- Full regular-season box scores for seasons ending 2024, 2025 and 2026 from
  ESPN's public statistics feed, including minutes and every scoring component.
- Current 2026–27 ESPN statistical projections from the saved league snapshot.
  Historical or current-season actual splits in that snapshot do not replace
  the separate prior-season inputs. ESPN ranks and RotoWire ranks never enter
  the statistical forecast; they are comparisons only.
- The 30 complete rows in Hashtag Basketball's publicly accessible October 17
  projection preview. Use the published shooting makes/attempts; do not derive
  attempts by dividing rounded percentages or access subscriber-only data.
- Basketball Reference's full 2026–27 Simple Projection System, including all
  shooting makes and attempts per 36 minutes. Convert to per-minute rates. It
  supplies neither projected games nor current rotation minutes; do not invent
  either. Match unique normalized names, and retain unmatched identities.
- FantasyPros' full public 2026–27 overall projection table supplies games and
  minutes estimates. Its rounded shooting percentages do not supply makes or
  attempts. Use this table only for playing-time forecasts, never to reconstruct
  the missing shooting statistics. It is publisher consensus, not necessarily
  independent of other forward sources.
- Capture DARKO's full public Fantasy Lab inputs for inspection. Its July 2026
  playing time/rosters are stale and its separately forecast components can
  violate box-score identities. Do not include it in this initial combined
  board. Report dates and quality findings rather than silently fixing numbers.
- Download SportsDataverse's public player-game CSV archives separately for
  expanded historical research. NBA IDs differ from ESPN IDs. Audit regular
  season rows, DNPs, duplicate player/game keys, seasons and scoring components.
  These historical outcomes are not preseason forecasts and are not evidence
  of a blind backtest without dated preseason inputs.
- Fresh public NBA rosters and injury estimates from ESPN, the NBA schedule
  already saved with the snapshot, and explicitly sourced NBA team previews.

Preserve input hashes, source URLs, capture times and model parameters. Report
missing or ambiguous identities and incomplete stat lines. Require a current
complete forward projection and verified NBA roster membership to rank a player;
do not revive a retired player using old statistics.

## Fixed calculation

1. Weight historical seasons newest to oldest 0.6 / 0.3 / 0.1. Estimate each
   stat per minute as weighted totals divided by weighted minutes.
2. Average current statistical rates by available publisher: ESPN, Hashtag's
   matched public rows, and the full Basketball Reference per-minute projections.
   Average minutes per game and games separately using ESPN, matched Hashtag,
   and matched FantasyPros opportunities. Basketball Reference contributes no
   playing-time estimate; FantasyPros contributes no statistical rates. Retain
   contributor lists separately so coverage is visible.
3. Blend historical and forward per-minute rates. Historical weight is
   `min(0.65, weighted_minutes / (weighted_minutes + 750))`. Cap it at 0.35 for
   verified team changes or the explicitly researched team-role changes. This
   gives current role information more weight when the environment has changed.
   Rookies or players without NBA minutes have zero historical weight and are
   visibly labeled as projection-only rather than independently modeled.
4. Use the mean current forward minutes estimate. Multiply blended per-minute
   rates by those minutes. Do not add a separate narrative scoring bonus or
   multiply a player's production twice for a role change.
5. Games forecast is 75% of the mean current forward games estimate plus 25%
   of historical durability. Include zero in an absent season only after a
   player first appeared in the historical NBA data; missing pre-debut seasons
   are not injury absences. Clip at 82.
6. Known injury returns cap games at opportunities on/after the provider's latest
   return estimate. Account for unassigned NBA Cup games as unknown opportunities
   and label incomplete schedules. Use `min(baseline_games, available_opportunities)`;
   do not subtract games already missing from an injury-aware forward forecast.
   Unknown/overdue estimates are flagged, never given an invented return date.
   Season-out designations are excluded from the comparison recommendations.
7. Score every projected box score with the exact league weights: FGM 2,
   FGA -1, FTM 1, FTA -1, 3PM 1, REB 1, AST 2, STL 3, BLK 3, TO -2, PTS 1.
   The main model rank is expected season points; also show per-game rank.
   Preserve raw analytical ranks and clearly mark personal bans separately.

These weights and thresholds are transparent first-version assumptions, not
parameters optimized on unseen outcomes. This is our reproducible statistical
model informed by outside projections and role research; it is not an independent
forecast for every rookie and not a new publisher consensus ranking.

## Checks and limits

Validate identity, coverage, season, positive minutes/games, finite nonnegative
statistics, makes <= attempts, 3PM <= FGM, and approximate box-score point identity.
Check source hashes again before building. Demonstrate that changing comparison
ranks or injecting target-season actuals cannot change forecasts. Test no
history/partial forecasts, bans, inactive/season-out players, injury dates and
repeatable output. Compare the largest disagreements with the expert board and
record why they occur without retuning the formula to make the ranks look nicer.

Season totals do not simulate weekly H2H lineups, replacement players, waivers,
late-season rest or position scarcity. Missing games can be partly replaced in a
real league. Historical durability can over-penalize a player returning from a
one-off injury. Limited outside projection coverage and provider uncertainty
remain visible. No new performance backtest is claimed by this build.
