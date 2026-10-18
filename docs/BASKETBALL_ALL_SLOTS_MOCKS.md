# ESPN API mocks from all 16 positions — October 18, 2026

**16/16 rooms passed all checks; 192/192 own selections have exact-pick API receipts.** There were 0 explicit selection refusals and 10 positional-scarcity changes.

Use the current RotoWire board with ESPN-rank next-pick timing, configured position balance, injury-price rules and Kuzma/Braun/Charlotte bans. These were actual ESPN CUSTOM_MOCK rooms with native API selections, observed in a visible local browser viewer. No player choices were scripted and no slot check was bypassed.

| Draft position | API receipts | Refusals | Balance changes | Checks | Opening three picks |
| --- | ---: | ---: | ---: | --- | --- |
| 1 | 12/12 | 0 | 0 | Pass | Nikola Jokic; Paolo Banchero; Bam Adebayo |
| 2 | 12/12 | 0 | 0 | Pass | Nikola Jokic; Bam Adebayo; Paolo Banchero |
| 3 | 12/12 | 0 | 1 | Pass | Victor Wembanyama; Austin Reaves; Paolo Banchero |
| 4 | 12/12 | 0 | 1 | Pass | Victor Wembanyama; Bam Adebayo; Paolo Banchero |
| 5 | 12/12 | 0 | 1 | Pass | Giannis Antetokounmpo; Bam Adebayo; Paolo Banchero |
| 6 | 12/12 | 0 | 0 | Pass | Cade Cunningham; Bam Adebayo; Paolo Banchero |
| 7 | 12/12 | 0 | 1 | Pass | Cade Cunningham; Karl-Anthony Towns; Paolo Banchero |
| 8 | 12/12 | 0 | 0 | Pass | Giannis Antetokounmpo; Karl-Anthony Towns; Paolo Banchero |
| 9 | 12/12 | 0 | 1 | Pass | Cooper Flagg; Alperen Sengun; Paolo Banchero |
| 10 | 12/12 | 0 | 0 | Pass | Cooper Flagg; Alperen Sengun; Paolo Banchero |
| 11 | 12/12 | 0 | 0 | Pass | Cooper Flagg; Alperen Sengun; Paolo Banchero |
| 12 | 12/12 | 0 | 0 | Pass | Jayson Tatum; Alperen Sengun; Paolo Banchero |
| 13 | 12/12 | 0 | 1 | Pass | Cooper Flagg; Alperen Sengun; Paolo Banchero |
| 14 | 12/12 | 0 | 1 | Pass | Scottie Barnes; Alperen Sengun; Paolo Banchero |
| 15 | 12/12 | 0 | 1 | Pass | Scottie Barnes; Alperen Sengun; Paolo Banchero |
| 16 | 12/12 | 0 | 2 | Pass | Alperen Sengun; Paolo Banchero; Matas Buzelis |

## Native slot checks

Offline replay reconstructed 192 own decision states. The first player on a counterfactual global-matching board was incompatible with an actually open native slot in 0 states (0 in rounds 11–12). These counterfactual candidates were not rechecked for public availability; this measures slot filtering, not how many server rejections were certainly prevented.

This series did not naturally reproduce the earlier Invalid Selection failure. The [separate controlled reproduction](BASKETBALL_DRAFT_SAFETY.md) established that slot mismatch and its recovery. Zero refusals here support operational readiness, but do not isolate the effect of native-slot checking from the current board, timing and balance rules.

Every passing roster has twelve players, nine distinct starter slots coverable, legal primary-position caps, no personal bans, all native draft slots filled, Autopick off and no pending command. All successful receipts retain the reverified expert-selection evidence.

## Clock, connections and interpretation

The production SELECT/reconciliation implementation was held fixed at commit 77a1441. Source hashes are recorded in the evidence. Four isolated rooms ran concurrently; each had its own credentials copy, source, caches, journal and receipts. A visible read-only viewer consumed append-only local events and never contacted ESPN.

Native mock clocks are roughly 25 seconds. A disposable subclass uses a five-second practice floor while calling the original final safety gate. The real league retains its >=25-second floor on a 60-second clock. This is a native transport/selection-policy rehearsal with an explicit timing exception, not an exact real-clock rehearsal. No real-league selections or setting changes were submitted.

There were 13 HTTP 500 connection retries while opening new rooms, before any selections in those connections. There were no in-draft disconnects. Each retry is listed with slot and reason in the JSON. Retries reconcile authoritative state before another command; no uncertain write is cleared by hand.

