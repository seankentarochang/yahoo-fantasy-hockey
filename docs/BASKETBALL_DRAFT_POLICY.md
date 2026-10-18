# Current draft policy — October 18, 2026

The live expert watcher now combines an updated points board, demand before our
next turn, and injury return estimates at an appropriate draft price. This policy
replaces the previous pure best-available expert selection for the configured
league. It does not change the frozen historical experiments or their results.

## Ranking source

[RotoWire's October 16 standard-points cheat sheet](https://www.rotowire.com/basketball/article/2026-27-fantasy-basketball-cheat-sheet-for-points-leagues-printable-excel-141449)
contains 200 published ranks. The saved capture matches 195 uniquely to the ESPN
STANDARD-ranked pool. Five unmatched or unranked names are reported explicitly:
Sandro Mamukelashvili, Pelle Larsson, Dailyn Swain, Daniss Jenkins and Dylan
Cardwell. No fuzzy player matching is used. Walker Kessler is ranked 36th here.

`draft refresh-rankings` captures the public page, validates its title, article
dates, 200 distinct names and contiguous ranks, and selects an immutable capture
through `basketball/data/draft-sources.json`. Board and source bytes are hashed.
The older NBA.com article and historical ranking files remain intact. Current
captures must precede the actual configured draft start, including draft-morning
updates before 11 a.m. Missing/corrupt selected data stops this policy.

These are publisher standard-points ranks, not projections rescored to this
league's exact weights. Players outside the published board follow ESPN order
and have no invented RotoWire rank. Jimmy Butler III is outside this top 200;
he can still enter consideration through this explicitly labeled ESPN tail.

## Wait until our next turn when possible

There is no fixed 10-spot reach limit. The watcher reads our authoritative snake
slot and consecutive completed selections, finds our next pick, and counts the
opponent picks in between. It sorts the remaining ESPN STANDARD market pool,
including players that only we have banned or cannot fit. Opponents do not share
our preferences.

The demand window contains those opponent selections plus our current selection.
Within this window, choose the best legal expert-ranked player that passes the
current availability and injury-price checks. Defer higher expert targets outside
the window. If every legal player inside the window fails availability, use the
best eligible deferred player. Consecutive picks and our final pick use best
eligible expert order directly. This is a transparent ESPN-demand heuristic, not
a calibrated probability or the older experimental two-pick utility hybrid.

At the saved mock's pick 47, our next turn was 50: two opponent selections, so a
three-player demand window. Kessler was 23rd in the remaining ESPN market and is
now deferred. Replaying that state with the new board, current bans and current
availability recommends Michael Porter Jr. (ESPN 48, RotoWire 66), the highest
eligible expert choice inside that demand window. This demonstrates the timing
tradeoff explicitly; it is not evidence that this pair will outperform another.
The policy checks again on the next turn rather than guaranteeing Kessler survives.

## Position scarcity and team balance

The owner requested keeping scarcity after reviewing the forward mock comparisons.
`draft.balance` enables a three-published-rank tiebreaker from round 2 onward.
The first-round elite choice and final roster selection retain expert priority.
After finding the best availability-verified expert player, consider alternatives
within three published ranks in the **same timing tier**. Unpublished ESPN tails
do not create artificial expert tiers. No timing buffer or ADP policy is added.

Weight each configured non-UTIL starter slot, including G/F flex slots, by the
inverse of its supply among the first 32 currently legal deferred candidates.
Exact distinct-player matching measures how much a candidate improves coverage;
one flexible player cannot fill two positions. Prefer a verified alternative
only when that coverage gain exceeds the best expert player's gain, with expert
order resolving ties. Every candidate still meets bans, injury-price rules and
roster legality. This is a team-balance preference, not a demonstrated scoring
improvement or calibrated forecast of future supply. Protecting round 1 avoids
the research example's Flagg-over-Giannis tradeoff; the production rule also
includes G/F slots, so it is a revised rule rather than the exact tested heuristic.

The final API gate recomputes the selected expert/timing/availability/balance choice,
refreshes authoritative events, rechecks the turn and clock, and stores the
source, timing and candidate with the acknowledged selection receipt. Manual API
commands still represent explicit owner selections; the timing rule governs
automatic expert picks. ESPN's own autopicks cannot enforce this policy. Do not
build an autopick fallback queue as part of this scheduled draft.

## Native draft slots and explicit refusals

ESPN assigns players to specific draft-slot IDs. The API now reconstructs occupied
slots from authoritative INIT and SELECTED/SOLD events and applies SLOT_CHANGED
events. Candidates must fit an actually open slot as well as pass the existing
whole-roster matching check. The latter permits rearranging players and cannot
alone establish that ESPN will accept the selection. The API never invents or
sends roster moves to make a candidate fit. Autopick must be confirmed off.

Only the exact server response `ERROR 1 Invalid+Selection.` (equivalent URL
encoding accepted), attributed to the one outstanding SELECT after the initial
server barrier, is treated as a definite refusal. It is persisted in the write
journal before recovery. The client finishes the frame batch, requests a fresh
server barrier and reconciles. A confirmed exact-pick receipt always wins; it
must never trigger another selection.

A definite refusal moves to `draft-rejections.json` before the intent clears.
The watcher chooses the next verified candidate using fresh state, normal source,
balance, ban, availability, turn and >=25-second clock checks. Rejection exclusions
apply only to the same league/team/season and exact pick-history/slot context,
not to the player in every room or future turn. If recovery crashes, persisted
refusal evidence can be reconciled after reconnect. Unknown errors, failed sends,
disconnects and missing acknowledgements keep their uncertain intent and stop
automatic writes until authoritative reconciliation. No blind retries are added.

## Injuries at the right draft price

`draft injuries --refresh` builds `basketball/data/injury-returns.json` and a
readable `injury-returns.md` from the current public ESPN injury feed. Individual
availability checks refresh this catalog as well. The October 17 capture has 94
distinct injured players. Each entry retains the provider's return estimate,
status, report time, source and commentary. Commentary may give a broader window
than the structured date: neither is a guaranteed medical clearance.

No injured-player count limit applies. The configured draft-price schedule is:

| Our draft round | Injury eligibility |
|---|---|
| 1–4 | Known estimated return within 14 days |
| 5–8 | Known estimated return within 42 days |
| 9–12 | Known estimated return before the regular season ends, April 11, 2027 |

These configurable thresholds implement the requested preference for healthy
early picks and late recovery bets; they have not been optimized by backtesting.
Conflicting return dates use the latest estimate. Unknown, malformed or overdue
estimates require review. Inactive/retired players, out-for-season designations,
suspensions, unresolved team conflicts and bans are never automatically cleared
by this policy. Actual writes still force fresh public profile, roster and injury
reads and must retain at least 25 seconds on the live clock.

Live checks verified that Chet Holmgren's October 20 estimate makes his temporary
injury eligible early. Jimmy Butler III's structured January 2 estimate and
January–February commentary keep him out of the early rounds but make him an
eligible late target from round 9, subject to his expert/ESPN order, availability
at our turn and roster fit. No explicit risk-review approval is generated.

[NBA regular-season end date](https://www.nba.com/news/2026-27-nba-regular-season-schedule).

## Validation

The earlier 79 targeted backend tests covered source parsing/capture integrity, draft-morning
cutoffs, current-source selection, timing windows and stale slots, final and
consecutive picks, Kessler deferral, injury price tiers, source/identity failures,
bans, fresh clocks, exact API acknowledgements and durable receipts. Additional
read-only checks used the current public sources and the saved mock state.

The October 18 balance/refusal change passes 69 focused backend tests, including
15 new regressions for native slot constraints, safe refusal recovery, crash
reconciliation, actual receipt precedence, unknown-error retention, Autopick
confirmation and bounded balance choices. A complete 192-selection native API
log also replays with exact slot occupancy across all 16 teams. See
[the slot investigation and mock verification](BASKETBALL_DRAFT_SAFETY.md).
No real-league selection was submitted during this work.
