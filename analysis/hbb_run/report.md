# Lukawhi: rest-of-season analysis

Built from the ESPN export dated 2026-11-11 (scoring period 23, week 4 in progress). Re-run with `python3 analysis/run_analysis.py <export folder>`. All numbers come from the export only.

**Rate source for this run: Hashtag Basketball rest-of-season projections** (378 players matched; the rest use the blended ESPN rates). Injuries, schedule, lineups and variance are handled exactly as in the main run.

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

This week (week 4, vs NYX2, partly played): expected 4.9 categories, 67% chance to win the matchup.

Model outlook with the current roster: **5.46 categories per regular week**, **4.76 per playoff week** vs the likely playoff field (BBB, NYK, TT, CAL, LS). Playoff odds 100%, top-2 seed (bye) 99%, title 34%.

Season simulation (20,000 runs, current rosters):

| team | record | proj final cat wins | playoffs | top-2 seed | title |
|---|---|---|---|---|---|
| LK (Tyler) | 19-7-1 | 106 | 100% | 99% | 34% |
| BBB (Bryan) | 15-12-0 | 95 | 99% | 68% | 31% |
| TT (Eric) | 15-12-0 | 88 | 88% | 15% | 14% |
| NYK (Juno) | 8-19-0 | 84 | 65% | 4% | 6% |
| BCn (Andrew) | 14-12-1 | 85 | 72% | 5% | 5% |
| CAL (Calvin) | 7-19-1 | 81 | 48% | 2% | 4% |
| LS (Sam) | 10-17-0 | 82 | 51% | 2% | 4% |
| SS (Simon) | 15-12-0 | 85 | 69% | 5% | 3% |
| 76Er (Andy) | 15-12-0 | 74 | 5% | 0% | 0% |
| NYX2 (John) | 15-11-1 | 72 | 4% | 0% | 0% |

| category | rank wk1-3 | my avg/week | won in my matchups | all-play W-L-T | all-play win% | proj win% (my schedule) | proj win% (playoffs) | proj win% vs field | group |
|---|---|---|---|---|---|---|---|---|---|
| PTS | 5 | 668.300 | 1/3 | 17-10-0 | 63% | 54% | 38% | 56% | SWING |
| REB | 3 | 243.300 | 2/3 | 20-7-0 | 74% | 85% | 70% | 80% | LOCK |
| AST | 5 | 149.300 | 3/3 | 14-12-1 | 54% | 48% | 27% | 46% | SWING |
| STL | 2 | 46.000 | 3/3 | 17-7-3 | 69% | 70% | 63% | 68% | SWING |
| BLK | 3 | 28.300 | 3/3 | 20-7-0 | 74% | 60% | 47% | 60% | SWING |
| 3PM | 2 | 80.700 | 1/3 | 20-7-0 | 74% | 81% | 78% | 82% | LOCK |
| FG% | 2 | 0.479 | 2/3 | 20-7-0 | 74% | 52% | 48% | 55% | SWING |
| FT% | 6 | 0.791 | 2/3 | 15-12-0 | 56% | 30% | 30% | 29% | LOST CAUSE |
| TO | 5 | 79.300 | 2/3 | 17-8-2 | 67% | 66% | 75% | 66% | LOCK |

Groups use the average of the regular-season and playoff projections: LOCK ≥ 70%, LOST CAUSE ≤ 30%, otherwise SWING.

**Who we are:** a deep, balanced Luka team. Strongest categories: 3PM (80%), REB (77%), TO (71%); locks: REB, 3PM, TO. Weakest: FT% (30%), AST (37%); lost causes: FT%. The categories that move the most per unit of talent are **AST**, **PTS** and **BLK** (one good specialist ≈ +0.12, +0.10, +0.07 categories a week). **Aim for** players whose value comes from AST, PTS and BLK. **Avoid paying for** STL or 3PM specialists: the same quality of player adds only +0.04 / +0.05 a week there, because you already win them 67% / 80% of the time. Players who hurt FT% are acceptable if they bring AST or PTS: FT% is already your weakest category (30%), and an elite FT% specialist only moves it +0.07 a week, less than a specialist in AST (+0.12).

### Punt or stay balanced?