Recorded time from submitted intent to confirmed receipt: median 0.241 seconds, maximum 0.856 seconds. This excludes availability research before submission and is not a real-draft latency guarantee.

One room per position cannot establish a strongest draft position, calibrated survival probability or future winning strategy. Any player projections in the evidence are forecasts, not observed season output. The real draft strategy and scheduled preparation time are unchanged.

## Complete rosters

### Position 1

| Overall pick | Player | Native slot | Published RotoWire rank |
| ---: | --- | --- | ---: |
| 1 | Nikola Jokic | C | 1 |
| 32 | Paolo Banchero | PF | 14 |
| 33 | Bam Adebayo | F | 17 |
| 64 | Matas Buzelis | SF | 30 |
| 65 | Donovan Clingan | UTIL | 31 |
| 96 | Ryan Rollins | SG | 65 |
| 97 | Cedric Coward | G | 77 |
| 128 | Day'Ron Sharpe | UTIL | 95 |
| 129 | Davion Mitchell | PG | 102 |
| 160 | Rui Hachimura | BE | 108 |
| 161 | Yaxel Lendeborg | BE | 116 |
| 192 | Ajay Mitchell | BE | 119 |

### Position 2

| Overall pick | Player | Native slot | Published RotoWire rank |
| ---: | --- | --- | ---: |
| 2 | Nikola Jokic | C | 1 |
| 31 | Bam Adebayo | PF | 17 |
| 34 | Paolo Banchero | SF | 14 |
| 63 | Trey Murphy III | SG | 59 |
| 66 | Matas Buzelis | F | 30 |
| 95 | Ryan Rollins | PG | 65 |
| 98 | Cedric Coward | G | 77 |
| 127 | Isaiah Hartenstein | UTIL | 105 |
| 130 | Day'Ron Sharpe | UTIL | 95 |
| 159 | P.J. Washington | BE | 141 |
| 162 | Rui Hachimura | BE | 108 |
| 191 | Ajay Mitchell | BE | 119 |

### Position 3

| Overall pick | Player | Native slot | Published RotoWire rank |
| ---: | --- | --- | ---: |
| 3 | Victor Wembanyama | C | 2 |
| 30 | Austin Reaves | SG | 25 |
| 35 | Paolo Banchero | PF | 14 |
| 62 | Onyeka Okongwu | UTIL | 55 |
| 67 | Matas Buzelis | SF | 30 |
| 94 | Ryan Rollins | PG | 65 |
| 99 | Cedric Coward | F | 77 |
| 126 | Zach LaVine | G | 106 |
| 131 | Day'Ron Sharpe | UTIL | 95 |
| 158 | Mikel Brown Jr. | BE | 126 |
| 163 | Rui Hachimura | BE | 108 |
| 190 | Khaman Maluach | BE | 113 |

### Position 4

| Overall pick | Player | Native slot | Published RotoWire rank |
| ---: | --- | --- | ---: |
| 4 | Victor Wembanyama | C | 2 |
| 29 | Bam Adebayo | PF | 17 |
| 36 | Paolo Banchero | SF | 14 |
| 61 | Cameron Boozer | F | 44 |
| 68 | Matas Buzelis | UTIL | 30 |
| 93 | Payton Pritchard | PG | 56 |
| 100 | Cedric Coward | SG | 77 |
| 125 | Zach LaVine | G | 106 |
| 132 | Day'Ron Sharpe | UTIL | 95 |
| 157 | Mikel Brown Jr. | BE | 126 |
| 164 | Rui Hachimura | BE | 108 |
| 189 | Khaman Maluach | BE | 113 |

### Position 5

| Overall pick | Player | Native slot | Published RotoWire rank |
| ---: | --- | --- | ---: |
| 5 | Giannis Antetokounmpo | PF | 4 |
| 28 | Bam Adebayo | C | 17 |
| 37 | Paolo Banchero | SF | 14 |
| 60 | Donovan Clingan | UTIL | 31 |
| 69 | Matas Buzelis | F | 30 |
| 92 | Ryan Rollins | SG | 65 |
| 101 | Cedric Coward | G | 77 |
| 124 | Zach LaVine | UTIL | 106 |
| 133 | Day'Ron Sharpe | BE | 95 |
| 156 | Mikel Brown Jr. | PG | 126 |
| 165 | Yaxel Lendeborg | BE | 116 |
| 188 | Khaman Maluach | BE | 113 |

### Position 6

