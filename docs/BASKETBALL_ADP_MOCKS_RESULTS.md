# ADP draft rehearsals across every draft position

Completed 1,200 forward simulations: all 16 slots, 25 seeds per slot, three opponent fields. This corrects the earlier assumption that slot 15 was decided. The real slot remains unknown. Our choices use the equal-publisher ESPN/RotoWire/NBC/Fantrax points consensus with ADP next-turn timing, positional coverage, injury price windows and personal bans.

## What the draft can look like

The table shows the first four selections from one actual representative typical-field draft at each position. These are examples, not a fixed script or a composite of independently common picks. Parentheses show overall pick numbers. Each representative maximizes the sum of round-choice frequencies within that position/field, breaking ties by lowest seed.

| Slot | First round | Second round | Third round | Fourth round |
|---|---|---|---|---|
| 1 | Nikola Jokic (1) | Bam Adebayo (32) | Evan Mobley (33) | Walker Kessler (64) |
| 2 | Victor Wembanyama (2) | Josh Giddey (31) | Evan Mobley (34) | Trey Murphy III (63) |
| 3 | Victor Wembanyama (3) | Jalen Duren (30) | Paolo Banchero (35) | Trey Murphy III (62) |
| 4 | Luka Doncic (4) | Bam Adebayo (29) | Evan Mobley (36) | Franz Wagner (61) |
| 5 | Giannis Antetokounmpo (5) | Bam Adebayo (28) | Evan Mobley (37) | Walker Kessler (60) |
| 6 | Giannis Antetokounmpo (6) | Bam Adebayo (27) | Evan Mobley (38) | Walker Kessler (59) |
| 7 | Cade Cunningham (7) | Josh Giddey (26) | Paolo Banchero (39) | Chet Holmgren (58) |
| 8 | Cade Cunningham (8) | Alperen Sengun (25) | Paolo Banchero (40) | Chet Holmgren (57) |
| 9 | Jayson Tatum (9) | Alperen Sengun (24) | Paolo Banchero (41) | Chet Holmgren (56) |
| 10 | Cooper Flagg (10) | Karl-Anthony Towns (23) | Paolo Banchero (42) | Chet Holmgren (55) |
| 11 | Jayson Tatum (11) | Alperen Sengun (22) | Paolo Banchero (43) | Chet Holmgren (54) |
| 12 | Jayson Tatum (12) | Alperen Sengun (21) | Lauri Markkanen (44) | Chet Holmgren (53) |
| 13 | Cooper Flagg (13) | Alperen Sengun (20) | Lauri Markkanen (45) | Chet Holmgren (52) |
| 14 | Tyrese Maxey (14) | Alperen Sengun (19) | Lauri Markkanen (46) | Chet Holmgren (51) |
| 15 | Scottie Barnes (15) | Alperen Sengun (18) | Mikal Bridges (47) | Lauri Markkanen (50) |
| 16 | Scottie Barnes (16) | Alperen Sengun (17) | Lauri Markkanen (48) | Chet Holmgren (49) |

Early positions trade access to the highest-ranked players for a long wait to the second turn. Late positions often pair Barnes or Maxey with Sengun, then wait until picks in the high 40s. Middle positions have shorter gaps and different opportunities to defer players. These patterns depend on the assumed opponents.

## Three complete example drafts

All three are actual typical-field trajectories, with legal 12-player rosters, all nine starting slots covered and no personal bans selected.

| Round | Slot 1 example | Slot 8 example | Slot 16 example |
|---|---|---|---|
| 1 | Nikola Jokic (1) | Cade Cunningham (8) | Scottie Barnes (16) |
| 2 | Bam Adebayo (32) | Alperen Sengun (25) | Alperen Sengun (17) |
| 3 | Evan Mobley (33) | Paolo Banchero (40) | Lauri Markkanen (48) |
| 4 | Walker Kessler (64) | Chet Holmgren (57) | Chet Holmgren (49) |
| 5 | Trey Murphy III (65) | Ivica Zubac (72) | Jaren Jackson Jr. (80) |
| 6 | Immanuel Quickley (96) | Immanuel Quickley (89) | Matas Buzelis (81) |
| 7 | Ryan Rollins (97) | Zach Edey (104) | Day'Ron Sharpe (112) |
| 8 | Day'Ron Sharpe (128) | Keegan Murray (121) | Cedric Coward (113) |
| 9 | Cedric Coward (129) | Jalen Suggs (136) | Jalen Suggs (144) |
| 10 | P.J. Washington (160) | Jonathan Kuminga (153) | Jonathan Kuminga (145) |
| 11 | Collin Murray-Boyles (161) | Collin Murray-Boyles (168) | Collin Murray-Boyles (176) |
| 12 | Ajay Mitchell (192) | Ajay Mitchell (185) | Ajay Mitchell (177) |

