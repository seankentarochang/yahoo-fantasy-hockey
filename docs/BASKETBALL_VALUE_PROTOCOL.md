# NHL-style basketball value board experiment, version 1

Specified October 17, 2026 before generating this experiment's projections or
draft results. This is an exploratory comparison of a fixed NHL-style method,
not a new independent holdout: several target years have been examined before.
No live drafting, odds integration or existing frozen experiments change.

## Fixed projection

Use only the two seasons preceding each target year from the verified NBA game
logs. Match players by unique historical names to stable NBA IDs. Require at
least 20 combined played games. Fantasy points/game is weighted total fantasy
points divided by weighted games, with 0.65 weight for the recent season and
0.35 for the older one. Project games with a separate 0.8/0.2 average of observed
games. Missing seasons are omitted, exactly as in the NHL prototype; this can
overvalue players absent for a whole year. Do not use target-year observations.

Projected games are capped at 80 and floored at 60 for players with at least
100 combined prior games, otherwise floored at 40. For fewer than 60 combined
games, multiply scoring rate by `0.85 + 0.15 * combined_games / 60`. These are
the NHL prototype's skater constants, not parameters tuned for basketball.
Short-season historical games are not silently rescaled. Also test the raw
projected total without positional replacement to isolate VOR's contribution.

## Replacement value and positions

Use primary PG/SG/SF/PF/C groups for replacement baselines, as the NHL model uses
primary positions. Derive replacement depth from this league's 16 teams and 12
roster spots. Allocate G equally to PG/SG, F equally to SF/PF, and UTIL and bench
spots equally across the five positions; IR is not a rostered replacement spot.
This gives PG/SG/SF/PF replacement rank 40 and C rank 32. Take the projected total
at that rank within each group; if a group is smaller, use its last player.
`VOR = projected total - positional replacement total`.

Only statistically modeled players establish replacement baselines. Historical
unmodeled players retain their preseason ESPN slots while modeled veterans
reorder, as in the empirical experiment. This is an explicit fallback, not a
statistical forecast of rookies. Full ESPN eligibility and position limits still
govern legal picks and completed rosters; primary-position VOR is an approximation
and does not price the complete value of multiple-position eligibility.

## Draft experiment

Use verified dated preseason packs for ending seasons 2019, 2023, 2024, 2025 and
2026. Run all 16 draft slots and seeds -1,0,1 against the same ESPN-based opponent
orders and noise construction as the prior empirical experiment. Three new
policies: NHL-style raw total, NHL-style VOR, NHL-style VOR with next-pick timing.
Re-run ESPN and available primary non-ESPN expert controls in the same cases.
For the overlapping 2025–26 target years, also show the already frozen empirical
results separately, provided the paired ESPN baseline totals match exactly.

Next-pick timing uses the actual remaining ESPN order and opponent selections
before the next pick; final picks have no timing restriction. Legal roster
construction and the draft simulator are reused unchanged. Lock selections and
input/implementation hashes before joining target-year NBA outcomes for scoring.
Primary metric is actual season fantasy points of all 12 drafted players, with
paired percentage differences/wins versus ESPN. Also report zero-game players
and modeled-pick coverage. No weekly H2H, waiver, replacement-streaming or playoff
simulation is claimed, and overlapping cases are not independent seasons.

## Current comparison board and adjustments

For 2026–27, reuse the current verified roster/eligibility universe and ban list.
Use the fixed historical production/games formula for modeled players and the
existing comparison forecast for players below the history threshold. Compute
replacement from modeled players and assign fallback players a clearly labeled
comparison forecast/VOR. Personal bans affect personal ranks, not analytical
replacement pools, since opponents can still draft those players.

Support explicit season-scoped manual adjustments of games and scoring-rate
multiplier with ESPN ID, source URL, observation timestamp and note. The default
file is empty. A team change or note alone does not change scoring. Never apply
2027 overrides to historical runs. Current sourced injury-return opportunity
caps can lower games after overrides; unknown return dates remain flagged and
season-out/inactive players remain excluded by the verified comparison universe.
The current injury-aware board is not validated by a historical experiment that
lacks equivalent dated injury snapshots. Retain the scheduled expert strategy.