| Overall pick | Player | Native slot | Published RotoWire rank |
| ---: | --- | --- | ---: |
| 6 | Cade Cunningham | PG | 6 |
| 27 | Bam Adebayo | C | 17 |
| 38 | Paolo Banchero | PF | 14 |
| 59 | Donovan Clingan | UTIL | 31 |
| 70 | Matas Buzelis | SF | 30 |
| 91 | Payton Pritchard | SG | 56 |
| 102 | Cedric Coward | F | 77 |
| 123 | Isaiah Hartenstein | UTIL | 105 |
| 134 | Day'Ron Sharpe | BE | 95 |
| 155 | Jonathan Kuminga | BE | 125 |
| 166 | Rui Hachimura | BE | 108 |
| 187 | Ajay Mitchell | G | 119 |

### Position 7

| Overall pick | Player | Native slot | Published RotoWire rank |
| ---: | --- | --- | ---: |
| 7 | Cade Cunningham | PG | 6 |
| 26 | Karl-Anthony Towns | C | 13 |
| 39 | Paolo Banchero | PF | 14 |
| 58 | Donovan Clingan | UTIL | 31 |
| 71 | Matas Buzelis | SF | 30 |
| 90 | Ryan Rollins | SG | 65 |
| 103 | Cedric Coward | F | 77 |
| 122 | Zach LaVine | G | 106 |
| 135 | Day'Ron Sharpe | UTIL | 95 |
| 154 | Rui Hachimura | BE | 108 |
| 167 | Yaxel Lendeborg | BE | 116 |
| 186 | Khaman Maluach | BE | 113 |

### Position 8

| Overall pick | Player | Native slot | Published RotoWire rank |
| ---: | --- | --- | ---: |
| 8 | Giannis Antetokounmpo | PF | 4 |
| 25 | Karl-Anthony Towns | C | 13 |
| 40 | Paolo Banchero | SF | 14 |
| 57 | Donovan Clingan | UTIL | 31 |
| 72 | Matas Buzelis | F | 30 |
| 89 | Payton Pritchard | PG | 56 |
| 104 | Cedric Coward | SG | 77 |
| 121 | Jabari Smith Jr. | UTIL | 97 |
| 136 | Day'Ron Sharpe | BE | 95 |
| 153 | Rui Hachimura | BE | 108 |
| 168 | Yaxel Lendeborg | BE | 116 |
| 185 | Ajay Mitchell | G | 119 |

### Position 9

| Overall pick | Player | Native slot | Published RotoWire rank |
| ---: | --- | --- | ---: |
| 9 | Cooper Flagg | SF | 7 |
| 24 | Alperen Sengun | C | 9 |
| 41 | Paolo Banchero | PF | 14 |
| 56 | Stephon Castle | PG | 32 |
| 73 | Matas Buzelis | F | 30 |
| 88 | Payton Pritchard | SG | 56 |
| 105 | Darryn Peterson | G | 86 |
| 120 | Zach Edey | UTIL | 87 |
| 137 | Day'Ron Sharpe | UTIL | 95 |
| 152 | Rui Hachimura | BE | 108 |
| 169 | Yaxel Lendeborg | BE | 116 |
| 184 | Khaman Maluach | BE | 113 |

### Position 10

| Overall pick | Player | Native slot | Published RotoWire rank |
| ---: | --- | --- | ---: |
| 10 | Cooper Flagg | SF | 7 |
| 23 | Alperen Sengun | C | 9 |
| 42 | Paolo Banchero | PF | 14 |
| 55 | Donovan Clingan | UTIL | 31 |
| 74 | Matas Buzelis | F | 30 |
| 87 | Payton Pritchard | PG | 56 |
| 106 | Zach Edey | UTIL | 87 |
| 119 | Cedric Coward | SG | 77 |
| 138 | Davion Mitchell | G | 102 |
| 151 | Rui Hachimura | BE | 108 |
| 170 | Yaxel Lendeborg | BE | 116 |
| 183 | Khaman Maluach | BE | 113 |

### Position 11

| Overall pick | Player | Native slot | Published RotoWire rank |
| ---: | --- | --- | ---: |
| 11 | Cooper Flagg | SF | 7 |
| 22 | Alperen Sengun | C | 9 |
| 43 | Paolo Banchero | PF | 14 |
| 54 | Donovan Clingan | UTIL | 31 |
| 75 | Matas Buzelis | F | 30 |
| 86 | Payton Pritchard | PG | 56 |
| 107 | Darryn Peterson | SG | 86 |
| 118 | Cedric Coward | G | 77 |
| 139 | Day'Ron Sharpe | UTIL | 95 |
| 150 | Davion Mitchell | BE | 102 |
| 171 | Yaxel Lendeborg | BE | 116 |
| 182 | Khaman Maluach | BE | 113 |