## Opponents and evidence

- ADP-led: numerical ESPN ADP in the usable range, with an explicit ESPN-rank tail. One deterministic draft per slot repeated across 25 seeds.
- Typical: independently 80% ADP-led and 20% ESPN-rank followers, with preference noise capped in scale at eight picks.
- Loose: 60% ADP-led and 40% rank followers, with preference noise capped in scale at sixteen picks.
- Noise scale is min(field scale, 25% of the player demand score), limiting extreme first-round slides. These assumptions were not calibrated to observed human picks.
- The final grid contains 800 noisy trajectories and 16 distinct deterministic controls, with controls repeated 25 times. Those are not 1,200 independent trials. Opponent preferences are paired between slots.

ESPN public fantasy player feed captured 2026-10-17T19:08:31.145646-04:00; complete pagination returned 3,228 unique players. Same-day verified research roster/injury evidence: 2026-10-17T17:36:18.856809-04:00. The final ranked, active, roster-verified pool has 352 players; 14 are banned for our team only. All 1,200 simulated full drafts passed unique-pick, roster-limit and positional-coverage checks.

## ADP limitation discovered during the rehearsal

Raw ESPN ADP ranged from 1.42 to 141.20 across the 352 eligible players. Of those, 231 had ADP at least 130 and 165 at least 140. That saturation makes hundredth-pick tail differences unsuitable as precise long-draft demand estimates. The public [Hashtag ESPN ADP table](https://hashtagbasketball.com/fantasy-basketball-adp) also displays this compressed tail.

The first 300 raw-ADP runs are retained locally as diagnostics. The amended model uses ADP below 130 and ESPN STANDARD rank thereafter; every fallback player is identified in JSON. The threshold is a disclosed heuristic. Do not interpret late-round selection frequencies as precise player survival probabilities. The amended 300-run slot-15 batch is also retained separately; it predates the user correction to test every position.

## Per-position shortlists

Counts below are selections out of 25 typical-field runs at that position. They reflect both availability and our draft choices. The full local report also records undrafted, policy-eligible availability on each actual path; a player in that pool may still fail roster fit. These are conditional simulation frequencies, not measured real-world probabilities.

### Slot 1

| Round / pick | Most selected | Other frequent selections |
|---|---|---|
| 1 / 1 | Nikola Jokic (25/25) | — |
| 2 / 32 | Bam Adebayo (8/25) | Jamal Murray (6/25); Evan Mobley (5/25) |
| 3 / 33 | Evan Mobley (10/25) | Paolo Banchero (7/25); Jamal Murray (4/25) |
| 4 / 64 | Walker Kessler (21/25) | Chet Holmgren (3/25); Franz Wagner (1/25) |
| 5 / 65 | Trey Murphy III (11/25) | Dejounte Murray (4/25); Franz Wagner (4/25) |
| 6 / 96 | Immanuel Quickley (12/25) | Ryan Rollins (9/25); Zach Edey (3/25) |
| 7 / 97 | Zach Edey (11/25) | Ryan Rollins (9/25); Josh Hart (2/25) |
| 8 / 128 | Day'Ron Sharpe (12/25) | Jalen Suggs (5/25); Cedric Coward (3/25) |
| 9 / 129 | Jalen Suggs (8/25) | Cedric Coward (7/25); Anthony Black (4/25) |
| 10 / 160 | P.J. Washington (10/25) | Jonathan Kuminga (9/25); Collin Murray-Boyles (4/25) |
| 11 / 161 | Collin Murray-Boyles (15/25) | P.J. Washington (5/25); Tre Jones (2/25) |
| 12 / 192 | Ajay Mitchell (23/25) | Jimmy Butler III (2/25) |

### Slot 2

| Round / pick | Most selected | Other frequent selections |
|---|---|---|
| 1 / 2 | Victor Wembanyama (21/25) | Nikola Jokic (4/25) |
| 2 / 31 | Bam Adebayo (9/25) | Josh Giddey (5/25); James Harden (3/25) |
| 3 / 34 | Evan Mobley (9/25) | Jamal Murray (6/25); Paolo Banchero (5/25) |
| 4 / 63 | Trey Murphy III (8/25) | Joel Embiid (6/25); Chet Holmgren (5/25) |
| 5 / 66 | Walker Kessler (16/25) | Trey Murphy III (3/25); Franz Wagner (3/25) |
| 6 / 95 | Jaden McDaniels (8/25) | Josh Hart (5/25); Ausar Thompson (4/25) |
| 7 / 98 | Ryan Rollins (10/25) | Immanuel Quickley (8/25); Zach Edey (6/25) |
| 8 / 127 | Yaxel Lendeborg (8/25) | Zach LaVine (3/25); Jaime Jaquez Jr. (3/25) |
| 9 / 130 | Day'Ron Sharpe (13/25) | Jalen Suggs (6/25); Cedric Coward (4/25) |
| 10 / 159 | Jonathan Kuminga (8/25) | Cameron Johnson (4/25); P.J. Washington (3/25) |
| 11 / 162 | Collin Murray-Boyles (13/25) | P.J. Washington (11/25); Jonathan Kuminga (1/25) |
| 12 / 191 | Ajay Mitchell (25/25) | — |

### Slot 3

| Round / pick | Most selected | Other frequent selections |
|---|---|---|
| 1 / 3 | Victor Wembanyama (18/25) | Shai Gilgeous-Alexander (7/25) |
| 2 / 30 | Bam Adebayo (11/25) | Josh Giddey (5/25); Jamal Murray (4/25) |
| 3 / 35 | Evan Mobley (11/25) | Paolo Banchero (9/25); Jalen Duren (3/25) |
| 4 / 62 | Trey Murphy III (10/25) | Chet Holmgren (6/25); Franz Wagner (4/25) |
| 5 / 67 | Walker Kessler (16/25) | Donovan Clingan (6/25); Franz Wagner (1/25) |
| 6 / 94 | Immanuel Quickley (6/25) | Jaden McDaniels (5/25); Ausar Thompson (4/25) |
| 7 / 99 | Ryan Rollins (10/25) | Zach Edey (8/25); Immanuel Quickley (4/25) |
| 8 / 126 | Zach LaVine (5/25) | Myles Turner (4/25); Cedric Coward (4/25) |
| 9 / 131 | Day'Ron Sharpe (12/25) | Jalen Suggs (8/25); Cedric Coward (3/25) |
| 10 / 158 | Jonathan Kuminga (11/25) | P.J. Washington (8/25); Jalen Suggs (3/25) |
| 11 / 163 | Collin Murray-Boyles (15/25) | P.J. Washington (8/25); Toumani Camara (1/25) |
| 12 / 190 | Ajay Mitchell (25/25) | — |

### Slot 4

| Round / pick | Most selected | Other frequent selections |
|---|---|---|
| 1 / 4 | Luka Doncic (13/25) | Shai Gilgeous-Alexander (7/25); Victor Wembanyama (5/25) |
| 2 / 29 | Bam Adebayo (10/25) | Josh Giddey (6/25); Jamal Murray (4/25) |
| 3 / 36 | Evan Mobley (11/25) | Paolo Banchero (9/25); Kawhi Leonard (1/25) |
| 4 / 61 | Trey Murphy III (9/25) | Chet Holmgren (8/25); Franz Wagner (6/25) |
| 5 / 68 | Walker Kessler (14/25) | Donovan Clingan (7/25); Trey Murphy III (2/25) |
| 6 / 93 | Immanuel Quickley (18/25) | Jaden McDaniels (3/25); Derik Queen (2/25) |
| 7 / 100 | Zach Edey (12/25) | Ryan Rollins (10/25); Ausar Thompson (1/25) |
| 8 / 125 | Isaiah Hartenstein (7/25) | Nic Claxton (5/25); Cedric Coward (5/25) |
| 9 / 132 | Day'Ron Sharpe (13/25) | Jalen Suggs (8/25); Cedric Coward (3/25) |
| 10 / 157 | Jonathan Kuminga (10/25) | P.J. Washington (8/25); Jalen Suggs (4/25) |
| 11 / 164 | Collin Murray-Boyles (19/25) | P.J. Washington (6/25) |
| 12 / 189 | Ajay Mitchell (22/25) | Collin Murray-Boyles (2/25); Jimmy Butler III (1/25) |

### Slot 5

| Round / pick | Most selected | Other frequent selections |
|---|---|---|
| 1 / 5 | Giannis Antetokounmpo (19/25) | Luka Doncic (6/25) |
| 2 / 28 | Bam Adebayo (10/25) | Josh Giddey (6/25); Alperen Sengun (4/25) |
| 3 / 37 | Evan Mobley (9/25) | Paolo Banchero (8/25); Jamal Murray (3/25) |
| 4 / 60 | Walker Kessler (14/25) | Chet Holmgren (9/25); Trey Murphy III (1/25) |
| 5 / 69 | Donovan Clingan (13/25) | Walker Kessler (5/25); Dejounte Murray (2/25) |
| 6 / 92 | Immanuel Quickley (22/25) | Ryan Rollins (3/25) |
| 7 / 101 | Zach Edey (11/25) | Ryan Rollins (10/25); Brandon Ingram (2/25) |
| 8 / 124 | Nic Claxton (7/25) | Cedric Coward (5/25); Keegan Murray (5/25) |
| 9 / 133 | Jalen Suggs (12/25) | Day'Ron Sharpe (11/25); Cedric Coward (1/25) |
| 10 / 156 | Jonathan Kuminga (12/25) | P.J. Washington (8/25); Jalen Suggs (3/25) |
| 11 / 165 | Collin Murray-Boyles (21/25) | P.J. Washington (4/25) |
| 12 / 188 | Ajay Mitchell (20/25) | Collin Murray-Boyles (3/25); Jimmy Butler III (2/25) |

### Slot 6

| Round / pick | Most selected | Other frequent selections |
|---|---|---|
| 1 / 6 | Giannis Antetokounmpo (17/25) | Cade Cunningham (5/25); Luka Doncic (3/25) |
| 2 / 27 | Bam Adebayo (8/25) | Josh Giddey (6/25); Alperen Sengun (4/25) |
| 3 / 38 | Paolo Banchero (13/25) | Evan Mobley (7/25); Jaylen Brown (2/25) |
| 4 / 59 | Walker Kessler (14/25) | Chet Holmgren (11/25) |
| 5 / 70 | Donovan Clingan (16/25) | Ivica Zubac (4/25); Walker Kessler (3/25) |
| 6 / 91 | Immanuel Quickley (22/25) | Ryan Rollins (3/25) |
| 7 / 102 | Zach Edey (12/25) | Ryan Rollins (10/25); Brandon Ingram (3/25) |
| 8 / 123 | Keegan Murray (8/25) | Nic Claxton (6/25); Cedric Coward (4/25) |
| 9 / 134 | Jalen Suggs (13/25) | Day'Ron Sharpe (10/25); Isaiah Hartenstein (2/25) |
| 10 / 155 | Jonathan Kuminga (10/25) | P.J. Washington (6/25); Jalen Suggs (5/25) |
| 11 / 166 | Collin Murray-Boyles (23/25) | P.J. Washington (2/25) |
| 12 / 187 | Ajay Mitchell (21/25) | Collin Murray-Boyles (2/25); Jimmy Butler III (2/25) |

### Slot 7

| Round / pick | Most selected | Other frequent selections |
|---|---|---|
| 1 / 7 | Cade Cunningham (13/25) | Giannis Antetokounmpo (8/25); Anthony Edwards (3/25) |
| 2 / 26 | Josh Giddey (8/25) | Bam Adebayo (7/25); Alperen Sengun (4/25) |
| 3 / 39 | Paolo Banchero (12/25) | Evan Mobley (6/25); Jaylen Brown (2/25) |
| 4 / 58 | Chet Holmgren (16/25) | Walker Kessler (8/25); Lauri Markkanen (1/25) |
| 5 / 71 | Donovan Clingan (13/25) | Ivica Zubac (7/25); Walker Kessler (4/25) |
| 6 / 90 | Immanuel Quickley (24/25) | Ryan Rollins (1/25) |
| 7 / 103 | Zach Edey (13/25) | Ryan Rollins (9/25); Brandon Ingram (3/25) |
| 8 / 122 | Keegan Murray (9/25) | Nic Claxton (4/25); Cedric Coward (3/25) |
| 9 / 135 | Jalen Suggs (12/25) | Day'Ron Sharpe (11/25); Myles Turner (1/25) |
| 10 / 154 | Jonathan Kuminga (12/25) | Jalen Suggs (5/25); P.J. Washington (4/25) |
| 11 / 167 | Collin Murray-Boyles (23/25) | P.J. Washington (2/25) |
| 12 / 186 | Ajay Mitchell (22/25) | Collin Murray-Boyles (2/25); Jimmy Butler III (1/25) |

### Slot 8

| Round / pick | Most selected | Other frequent selections |
|---|---|---|
| 1 / 8 | Cade Cunningham (14/25) | Giannis Antetokounmpo (5/25); Anthony Edwards (4/25) |
| 2 / 25 | Josh Giddey (8/25) | Alperen Sengun (7/25); Bam Adebayo (5/25) |
| 3 / 40 | Paolo Banchero (13/25) | Lauri Markkanen (5/25); Jalen Williams (3/25) |
| 4 / 57 | Chet Holmgren (17/25) | Walker Kessler (7/25); Lauri Markkanen (1/25) |
| 5 / 72 | Donovan Clingan (10/25) | Ivica Zubac (10/25); Walker Kessler (3/25) |
| 6 / 89 | Immanuel Quickley (24/25) | Ryan Rollins (1/25) |
| 7 / 104 | Zach Edey (17/25) | Ryan Rollins (4/25); Brandon Ingram (4/25) |
| 8 / 121 | Keegan Murray (12/25) | Cedric Coward (4/25); Isaiah Hartenstein (3/25) |
| 9 / 136 | Jalen Suggs (13/25) | Day'Ron Sharpe (10/25); Saddiq Bey (2/25) |
| 10 / 153 | Jonathan Kuminga (12/25) | Jalen Suggs (5/25); P.J. Washington (5/25) |
| 11 / 168 | Collin Murray-Boyles (24/25) | P.J. Washington (1/25) |
| 12 / 185 | Ajay Mitchell (24/25) | Collin Murray-Boyles (1/25) |

### Slot 9

| Round / pick | Most selected | Other frequent selections |
|---|---|---|
| 1 / 9 | Jayson Tatum (11/25) | Cade Cunningham (9/25); Anthony Edwards (5/25) |
| 2 / 24 | Alperen Sengun (11/25) | Josh Giddey (7/25); Amen Thompson (2/25) |
| 3 / 41 | Paolo Banchero (11/25) | Lauri Markkanen (6/25); Deni Avdija (2/25) |
| 4 / 56 | Chet Holmgren (20/25) | Walker Kessler (5/25) |
| 5 / 73 | Ivica Zubac (9/25) | Donovan Clingan (9/25); Walker Kessler (4/25) |
| 6 / 88 | Immanuel Quickley (23/25) | Ryan Rollins (1/25); Alex Sarr (1/25) |
| 7 / 105 | Zach Edey (16/25) | Brandon Ingram (5/25); Ryan Rollins (4/25) |
| 8 / 120 | Keegan Murray (12/25) | Isaiah Hartenstein (4/25); Jaime Jaquez Jr. (2/25) |
| 9 / 137 | Saddiq Bey (10/25) | Day'Ron Sharpe (7/25); Anthony Black (7/25) |
| 10 / 152 | Jalen Suggs (15/25) | Jonathan Kuminga (5/25); Davion Mitchell (2/25) |
| 11 / 169 | Rui Hachimura (8/25) | Wendell Carter Jr. (5/25); Santi Aldama (5/25) |
| 12 / 184 | Ajay Mitchell (15/25) | Collin Murray-Boyles (10/25) |

### Slot 10

| Round / pick | Most selected | Other frequent selections |
|---|---|---|
| 1 / 10 | Jayson Tatum (11/25) | Cooper Flagg (4/25); Anthony Edwards (4/25) |
| 2 / 23 | Alperen Sengun (10/25) | Karl-Anthony Towns (7/25); Josh Giddey (5/25) |
| 3 / 42 | Lauri Markkanen (12/25) | Paolo Banchero (11/25); Evan Mobley (2/25) |
| 4 / 55 | Chet Holmgren (20/25) | Walker Kessler (4/25); Lauri Markkanen (1/25) |
| 5 / 74 | Ivica Zubac (11/25) | Donovan Clingan (9/25); Walker Kessler (3/25) |
| 6 / 87 | Immanuel Quickley (23/25) | Ivica Zubac (1/25); Alex Sarr (1/25) |
| 7 / 106 | Zach Edey (17/25) | Brandon Ingram (4/25); Ryan Rollins (3/25) |
| 8 / 119 | Keegan Murray (16/25) | Nic Claxton (3/25); Cedric Coward (2/25) |
| 9 / 138 | Saddiq Bey (14/25) | Day'Ron Sharpe (6/25); Anthony Black (5/25) |
| 10 / 151 | Jalen Suggs (15/25) | Jonathan Kuminga (6/25); Davion Mitchell (2/25) |
| 11 / 170 | Santi Aldama (7/25) | Rui Hachimura (5/25); Keaton Wagler (4/25) |
| 12 / 183 | Ajay Mitchell (15/25) | Collin Murray-Boyles (10/25) |

### Slot 11

| Round / pick | Most selected | Other frequent selections |
|---|---|---|
| 1 / 11 | Cooper Flagg (8/25) | Jayson Tatum (6/25); Tyrese Maxey (5/25) |
| 2 / 22 | Alperen Sengun (13/25) | Karl-Anthony Towns (8/25); Josh Giddey (4/25) |
| 3 / 43 | Lauri Markkanen (13/25) | Paolo Banchero (8/25); Darius Garland (2/25) |
| 4 / 54 | Chet Holmgren (22/25) | Walker Kessler (3/25) |
| 5 / 75 | Ivica Zubac (13/25) | Donovan Clingan (5/25); Jaren Jackson Jr. (5/25) |
| 6 / 86 | Immanuel Quickley (18/25) | Matas Buzelis (4/25); Jaren Jackson Jr. (2/25) |
| 7 / 107 | Zach Edey (16/25) | Brandon Ingram (6/25); Ryan Rollins (2/25) |
| 8 / 118 | Keegan Murray (18/25) | Nic Claxton (2/25); Brandon Ingram (2/25) |
| 9 / 139 | Saddiq Bey (17/25) | Day'Ron Sharpe (3/25); Anthony Black (3/25) |
| 10 / 150 | Jalen Suggs (14/25) | Jonathan Kuminga (7/25); Davion Mitchell (2/25) |
| 11 / 171 | Santi Aldama (11/25) | Rui Hachimura (4/25); Wendell Carter Jr. (3/25) |
| 12 / 182 | Ajay Mitchell (19/25) | Collin Murray-Boyles (6/25) |

### Slot 12

| Round / pick | Most selected | Other frequent selections |
|---|---|---|
| 1 / 12 | Tyrese Maxey (8/25) | Jayson Tatum (5/25); Cooper Flagg (4/25) |
| 2 / 21 | Alperen Sengun (12/25) | Karl-Anthony Towns (7/25); Scottie Barnes (3/25) |
| 3 / 44 | Lauri Markkanen (15/25) | Paolo Banchero (8/25); Darius Garland (2/25) |
| 4 / 53 | Chet Holmgren (20/25) | Lauri Markkanen (3/25); Darius Garland (1/25) |
| 5 / 76 | Ivica Zubac (12/25) | Jaren Jackson Jr. (5/25); Donovan Clingan (3/25) |
| 6 / 85 | Immanuel Quickley (18/25) | Matas Buzelis (4/25); Alex Sarr (2/25) |
| 7 / 108 | Zach Edey (18/25) | Brandon Ingram (5/25); John Collins (1/25) |
| 8 / 117 | Keegan Murray (16/25) | Nic Claxton (3/25); Andrew Wiggins (2/25) |
| 9 / 140 | Saddiq Bey (16/25) | Day'Ron Sharpe (3/25); Aaron Gordon (3/25) |
| 10 / 149 | Jalen Suggs (18/25) | Jonathan Kuminga (4/25); Davion Mitchell (2/25) |
| 11 / 172 | Santi Aldama (14/25) | Wendell Carter Jr. (4/25); Bobby Portis (1/25) |
| 12 / 181 | Ajay Mitchell (14/25) | Collin Murray-Boyles (11/25) |

### Slot 13

| Round / pick | Most selected | Other frequent selections |
|---|---|---|
| 1 / 13 | Tyrese Maxey (8/25) | Scottie Barnes (6/25); Cooper Flagg (4/25) |
| 2 / 20 | Alperen Sengun (14/25) | Karl-Anthony Towns (5/25); Scottie Barnes (4/25) |
| 3 / 45 | Lauri Markkanen (16/25) | Paolo Banchero (4/25); Darius Garland (3/25) |
| 4 / 52 | Chet Holmgren (22/25) | Lauri Markkanen (2/25); Darius Garland (1/25) |
| 5 / 77 | Ivica Zubac (11/25) | Jaren Jackson Jr. (5/25); Donovan Clingan (3/25) |
| 6 / 84 | Immanuel Quickley (9/25) | Matas Buzelis (9/25); Alex Sarr (5/25) |
| 7 / 109 | Zach Edey (16/25) | Brandon Ingram (5/25); Andrew Wiggins (2/25) |
| 8 / 116 | Day'Ron Sharpe (11/25) | Keegan Murray (8/25); Andrew Wiggins (3/25) |
| 9 / 141 | Saddiq Bey (18/25) | Cason Wallace (3/25); Dillon Brooks (2/25) |
| 10 / 148 | Jalen Suggs (21/25) | Davion Mitchell (2/25); Jonathan Kuminga (2/25) |
| 11 / 173 | Scoot Henderson (8/25) | Morez Johnson Jr. (7/25); Alex Caruso (3/25) |
| 12 / 180 | Collin Murray-Boyles (15/25) | Ajay Mitchell (10/25) |

### Slot 14

| Round / pick | Most selected | Other frequent selections |
|---|---|---|
| 1 / 14 | Tyrese Maxey (8/25) | Scottie Barnes (6/25); Donovan Mitchell (4/25) |
| 2 / 19 | Alperen Sengun (16/25) | Scottie Barnes (4/25); Karl-Anthony Towns (4/25) |
| 3 / 46 | Darius Garland (9/25) | Lauri Markkanen (5/25); Desmond Bane (3/25) |
| 4 / 51 | Chet Holmgren (17/25) | Lauri Markkanen (7/25); Darius Garland (1/25) |
| 5 / 78 | Ivica Zubac (10/25) | Jaren Jackson Jr. (7/25); Matas Buzelis (4/25) |
| 6 / 83 | Immanuel Quickley (9/25) | Matas Buzelis (8/25); Alex Sarr (5/25) |
| 7 / 110 | Zach Edey (15/25) | Brandon Ingram (5/25); Jabari Smith Jr. (4/25) |
| 8 / 115 | Day'Ron Sharpe (10/25) | Keegan Murray (8/25); Brandon Ingram (3/25) |
| 9 / 142 | Saddiq Bey (11/25) | Aaron Gordon (5/25); Dillon Brooks (5/25) |
| 10 / 147 | Jalen Suggs (21/25) | Jonathan Kuminga (3/25); Davion Mitchell (1/25) |
| 11 / 174 | Morez Johnson Jr. (10/25) | Alex Caruso (5/25); Jamal Shead (4/25) |
| 12 / 179 | Collin Murray-Boyles (15/25) | Ajay Mitchell (10/25) |

### Slot 15

| Round / pick | Most selected | Other frequent selections |
|---|---|---|
| 1 / 15 | Scottie Barnes (9/25) | Tyrese Maxey (6/25); Jalen Brunson (4/25) |
| 2 / 18 | Alperen Sengun (15/25) | Scottie Barnes (5/25); Karl-Anthony Towns (2/25) |
| 3 / 47 | Stephon Castle (9/25) | Darius Garland (6/25); Desmond Bane (4/25) |
| 4 / 50 | Lauri Markkanen (14/25) | Chet Holmgren (11/25) |
| 5 / 79 | Jaren Jackson Jr. (14/25) | Alex Sarr (4/25); Ivica Zubac (2/25) |
| 6 / 82 | Matas Buzelis (11/25) | Alex Sarr (5/25); Ivica Zubac (5/25) |
| 7 / 111 | Zach Edey (7/25) | Brandon Ingram (5/25); Andrew Wiggins (3/25) |
| 8 / 114 | Day'Ron Sharpe (10/25) | Keegan Murray (7/25); Zach Edey (5/25) |
| 9 / 143 | Dillon Brooks (8/25) | Aaron Gordon (4/25); Saddiq Bey (4/25) |
| 10 / 146 | Jalen Suggs (22/25) | Saddiq Bey (1/25); Jonathan Kuminga (1/25) |
| 11 / 175 | Morez Johnson Jr. (11/25) | Alex Caruso (5/25); Tim Hardaway Jr. (3/25) |
| 12 / 178 | Collin Murray-Boyles (21/25) | Ajay Mitchell (4/25) |

### Slot 16

| Round / pick | Most selected | Other frequent selections |
|---|---|---|
| 1 / 16 | Scottie Barnes (9/25) | Alperen Sengun (8/25); Tyrese Maxey (4/25) |
| 2 / 17 | Alperen Sengun (8/25) | Domantas Sabonis (7/25); Karl-Anthony Towns (6/25) |
| 3 / 48 | Lauri Markkanen (16/25) | Chet Holmgren (5/25); Darius Garland (3/25) |
| 4 / 49 | Chet Holmgren (17/25) | Walker Kessler (5/25); Darius Garland (2/25) |
| 5 / 80 | Jaren Jackson Jr. (8/25) | Ivica Zubac (7/25); Matas Buzelis (6/25) |
| 6 / 81 | Immanuel Quickley (10/25) | Matas Buzelis (10/25); Alex Sarr (3/25) |
| 7 / 112 | Zach Edey (8/25) | Keegan Murray (7/25); Day'Ron Sharpe (5/25) |
| 8 / 113 | Cedric Coward (8/25) | Keegan Murray (7/25); Andrew Wiggins (3/25) |
| 9 / 144 | Jalen Suggs (22/25) | Saddiq Bey (2/25); Jonathan Kuminga (1/25) |
| 10 / 145 | Jonathan Kuminga (13/25) | Saddiq Bey (10/25); Aaron Gordon (1/25) |
| 11 / 176 | Collin Murray-Boyles (22/25) | Ajay Mitchell (3/25) |
| 12 / 177 | Ajay Mitchell (22/25) | Santi Aldama (2/25); Jimmy Butler III (1/25) |

## Reproduction and limits

Run `python -m basketball research adp-mocks --refresh-market` for all positions, or supply `--slot N` for a specific position; `--count` controls seeds per position/field. Source, input, protocol and code hashes are retained with every report. Older-than-24-hour research roster/injury evidence must be refreshed separately before another run.

Focused validation: 14 backend tests passed. No browser room was joined or picks submitted. These simulations do not change the scheduled draft strategy, live source selection or API execution rules. Same-day research injury checks are less stringent than the live pre-pick checks. This is a forward rehearsal, not a historical backtest or evidence of future points/wins. Bans apply only to our team; injury price windows apply to all teams.

Final report SHA256: `c3ddda778987e9c6d1de119abe0aebf172e7fd66feac540fbb4f26a4a4dbaefe`.

See [protocol](BASKETBALL_ADP_MOCKS_PROTOCOL.md) and [aggregate JSON](basketball_adp_mocks_results.json). Full 192-pick logs and all availability traces remain in ignored local `basketball/data/research-adp-mocks/mocks.json`.
