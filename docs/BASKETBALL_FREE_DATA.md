# Free basketball research datasets

Verified October 17, 2026. Access and usable coverage were checked directly;
search snippets alone do not establish that a full dataset is freely available.

| Source | Verified coverage | Appropriate use | Important qualification |
|---|---|---|---|
| [Basketball Reference SPS](https://www.basketball-reference.com/friv/projections.cgi?year=2027) | 578 projected player lines, all 11 league scoring components per 36 minutes | Full statistical-rate baseline and input to our comparison board | No forecast games or rotation minutes; no new rookies without prior NBA games. Unique name matching and current roster verification required. |
| [FantasyPros overall projections](https://www.fantasypros.com/nba/projections/overall.php) | 264 public player lines, updated October 16, 2026 | Current projected games and minutes; alternative durability assumptions | Overall table omits shooting makes/attempts. Do not reconstruct them from rounded percentages. Individual public projection pages show makes/attempts; the Jokic page's totals match the upcoming-season overall table. Consensus source overlap is possible. |
| [DARKO Fantasy Lab](https://www.darko.app/projections) | 530 public raw projection records; displayed table filters out very low minutes | Next-game box-stat rate research; future candidate for rates with current rotation estimates | Captured as of July 26, 2026. Some players have older individual dates. Two records have 3PA greater than FGA. Separately estimated points and shooting can disagree. Captured for inspection, excluded from initial combined forecast. DPM itself is not fantasy scoring. |
| [SportsDataverse player box-score release](https://github.com/sportsdataverse/sportsdataverse-data/releases/tag/nba_stats_player_boxscores) | Provider advertises 30 ending seasons, 1997–2026; downloaded and audited ten seasons, 2017–2026 | Game-level training, actual fantasy outcomes, minutes stability, schedule-aware evaluation | NBA IDs differ from ESPN. Files also contain other game types and DNP rows. Filter regular-season type 2 and game prefix 002. Historical results do not establish preseason forecast availability. |
| [llimllib/nba_data](https://github.com/llimllib/nba_data) | Maintainer documents NBA game logs and season stats from 2009–10, Parquet/DuckDB storage | Alternative bulk data and advanced/team-context joins | Inspected primary documentation; not downloaded into this run. Different source families can share the same upstream NBA observations. |
| [nbadb](https://github.com/wyattowalsh/nbadb) | Maintainer documents historical NBA statistics, tracking, rotations and multiple export formats | Broader candidate for feature engineering beyond basic box scores | Inspected primary documentation; not yet imported or audited. Endpoint coverage varies by season. |
| [Hashtag](https://hashtagbasketball.com/fantasy-basketball-projections) | 30 publicly visible complete projected stat lines | Additional current projection cross-check | Full forecasts require a subscription. Kept as a limited contributor, not the primary outside dataset. |

## Sources that did not meet the full-free criterion

- [FanScout](https://fanscout.pro/projections): the inspected website explicitly
  limited its public view to the top 20 and offered an upgrade. Its mobile app may
  offer different access; full free web export was not verified.
- [League Winner](https://leaguewinnersports.com/projections): the page says full
  projected stat lines are Pro, although some top ranks are public.
- [RotoWire projections](https://www.rotowire.com/basketball/projections.php): full
  sortable statistical projections require a subscription. The existing public
  expert ranking board remains a separate rank comparison.
- CBS projection URLs returned server errors during direct checks. Not imported.
- [Dunk Walrus](https://www.dunkwalrus.com/): public tools exist, but the inspected
  home page still described the 2026–27 official projection release as forthcoming.
  A complete dated export was not verified in this pass.

## Methods and independence

[SPS methodology](https://www.basketball-reference.com/about/projections.html)
uses recent seasons, regression and age. Its historical data overlap our own
weighted historical component. [DARKO methodology](https://www.darko.app/about)
describes a next-game model with stat-specific decay and aging, and specifically
identifies minutes as difficult. Neither a publisher's accuracy claim nor broader
data coverage proves improved results in this league.

Historical projection pages such as
[2025–26 SPS](https://www.basketball-reference.com/friv/projections.cgi?year=2026)
are candidates for future evaluation. A historical URL fetched today does not
prove the exact numbers were published before that year's draft. Blind evaluation
needs dated preseason captures or a fully specified model trained only on earlier
seasons. Keep training, parameter selection and held-out evaluation separate.

## Reproduce the comparison

Run from a checkout with a current normalized league snapshot and the existing
public expert-board library:

```text
python -m basketball research collect
python -m basketball research build
python -m basketball research datasets --years 2017 2018 2019 2020 2021 2022 2023 2024 2025 2026
python -m unittest discover -s tests -p test_basketball_research.py -v
```

Collection uses public feeds and reads local normalized data; it does not open
an authenticated draft connection. Captured source bytes and input packs have
SHA-256 identities. Builds verify them before forecasting. Historical files and
large captures stay in the ignored data directory. Source code licensing is not
a grant of unrestricted rights to the underlying NBA observations.

See [the prespecified model](BASKETBALL_RESEARCH_PROTOCOL.md) and
[the resulting comparison](BASKETBALL_RESEARCH_RESULTS.md).
