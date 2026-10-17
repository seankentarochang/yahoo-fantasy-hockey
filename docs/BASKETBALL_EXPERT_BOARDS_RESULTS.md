# Comparing expert points draft boards

The specific board, publication date and scoring basis matter. A current points
board is a better-supported choice than an arbitrary expert list. The fixed
publisher consensus is promising against ESPN-based opponents, but its advantage
largely disappears in the alternate-opponent test. No live source was changed.

The [protocol](BASKETBALL_EXPERT_BOARDS_PROTOCOL.md) was committed at `ed6bfd9`
before this expanded evaluation. These are previously studied seasons and
exploratory results, not fresh independent holdouts. No ranking/timing parameters
were selected from these outcomes.

## Scope

Test 13 historical boards across six publisher families: ESPN, RotoWire,
NBC/Rotoworld, Yahoo/Dan Titus, RotoBaller and FantraxHQ. NBA.com's RotoWire
republication is another snapshot of RotoWire, not another publisher vote.

Run 3,744 legal 16-team, 12-round simulations across 480 paired settings:
all 16 draft slots, seeds -1,0,1, four seasons, full/top-50 source depth and an
additional consensus-opponent field for 2024–25. Results score actual full-roster
season fantasy points using this league's weights. Roster/position rules and
the simulator are unchanged. These are overlapping scenarios, not thousands of
independent seasons or weekly H2H/waiver/playoff simulations.

## Main comparison

Mean paired percent change in actual roster-season points versus ESPN, against
the same ESPN-based opponents. Direct picks use highest available expert rank
that satisfies roster constraints. Public partial boards use ESPN for their tail.
ESPN is 0% by construction; dashes mean no eligible source for that year.

| Board | 2022–23 | 2023–24 | 2024–25 | 2025–26 |
|---|---:|---:|---:|---:|
| ESPN | 0.00% | 0.00% | 0.00% | 0.00% |
| RotoWire primary points board | +0.66% | — | -0.05% | +8.99% |
| Yahoo points | — | +4.68% | — | — |
| RotoBaller points | — | -0.60% | — | — |
| NBC/Rotoworld points | — | — | -0.40% | — |
| FantraxHQ points | — | — | -11.52% | — |
| Equal-publisher consensus | +1.11% | +4.71% | +6.42% | +3.92% |

Consensus completes each publisher's partial board with ESPN order, includes one
ESPN vote, and averages one completed ordinal ranking per publisher. RotoWire
contributes one primary snapshot, preferring total/published order over per-game
and then the latest eligible date. Ties resolve by ESPN order. The voters change
by year: 2,3,4,2 publisher families respectively. This is not an independently
projected consensus: ESPN influences both its own vote and incomplete-board tails.

Equal-year averages in the ESPN-opponent field are +4.04% for direct consensus
over four years and +3.20% for primary RotoWire over its three available years.
Those averages are **not a fair global publisher league table**: available years,
depth, scoring formulas and opponents differ. Yahoo/NBC/Fantrax/RotoBaller each
have only one eligible year here.

## Format and freshness within the same publisher

RotoWire's three 2025–26 boards produce very different results:

| RotoWire snapshot | Direct picks | With next-turn timing | Direct, top-50-only |
|---|---:|---:|---:|
| Earlier NBA.com points snapshot | -9.95% | -5.79% | +0.33% |
| September projected points/game | -8.23% | -2.14% | -0.26% |
| September projected total points | +8.99% | +11.81% | +6.35% |

For the total-points board, timing raises the paired win rate against ESPN from
77.1% to 85.4%. The earlier snapshot averages 1.38 zero-game players per roster;
the total-points board averages 0.04 (ESPN 0.56). Those figures support considering
availability and snapshot date, but do not isolate a causal effect of freshness:
rank order, coverage and scoring basis change together.

The result is not simply “RotoWire always wins.” Its per-game and earlier points
snapshots lose in the same season where its total-points board wins substantially.

## Timing is board-dependent

| Board/year | Direct | With timing |
|---|---:|---:|
| RotoWire 2022–23 | +0.66% | +0.23% |
| Yahoo 2023–24 | +4.68% | -2.30% |
| RotoBaller 2023–24 | -0.60% | -0.42% |
| NBC 2024–25 | -0.40% | -1.07% |
| Fantrax 2024–25 | -11.52% | -11.21% |
| RotoWire total 2025–26 | +8.99% | +11.81% |

Timing uses the existing ESPN remaining-order/next-turn heuristic. It is not a
calibrated probability that a player survives until the next turn. It helps
some boards and hurts others; the Yahoo result is a material counterexample to
assuming timing is a universal improvement. Direct/timed orders share the same
board, seed, slot, opponent field and legality rules.

Consensus with timing returns +0.89%, +4.79%, +6.89%, +8.48% by year, averaging
+5.26% equally across years against ESPN-based opponents. That does not eliminate
the coverage and opponent sensitivities below.

## Control for public board length

Some sources expose only a top-50 preview. Repeat the experiment using only each
source's published ranks <=50, with ESPN fallback thereafter. Do not take the
first 50 matched rows if a published player is missing. All new sources' top 50
match the frozen historical identities.

