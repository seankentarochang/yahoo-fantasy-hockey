# Current-season ADP mock drafts

Comparison only. No ESPN mock room is joined and no picks, queues, live policy or automation are changed.

Use the configured 16-team, 12-round snake rules, slot 15 (last known league slot), current public ESPN fantasy ADP and STANDARD ranks. Refresh the public fantasy pool without credentials and capture source bytes. Require complete pagination and unique identities. Use the existing hash-locked, same-day research roster/injury evidence; reject evidence older than 24 hours. This is less stringent than live execution verification.

Our quality order is the existing equal-publisher consensus: ESPN, selected current RotoWire points sheet, NBC/Rotoworld points and FantraxHQ points, one vote per publisher. Unpublished tails follow ESPN rank. Compare the existing next-turn heuristic using the remaining ADP order instead of the ESPN rank order. Choose the best legal expert player among the first N remaining ADP players, where N is the number of opponents' picks until our next turn. On the final or consecutive pick, or when that window has no eligible player, take the best legal consensus player. This window is not a calibrated survival probability or an absolute reach cap.

Run 100 seeds for each of three assumed fields, fixed before examining outputs:

- ADP: every opponent follows numerical ESPN ADP without preference noise.
- Typical: each opponent is independently an ADP follower (80%) or ESPN-rank follower (20%); add fixed per-player Gaussian preference noise with standard deviation 8 pick units.
- Loose: ADP followers (60%) or rank followers (40%); Gaussian preference noise with standard deviation 16 pick units.

These are sensitivity assumptions, not parameters fitted to observed human choices. ADP does not supply draft-position variance or points-only, 16-team sample guarantees. Missing, nonfinite, zero or sentinel ADP falls back explicitly to ESPN rank. Generate preference noise in stable ID order with seeded RNGs. No target outcomes exist or are used. A deterministic ADP field repeats identically across seeds and must not be described as 100 independent drafts.

All teams must finish with legal, unique rosters and all nine starting positions covered. All candidates need active fantasy status and active current NBA roster membership. Exclude out-for-season and suspended players. Apply the existing injury price windows to all teams: known, non-overdue returns within 14 days in rounds 1–4, 42 days in rounds 5–8, and before the configured season end in rounds 9–12. Unknown injury returns stay excluded. Recompute days from the configured draft date, using sourced structured return estimates; no injured-player count limit. Our player/team bans apply only to our team, including current roster team identity.

Report per-round selections, conditional availability on our actual simulated paths, final roster frequencies and three representative complete drafts (one per field). Choose each representative by maximal sum of its round-choice frequencies within that field, then lowest seed; never fabricate a composite roster. Include full pick logs, source/input/code hashes and exclusions in ignored local JSON; publish a compact report and aggregate evidence. Projected points are optional context, not proof of strategy quality. This is a forward draft rehearsal, not another historical backtest or evidence of future wins.

## Diagnostic amendment before the second rehearsal

The first 300 simulations are retained as `mocks-raw-adp.json`, SHA 9caa00471ffc95fd092b75ce666669640daf19eab79eab635006800e850aaa37. Inspection found 231 of 352 eligible players at ADP 130 or above, including 165 at 140 or above; maximum 141.20. The public Hashtag ESPN column independently shows the same saturation. Tiny late ADP differences should not be interpreted as reliable long-draft demand. Constant 16-pick noise also allowed implausibly large first-round slides. These are forward plausibility diagnostics, not season-outcome optimization.

For a second, separately identified 300-case rehearsal, use numerical ESPN ADP below 130 and explicit ESPN STANDARD-rank fallback at/above 130. This cutoff is a disclosed heuristic, not inferred draft-position variance. Label the first field ADP-led with ESPN tail, rather than pure ADP. Mark every fallback player and expose each player's demand score/basis. For noisy fields, use Gaussian sigma `min(field_sigma, 0.25 * demand_score)` so top-ranked players have less absolute preference variation than later picks. Rank followers use their ESPN rank for this calculation. All other settings remain fixed. Preserve both raw and amended results; report differences as sensitivity, not evidence that the amended model is calibrated to human drafts.

## User correction: draft position undecided

The user clarified that the draft position has not been decided. Preserve the amended slot-15 rehearsal as `mocks-slot15.json` (SHA 94da2345a587c60867d0f0327b107520af8c5f19cdefa0967c3770c0f2dfd19d); it is not the assumed real slot. Expand the final rehearsal to all 16 positions, 25 seeds per position per field, 1,200 total trajectories. Summarize each position separately and show actual representative drafts for early/middle/late positions. Keep opponent seeds identical between positions so the simulated field preferences are paired. Default future runs to all slots unless a slot is explicitly supplied. There are 800 noisy trajectories and 16 distinct deterministic ADP-led controls repeated across their 25 seeds; do not pool overlapping scenarios as independent evidence.
