# NHL-style basketball board and backtest — October 17, 2026

The fixed NHL-style statistical core beat ESPN in 2018–19 but underperformed in the other four evaluated seasons. Positional VOR did not consistently improve the raw projection. The results do not justify replacing the current expert draft strategy.

## Method

- Production: two prior seasons, 65/35 weighted fantasy-point totals divided by weighted games.
- Games: 80/20 recent/older average; cap 80; floor 60 for at least 100 combined prior games, otherwise 40. Below 60 combined games, scoring gets the NHL sample-size discount; fewer than 20 games uses a marked fallback. These fixed constants were borrowed from the NHL skater prototype, not tuned to basketball outcomes.
- Projected totals are converted to value over replacement in primary-position groups. Depth is derived from the actual 16-team, 12-player league: PG/SG/SF/PF rank 40; C rank 32. Flexible slots and bench depth are split equally. Actual picks still respect all eligible positions and roster limits.
- Three variants: raw projected season totals; VOR; VOR with the existing next-pick market window. No historical manual adjustments, current injury reports or current team information enter those forecasts.
- Five dated preseason input packs: ending seasons 2019, 2023, 2024, 2025 and 2026. All 16 slots and three fixed opponent seeds per policy/year. Same opponent construction, simulator and scoring as the prior empirical experiment.

## Results versus ESPN

1,152 complete 16-team, 12-round draft scenarios, comprising 720 new-policy drafts and 432 control drafts. There are 240 paired year/slot/seed settings; these are not 1,152 independent seasons. Values below are mean paired percentage differences in actual total fantasy points of the 12 drafted players. They are not weekly H2H wins.

| Season | Raw NHL-style totals | NHL-style VOR | VOR + next-pick timing | RotoWire control |
|---|---:|---:|---:|---:|
| 2018–19 | +24.38% | +25.48% | +24.44% | Unavailable |
| 2022–23 | -7.09% | -11.07% | -2.94% | +0.66% |
| 2023–24 | -5.91% | -13.24% | -8.21% | Unavailable |
| 2024–25 | -4.17% | -7.94% | -8.37% | -0.05% |
| 2025–26 | -52.22% | -48.35% | -16.99% | +8.99% |

NBC / Rotoworld is also available in 2024–25: -0.40% versus ESPN under this metric. Unavailable controls were not filled with rankings from another year.

## Earlier learned-model comparison

Every paired ESPN baseline score in the overlapping test years matched the frozen earlier experiment exactly. These rows reuse that experiment, with its locked choices and the same outcome dataset; they do not represent newly rerun or independently selected models.

| Policy | 2024–25 vs ESPN | 2025–26 vs ESPN |
|---|---:|---:|
| Learned production × historical workload | +2.58% | -54.84% |
| Learned totals + next-pick timing | +5.23% | -16.87% |
| NHL-style VOR | -7.94% | -48.35% |
| NHL-style VOR + next-pick timing | -8.37% | -16.99% |

## Availability diagnostic

The historical experiments do not include dated injury, retirement or rotation updates. The copied NHL rules also omit an entirely absent prior season rather than treating it as zero workload, and impose games floors. These can carry old production forward with overly optimistic availability.

| Season | ESPN: zero-game players/roster | VOR: zero-game players/roster | VOR + timing: zero-game players/roster |
|---|---:|---:|---:|
| 2018–19 | 0.21 | 0.00 | 0.02 |
| 2022–23 | 0.08 | 1.79 | 0.90 |
| 2023–24 | 0.04 | 0.65 | 0.60 |
| 2024–25 | 0.15 | 0.46 | 0.52 |
| 2025–26 | 0.56 | 3.77 | 0.96 |

VOR adjusts positional scarcity; it does not repair inaccurate production or availability forecasts. Its static primary-position baselines also approximate a basketball league where multiple-position eligibility and flexible slots matter. No causal claim is made that one of these limitations alone explains every loss.

## Current 2026–27 comparison board