| strategy | moves | cats/reg week | cats/playoff week | matchup win % | still win punted cat |
|---|---|---|---|---|---|
| Current roster (no moves) |  | 5.46 | 4.76 | 74% |  |
| Balanced (best 2 waiver moves for all 9 cats) | add Kris Dunn / drop Kyshawn George; add Cam Spencer / drop Jrue Holiday | 5.53 | 5.18 | 76% |  |
| Punt PTS (best 2 waiver moves ignoring PTS) | add Kris Dunn / drop Norman Powell; add Cam Spencer / drop Jrue Holiday | 5.48 | 5.02 | 74% | 38% |
| Punt REB (best 2 waiver moves ignoring REB) | add Cam Spencer / drop Kyshawn George; add Kris Dunn / drop Jrue Holiday | 5.53 | 5.18 | 76% | 80% |
| Punt AST (best 2 waiver moves ignoring AST) | add Karlo Matkovic / drop Davion Mitchell; add Christian Braun / drop Kyshawn George | 5.40 | 4.76 | 73% | 20% |
| Punt STL (best 2 waiver moves ignoring STL) | add Cam Spencer / drop Kyshawn George; add Christian Braun / drop Jrue Holiday | 5.52 | 5.07 | 75% | 67% |
| Punt BLK (best 2 waiver moves ignoring BLK) | add Cam Spencer / drop Kyshawn George; add Kris Dunn / drop Jrue Holiday | 5.53 | 5.18 | 76% | 55% |
| Punt 3PM (best 2 waiver moves ignoring 3PM) | add Kris Dunn / drop Kyshawn George; add Nic Claxton / drop Jrue Holiday | 5.54 | 5.01 | 77% | 73% |
| Punt FG% (best 2 waiver moves ignoring FG%) | add Cam Spencer / drop Jrue Holiday; add Kris Dunn / drop Kyshawn George | 5.53 | 5.18 | 76% | 58% |
| Punt FT% (best 2 waiver moves ignoring FT%) | add Kris Dunn / drop Jrue Holiday; add Nic Claxton / drop Kyshawn George | 5.54 | 5.01 | 77% | 23% |
| Punt TO (best 2 waiver moves ignoring TO) | add Kris Dunn / drop Rui Hachimura; add Cam Spencer / drop Jrue Holiday | 5.50 | 5.05 | 75% | 66% |

Each strategy gets the same tools (the two best waiver moves), chosen to maximise that strategy's target categories; the columns then count all 9 categories honestly.