| Direct policy | Year | Full available depth | Top-50-only |
|---|---|---:|---:|
| Yahoo | 2023–24 | +4.68% | +2.32% |
| RotoBaller | 2023–24 | -0.60% | -0.60% |
| RotoWire | 2024–25 | -0.05% | -0.05% |
| NBC | 2024–25 | -0.40% | -11.44% |
| Fantrax | 2024–25 | -11.52% | -7.58% |
| Consensus | 2024–25 | +6.42% | -2.21% |
| RotoWire total | 2025–26 | +8.99% | +6.35% |

Depth materially changes the outcome. The 2024–25 full-consensus advantage does
not survive uniform top-50 coverage. A top-50 source plus ESPN tail should not be
described as a complete expert draft. In full-depth direct runs, RotoWire's
50-player previews cover about 47% of our picks; NBC/Fantrax cover all picks in
2024–25. Consensus's coverage statistic is the fraction ranked by every voter,
not merely by one publisher.

## Alternate opponents

In 2024–25, also draft against opponents following the full publisher consensus,
using the same fixed noise by player. The opponent field stays full-depth even
when our board is limited to top 50.

| Full-depth policy | ESPN-based opponents | Consensus-based opponents |
|---|---:|---:|
| Consensus, direct | +6.42% | +0.68% |
| Consensus, timing | +6.89% | -0.13% |
| RotoWire, direct | -0.05% | -6.58% |
| NBC, direct | -0.40% | -3.08% |
| Fantrax, direct | -11.52% | -14.30% |

Each column compares with ESPN drafting in that same opponent field. Much of the
consensus benefit is exploiting disagreement with ESPN-order opponents, rather
than a market-independent advantage. This one-season sensitivity test is not
proof about all real drafts, mixed human strategies or actual ESPN ADP.

## Data coverage and source eligibility

New eligible captures:
- [Yahoo 2023–24 points article](https://sports.yahoo.com/2023-24-fantasy-basketball-draft-rankings-points-leagues-220930771.html)
  and its published FantasyPros widget: 261 ranks, 253 matched. The response's
  overall and expert timestamps precede the frozen cutoff. Current teams,
  positions and headshots in that response are ignored.
- [RotoBaller 2023–24 points top 50](https://www.rotoballer.com/fantasy-basketball-rankings-points-leagues-2023-2024/1214219):
  all 50 matched; published August 12 and modified October 12, 2023.
- [FantraxHQ 2024–25 points top 200](https://www.fantraxhq.com/2024-25-fantasy-basketball-points-league-rankings-top-200/):
  all 200 matched; published September 26 and modified September 28, 2024.

Before inspecting results, name-join checks identified and corrected the known
Cameron/Cam Thomas and Xavier Tillman Sr./Xavier Tillman aliases. The final run
uses those canonical joins. Eight Yahoo-listed rookies are absent from the frozen
2023–24 eligible pool and remain unmatched, including published ranks 153 and 176;
the other six are after rank 200. Published depth is retained rather than inflated
to replace missing players. Yahoo also adds Miles Bridges, an already eligible
pack player with no prior-season appearances who was absent from the old market;
he joins ESPN's market tail. All ESPN controls still match the prior experiment
exactly, including that expanded-pool year. The existing 2025–26 ESPN pack matches
149 of 150 published ranks.

The Yahoo ending-2023/2025/2026 responses have global update timestamps after our
frozen cutoffs, despite earlier individual publication/article dates. They stay
diagnostic and are not silently admitted. This is a conservative cutoff rule,
not a claim that every rejected update necessarily used regular-season outcomes.
High Score, category, dynasty and rest-of-season sources are excluded. Native
points scoring differs by publisher; ranking performance is tested using our
league's actual weights, not by pretending those formulas are identical.

Captures are retrospective and publisher-dated, without independent archival
timestamps. Publisher families can share information; six publishers do not mean
six statistically independent prediction systems. No current bans, injury news
or return dates are retrospectively applied to historical picks.

## Reproduction and evidence

```text
python -m basketball research expert-collect
python -m basketball research expert-backtest
python -m unittest discover -s tests -p test_basketball_expert_boards.py
```

Twelve focused backend tests pass for source parsing, timestamp/format/expert
eligibility, dynamic-metadata exclusion, alias joins, partial-board fallback,
single publisher votes, published-depth truncation, timing isolation, paired
baselines, capture integrity and comparison-only command routing. The full run
checks roster legality/unique picks and repeated controls. Source/catalog and
decision locks verify; summaries reconcile with the saved per-case results.

The committed [aggregate evidence](basketball_expert_boards_results.json) includes
all year/depth/field policies, paired timing changes, source coverage, equal-year
publisher aggregates and provenance. Raw captures and individual draft receipts
stay in ignored `basketball/data/research-experts/`.

Decision SHA-256:
`0eee4fd899b3aab00ec999e37c2a25833fd9019247fa12f9e989f3c2cc3cf01b`.
