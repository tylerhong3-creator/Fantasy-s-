# Lukawhi: rest-of-season analysis

Built from the ESPN export dated 2026-11-11 (scoring period 23, week 4 in progress). Re-run with `python3 analysis/run_analysis.py <export folder>`. All numbers come from the export only.

## Data checks

- Game logs (`counts_for_team=1`) vs `matchups.csv`: **40 of 40 team-weeks match exactly** (all 11 stat totals, games started, and FG%/FT% recomputed from makes/attempts).
- Completed weeks used for results: 1, 2, 3. Week 4 is partial: its banked totals are added to the projection for the 4 remaining days (today's unfinished games count as final).
- FG% and FT% are always summed makes / summed attempts.
- Matchup periods 5-22 are derived, not confirmed by ESPN. Playoff weeks 20-22 = 2027-03-08 to 2027-03-28. Anything about playoff schedules (games per team in weeks 20-22) depends on those boundaries and is flagged ⚠️.
- Players in the export: 399; with usable rates: 397. Game-to-game noise was measured from 1589 game-log rows; model noise vs real week-to-week swings:

| category | empirical_to_model_sd_ratio |
|---|---|
| PTS | 0.90 |
| REB | 1.20 |
| AST | 1.01 |
| STL | 1.13 |
| BLK | 1.11 |
| 3PM | 1.08 |
| FG% | 0.88 |
| FT% | 1.04 |
| TO | 1.03 |

Ratios above 1 mean real weeks swing more than pure game-to-game noise; the model uses max(1, ratio).

## My team identity

Record 19-7-1 (seed 1); all-play 160-77-6 (best in the league).

This week (week 4, vs NYX2, partly played): expected 5.0 categories, 72% chance to win the matchup.

Model outlook with the current roster: **5.40 categories per regular week**, **4.64 per playoff week** vs the likely playoff field (BBB, NYK, CAL, TT, BCn). Playoff odds 100%, top-2 seed (bye) 99%, title 28%.

Season simulation (20,000 runs, current rosters):

| team | record | proj final cat wins | playoffs | top-2 seed | title |
|---|---|---|---|---|---|
| BBB (Bryan) | 15-12-0 | 98 | 100% | 89% | 45% |
| LK (Tyler) | 19-7-1 | 105 | 100% | 99% | 28% |
| TT (Eric) | 15-12-0 | 86 | 78% | 4% | 6% |
| CAL (Calvin) | 7-19-1 | 83 | 64% | 2% | 6% |
| NYK (Juno) | 8-19-0 | 84 | 67% | 2% | 6% |
| BCn (Andrew) | 14-12-1 | 84 | 72% | 2% | 4% |
| SS (Simon) | 15-12-0 | 84 | 68% | 2% | 2% |
| LS (Sam) | 10-17-0 | 80 | 34% | 0% | 2% |
| NYX2 (John) | 15-11-1 | 76 | 13% | 0% | 0% |
| 76Er (Andy) | 15-12-0 | 73 | 4% | 0% | 0% |

| category | rank wk1-3 | my avg/week | won in my matchups | all-play W-L-T | all-play win% | proj win% (my schedule) | proj win% (playoffs) | proj win% vs field | group |
|---|---|---|---|---|---|---|---|---|---|
| PTS | 5 | 668.300 | 1/3 | 17-10-0 | 63% | 50% | 28% | 52% | SWING |
| REB | 3 | 243.300 | 2/3 | 20-7-0 | 74% | 77% | 49% | 72% | SWING |
| AST | 5 | 149.300 | 3/3 | 14-12-1 | 54% | 61% | 48% | 59% | SWING |
| STL | 2 | 46.000 | 3/3 | 17-7-3 | 69% | 66% | 61% | 63% | SWING |
| BLK | 3 | 28.300 | 3/3 | 20-7-0 | 74% | 55% | 36% | 55% | SWING |
| 3PM | 2 | 80.700 | 1/3 | 20-7-0 | 74% | 78% | 73% | 80% | LOCK |
| FG% | 2 | 0.479 | 2/3 | 20-7-0 | 74% | 57% | 62% | 60% | SWING |
| FT% | 6 | 0.791 | 2/3 | 15-12-0 | 56% | 39% | 31% | 39% | SWING |
| TO | 5 | 79.300 | 2/3 | 17-8-2 | 67% | 57% | 76% | 57% | SWING |

Groups use the average of the regular-season and playoff projections: LOCK ≥ 70%, LOST CAUSE ≤ 30%, otherwise SWING.

**Who we are:** a deep, balanced Luka team. Strongest categories: 3PM (76%), TO (67%), STL (63%); locks: 3PM. Weakest: FT% (35%), PTS (39%); no category is a lost cause. The categories that move the most per unit of talent are **AST**, **PTS** and **REB** (one good specialist ≈ +0.11, +0.10, +0.08 categories a week). **Aim for** players whose value comes from AST, PTS and REB. **Avoid paying for** STL or 3PM specialists: the same quality of player adds only +0.05 / +0.05 a week there, because you already win them 63% / 76% of the time. Players who hurt FT% are acceptable if they bring AST or PTS: FT% is already your weakest category (35%), and an elite FT% specialist only moves it +0.07 a week, less than a specialist in AST (+0.11).

### Punt or stay balanced?

| strategy | moves | cats/reg week | cats/playoff week | matchup win % | still win punted cat |
|---|---|---|---|---|---|
| Current roster (no moves) |  | 5.40 | 4.64 | 73% |  |
| Balanced (best 2 waiver moves for all 9 cats) | add Collin Gillespie / drop Rui Hachimura; add DeMar DeRozan / drop Jrue Holiday | 5.49 | 4.87 | 75% |  |
| Punt PTS (best 2 waiver moves ignoring PTS) | add Kris Dunn / drop Rui Hachimura; add Collin Gillespie / drop Norman Powell | 5.41 | 4.79 | 73% | 33% |
| Punt REB (best 2 waiver moves ignoring REB) | add DeMar DeRozan / drop Rui Hachimura; add Collin Gillespie / drop Jrue Holiday | 5.49 | 4.87 | 75% | 71% |
| Punt AST (best 2 waiver moves ignoring AST) | add Isaiah Stewart / drop Davion Mitchell; add Brook Lopez / drop Rui Hachimura | 5.35 | 4.71 | 71% | 37% |
| Punt STL (best 2 waiver moves ignoring STL) | add Isaiah Stewart / drop Rui Hachimura; add DeMar DeRozan / drop Norman Powell | 5.44 | 4.76 | 72% | 57% |
| Punt BLK (best 2 waiver moves ignoring BLK) | add Collin Gillespie / drop Rui Hachimura; add DeMar DeRozan / drop Kyshawn George | 5.45 | 4.78 | 74% | 45% |
| Punt 3PM (best 2 waiver moves ignoring 3PM) | add DeMar DeRozan / drop Rui Hachimura; add Nic Claxton / drop Jrue Holiday | 5.49 | 4.77 | 75% | 66% |
| Punt FG% (best 2 waiver moves ignoring FG%) | add Collin Gillespie / drop Rui Hachimura; add DeMar DeRozan / drop Jrue Holiday | 5.49 | 4.87 | 75% | 52% |
| Punt FT% (best 2 waiver moves ignoring FT%) | add Nic Claxton / drop Rui Hachimura; add Collin Gillespie / drop Jrue Holiday | 5.47 | 4.81 | 75% | 33% |
| Punt TO (best 2 waiver moves ignoring TO) | add Collin Gillespie / drop Rui Hachimura; add DeMar DeRozan / drop Jrue Holiday | 5.49 | 4.87 | 75% | 57% |

Each strategy gets the same tools (the two best waiver moves), chosen to maximise that strategy's target categories; the columns then count all 9 categories honestly.

**Verdict: stay balanced.** No punt beats the balanced plan (best punt: Punt 3PM, 5.49 vs 5.49 categories a regular week and 4.77 vs 4.87 in the playoffs). Your swing categories are close enough that giving one away costs more than it frees up. (For REB, FG%, TO the best 'punt' moves are the same as the balanced moves, so those aren't real punts.)

## Stats to target

| category | boost tested (≈ one good specialist) | extra cats / reg week | extra cats / playoff week | extra matchup wins ROS |
|---|---|---|---|---|
| AST | +7.1 AST per week | +0.112 | +0.114 | +0.43 |
| PTS | +20.0 PTS per week | +0.100 | +0.096 | +0.36 |
| REB | +8.4 REB per week | +0.077 | +0.099 | +0.30 |
| BLK | +1.8 BLK per week | +0.079 | +0.077 | +0.27 |
| FT% | +1.1 extra made FT on the same attempts per week | +0.068 | +0.061 | +0.21 |
| TO | -2.8 TO per week | +0.072 | +0.052 | +0.22 |
| FG% | +2.2 extra made FG on the same attempts per week | +0.060 | +0.053 | +0.19 |
| 3PM | +3.5 3PM per week | +0.053 | +0.057 | +0.22 |
| STL | +1.3 STL per week | +0.047 | +0.043 | +0.17 |

Boost = one standard deviation of that stat among the top 150 players, times 3.5 games a week.

**Focus on, in order:** 1. AST (+0.11/wk), 2. PTS (+0.10/wk), 3. REB (+0.08/wk), 4. BLK (+0.08/wk).

## Player rankings

Per-game values are rest-of-season blended rates. **z** = 9-cat value per game vs the top 150 players (FG%/FT% weighted by attempts). **ROS games** = remaining NBA games × availability. **VORP** = value above the 10th-best healthy free agent (z -2.24) × ROS games. **Cats vs best FA** = categories I'd lose (full simulation) if I swapped him for the best free agent for my team; near zero or negative = replaceable. **Playoff games** = NBA games in weeks 20-22 ⚠️ (derived week boundaries).

### My roster

| player | pos | GP | PTS | REB | AST | STL | BLK | 3PM | FG% | FT% | TO | z | ROS games | playoff games | VORP | cats vs best FA (reg) | cats vs best FA (playoffs) | best FA swap | RotoWire | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Luka Doncic | PG | 10 | 35.97 | 8.01 | 8.31 | 1.79 | 0.64 | 4.66 | 0.490 | 0.846 | 4.45 | 9.76 | 50 | 10 | 598 | +10.03 | +1.73 | Collin Gillespie | 4 |  |
| Kawhi Leonard | SF/PF | 2 | 25.24 | 6.44 | 3.25 | 2.02 | 0.53 | 2.39 | 0.471 | 0.903 | 1.96 | 5.77 | 0 | 11 | 0 |  |  |  | 8 | on IR slot: not projected (no return date in data); OUT: assumed back after week 5 (no date in data); small sample (2 GP) |
| Karl-Anthony Towns | C | 10 | 21.06 | 12.52 | 3.51 | 0.85 | 0.54 | 1.79 | 0.524 | 0.808 | 2.89 | 2.40 | 52 | 10 | 240 | +3.80 | +0.86 | Nic Claxton | 14 |  |
| Dyson Daniels | PG/SG | 12 | 10.81 | 6.86 | 5.74 | 2.49 | 0.37 | 0.25 | 0.501 | 0.604 | 1.49 | 1.83 | 56 | 11 | 226 | +3.29 | +0.70 | Collin Gillespie | 35 |  |
| Evan Mobley | PF/C | 11 | 18.10 | 8.56 | 3.62 | 0.74 | 1.42 | 1.50 | 0.555 | 0.640 | 1.80 | 1.01 | 48 | 9 | 156 | +2.34 | +0.22 | DeMar DeRozan | 30 |  |
| Donovan Clingan | C | 10 | 11.57 | 10.84 | 1.80 | 0.46 | 1.88 | 1.06 | 0.540 | 0.669 | 1.30 | 0.74 | 55 | 10 | 164 | +3.12 | +0.58 | Nic Claxton | 18 |  |
| Jabari Smith Jr. | PF/C | 11 | 15.85 | 6.65 | 2.02 | 0.78 | 0.88 | 2.42 | 0.474 | 0.808 | 1.10 | 0.51 | 54 | 10 | 149 | +2.93 | +0.24 | Collin Gillespie |  |  |
| OG Anunoby | SF/PF | 10 | 16.77 | 5.26 | 2.29 | 1.28 | 0.61 | 2.28 | 0.442 | 0.853 | 1.90 | -0.03 | 51 | 10 | 112 | +0.72 | +0.14 | DeMar DeRozan | 37 |  |
| Brandin Podziemski | PG/SG | 9 | 15.37 | 5.23 | 4.03 | 1.18 | 0.35 | 2.31 | 0.466 | 0.757 | 1.52 | -0.36 | 57 | 11 | 107 | +1.47 | +0.27 | Collin Gillespie | 93 |  |
| Norman Powell | SG/SF | 8 | 21.57 | 3.20 | 2.18 | 1.35 | 0.17 | 2.60 | 0.442 | 0.810 | 1.92 | -1.25 | 47 | 10 | 47 | +0.04 | -0.17 | Collin Gillespie | 72 | OUT: assumed back after week 5 (no date in data) |
| Kyshawn George | SG/SF | 11 | 16.03 | 4.75 | 4.59 | 0.78 | 1.12 | 2.12 | 0.460 | 0.796 | 2.77 | -1.31 | 49 | 10 | 45 | +1.15 | -0.12 | Collin Gillespie | 119 |  |
| Jrue Holiday | PG/SG | 10 | 13.37 | 3.95 | 4.53 | 0.92 | 0.25 | 2.24 | 0.475 | 0.854 | 1.78 | -1.38 | 51 | 10 | 44 | +0.21 | -0.42 | Collin Gillespie | 102 |  |
| Payton Pritchard | PG/SG | 11 | 14.92 | 3.71 | 4.45 | 0.76 | 0.14 | 2.47 | 0.442 | 0.880 | 1.26 | -1.42 | 54 | 11 | 44 | +0.44 | +0.31 | DeMar DeRozan | 141 |  |
| Davion Mitchell | PG | 11 | 12.61 | 2.30 | 7.27 | 1.09 | 0.36 | 1.74 | 0.492 | 0.664 | 2.01 | -1.80 | 53 | 10 | 24 | +0.32 | -0.14 | Collin Gillespie | 130 | minutes up (+5 last 15d) |
| Rui Hachimura | SF/PF | 8 | 13.18 | 4.62 | 1.24 | 0.84 | 0.27 | 1.95 | 0.463 | 0.704 | 1.10 | -3.51 | 54 | 11 | 0 | -0.97 | -0.48 | Collin Gillespie | 126 |  |

### Top available players (free agents / waivers)

| player | status | pos | GP | PTS | REB | AST | STL | BLK | 3PM | FG% | FT% | TO | z | RotoWire | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Jalen Williams | FREEAGENT | SF/PF | 3 | 18.21 | 4.80 | 4.98 | 1.26 | 0.52 | 1.15 | 0.473 | 0.820 | 1.84 | 0.12 | 266 | OUT; OUT: assumed back after week 5 (no date in data); small sample (3 GP) |
| Devin Vassell | FREEAGENT | SG/SF | 10 | 13.13 | 3.75 | 2.84 | 1.25 | 0.35 | 1.97 | 0.430 | 0.855 | 1.01 | -1.25 | 95 | OUT; OUT: assumed back after week 5 (no date in data) |
| Robert Williams III | FREEAGENT | C | 8 | 7.22 | 7.09 | 1.08 | 0.74 | 1.41 | 0.09 | 0.692 | 0.651 | 0.91 | -1.28 |  |  |
| Meleek Thomas | FREEAGENT | SG | 8 | 13.00 | 2.62 | 1.25 | 1.12 | 0.38 | 2.75 | 0.470 | 1.000 | 1.00 | -1.40 | 269 |  |
| Kris Dunn | WAIVERS | PG/SG | 10 | 7.41 | 3.49 | 3.76 | 1.85 | 0.36 | 0.94 | 0.475 | 0.779 | 1.43 | -1.49 | 144 |  |
| Cason Wallace | FREEAGENT | PG/SG | 3 | 8.03 | 2.95 | 2.30 | 1.99 | 0.30 | 1.23 | 0.431 | 0.809 | 0.93 | -1.56 | 278 | OUT; OUT: assumed back after week 5 (no date in data); small sample (3 GP) |
| Christian Braun | FREEAGENT | SG/SF | 9 | 11.82 | 4.25 | 2.37 | 1.30 | 0.22 | 1.19 | 0.517 | 0.778 | 1.07 | -1.67 | 78 |  |
| Collin Gillespie | FREEAGENT | PG | 10 | 9.93 | 3.17 | 4.45 | 1.57 | 0.16 | 2.39 | 0.389 | 0.836 | 1.48 | -1.68 | 74 |  |
| Jordan Goodwin | FREEAGENT | PG/SG | 6 | 8.97 | 4.36 | 2.22 | 1.51 | 0.13 | 1.90 | 0.434 | 0.696 | 0.81 | -1.84 | 238 | minutes down (-5 last 15d) |
| Cam Spencer | FREEAGENT | PG/SG | 10 | 10.00 | 2.89 | 5.30 | 0.80 | 0.08 | 1.88 | 0.488 | 0.946 | 1.34 | -2.03 | 250 |  |
| Ziaire Williams | FREEAGENT | SG/SF | 9 | 10.62 | 2.70 | 1.34 | 1.38 | 0.32 | 1.78 | 0.460 | 0.845 | 0.81 | -2.04 | 262 |  |
| Jalen Smith | FREEAGENT | PF/C | 9 | 10.69 | 7.06 | 1.45 | 0.38 | 0.98 | 1.46 | 0.488 | 0.741 | 0.82 | -2.13 | 137 |  |
| Derrick Jones Jr. | FREEAGENT | SF/PF | 9 | 10.39 | 4.05 | 1.31 | 0.99 | 0.83 | 1.42 | 0.503 | 0.728 | 0.93 | -2.24 |  |  |
| Brook Lopez | WAIVERS | C | 10 | 11.50 | 4.57 | 1.23 | 0.51 | 1.22 | 1.45 | 0.501 | 0.747 | 0.93 | -2.32 | 195 |  |
| Cameron Johnson | FREEAGENT | SF/PF | 6 | 11.97 | 3.85 | 2.21 | 0.90 | 0.26 | 2.08 | 0.473 | 0.819 | 1.13 | -2.41 | 105 |  |
| Paul Reed | FREEAGENT | PF/C | 10 | 9.30 | 5.79 | 1.62 | 0.99 | 0.91 | 0.33 | 0.593 | 0.673 | 1.35 | -2.45 | 149 | minutes up (+8 last 15d) |
| Sandro Mamukelashvili | FREEAGENT | PF/C | 12 | 10.50 | 4.76 | 1.74 | 0.78 | 0.55 | 1.39 | 0.506 | 0.766 | 0.79 | -2.49 | 182 |  |
| Nic Claxton | FREEAGENT | C | 1 | 11.04 | 6.80 | 3.55 | 0.63 | 1.23 | 0.05 | 0.574 | 0.608 | 1.37 | -2.54 | 85 | small sample (1 GP) |
| Justin Champagnie | FREEAGENT | SF/PF | 4 | 8.30 | 6.05 | 1.23 | 0.77 | 0.59 | 0.70 | 0.514 | 0.795 | 0.49 | -2.61 | 338 | OUT; OUT: assumed back after week 5 (no date in data); small sample (4 GP) |
| Tre Jones | FREEAGENT | PG | 9 | 11.46 | 2.75 | 4.01 | 1.09 | 0.12 | 0.46 | 0.533 | 0.816 | 1.08 | -2.62 | 109 |  |

## Trade recommendations

### Other teams at a glance

| team | record | proj cats/wk vs field | strong | weak | surplus (trade value they need least) |
|---|---|---|---|---|---|
| BBB (Bryan) | 15-12-0 | 5.23 | BLK, REB, AST, FG%, STL | 3PM, TO | Walker Kessler, Cooper Flagg, Anthony Davis |
| NYK (Juno) | 8-19-0 | 4.83 | AST, REB, PTS | 3PM, FG%, TO | LeBron James, Fred VanVleet, Saddiq Bey |
| CAL (Calvin) | 7-19-1 | 4.71 | FT%, 3PM, TO | STL, REB, AST | Daniel Gafford, Grayson Allen, Damian Lillard |
| TT (Eric) | 15-12-0 | 4.55 | PTS, BLK | TO, AST | Austin Reaves, Zach Edey, Joel Embiid |
| BCn (Andrew) | 14-12-1 | 4.42 | 3PM, FT%, PTS | FG%, TO, STL, AST | John Collins, Brandon Miller, Tari Eason |
| LS (Sam) | 10-17-0 | 4.32 | 3PM, AST | REB, BLK, STL | Zach LaVine, Ausar Thompson, James Harden |
| SS (Simon) | 15-12-0 | 4.30 | REB, FG% | FT%, AST, 3PM | Jarrett Allen, Tyler Herro, Cedric Coward |
| 76Er (Andy) | 15-12-0 | 3.65 | TO, 3PM, STL | BLK, PTS, REB, AST, FT% | Zion Williamson, Anthony Black, Isaiah Hartenstein |
| NYX2 (John) | 15-11-1 | 3.63 | TO, BLK | 3PM, REB, PTS, AST | Matisse Thybulle, Josh Hart, Jakob Poeltl |

867 trade ideas passed the quick screen; the best 552 were fully simulated (123 help me and look acceptable to the other side). All of them are in trades_evaluated.csv.

**Trades are measured after the free first move: add Collin Gillespie, drop Rui Hachimura** (see Free-agent moves). So every gain below is on top of that pickup. Title odds after the pickup alone: 33%.

The 15 best acceptable trades by category score were each run through the full season simulation; the five below have the biggest title-odds gain, rounded to the nearest point; differences under about 1 point are simulation noise, so ties are ordered by category score (trade_shortlist_with_title_odds.csv has all 15).

**Score** = extra categories over the remaining regular season + 3 × extra categories in playoff weeks 20-22. **Their gain** = change in their expected categories per week vs the whole league (their own needs). **Acceptable** = value ratio ≥ 0.85 and they lose no more than 0.05 categories a week, or they gain 0.10+ a week with ratio ≥ 0.75. **Value ratio** = trade value they receive ÷ value they give, where trade value = (value above replacement)^1.5 × games (so one star is worth more than two average players); ≥ 0.9 is roughly even.

### 1. Give OG Anunoby + Jrue Holiday → get Miles Bridges (BCn (Andrew))

- **Me:** +1.40 categories over the regular season, +1.15 over playoff weeks, +0.48 expected matchup wins. Title odds 33% → 43%.
- **Categories that move for me:** up REB, AST, BLK, FG%, TO; down PTS, STL, 3PM, FT%.
- **Them:** -0.04 categories per week vs the league (up AST, STL, 3PM, FT%; down REB, BLK, TO); value ratio 0.93. Their playoff odds 72% → 68%, title odds 4% → 1%.
- **Roster:** I add Cam Spencer from waivers; they drop P.J. Washington.
- **Risks:** no injury flags; normal projection uncertainty.
- **Pitch:** "You'd get two starters (OG Anunoby and Jrue Holiday) for Miles Bridges. It fixes your AST, STL and adds 3PM, FT%. By my numbers your team comes out ahead in weekly categories. Interested?"

### 2. Give Jrue Holiday → get Cameron Boozer (NYK (Juno))

- **Me:** +1.12 categories over the regular season, +0.88 over playoff weeks, +0.39 expected matchup wins. Title odds 33% → 43%.
- **Categories that move for me:** up PTS, REB, BLK, FT%; down STL, 3PM, FG%, TO.
- **Them:** -0.03 categories per week vs the league (up AST, STL, 3PM, FG%, TO; down PTS, REB, BLK, FT%); value ratio 1.54. Their playoff odds 66% → 67%, title odds 6% → 4%.
- **Risks:** no injury flags; normal projection uncertainty.
- **Pitch:** "I'd send you Jrue Holiday for Cameron Boozer. It fixes your 3PM, FG%, TO and adds AST, STL. By my numbers your team comes out ahead in weekly categories. Interested?"

### 3. Give OG Anunoby + Davion Mitchell → get Jaylen Brown (SS (Simon))

- **Me:** +0.98 categories over the regular season, +0.64 over playoff weeks, +0.38 expected matchup wins. Title odds 33% → 43%.
- **Categories that move for me:** up PTS, REB, AST, FG%; down STL, BLK, FT%, TO.
- **Them:** +0.01 categories per week vs the league (up AST, STL, FG%, FT%, TO; down PTS, REB); value ratio 1.60. Their playoff odds 69% → 74%, title odds 2% → 1%.
- **Roster:** I add Cam Spencer from waivers; they drop Jalen Green.
- **Risks:** Davion Mitchell: minutes up (+5 last 15d).
- **Pitch:** "You'd get two starters (OG Anunoby and Davion Mitchell) for Jaylen Brown. It fixes your AST, FT% and adds STL, FG%. By my numbers your team comes out ahead in weekly categories. Interested?"

### 4. Give Dyson Daniels + Jrue Holiday → get Devin Booker (NYX2 (John))

- **Me:** +0.54 categories over the regular season, +0.72 over playoff weeks, +0.32 expected matchup wins. Title odds 33% → 43%.
- **Categories that move for me:** up PTS, AST, 3PM, FT%; down REB, STL, BLK, FG%, TO.
- **Them:** +0.14 categories per week vs the league (up REB, AST, STL, FG%, TO; down PTS, BLK, 3PM, FT%); value ratio 1.13. Their playoff odds 14% → 21%, title odds 0% → 0%.
- **Roster:** I add Cam Spencer from waivers; they drop Jonathan Kuminga.
- **Risks:** no injury flags; normal projection uncertainty.
- **Pitch:** "You'd get two starters (Dyson Daniels and Jrue Holiday) for Devin Booker. It fixes your REB, AST and adds STL, FG%. By my numbers your team comes out ahead in weekly categories. Interested?"

### 5. Give Dyson Daniels + Jrue Holiday → get Cade Cunningham (BBB (Bryan))

- **Me:** +0.63 categories over the regular season, +0.63 over playoff weeks, +0.35 expected matchup wins. Title odds 33% → 43%.
- **Categories that move for me:** up PTS, AST, BLK, 3PM, FT%; down REB, STL, FG%, TO.
- **Them:** +0.07 categories per week vs the league (up STL, 3PM, FT%, TO; down PTS, REB, AST, BLK); value ratio 0.92. Their playoff odds 100% → 100%, title odds 43% → 39%.
- **Roster:** I add Cam Spencer from waivers; they drop Rudy Gobert.
- **Risks:** no injury flags; normal projection uncertainty.
- **Pitch:** "You'd get two starters (Dyson Daniels and Jrue Holiday) for Cade Cunningham. It fixes your 3PM, TO and adds STL, FT%. By my numbers your team comes out ahead in weekly categories. Interested?"

## Free-agent moves

| add | status | drop | reg cats | playoff cats | matchup wins | cats up | cats down | notes |
|---|---|---|---|---|---|---|---|---|
| Collin Gillespie | FREEAGENT | Rui Hachimura | +0.97 | +0.48 | +0.26 | AST, STL, 3PM, FT% | PTS, REB, BLK, FG%, TO |  |
| DeMar DeRozan | FREEAGENT | Rui Hachimura | +1.41 | +0.27 | +0.27 | PTS, AST, FT% | REB, 3PM, TO |  |
| Cam Spencer | FREEAGENT | Rui Hachimura | +0.42 | +0.48 | +0.06 | AST, FG%, FT% | PTS, REB, STL, BLK, 3PM, TO |  |
| Nic Claxton | FREEAGENT | Rui Hachimura | +1.04 | +0.21 | +0.25 | REB, AST, BLK, FG% | PTS, STL, 3PM, FT%, TO | small sample (1 GP) |
| Kris Dunn | WAIVERS | Rui Hachimura | +0.65 | +0.30 | +0.11 | AST, STL, BLK, FG%, FT% | PTS, REB, 3PM, TO |  |

Each pickup is paired with the drop that leaves my team strongest. Waiver claims process on Sundays (24h waivers).

## Assumptions and limits

- **Rates:** this season gets weight GP/(GP+12) (10 games → 45%, 20 → 63%, 40 → 77%). The rest comes from a prior = 60% ESPN 2026-27 projection + 40% last season (last season's share shrinks if he played under 40 games). FG% and FT% shrink by attempts (prior worth 150 FGA / 60 FTA). Last-15/30-day splits are reported as trends, not used in the rates, to avoid overreacting to 5-7 game samples.
- **Availability:** each player plays ESPN-projected GP/82 of remaining games (capped 60-95%; 85% if no projection). OUT players have no return date in the export, so they are assumed out for the rest of week 4 and week 5. OUT with zero games this season, and anyone in an IR slot, are not projected at all. DAY_TO_DAY = 75% for the rest of this week.
- **Kawhi Leonard (my IR):** not counted anywhere above. If he returned in week 8 at his blended rates and I dropped Norman Powell, the model adds +1.59 regular-season categories and +0.86 playoff categories. That is a scenario, not a forecast: the export has no return date.
- **Lineups:** every day the 10 slots are filled by position eligibility, best players first; bench players only count on days a slot is open. Opponents are assumed to set optimal lineups and keep their current rosters.
- **Week-to-week noise:** game-to-game variance from the game logs, scaled up where real weekly swings were larger. Categories are treated as independent when converting to matchup win odds.
- **Playoffs:** opponent = average of the five strongest other teams by projection (BBB, NYK, CAL, TT, BCn). ⚠️ Week 20-22 boundaries are derived, so games-per-team in those weeks may shift.
- **Trades:** Luka is never offered. OUT and IR players are left out of trades (no return dates). When I receive more players than I send, the weakest fit on my roster is cut; when I send more, I add the best free agent for my needs. Acceptance uses the partner's own category gain plus a value check; real managers may value players differently.
- **Small samples:** about 10 games into the season. Trends in the last 15 days are shown but not trusted on their own.
- **RotoWire rankings** are shown for reference only and are not used in any calculation.