The current board has 317 players, with 303 historical projections and 14 marked existing-comparison fallbacks. It uses verified current roster membership, preserves all personal bans and caps games using current sourced injury-return opportunities. The default source-scoped manual adjustment file is empty. A team label or research note alone does not change production. This current pipeline is different from the news-free historical test and has not been validated by it.

| VOR rank | Player | Primary | Fpts/game | Games | Season points | VOR |
|---:|---|---|---:|---:|---:|---:|
| 1 | Nikola Jokic | C | 65.2 | 66.0 | 4306 | 3148 |
| 2 | Shai Gilgeous-Alexander | PG | 54.3 | 69.6 | 3780 | 2565 |
| 3 | Kevin Durant | PF | 42.6 | 74.8 | 3187 | 2313 |
| 4 | Giannis Antetokounmpo | PF | 51.5 | 60.0 | 3092 | 2219 |
| 5 | Luka Doncic | PG | 55.2 | 61.2 | 3376 | 2160 |
| 6 | Tyrese Haliburton | PG | 45.4 | 73.0 | 3316 | 2101 |
| 7 | Jalen Johnson | PF | 45.6 | 64.8 | 2958 | 2084 |
| 8 | Jamal Murray | PG | 43.6 | 73.4 | 3198 | 1983 |
| 9 | Victor Wembanyama | C | 51.6 | 60.4 | 3118 | 1961 |
| 10 | Tyrese Maxey | PG | 47.8 | 66.4 | 3171 | 1956 |
| 11 | Cade Cunningham | PG | 47.7 | 65.2 | 3110 | 1895 |
| 12 | Karl-Anthony Towns | C | 40.3 | 74.4 | 2998 | 1841 |
| 13 | James Harden | PG | 42.4 | 71.8 | 3042 | 1826 |
| 14 | Julius Randle | PF | 34.8 | 77.0 | 2677 | 1804 |
| 15 | Jalen Brunson | PG | 41.6 | 72.2 | 3003 | 1788 |
| 16 | Alperen Sengun | C | 40.4 | 72.8 | 2940 | 1783 |
| 17 | Donovan Mitchell | SG | 43.1 | 70.2 | 3023 | 1737 |
| 18 | Scottie Barnes | SF | 40.3 | 77.0 | 3106 | 1694 |
| 19 | Evan Mobley | PF | 38.6 | 66.2 | 2556 | 1682 |
| 20 | Bam Adebayo | C | 37.5 | 74.0 | 2772 | 1615 |

The mechanical board has conspicuous disagreements with expert forecasts. For example, Walker Kessler projects to 40 games from the fixed two-season formula and ranks 163 by VOR. That is an availability-model assumption, not a sourced medical prognosis. No parameter was changed to make this rank look more reasonable.

## Reproducibility and scope

- Protocol committed before this experiment: `BASKETBALL_VALUE_PROTOCOL.md`.
- Locked decision hash: `feb45da93c617c75fac3ea29bcf45d7202e73bb2a1df91c1dfb25c8bc7c77052`.
- Complete aggregate results, source/implementation hashes and replacement baselines: `basketball_value_results.json`.
- Local full board: `basketball/data/research-value/rankings.md`; full projections: `rankings.json`; complete locked historical choices: `decisions.json`.
- Current adjustment schema: `basketball/value_adjustments.json`. Entries require ESPN ID, source URL, timestamp and note; optional games or scoring multiplier changes are explicit. Future observations are rejected, and current-season overrides never apply to historical tests.
- Eleven targeted backend tests pass for weighting, sample thresholds, games floors/cap, chronological isolation, replacement arithmetic, adjustment scope/time, injury caps and comparison-only CLI actions.
- Several seasons have been studied before. These are exploratory chronological comparisons, not newly untouched independent holdouts. No parameters were retuned after seeing this experiment's outcomes.
- Roster asset scoring omits weekly lineup scheduling, waiver replacements, trades and playoff timing. Primary-position VOR is not a full marginal roster optimizer.

Reproduce from the captured inputs:

```text
python -m basketball research value-backtest
python -m basketball research value-rank
python -m unittest discover -s tests -p test_basketball_value_board.py -v
```

The live expert board, API drafting transport, injury policy, personal bans and scheduled real draft remain unchanged.
