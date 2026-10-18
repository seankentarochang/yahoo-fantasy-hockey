# Position balance and late-selection safety — October 18, 2026

The reported late-round Invalid Selection pattern is reproducible: **whole-roster
matching can pass while ESPN's only open draft slot cannot accept the player**.
The live selector now requires an actually open native slot. A definite server
refusal also has a durable, scoped recovery path instead of aborting the watcher.
The owner requested retaining positional scarcity for team balance; that preference
is enabled within a three-published-rank band and the existing ESPN timing tier.

## Reproduced cause

In a new 16-team, 12-round ESPN CUSTOM_MOCK, replay the first 11 selections from
the previously failing slot-1 roster. All 11 planned players remain available,
pass availability checks and receive native API confirmations. ESPN assigns:

| Player | Native draft slot |
| --- | --- |
| Nikola Jokic | C |
| Jaylen Brown | SF |
| Kawhi Leonard | PF |
| Walker Kessler | UTIL 1 |
| Donovan Clingan | UTIL 2 |
| Zach Edey | BE 1 |
| Ryan Rollins | SG |
| Yaxel Lendeborg | F |
| Ajay Mitchell | PG |
| Collin Murray-Boyles | BE 2 |
| P.J. Washington | BE 3 |

Only **G** remains open. Tari Eason is eligible for SF/PF/F and composite slots,
but not plain G. The global matching check still allows his completed roster:
it can move Jaylen Brown from SF to G and place Eason at SF. That rearrangement
has not happened in ESPN's authoritative draft state.

The new native-slot preflight correctly excludes Eason. For a disposable diagnostic
only, deliberately bypass that one slot check and send him at pick 192. ESPN
returns the exact `ERROR 1 Invalid+Selection.` response. The production refusal
path persists the evidence, drains through a new server barrier, clears only
the definitively refused intent and permits a fresh candidate. Brayden Burries
is then selected into G and confirmed **3.588 seconds after the refused intent**.
The room completes with 192 unique selections, all 12 team picks API-confirmed,
Autopick off, full nine-starter coverage and no unresolved journal.

This is direct evidence for one reproduced failure mechanism matching the earlier
candidate-by-roster pattern. The old run-3 logs lack native slot assignments, so
we cannot retrospectively prove that all nine earlier refusals had this exact
cause. No blanket ban on Eason, Washington, Murray-Boyles or forwards is added.
Primary-position center limits remain unchanged.

## Prevention and recovery

- Reconstruct native slot IDs/categories and current placements from INIT. Update
  them from SELECTED/SOLD and validated SLOT_CHANGED events. Slot IDs distinguish
  repeated UTIL/bench positions. Require an open compatible slot in both the
  recommendation list and the final command gate, alongside global coverage.
- Confirm Autopick disabled before automatic execution and track subsequent changes.
- Classify only the exact, URL-decoded code-1 Invalid Selection response associated
  with the single outstanding SELECT. Persist the refusal inside the existing
  intent before recovery; do not classify arbitrary errors as non-execution.
- Finish processing the response batch, refresh through a PING/PONG barrier and
  reconcile. A confirmed exact-pick receipt takes precedence and prevents a second
  selection, even if a refusal appears in the same batch.
- Store definite refusals separately from successful receipts. Exclude the candidate
  only for the same identity and exact pick-history/native-slot context. The
  watcher immediately recomputes its next verified candidate. Every new write
  retains source, availability, bans, roster, turn and >=25-second clock gates.
- If recovery crashes, reconnect and reconcile the durable refusal. A failed send,
  disconnect, timeout, unknown error or contradictory slot event still requires
  reconciliation; an uncertain intent is never silently discarded or resent.

An upstream outage or exhausted clock can still prevent execution. This change
prevents the reproduced incompatible-slot attempt and handles a definite refusal;
it does not promise that ESPN can never reject a command.

## Balance policy

Keep RotoWire plus the existing unbuffered ESPN-rank next-pick timing. From round 2,
consider availability-verified alternatives within three published expert ranks
of the best eligible player **in the same timing tier**. Weight configured non-UTIL
starter positions, including G/F flex slots, by estimated scarcity in the first
32 legal deferred candidates. Exact matching prevents one flexible player from
counting as two starters. Choose an alternative only when its coverage gain is
greater, resolving ties in expert order. First-round elite selection and the final
pick keep expert priority; unpublished tails do not gain invented expert tiers.

The owner chose balance despite the earlier experiment's inconsistent scoring
proxies. This implementation adds first-round protection and G/F coverage to that
research idea; it is a revised preference rule, not a newly validated scoring model.
Injury-price rules and Kuzma/Braun/Charlotte bans remain in force.

## Verification scope

- **69 focused backend tests pass**, including 15 new safety/balance regressions:
  a completed lineup that fits only after rearrangement, native slot identity/duplicates,
  current placements after moves, explicit refusal/fallback, full-frame receipt
  precedence, reconnect during recovery, idempotence, context-scoped exclusions,
  unknown errors, Autopick and the unchanged clock guard.
- Two actual ESPN CUSTOM_MOCK rooms complete, each with **12 API receipts**, no
  ESPN timeout picks, Autopick off and 192 unique selections. The first room has
  no refusals; its complete native log also replays through the current slot-state
  implementation across all 16 teams. The second is the scripted reproduction
  above with one deliberate rejected command and confirmed fallback. These are
  transport/roster tests, not strategy-performance comparisons.
- Native practice rooms use a roughly 25-second clock. Disposable probes use a
  five-second floor; the real production gate remains >=25 seconds on the league's
  60-second clock. The diagnostic slot bypass is confined to ignored probe code
  and must never be used for the real draft. Live probes exercised the SELECT/
  refusal path; final additional defensive validation is covered by focused tests.
- No real-league pick, waiver, trade or setting change was submitted. Real-room
  read-only access still returns HTTP 500 before opening; the scheduled preflight
  must establish its live connection when available.

Aggregate evidence: [native mock results](basketball_draft_safety_results.json).
Raw inputs, native frames, journals and disposable probe scripts remain ignored
under `basketball/data/draft-slot-investigation/`. The scheduled draft remains
October 18 at 11 a.m. Eastern, with preparation starting at 10:01 a.m.