**Verdict: stay balanced.** No punt beats the balanced plan (best punt: Punt STL, 5.52 vs 5.53 categories a regular week and 5.07 vs 5.18 in the playoffs). Your swing categories are close enough that giving one away costs more than it frees up. (For REB, BLK, FG% the best 'punt' moves are the same as the balanced moves, so those aren't real punts.)

## Stats to target

| category | boost tested (≈ one good specialist) | extra cats / reg week | extra cats / playoff week | extra matchup wins ROS |
|---|---|---|---|---|
| AST | +7.1 AST per week | +0.120 | +0.110 | +0.41 |
| PTS | +18.9 PTS per week | +0.100 | +0.099 | +0.37 |
| BLK | +1.8 BLK per week | +0.074 | +0.072 | +0.26 |
| TO | -2.7 TO per week | +0.072 | +0.055 | +0.22 |
| FT% | +1.0 extra made FT on the same attempts per week | +0.065 | +0.061 | +0.19 |
| REB | +8.2 REB per week | +0.058 | +0.072 | +0.24 |
| FG% | +2.1 extra made FG on the same attempts per week | +0.056 | +0.056 | +0.18 |
| 3PM | +3.4 3PM per week | +0.049 | +0.054 | +0.21 |
| STL | +1.2 STL per week | +0.040 | +0.038 | +0.15 |

Boost = one standard deviation of that stat among the top 150 players, times 3.5 games a week.

**Focus on, in order:** 1. AST (+0.12/wk), 2. PTS (+0.10/wk), 3. BLK (+0.07/wk), 4. TO (+0.07/wk).

## Player rankings

Per-game values are rest-of-season blended rates. **z** = 9-cat value per game vs the top 150 players (FG%/FT% weighted by attempts). **ROS games** = remaining NBA games × availability. **VORP** = value above the 10th-best healthy free agent (z -1.76) × ROS games. **Cats vs best FA** = categories I'd lose (full simulation) if I swapped him for the best free agent for my team; near zero or negative = replaceable. **Playoff games** = NBA games in weeks 20-22 ⚠️ (derived week boundaries).

### My roster

| player | pos | GP | PTS | REB | AST | STL | BLK | 3PM | FG% | FT% | TO | z | ROS games | playoff games | VORP | cats vs best FA (reg) | cats vs best FA (playoffs) | best FA swap | RotoWire | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Luka Doncic | PG | 10 | 37.30 | 8.70 | 8.60 | 1.70 | 0.50 | 4.90 | 0.486 | 0.802 | 4.00 | 9.55 | 50 | 10 | 564 | +8.88 | +1.65 | Kris Dunn | 4 |  |
| Kawhi Leonard | SF/PF | 2 | 23.80 | 5.00 | 3.00 | 1.60 | 0.40 | 2.10 | 0.491 | 0.880 | 1.90 | 3.53 | 0 | 11 | 0 |  |  |  | 8 | on IR slot: not projected (no return date in data); OUT: assumed back after week 5 (no date in data); small sample (2 GP) |
| Karl-Anthony Towns | C | 10 | 20.30 | 12.20 | 3.40 | 0.90 | 0.60 | 1.60 | 0.511 | 0.808 | 2.40 | 2.55 | 52 | 10 | 223 | +2.88 | +0.54 | Kris Dunn | 14 |  |
| Evan Mobley | PF/C | 11 | 19.30 | 9.60 | 3.60 | 0.80 | 1.80 | 1.10 | 0.547 | 0.660 | 2.10 | 1.78 | 48 | 9 | 170 | +2.85 | +0.04 | Kris Dunn | 30 |  |
| OG Anunoby | SF/PF | 10 | 16.70 | 4.80 | 2.10 | 1.50 | 0.80 | 2.20 | 0.480 | 0.833 | 1.50 | 1.48 | 51 | 10 | 164 | +1.02 | -0.11 | Kris Dunn | 37 |  |
| Dyson Daniels | PG/SG | 12 | 10.60 | 6.70 | 4.30 | 2.40 | 0.60 | 0.60 | 0.465 | 0.600 | 1.60 | 1.10 | 56 | 11 | 159 | +0.68 | +0.35 | Kris Dunn | 35 |  |
| Donovan Clingan | C | 10 | 11.40 | 11.40 | 1.90 | 0.60 | 1.80 | 1.10 | 0.524 | 0.667 | 1.30 | 0.94 | 55 | 10 | 149 | +2.36 | +0.29 | Kris Dunn | 18 |  |
| Brandin Podziemski | PG/SG | 9 | 15.10 | 5.90 | 4.20 | 1.30 | 0.20 | 2.20 | 0.454 | 0.778 | 1.60 | -0.28 | 57 | 11 | 85 | +0.21 | +0.29 | Kris Dunn | 93 |  |
| Jabari Smith Jr. | PF/C | 11 | 16.30 | 7.50 | 1.60 | 0.70 | 0.90 | 2.20 | 0.469 | 0.778 | 1.30 | -0.34 | 54 | 10 | 77 | +1.35 | -0.05 | Kris Dunn |  |  |
| Norman Powell | SG/SF | 8 | 20.90 | 3.20 | 2.20 | 1.10 | 0.20 | 2.70 | 0.473 | 0.830 | 1.80 | -0.65 | 47 | 10 | 52 | -0.04 | -0.13 | Kris Dunn | 72 | OUT: assumed back after week 5 (no date in data) |
| Payton Pritchard | PG/SG | 11 | 15.60 | 3.20 | 4.30 | 0.80 | 0.20 | 2.90 | 0.463 | 0.857 | 1.20 | -0.85 | 54 | 11 | 49 | +0.90 | +0.07 | Kris Dunn | 141 |  |
| Davion Mitchell | PG | 11 | 14.00 | 3.00 | 7.30 | 1.20 | 0.20 | 1.70 | 0.487 | 0.692 | 2.00 | -1.12 | 53 | 10 | 34 | +0.34 | -0.00 | Kris Dunn | 130 | minutes up (+5 last 15d) |
| Rui Hachimura | SF/PF | 8 | 15.60 | 5.40 | 1.20 | 0.80 | 0.40 | 1.90 | 0.485 | 0.733 | 0.70 | -1.57 | 54 | 11 | 11 | -0.34 | -0.25 | Kris Dunn | 126 |  |
| Jrue Holiday | PG/SG | 10 | 12.80 | 4.20 | 4.60 | 1.00 | 0.30 | 2.00 | 0.443 | 0.867 | 1.80 | -1.96 | 51 | 10 | 0 | -1.14 | -0.46 | Kris Dunn | 102 |  |
| Kyshawn George | SG/SF | 11 | 11.90 | 4.90 | 3.50 | 1.10 | 0.90 | 2.00 | 0.408 | 0.762 | 2.00 | -2.37 | 49 | 10 | 0 | -0.76 | -0.60 | Kris Dunn | 119 |  |

### Top available players (free agents / waivers)

| player | status | pos | GP | PTS | REB | AST | STL | BLK | 3PM | FG% | FT% | TO | z | RotoWire | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Kris Dunn | WAIVERS | PG/SG | 10 | 8.30 | 3.90 | 4.50 | 2.00 | 0.50 | 1.30 | 0.485 | 0.750 | 1.40 | 0.41 | 144 |  |
| Jalen Williams | FREEAGENT | SF/PF | 3 | 17.10 | 4.40 | 4.60 | 1.30 | 0.50 | 1.30 | 0.471 | 0.784 | 1.80 | -0.64 | 266 | OUT; OUT: assumed back after week 5 (no date in data); small sample (3 GP) |
| Charles Bassey | FREEAGENT | C | 9 | 10.00 | 8.00 | 0.90 | 0.70 | 1.60 | 0.00 | 0.603 | 0.774 | 1.10 | -0.72 | 340 |  |
| Cason Wallace | FREEAGENT | PG/SG | 3 | 8.90 | 3.40 | 2.70 | 1.90 | 0.50 | 1.30 | 0.455 | 0.750 | 1.00 | -0.75 | 278 | OUT; OUT: assumed back after week 5 (no date in data); small sample (3 GP) |
| Paul Reed | FREEAGENT | PF/C | 10 | 10.00 | 5.60 | 1.70 | 1.30 | 1.00 | 0.30 | 0.586 | 0.714 | 1.10 | -0.88 | 149 | minutes up (+8 last 15d) |
| Christian Braun | FREEAGENT | SG/SF | 9 | 13.80 | 4.90 | 2.60 | 0.90 | 0.40 | 1.00 | 0.558 | 0.800 | 1.00 | -0.94 | 78 |  |
| Alex Caruso | FREEAGENT | PG/SG | 8 | 8.60 | 3.70 | 2.90 | 1.60 | 0.60 | 1.30 | 0.431 | 0.833 | 1.00 | -1.25 | 51 |  |
| Aaron Nesmith | FREEAGENT | SG/SF | 9 | 14.50 | 4.60 | 1.80 | 0.80 | 0.50 | 2.40 | 0.459 | 0.875 | 1.30 | -1.43 | 138 |  |
| Mitchell Robinson | FREEAGENT | C | 10 | 6.70 | 8.50 | 1.00 | 1.10 | 1.40 | 0.00 | 0.707 | 0.474 | 0.80 | -1.44 | 172 |  |
| Cam Spencer | FREEAGENT | PG/SG | 10 | 11.10 | 2.60 | 5.30 | 0.80 | 0.20 | 2.00 | 0.462 | 0.947 | 1.20 | -1.58 | 250 |  |
| Obi Toppin | FREEAGENT | PF | 8 | 13.70 | 5.20 | 2.30 | 0.70 | 0.40 | 1.80 | 0.520 | 0.800 | 1.20 | -1.59 | 175 |  |
| Robert Williams III | FREEAGENT | C | 8 | 6.50 | 6.80 | 1.00 | 0.60 | 1.50 | 0.10 | 0.690 | 0.667 | 0.80 | -1.76 |  |  |
| Devin Vassell | FREEAGENT | SG/SF | 10 | 13.40 | 3.60 | 2.40 | 1.00 | 0.40 | 2.20 | 0.441 | 0.824 | 1.00 | -2.01 | 95 | OUT; OUT: assumed back after week 5 (no date in data) |
| Ziaire Williams | FREEAGENT | SG/SF | 9 | 11.20 | 3.90 | 1.30 | 1.30 | 0.50 | 1.80 | 0.451 | 0.800 | 1.20 | -2.22 | 262 |  |
| Isaiah Jackson | FREEAGENT | PF/C | 9 | 9.50 | 7.50 | 1.40 | 0.90 | 1.30 | 0.00 | 0.629 | 0.643 | 1.50 | -2.27 | 185 |  |
| Collin Gillespie | FREEAGENT | PG | 10 | 10.70 | 3.60 | 4.00 | 1.10 | 0.20 | 2.40 | 0.420 | 0.800 | 1.30 | -2.30 | 74 |  |
| Santi Aldama | FREEAGENT | SF/PF | 3 | 13.20 | 5.10 | 2.90 | 0.80 | 0.60 | 1.80 | 0.486 | 0.650 | 1.20 | -2.33 | 174 | small sample (3 GP); minutes down (-8 last 15d) |
| Draymond Green | FREEAGENT | PF/C | 9 | 8.90 | 6.00 | 5.70 | 1.20 | 0.90 | 1.40 | 0.421 | 0.706 | 2.70 | -2.37 | 143 |  |
| Khaman Maluach | FREEAGENT | C | 10 | 8.70 | 7.80 | 0.60 | 0.50 | 1.70 | 0.30 | 0.545 | 0.706 | 1.40 | -2.52 | 176 |  |
| Meleek Thomas | FREEAGENT | SG | 8 | 11.50 | 2.10 | 1.40 | 0.80 | 0.10 | 3.20 | 0.449 | 0.875 | 0.60 | -2.52 | 269 |  |

## Trade recommendations

### Other teams at a glance

| team | record | proj cats/wk vs field | strong | weak | surplus (trade value they need least) |
|---|---|---|---|---|---|
| BBB (Bryan) | 15-12-0 | 5.00 | REB, BLK, AST, STL | 3PM, TO | Anthony Davis, Walker Kessler, Cooper Flagg |
| NYK (Juno) | 8-19-0 | 4.85 | AST, REB, STL, PTS, BLK | 3PM, FT%, TO, FG% | LeBron James, Fred VanVleet, Jalen Johnson |
| TT (Eric) | 15-12-0 | 4.72 | PTS, BLK | TO, AST, STL | Joel Embiid, Zach Edey, Austin Reaves |
| CAL (Calvin) | 7-19-1 | 4.59 | 3PM, TO, FT% | STL, BLK, PTS | Alex Sarr, Grayson Allen, Nikola Jokic |
| LS (Sam) | 10-17-0 | 4.52 | AST, TO, FG%, 3PM, FT% | REB, BLK | Kyrie Irving, Ausar Thompson, Zach LaVine |
| BCn (Andrew) | 14-12-1 | 4.43 | 3PM, FT%, PTS | FG%, STL, AST | Neemias Queta, Tari Eason, Brandon Miller |
| SS (Simon) | 15-12-0 | 4.32 | REB, FG%, PTS | AST, 3PM | Jarrett Allen, Shai Gilgeous-Alexander, Bam Adebayo |
| 76Er (Andy) | 15-12-0 | 3.73 | TO | BLK, PTS, REB, AST | Moussa Diabate, Zion Williamson, VJ Edgecombe |
| NYX2 (John) | 15-11-1 | 3.42 | FT% | REB, 3PM, PTS, STL | Josh Hart, Victor Wembanyama, Devin Booker |

1443 trade ideas passed the quick screen; the best 555 were fully simulated (251 help me and look acceptable to the other side). All of them are in trades_evaluated.csv.

**Trades are measured after the free first move: add Kris Dunn, drop Kyshawn George** (see Free-agent moves). So every gain below is on top of that pickup. Title odds after the pickup alone: 39%.

The 15 best acceptable trades by category score were each run through the full season simulation; the five below have the biggest title-odds gain, rounded to the nearest point; differences under about 1 point are simulation noise, so ties are ordered by category score (trade_shortlist_with_title_odds.csv has all 15).

**Score** = extra categories over the remaining regular season + 3 × extra categories in playoff weeks 20-22. **Their gain** = change in their expected categories per week vs the whole league (their own needs). **Acceptable** = value ratio ≥ 0.85 and they lose no more than 0.05 categories a week, or they gain 0.10+ a week with ratio ≥ 0.75. **Value ratio** = trade value they receive ÷ value they give, where trade value = (value above replacement)^1.5 × games (so one star is worth more than two average players); ≥ 0.9 is roughly even.

### 1. Give Dyson Daniels + OG Anunoby → get Cooper Flagg (BBB (Bryan))

- **Me:** +2.28 categories over the regular season, +1.69 over playoff weeks, +0.46 expected matchup wins. Title odds 39% → 61%.
- **Categories that move for me:** up PTS, AST, 3PM, FT%; down REB, STL, BLK, TO.
- **Them:** +0.03 categories per week vs the league (up STL, 3PM, FT%, TO; down PTS, REB, BLK); value ratio 0.87. Their playoff odds 99% → 99%, title odds 29% → 16%.
- **Roster:** I add Cam Spencer from waivers; they drop Rudy Gobert.
- **Risks:** no injury flags; normal projection uncertainty.
- **Pitch:** "You'd get two starters (Dyson Daniels and OG Anunoby) for Cooper Flagg. It fixes your 3PM, TO and adds STL, FT%. By my numbers your team comes out ahead in weekly categories. Interested?"

### 2. Give Dyson Daniels + Jrue Holiday → get Devin Booker (NYX2 (John))

- **Me:** +2.91 categories over the regular season, +1.31 over playoff weeks, +0.74 expected matchup wins. Title odds 39% → 56%.
- **Categories that move for me:** up PTS, AST, 3PM, FT%; down REB, STL, BLK, TO.
- **Them:** +0.07 categories per week vs the league (up REB, STL, BLK, TO; down PTS, AST, 3PM, FT%); value ratio 1.59. Their playoff odds 4% → 5%, title odds 0% → 0%.
- **Roster:** I add Cam Spencer from waivers; they drop Jonathan Kuminga.
- **Risks:** no injury flags; normal projection uncertainty.
- **Pitch:** "You'd get two starters (Dyson Daniels and Jrue Holiday) for Devin Booker. It fixes your REB, STL and adds BLK, TO. By my numbers your team comes out ahead in weekly categories. Interested?"

### 3. Give OG Anunoby + Jrue Holiday → get Franz Wagner (BBB (Bryan))

- **Me:** +1.08 categories over the regular season, +1.20 over playoff weeks, +0.21 expected matchup wins. Title odds 39% → 54%.
- **Categories that move for me:** up PTS, AST, FT%; down STL, BLK, 3PM.
- **Them:** +0.08 categories per week vs the league (up AST, STL, 3PM, FT%; down PTS, REB, BLK); value ratio 1.12. Their playoff odds 99% → 100%, title odds 29% → 23%.
- **Roster:** I add Cam Spencer from waivers; they drop Rudy Gobert.
- **Risks:** no injury flags; normal projection uncertainty.
- **Pitch:** "You'd get two starters (OG Anunoby and Jrue Holiday) for Franz Wagner. It fixes your 3PM and adds AST, STL. By my numbers your team comes out ahead in weekly categories. Interested?"

### 4. Give OG Anunoby + Jrue Holiday → get Jaylen Brown (SS (Simon))

- **Me:** +0.71 categories over the regular season, +0.95 over playoff weeks, +0.36 expected matchup wins. Title odds 39% → 53%.
- **Categories that move for me:** up PTS, REB, AST, FG%; down STL, BLK, FT%, TO.
- **Them:** +0.17 categories per week vs the league (up AST, STL, BLK, 3PM, FT%, TO; down PTS, REB, FG%); value ratio 5.06. Their playoff odds 70% → 85%, title odds 2% → 3%.
- **Roster:** I add Cam Spencer from waivers; they drop Kyle Kuzma.
- **Risks:** no injury flags; normal projection uncertainty.
- **Pitch:** "You'd get two starters (OG Anunoby and Jrue Holiday) for Jaylen Brown. It fixes your AST, 3PM and adds STL, BLK. By my numbers your team comes out ahead in weekly categories. Interested?"

### 5. Give OG Anunoby + Jrue Holiday → get Yaxel Lendeborg (TT (Eric))

- **Me:** +1.52 categories over the regular season, +1.30 over playoff weeks, +0.35 expected matchup wins. Title odds 39% → 52%.
- **Categories that move for me:** up PTS, REB, AST; down STL, 3PM.
- **Them:** -0.03 categories per week vs the league (up 3PM, FG%, FT%, TO; down PTS, REB, AST, BLK); value ratio 1.09. Their playoff odds 89% → 88%, title odds 13% → 7%.
- **Roster:** I add Cam Spencer from waivers; they drop Jeremiah Fears.
- **Risks:** no injury flags; normal projection uncertainty.
- **Pitch:** "You'd get two starters (OG Anunoby and Jrue Holiday) for Yaxel Lendeborg. It fixes your TO and adds 3PM, FG%. By my numbers your team comes out ahead in weekly categories. Interested?"

## Free-agent moves

| add | status | drop | reg cats | playoff cats | matchup wins | cats up | cats down | notes |
|---|---|---|---|---|---|---|---|---|
| Kris Dunn | WAIVERS | Kyshawn George | +0.76 | +0.60 | +0.11 | AST, STL, FG%, TO | PTS, REB, BLK, 3PM |  |
| Cam Spencer | FREEAGENT | Jrue Holiday | +0.38 | +0.63 | +0.10 | AST, FG%, FT%, TO | PTS, REB, STL, BLK |  |
| Collin Gillespie | FREEAGENT | Kyshawn George | +0.22 | +0.43 | +0.05 | AST, 3PM, FG%, TO | REB, BLK |  |
| Christian Braun | FREEAGENT | Kyshawn George | +0.44 | +0.30 | +0.01 | PTS, FG%, FT%, TO | AST, STL, BLK, 3PM |  |
| Nic Claxton | FREEAGENT | Kyshawn George | +0.26 | +0.12 | +0.04 | REB, BLK, FG%, TO | PTS, STL, 3PM, FT% | small sample (1 GP) |

Each pickup is paired with the drop that leaves my team strongest. Waiver claims process on Sundays (24h waivers).

## Assumptions and limits

- **Rates:** this season gets weight GP/(GP+12) (10 games → 45%, 20 → 63%, 40 → 77%). The rest comes from a prior = 60% ESPN 2026-27 projection + 40% last season (last season's share shrinks if he played under 40 games). FG% and FT% shrink by attempts (prior worth 150 FGA / 60 FTA). Last-15/30-day splits are reported as trends, not used in the rates, to avoid overreacting to 5-7 game samples.
- **Availability:** each player plays ESPN-projected GP/82 of remaining games (capped 60-95%; 85% if no projection). OUT players have no return date in the export, so they are assumed out for the rest of week 4 and week 5. OUT with zero games this season, and anyone in an IR slot, are not projected at all. DAY_TO_DAY = 75% for the rest of this week.
- **Kawhi Leonard (my IR):** not counted anywhere above. If he returned in week 8 at his blended rates and I dropped Jrue Holiday, the model adds +0.44 regular-season categories and +0.71 playoff categories. That is a scenario, not a forecast: the export has no return date.
- **Lineups:** every day the 10 slots are filled by position eligibility, best players first; bench players only count on days a slot is open. Opponents are assumed to set optimal lineups and keep their current rosters.
- **Week-to-week noise:** game-to-game variance from the game logs, scaled up where real weekly swings were larger. Categories are treated as independent when converting to matchup win odds.
- **Playoffs:** opponent = average of the five strongest other teams by projection (BBB, NYK, TT, CAL, LS). ⚠️ Week 20-22 boundaries are derived, so games-per-team in those weeks may shift.
- **Trades:** Luka is never offered. OUT and IR players are left out of trades (no return dates). When I receive more players than I send, the weakest fit on my roster is cut; when I send more, I add the best free agent for my needs. Acceptance uses the partner's own category gain plus a value check; real managers may value players differently.
- **Small samples:** about 10 games into the season. Trends in the last 15 days are shown but not trusted on their own.
- **RotoWire rankings** are shown for reference only and are not used in any calculation.