### Position 12

| Overall pick | Player | Native slot | Published RotoWire rank |
| ---: | --- | --- | ---: |
| 12 | Jayson Tatum | PF | 11 |
| 21 | Alperen Sengun | C | 9 |
| 44 | Paolo Banchero | SF | 14 |
| 53 | Donovan Clingan | UTIL | 31 |
| 76 | Matas Buzelis | F | 30 |
| 85 | Payton Pritchard | PG | 56 |
| 108 | Nic Claxton | UTIL | 88 |
| 117 | Cedric Coward | SG | 77 |
| 140 | Day'Ron Sharpe | BE | 95 |
| 149 | Davion Mitchell | G | 102 |
| 172 | Yaxel Lendeborg | BE | 116 |
| 181 | Ajay Mitchell | BE | 119 |

### Position 13

| Overall pick | Player | Native slot | Published RotoWire rank |
| ---: | --- | --- | ---: |
| 13 | Cooper Flagg | SF | 7 |
| 20 | Alperen Sengun | C | 9 |
| 45 | Paolo Banchero | PF | 14 |
| 52 | Stephon Castle | PG | 32 |
| 77 | Matas Buzelis | F | 30 |
| 84 | Payton Pritchard | SG | 56 |
| 109 | Nic Claxton | UTIL | 88 |
| 116 | Cedric Coward | G | 77 |
| 141 | Day'Ron Sharpe | UTIL | 95 |
| 148 | Davion Mitchell | BE | 102 |
| 173 | Wendell Carter Jr. | BE | 144 |
| 180 | Ajay Mitchell | BE | 119 |

### Position 14

| Overall pick | Player | Native slot | Published RotoWire rank |
| ---: | --- | --- | ---: |
| 14 | Scottie Barnes | SF | 16 |
| 19 | Alperen Sengun | C | 9 |
| 46 | Paolo Banchero | PF | 14 |
| 51 | Stephon Castle | PG | 32 |
| 78 | Matas Buzelis | F | 30 |
| 83 | Payton Pritchard | SG | 56 |
| 110 | Nic Claxton | UTIL | 88 |
| 115 | Cedric Coward | G | 77 |
| 142 | Saddiq Bey | UTIL | 115 |
| 147 | Davion Mitchell | BE | 102 |
| 174 | Yaxel Lendeborg | BE | 116 |
| 179 | Khaman Maluach | BE | 113 |

### Position 15

| Overall pick | Player | Native slot | Published RotoWire rank |
| ---: | --- | --- | ---: |
| 15 | Scottie Barnes | SF | 16 |
| 18 | Alperen Sengun | C | 9 |
| 47 | Paolo Banchero | PF | 14 |
| 50 | Stephon Castle | PG | 32 |
| 79 | Matas Buzelis | F | 30 |
| 82 | Payton Pritchard | SG | 56 |
| 111 | Darryn Peterson | G | 86 |
| 114 | Cedric Coward | UTIL | 77 |
| 143 | Saddiq Bey | UTIL | 115 |
| 146 | Davion Mitchell | BE | 102 |
| 175 | Wendell Carter Jr. | BE | 144 |
| 178 | Khaman Maluach | BE | 113 |

### Position 16

| Overall pick | Player | Native slot | Published RotoWire rank |
| ---: | --- | --- | ---: |
| 16 | Alperen Sengun | C | 9 |
| 17 | Paolo Banchero | PF | 14 |
| 48 | Matas Buzelis | SF | 30 |
| 49 | Stephon Castle | PG | 32 |
| 80 | Payton Pritchard | SG | 56 |
| 81 | Derik Queen | F | 58 |
| 112 | Cedric Coward | G | 77 |
| 113 | Zach Edey | UTIL | 87 |
| 144 | Rui Hachimura | UTIL | 108 |
| 145 | Saddiq Bey | BE | 115 |
| 176 | Khaman Maluach | BE | 113 |
| 177 | Ajay Mitchell | BE | 119 |

[Aggregate evidence, slot analysis and all verification checks](basketball_all_slots_mock_results.json).

Raw native INIT/player captures, frame streams, selection receipts, availability evidence and disposable runners remain ignored under `basketball/data/all-slots-20261018/`. No credentials or authenticated URLs are published.
