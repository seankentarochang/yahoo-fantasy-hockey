# Expert points-board comparison, version 1

Specified October 17, 2026 before running this expanded comparison. Previous
years/source outcomes have already been studied, so results are exploratory,
not fresh independent holdouts. Reuse the research branch/PR. Do not change the
live expert source or earlier locked experiments.

## Sources and temporal eligibility

Use ending seasons 2023–2026 and the existing hash-verified preseason packs,
cutoffs, eligible players and source captures. Test every accepted points board,
including RotoWire total/per-game/early variants as separate boards of the same
publisher. Do not count NBA.com republication as an independent publisher.

Add these discovered captures in a separate catalog without rewriting frozen
ranking packs:
- RotoBaller ending 2024: explicit points top 50, static tables, article dates
  2023-08-12/2023-10-12, URL ending `/1214219`.
- FantraxHQ ending 2025: static points top 200, dates 2024-09-26/2024-09-28,
  `/2024-25-fantasy-basketball-points-league-rankings-top-200/`.
- Yahoo/Dan Titus ending 2024: published FantasyPros NBA draft/PTS widget,
  year 2023, expert 3793, 261 rows, last_updated_ts 1697612943, preceding cutoff.

The Yahoo article embeds identify the public widget; the widget's published
script identifies its public ranking endpoint. Capture article/widget/script/API
provenance. Use rank/name fields only; current teams, headshots, eligibility and
other dynamic fields in old widget responses are not historical predictors.
Validate NBA, year, draft/week0, PTS scoring, individual expert identity and
unique contiguous ranks. Reject responses whose global last-updated timestamp
or individual expert-publication timestamp is after the frozen cutoff, even if
the article date itself precedes it. Ending 2023/2025/2026 Yahoo responses fail
that stricter timestamp test and stay diagnostic, not primary results. Do not
substitute High Score, category, dynasty or rest-of-season rankings.

Raw captures and normalized ranks retain hashes. Match only unique known ESPN
names, preferring IDs with prior played statistics when stale duplicates exist.
New source players absent from the frozen pack remain unmatched. Eligible pack
players ranked only by a new source may join the pool; append them to the ESPN
market tail by prior-season league points then stable ID. No target outcomes
establish ranking, eligibility or pool membership. Record unmatched rows and
published-versus-matched depth. Publishers' native points formulas differ;
outcomes are always scored under this league's actual weights.

## Fixed policies and depth controls

For each year compare ESPN, every other source board and equal-publisher
consensus. Complete partial expert boards by putting their published players
first in expert order, then remaining players in ESPN order. Report covered
pick share; a public top-50 preview plus ESPN tail is not a full expert board.

Run both full available coverage and top-50-only coverage for every board.
Truncation uses published ordinal <=50, never the first 50 matched players.
For consensus, select one primary board per publisher: prefer total/published
order over per-game, then the latest eligible publisher date and source ID.
Average completed ordinal ranks with one vote per publisher, ESPN included;
tie-break by ESPN order/ID. This is a fixed equal-weight policy, not tuned to
results. Same-publisher variants are not extra consensus votes.

Each non-ESPN board and consensus runs directly and with the existing next-turn
timing rule. Legal roster construction/eligibility is unchanged. Use all 16
draft slots and seeds -1,0,1. Primary opponent field is ESPN for all four years.
Additionally run a publisher-consensus opponent field in 2024–25, the common
season containing four independent publishers. That field uses full-coverage
consensus for both depth tests, so changing our board depth does not change
opponents. Use exactly the previous `empirical-v1:{year}:{seed}:{team}` noise,
allocated in ESPN market order, and Gaussian standard deviation 12 (zero for -1).
No current personal bans or retrospective injury overrides alter historical picks.

## Evaluation and interpretation

Lock source/input/data/implementation/protocol/config hashes, completed orders,
policy provenance, candidate pool and draft choices before joining target-year
outcomes. Primary outcome is actual full-roster season fantasy points, with
paired percent gains/wins versus ESPN, zero-game picks and source coverage.
Use the audited SportsDataverse outcomes and unchanged legal-roster simulator.
No weekly H2H, waiver, playoff or live-draft superiority is claimed.

Report source-by-year/depth/field results and equal-year publisher aggregates
where multiple eligible years exist. Compare common seasons explicitly; do not
declare a universal winner by averaging publishers with different year coverage.
Report timing's paired contribution. Verify repeated ESPN controls against
earlier experiments where the candidate pool is unchanged. Depth truncation,
opponent sensitivity and overlapping scenarios are not independent years.
