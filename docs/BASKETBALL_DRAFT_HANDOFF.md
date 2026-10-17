# October 18, 2026 draft execution

The user asked, "Can you just draft for me tomorrow" on October 17. This
authorizes selecting the full team during this draft; do not ask for approval
again for each pick. Use the updated RotoWire board with next-turn market timing,
injury return estimates at the configured round, personal bans, position caps
and the ability to fill every starter slot. Follow BASKETBALL_DRAFT_POLICY.md. Do not
switch to the older projection/VOR strategy or the experimental timing hybrid.

## Scope and readiness

- League **2141453434**, team **18**, season **2027** (Diddy League).
- ESPN verified October 17: **October 18 at 11:00 a.m. America/New_York**.
- 16-team snake, 12 selections, 60-second clock, maximum four primary centers.
- ESPN currently reports slot 15; re-read authoritative order on draft day.
- Execution checkout: the directory specified in the scheduled follow-up prompt.
  Use its tested implementation and runtime data while the policy PR is pending.
- Config: `basketball/league.json`; saved login and source library are in ignored
  `basketball/data/`. The permanent main checkout also retains the earlier runtime
  archive; do not silently run its older selection policy.
- Authenticated league reads work. The live draft connection returned HTTP 500
  before the draft room opened; that connection is not yet verified for this
  league. The API transport was previously rehearsed in a separate mock. The October 17 expert rehearsal (practice 2035580386) completed 11 current-source API selections after one browser pick, with zero ESPN autopicks; see BASKETBALL_EXPERT_API_REHEARSAL.md.

## Preflight and execution

Start the scheduled follow-up at 10:30 a.m. Eastern on October 18. Check local
Eastern time before actions. Do not select players on a different date, in a
different league/team/season, or after this draft has completed. If the draft
time changed, report it and use the authoritative new time only within October
18; a different date needs user input. Never create or join another mock.

Read league settings, confirm identity, order, scoring and current source
checksums. Check `draft bans` and `draft injuries --refresh`. Run
`draft refresh-rankings` before draft start to capture the October 16 public
RotoWire points cheat sheet (200 published ranks) or its latest update. Require
`selection_policy: next_turn` and the configured injury round schedule. Names
with ambiguous identity or missing ESPN ranks are reported,
never guessed. Unpublished tails explicitly follow ESPN. A missing/corrupt board
must stop expert drafting rather than fall back to the older model.

Connect to the API when the room opens. HTTP 500 before opening is not proof of
invalid login: retry read-only connection checks with bounded waits. If login
fails, the room stays inaccessible near start, the source cannot validate, or a
pending write cannot be reconciled, notify the user promptly. Never print saved
cookies, JOIN tokens or authenticated URLs.

Keep ESPN Autopick disabled. Do not build an ESPN fallback queue: it cannot
enforce next-turn demand and injury-price rules. Do not clear unrelated queue
entries. ESPN's own autopicks remain outside our local safety policy.

Run the explicitly selected expert watcher from the execution checkout:

```sh
python -u -m basketball draft watch --transport api --strategy expert --source rotowire --execute
```

Keep supervising until ESPN confirms draft completion and all 12 team selections
are recorded. Redirect ordinary output to an ignored local log if useful; poll
the process in bounded intervals and inspect failures. The watcher chooses the
highest legal expert-ranked candidate inside the remaining ESPN demand window
before our next turn, with a deferred tier only after urgent candidates fail
availability. Known return estimates allow temporary injuries at the configured
round: 14 days in rounds 1–4, 42 days in rounds 5–8, known returns this season
from round 9. There is no injured-player count limit. The existing public profile,
NBA roster and injury checks remain mandatory before native API submission. It
requires the authoritative current turn, at least 25 seconds remaining, and
server acknowledgement. A rookie need not have a historical projection to be a
legal expert selection. Do not create manual injury risk reviews or override a
ban; configured automatic injury eligibility is recorded separately.

On disconnect or an uncertain command, reconnect and reconcile server state
before attempting another selection. An authenticated ESPN browser or phone can displace the API connection; use the local read-only viewer to observe rather than reconnecting the ESPN room. Never blindly resend, claim a failed write
did not execute, delete its journal, or run competing watcher processes. Existing
turn, clock, identity, availability and receipt gates remain mandatory. If a
fresh connection confirms the intended pick, retain its receipt and continue.
If the clock guard prevents a pick, report ESPN's actual resulting selection.

## Completion

Inspect `basketball/data/draft-result.json` and the authoritative completed roster.
Report the 12 players, positions, confirmed API picks versus ESPN autopicks, and
any availability/connection issues. No waiver adds, trades, league setting
changes or season-management mutations are authorized by this draft request.
The follow-up is one-time and should not draft again on later days.

The computer must remain on, awake, online, with the desktop app running. A
scheduled local follow-up cannot guarantee execution if those prerequisites or
ESPN access fail.
