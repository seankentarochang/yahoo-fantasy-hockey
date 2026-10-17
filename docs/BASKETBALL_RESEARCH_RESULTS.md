# Comparison model results — October 17, 2026

Version 2; comparison only. Model assumptions were recorded before generating revised scores. This board has not passed a predictive backtest and does not select automatic draft picks.

## Actual data coverage

- 317 currently rostered players with complete forward statistical projections.
- Statistical rate coverage: 317 ESPN, 299 Basketball Reference, 30 Hashtag. 301 players have at least one outside statistical source.
- Playing-time coverage: 317 ESPN, 243 FantasyPros, 30 Hashtag. FantasyPros shooting percentages were not used to invent makes/attempts.
- DARKO: 530 raw records captured, as of July 26, 2026; excluded from the combined model pending current-role adjustment and component validation.
- Ten completed ending seasons, 2017–2026: 255,085 regular-season played observations and 11,979 games. Raw files retain playoffs, play-in and Cup finals; those are explicitly excluded from the audit totals.
- Historical source audit: 602 minute strings ended in :60, explicitly converted as a seconds rollover in the audit. Two all-zero rows with missing minutes and no absence comment are separately classified, not treated as played games or assigned an injury reason.

## Initial ranking comparison

Main rank measures expected season total under the league scoring; per-game rank helps distinguish production from availability. RotoWire is an expert-board comparison with its own assumptions. Rank agreement is not an accuracy test. The two top 100s share 90 players. Historical and publisher inputs overlap; source counts are not independent votes.

| Our season rank | Player | Fpts/game | Games | Our per-game rank | RotoWire | ESPN |
|---:|---|---:|---:|---:|---:|---:|
| 1 | Nikola Jokic | 65.0 | 71.7 | 1 | 1 | 1 |
| 2 | Shai Gilgeous-Alexander | 54.7 | 73.8 | 4 | 3 | 2 |
| 3 | Luka Doncic | 57.4 | 67.6 | 2 | 5 | 3 |
| 4 | Victor Wembanyama | 53.8 | 66.3 | 5 | 2 | 4 |
| 5 | Giannis Antetokounmpo | 54.7 | 64.5 | 3 | 4 | 5 |
| 6 | Cade Cunningham | 47.6 | 69.2 | 6 | 6 | 7 |
| 7 | Jalen Johnson | 46.3 | 69.7 | 7 | 10 | 6 |
| 8 | Donovan Mitchell | 44.0 | 71.7 | 11 | 19 | 10 |
| 9 | Anthony Edwards | 43.3 | 72.3 | 15 | 8 | 8 |
| 10 | Scottie Barnes | 41.2 | 75.1 | 23 | 16 | 17 |
| 11 | Jalen Brunson | 42.4 | 73.0 | 19 | 20 | 15 |
| 12 | Jamal Murray | 43.1 | 71.8 | 16 | 24 | 28 |
| 13 | Tyrese Maxey | 43.7 | 70.2 | 12 | 15 | 13 |
| 14 | Alperen Sengun | 40.8 | 73.2 | 26 | 9 | 22 |
| 15 | Kevin Durant | 41.0 | 72.5 | 24 | 29 | 23 |
| 16 | LaMelo Ball | 43.4 | 67.8 | 14 | 50 | 14 |
| 17 | James Harden | 40.0 | 73.5 | 32 | 35 | 25 |
| 18 | Karl-Anthony Towns | 40.3 | 72.5 | 29 | 13 | 24 |
| 19 | Josh Giddey | 42.8 | 68.2 | 17 | 22 | 18 |
| 20 | Cooper Flagg | 40.3 | 72.2 | 27 | 7 | 11 |

## Disagreements to investigate

These are model diagnostics, not conclusions that the expert is wrong. Durability is a weighted historical heuristic, not a medical prognosis. No parameter was retuned to eliminate a disagreement.

| Player | Our season rank | Our per-game rank | RotoWire | Expected games |
|---|---:|---:|---:|---:|
| Walker Kessler | 95 | 59 | 36 | 57.7 |
| Donovan Clingan | 70 | 90 | 31 | 74.3 |
| Matas Buzelis | 75 | 96 | 30 | 75.8 |
| Kon Knueppel | 32 | 65 | 74 | 78.8 |
| Ja Morant | 88 | 54 | 130 | 58.4 |
| Jimmy Butler III | 158 | 46 | Outside published top 200 | 42.5 |

Kessler illustrates a limitation: our per-game rank is 59 but the historical durability blend estimates only 57.7 games, dropping his season-total rank to 95. This may over-penalize his one-off absence. It should be tested against a forward-games-only baseline, not promoted into the draft because it produces a different answer.

Expected season points omit replacement players, weekly lineup constraints and waivers; they are not a complete H2H win model. Rookies without prior NBA data retain a visible projection-only label. Personal bans remain marked separately.

## Reproducibility

- Input pack SHA-256: `985d65f13f9dc007a9c953dd5dcb2fd7b95edc3b3ece3fd62faa2022762c955a`.
- Ranking JSON SHA-256: `d3dc7cdeadf5a23fc11f63d5b9398c02c73f2dfe0948f57d69e7c5c1bae9efc2`.
- Rebuilding twice from the same captured inputs produced identical ranking JSON.
- Focused backend tests cover hand-calculated scoring, source roles, no target-season actual leakage, rank independence, injury caps, durability, bans, retired/inactive filtering, manifest tampering, source identities and game-log quality.

Local full 317-player board: `basketball/data/research-board/rankings.md`; complete forecasts: `rankings.json`; capture provenance: `manifest.json`. Historical download provenance: `basketball/data/research-datasets/manifest.json`. Large raw data and local league information stay ignored by Git.

The independent research worktree is separate from the scheduled draft checkout. No draft source pointer, transport, selection policy or automation was changed.
