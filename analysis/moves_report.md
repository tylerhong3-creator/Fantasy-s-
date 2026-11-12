# Lukawhi: moves report (ESPN export + Hashtag Basketball cross-check)

Data: ESPN export 2026-11-11 (week 4 in progress) and the HBB supplement pulled the same day. Every move below was simulated twice with the same engine (daily lineups, real schedule, injuries, week-to-week noise): once with my blended ESPN rates and once with HBB's rest-of-season projections. **ROBUST** = helps in both. The HBB file confirmed the ESPN matchup weeks (P7 Nov 30-Dec 6, P8 Dec 7-13, P18 Feb 15-28, playoffs Mar 8-28), so the week-boundary warning in report.md no longer applies.

## Bottom line: moves in order

1. **Waiver move: add Kris Dunn, drop Rui Hachimura.** +1.57 (ESPN-blend) / +1.07 (HBB) on the season score (regular-season categories + 3× playoff categories). It is the best pickup that helps under both projections.
2. **Trade: give Dyson Daniels + Jrue Holiday to NYX2 (John) for Devin Booker.** Score +4.23 / +6.49; title odds 31%→43% (ESPN-blend), 37%→52% (HBB).
3. **If that's declined**, in order: Dyson Daniels + Jrue Holiday → Jalen Johnson (NYK); OG Anunoby + Jrue Holiday → Derrick White (CAL); OG Anunoby + Jrue Holiday → Miles Bridges (BCn). Details below.
4. **Week 8 (Dec 7-13) is a near-empty week:** only 14 NBA games (2026-12-12, 2026-12-13), no team plays twice, and DAL, LAL don't play at all, so **Luka has 0 games**. Your opponent is 76Er. Every other player of yours has 1 game, so start everyone who plays; the week is mostly luck. Don't make long-term roster moves just for it.
5. **Don't punt FT%.** It is your weakest category in both projections, but punting it gains nothing measurable (see report.md). Treat it as soft: never pay for FT%, don't avoid good players because of it.

## What the team is good and bad at

Projected title odds now: **28% (ESPN-blend) / 34% (HBB)**; playoffs ~100%, top-2 seed 99% / 99%. Main rival: BBB (title 45% / 31%).

| category | actual rank wk1-3 | HBB rank (ROS z, top-10) | win% reg (ESPN-blend) | win% reg (HBB) | win% playoffs (ESPN-blend) | win% playoffs (HBB) | verdict |
|---|---|---|---|---|---|---|---|
| PTS | 5 | 5 | 50% | 54% | 28% | 38% | IMPROVE (swing) |
| REB | 3 | 1 | 77% | 85% | 49% | 70% | SOLIDIFY (strength) |
| AST | 5 | 9 | 61% | 48% | 48% | 27% | IMPROVE (swing) |
| STL | 2 | 4 | 66% | 70% | 61% | 63% | SOLIDIFY (strength) |
| BLK | 3 | 5 | 55% | 60% | 36% | 47% | IMPROVE (swing) |
| 3PM | 2 | 3 | 78% | 81% | 73% | 78% | SOLIDIFY (strength) |
| FG% | 2 | 5 | 57% | 52% | 62% | 48% | IMPROVE (swing) |
| FT% | 6 | 10 | 39% | 30% | 31% | 30% | WEAK: soft-concede |
| TO | 5 | 9 | 57% | 66% | 76% | 75% | SOLIDIFY (strength) |

