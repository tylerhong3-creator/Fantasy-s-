# Lukawhi analysis

How to refresh after a new ESPN export:

1. Unzip the export into the repo root (a folder like `espn_fantasy_2026-27_YYYY-MM-DD/`).
2. From the repo root run: `python3 analysis/run_analysis.py espn_fantasy_2026-27_YYYY-MM-DD`
   (with no argument it uses `espn_fantasy_2026-27_2026-11-11`). Takes about 40 seconds. Needs Python 3 with numpy and pandas.
3. Read `analysis/report.md`.

Files:
- `fantasy.py`: loading, data checks, per-game rates, z-scores, daily lineup simulator, variance model.
- `season.py`: weekly win odds against each opponent, playoff/title simulation, quick trade screening.
- `run_analysis.py`: runs everything and writes the report and CSVs.
- `report.md`: the write-up.
- `player_values.csv`: every player's blended rates, z-scores, rest-of-season value.
- `my_category_win_probs_by_week.csv`: my chance to win each category, every remaining week.
- `trades_evaluated.csv`, `trade_shortlist_with_title_odds.csv`: every simulated trade.
- `free_agent_moves_evaluated.csv`, `punt_vs_balanced.csv`, `stats_to_target.csv`, `my_category_identity.csv`,
  `playoff_odds_baseline.csv`, `data_checks.csv`: supporting tables.
- `rotowire/`: put the RotoWire rankings file here as `overall-rankings_4.xlsx` (reference column only; not committed).

Hashtag Basketball cross-check (optional):
- Put the HBB supplement at `analysis/hbb/HBB_supplement_Lukawhi_<date>.xlsx` (not committed).
- `python3 analysis/run_analysis.py --hbb analysis/hbb/<file>.xlsx --out analysis/hbb_run` runs the whole model with HBB's projections.
- `python3 analysis/hbb_crosscheck.py <export folder> analysis/hbb/<file>.xlsx` scores every move under both projections and writes `analysis/moves_report.md`.
- `python3 analysis/team_breakdown.py` (after hbb_crosscheck.py) writes `analysis/team_breakdown.md`: player ratings out of 10, sell-high trade search, category rank breakdown.
