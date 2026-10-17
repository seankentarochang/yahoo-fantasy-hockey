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