- **Strengths to keep (don't trade away the players who drive them):** REB, STL, 3PM, TO.
- **Swing categories, where upgrades pay off most:** PTS, AST, BLK, FG%. Per unit of talent, the simulator ranks AST and PTS as the highest-leverage adds in both projections, then REB/BLK.
- **Weak spots:** FT%. FT% is last in HBB's league profile (rank 10) and ~30-39% in the simulator. HBB also ranks you 9th in AST and TO on its projected top-10 players, while your actual weekly results were better (AST 5th, TO 5th): your depth plays more games than a top-10 snapshot counts.
- **Biggest single swing: playoff PTS.** Against the likely playoff field you win PTS only ~28% (ESPN-blend) of weeks. A real scorer is the upgrade that matters most in March.

## My players

**Keep score** = categories (season score: regular + 3× playoffs) I'd lose by swapping him for the best free agent. High = core; near zero or negative = replaceable. HBB values are HBB's 9-cat z totals (TO weighted ×1).

| player | status | z (ESPN-blend) | HBB ROS value | HBB last-14 value | HBB season value | MPG chg (L7) | keep score ESPN-blend | keep score HBB | P8 games (Dec 7-13) | playoff games | off-night games left | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Luka Doncic | ACTIVE | +9.76 | +12.85 | +24.09 | +16.37 | +1.3 | +15.21 | +13.83 | 0 | 10 | 17 | CORE |
| Kawhi Leonard | OUT (IR) | +5.77 | +4.79 |  | +8.54 |  |  |  | 1 | 11 | 16 | HOLD (IR) |
| Karl-Anthony Towns | ACTIVE | +2.40 | +5.36 | +8.40 | +5.31 | -2.3 | +6.47 | +4.50 | 1 | 10 | 20 | CORE |
| Dyson Daniels | ACTIVE | +1.83 | +2.35 | +6.34 | +3.81 | +2.4 | +5.40 | +1.75 | 1 | 11 | 20 | KEEP |
| Evan Mobley | ACTIVE | +1.01 | +5.14 | +6.67 | +4.12 | -1.4 | +3.01 | +2.97 | 1 | 9 | 19 | CORE |
| Donovan Clingan | ACTIVE | +0.74 | +3.38 | +8.32 | +4.11 | +1.4 | +5.04 | +3.22 | 1 | 10 | 23 | CORE |
| Jabari Smith Jr. | ACTIVE | +0.51 | +1.80 | +7.04 | +5.62 | +2.0 | +3.64 | +1.21 | 1 | 10 | 24 | KEEP |
| OG Anunoby | ACTIVE | -0.03 | +3.34 | +4.94 | +1.93 | -3.7 | +1.13 | +0.68 | 1 | 10 | 20 | TRADE CHIP / replaceable |
| Brandin Podziemski | ACTIVE | -0.36 | +1.46 | +5.00 | +3.57 | -0.8 | +2.28 | +1.07 | 1 | 11 | 19 | KEEP |
| Norman Powell | OUT | -1.25 | +1.58 | -0.95 | -0.61 | -6.6 | -0.46 | -0.45 | 1 | 10 | 20 | DROP/REPLACE |
| Kyshawn George | ACTIVE | -1.31 | -0.73 | +7.52 | +3.25 | +1.6 | +0.80 | -2.56 | 1 | 10 | 20 | TRADE CHIP / replaceable |
| Jrue Holiday | ACTIVE | -1.38 | +0.05 | +4.04 | +2.06 | +0.3 | -1.05 | -2.51 | 1 | 10 | 23 | DROP/REPLACE |
| Payton Pritchard | ACTIVE | -1.42 | +1.37 | +2.83 | +0.76 | -1.9 | +1.39 | +1.11 | 1 | 11 | 25 | KEEP |
| Davion Mitchell | ACTIVE | -1.80 | +0.81 | +6.21 | +3.21 | +4.0 | -0.08 | +0.34 | 1 | 10 | 11 | TRADE CHIP / replaceable |
| Rui Hachimura | ACTIVE | -3.51 | +0.46 | +3.44 | -2.02 | -0.8 | -2.41 | -1.07 | 1 | 11 | 16 | DROP/REPLACE |

**Where the two projections disagree most:** Karl-Anthony Towns (+6.5 vs +4.5), Dyson Daniels (+5.4 vs +1.7), Donovan Clingan (+5.0 vs +3.2), Jabari Smith Jr. (+3.6 vs +1.2), Kyshawn George (+0.8 vs -2.6). Usually this is HBB weighting a player's recent role differently: compare his HBB last-14 value and minutes change before acting.

## Free-agent moves

| add | drop | reg cats (ESPN-blend) | playoff cats (ESPN-blend) | reg cats (HBB) | playoff cats (HBB) | ROBUST? | HBB last-14 value | MPG chg (L7) |
|---|---|---|---|---|---|---|---|---|
| Kris Dunn | Rui Hachimura | +0.65 | +0.30 | +0.34 | +0.25 | yes | +2.97 | -2.7 |
| Collin Gillespie | Jrue Holiday | -0.21 | +0.42 | +0.05 | +0.44 | yes | +1.55 | -1.9 |
| Cam Spencer | Jrue Holiday | -0.54 | +0.42 | +0.38 | +0.63 | yes | +4.31 | +0.5 |
| Nic Claxton | Jrue Holiday | +0.06 | +0.14 | +0.13 | +0.16 | yes | +2.83 | +0.0 |
| Christian Braun | Rui Hachimura | +0.54 | +0.09 | -0.18 | -0.07 | no | +5.05 | -4.3 |
| Isaiah Stewart | Jrue Holiday | -1.25 | +0.21 | -1.14 | +0.30 | no | +5.13 | -8.6 |
| Devin Vassell | Jrue Holiday | -0.35 | -0.11 | -0.51 | -0.08 | no | +4.61 | -2.5 |
| DeMar DeRozan | Kyshawn George | -0.69 | -0.08 | -0.49 | +0.02 | no | -2.24 | -3.4 |

Each add is paired with its best drop (the one that scores best in the worse of the two projections). All combinations: crosscheck_free_agents.csv.

## Trades

28 trade ideas (the shortlists from both full runs) were re-simulated in both worlds on top of the waiver move above. 17 help me in both and pass the fairness check (their own category change ≥ -0.05/week in at least one projection, my value ratio ≥ 0.85, and HBB's market value they receive within 1.5 of what they give).

### 1. Give Dyson Daniels + Jrue Holiday → get Devin Booker (NYX2 (John))

- **Me:** season score +4.23 (ESPN-blend) / +6.49 (HBB); playoff categories +0.93 / +1.27; title odds 31%→43% / 37%→52%.
- **Categories (agreed by both):** up PTS, AST, 3PM, FT%; down REB, STL, BLK, TO.
- **Them:** +0.14 / +0.08 categories a week; HBB market value they get +2.4 vs give +3.6.
- **Roster:** I add Collin Gillespie; they drop Jonathan Kuminga.
- **Risks:** Devin Booker: HBB last-14 +8.2 vs ROS +3.6.

### 2. Give Dyson Daniels + Jrue Holiday → get Jalen Johnson (NYK (Juno))

- **Me:** season score +4.15 (ESPN-blend) / +6.71 (HBB); playoff categories +0.88 / +1.26; title odds 31%→40% / 37%→51%.
- **Categories (agreed by both):** up PTS, REB, AST, 3PM, FT%; down STL, TO.
- **Them:** -0.01 / -0.08 categories a week; HBB market value they get +2.4 vs give +3.3.
- **Roster:** I add Collin Gillespie; they drop Dillon Brooks.
- **Risks:** Jalen Johnson: minutes +3.5 last 7 days.

### 3. Give OG Anunoby + Jrue Holiday → get Derrick White (CAL (Calvin))

- **Me:** season score +3.92 (ESPN-blend) / +4.51 (HBB); playoff categories +0.78 / +0.84; title odds 31%→38% / 37%→41%.
- **Categories (agreed by both):** up REB, AST, BLK, TO; down STL, 3PM, FT%.
- **Them:** -0.05 / -0.00 categories a week; HBB market value they get +3.4 vs give +2.7.
- **Roster:** I add Jalen Smith; they drop RJ Barrett.
- **Risks:** OG Anunoby: minutes -3.7 last 7 days.

### 4. Give OG Anunoby + Jrue Holiday → get Miles Bridges (BCn (Andrew))

- **Me:** season score +6.17 (ESPN-blend) / +3.91 (HBB); playoff categories +1.12 / +1.04; title odds 31%→39% / 37%→47%.
- **Categories (agreed by both):** up PTS, REB, AST, TO; down STL.
- **Them:** -0.04 / +0.05 categories a week; HBB market value they get +3.4 vs give +1.1.
- **Roster:** I add DeMar DeRozan; they drop P.J. Washington.
- **Risks:** OG Anunoby: minutes -3.7 last 7 days; Miles Bridges: HBB last-14 +7.8 vs ROS +1.1.

### 5. Give Karl-Anthony Towns + Jrue Holiday → get Jayson Tatum (BCn (Andrew))

- **Me:** season score +3.73 (ESPN-blend) / +7.38 (HBB); playoff categories +0.87 / +1.28; title odds 31%→36% / 37%→47%.
- **Categories (agreed by both):** up PTS, AST, 3PM, FT%; down REB, FG%.
- **Them:** -0.01 / -0.13 categories a week; HBB market value they get +5.4 vs give +6.8.
- **Roster:** I add Isaiah Stewart; they drop P.J. Washington.
- **Risks:** Jayson Tatum: minutes -3.6 last 7 days, HBB last-14 +11.0 vs ROS +6.8.

### 6. Give OG Anunoby + Jrue Holiday → get Jaylen Brown (SS (Simon))

- **Me:** season score +3.41 (ESPN-blend) / +2.84 (HBB); playoff categories +0.67 / +0.90; title odds 31%→39% / 37%→49%.
- **Categories (agreed by both):** up PTS, AST, FG%; down BLK, 3PM, FT%, TO.
- **Them:** +0.05 / +0.18 categories a week; HBB market value they get +3.4 vs give +1.8.
- **Roster:** I add DeMar DeRozan; they drop Jalen Green.
- **Risks:** OG Anunoby: minutes -3.7 last 7 days; Jaylen Brown: HBB last-14 +6.0 vs ROS +1.8.

All evaluated trades with both projections: crosscheck_trades.csv.

## Schedule notes (from HBB, matches the ESPN export)

- **Week 8 (Dec 7-13):** total roster games = 14 (Luka 0; no NBA team plays more than once). With so few games every slot is open, so all your players who play will count.
- **Playoff weeks (Mar 8-28):** roster games = 154. Fewest: Evan Mobley 9, Luka Doncic 10, Karl-Anthony Towns 10. Most: Kawhi Leonard (IR) 11, Dyson Daniels 11, Payton Pritchard 11, Brandin Podziemski 11.
- **Off-night games** (days with ≤7 NBA games, when bench players actually get a slot): Pritchard, Jabari, Clingan and Jrue have the most; Davion Mitchell has the fewest. Players with many off-night games are worth more on a deep roster like yours.

## HBB free-agent radar (minutes trends)

| Player | Pos | NBA | GP | MPG | MPG chg L7 | Value ROS proj | Value L14 | Games left reg season | Playoff games (Mar 8-28) |
|---|---|---|---|---|---|---|---|---|---|
| Kris Dunn | PG,SG | LAC | 10 | 28.5 | -2.7 | +1.95 | +2.97 | 51 | 11 |
| Charles Bassey | C | GS | 9 | 12.4 | +2.1 | +1.95 | +2.05 | 49 | 11 |
| Christian Braun | SG,SF,PF | DEN | 9 | 34.1 | -4.3 | +1.69 | +5.05 | 51 | 11 |
| Paul Reed | PF,C | DET | 10 | 25.9 | -2.4 | +1.56 | +3.32 | 51 | 11 |
| Mitchell Robinson | C | BOS | 10 | 18.6 | -1.0 | +1.17 | +0.08 | 50 | 11 |
| Jalen Williams | SF,PF | OKC | 3 | 31.6 |  | +0.87 |  | 50 | 11 |
| Obi Toppin | SF,PF | IND | 8 | 21.9 | -1.7 | +0.83 | -1.83 | 50 | 10 |
| Robert Williams III | C | POR | 8 | 16.3 | -0.7 | +0.73 | +2.12 | 52 | 10 |
| Nic Claxton | C | CHI | 1 | 17.7 | +0.0 | +0.71 | +2.83 | 52 | 10 |
| Cam Spencer | PG,SG | MEM | 10 | 19.3 | +0.5 | +0.69 | +4.31 | 50 | 12 |
| Cason Wallace | PG,SG,SF | OKC | 3 | 16.3 |  | +0.54 |  | 50 | 11 |
| Aaron Nesmith | SG,SF | IND | 9 | 25.6 | +4.9 | +0.45 | +0.79 | 50 | 10 |

Only players listed as unrostered in the ESPN export are shown. Rising minutes plus a strong last-14 value are the pickups to watch if a roster spot opens (e.g. when Kawhi returns).

## Assumptions and limits

- HBB rates replace the ESPN-blend per-game rates for players matched by name; injury status, availability, lineups and schedule come from the ESPN export in both worlds. HBB's FG%/FT% z-scores and 'Value' are shown as HBB computes them.
- Kawhi Leonard is on IR with no return date in either source and is not projected. Week 4 is partly played; its banked totals are included.
- Trade acceptance is an estimate. HBB 'market value' is a proxy for how the other manager might rate the players.
- RotoWire rankings were not used.
