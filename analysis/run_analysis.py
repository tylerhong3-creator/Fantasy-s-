"""Run the full Lukawhi analysis and write ./analysis/report.md plus CSV tables.

Usage (from the repo root):   python3 analysis/run_analysis.py [path/to/export_folder]
Default export folder: ./espn_fantasy_2026-27_2026-11-11
"""
import itertools
import math
import os
import sys
import time

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from fantasy import (CATS, COUNT_CATS, SI, STATS, MY_TEAM_ID, PLAYOFF_PERIODS, PLAYOFF_WEIGHT, K_GAMES,
                     FG_PRIOR_ATT, FT_PRIOR_ATT, PRIOR_PROJ_W, OUT_PERIODS, DTD_AVAIL, DEFAULT_HEALTH,
                     Data, Model, blend_rates, zscores, estimate_dispersion, calibrate,
                     check_logs_vs_matchups, matchup_win_prob)
from season import Season

T0 = time.time()
args = sys.argv[1:]
HBB = None
OUT = HERE
if '--hbb' in args:                       # use Hashtag Basketball ROS projections as the per-game rates
    i = args.index('--hbb'); HBB = args[i + 1]; del args[i:i + 2]
if '--out' in args:
    i = args.index('--out'); OUT = args[i + 1]; del args[i:i + 2]
os.makedirs(OUT, exist_ok=True)
FOLDER = args[0] if args else os.path.join(os.path.dirname(HERE), 'espn_fantasy_2026-27_2026-11-11')
LUKA = 'Luka Doncic'


def log(*a):
    print(f'[{time.time() - T0:6.1f}s]', *a, flush=True)


def f1(x, n=1):
    return f'{x:+.{n}f}'


def md_table(df, floatfmt=None):
    cols = list(df.columns)
    lines = ['| ' + ' | '.join(str(c) for c in cols) + ' |', '|' + '|'.join('---' for _ in cols) + '|']
    for _, r in df.iterrows():
        cells = []
        for c in cols:
            v = r[c]
            if isinstance(v, float):
                fmt = (floatfmt or {}).get(c, '{:.2f}')
                cells.append(fmt.format(v) if not math.isnan(v) else '')
            else:
                cells.append(str(v))
        lines.append('| ' + ' | '.join(cells) + ' |')
    return '\n'.join(lines)


# =============================================================================== load
d = Data(FOLDER)
ab = d.abbrev
owner = {t['team_id']: t['owner'].split()[0] for t in d.league['teams']}   # first names only
tname = lambda t: f"{ab[t]} ({owner[t]})"
log('loaded', FOLDER)

checks = check_logs_vs_matchups(d)
checks.to_csv(os.path.join(OUT, 'data_checks.csv'), index=False)
n_bad = int((~checks.ok).sum())
log('log-vs-matchup mismatches:', n_bad)

rates = blend_rates(d)
if HBB:
    from fantasy import apply_hbb_rates
    rates = apply_hbb_rates(rates, HBB)
    log('HBB rates applied to', rates.attrs['hbb_matched'], 'players')
Z = zscores(rates)
m = Model(d, Z)
m.disp = estimate_dispersion(d, m)
m.calib, calib_tab = calibrate(d, m)
S = Season(m)
strong, ap_base = S.set_strong()
log('model ready; playoff field =', [ab[t] for t in strong])

# RotoWire reference (not used in any calculation)
rw = {}
rw_path = os.path.join(HERE, 'rotowire', 'overall-rankings_4.xlsx')
if os.path.exists(rw_path):
    try:
        import openpyxl
        ws = openpyxl.load_workbook(rw_path, read_only=True).worksheets[0]
        for r in ws.iter_rows(values_only=True):
            if r and isinstance(r[0], int) and r[2]:
                rw[str(r[2]).replace('.', '').lower()] = r[0]
    except Exception as e:  # reference only
        log('rotowire file not read:', e)
rw_rank = lambda name: rw.get(name.replace('.', '').lower(), '')

# =============================================================================== player values
ROSTERED = {pid for tid in d.teams for pid in S.base[tid]}
pid_by_name = {r['name']: pid for pid, r in m.Z.iterrows()}
name = lambda pid: m.Z.loc[pid, 'name']
fut = [mp for mp in d.future_periods]


def ros_games(pid):
    return sum(S.games(pid, mp) * m.avail[pid][mp] for mp in fut)


Z = m.Z
Z['ros_games'] = [ros_games(p) for p in Z.index]
Z['ros_value'] = Z.z_total * Z.ros_games
weeks_left = len(fut)
Z['value_per_week'] = Z.ros_value / weeks_left
healthy_fa = Z[(Z.fantasy_team_id == 0) & (Z.injury_status != 'OUT') & (Z.ros_games > 20)].sort_values('z_total', ascending=False)
REPL = float(healthy_fa.z_total.iloc[9])      # 10th-best healthy free agent = replacement level
Z['vorp'] = np.maximum(0, Z.z_total - REPL) * Z.ros_games
# trade value: convex in per-game value so one star is worth more than two average players
TV_EXP = 1.5
Z['trade_value'] = np.maximum(0, Z.z_total - REPL) ** TV_EXP * Z.ros_games / 10
Z['playoff_games'] = [sum(S.games(p, mp) for mp in PLAYOFF_PERIODS) for p in Z.index]
Z['FG%'] = Z.r_FGM / Z.r_FGA
Z['FT%'] = (Z.r_FTM / Z.r_FTA).fillna(0)
Z['rotowire_ros_rank'] = [rw_rank(n) for n in Z.name]
Z['value_rank'] = Z.z_total.rank(ascending=False).astype(int)
pv_cols = ['value_rank', 'name', 'fantasy_team', 'roster_status', 'lineup_slot', 'pro_team', 'eligible_pos', 'injury_status',
           's27_GP', 'w_s27', 'prior_src', 'health', 'r_MIN', 'r_PTS', 'r_REB', 'r_AST', 'r_STL', 'r_BLK', 'r_3PM',
           'FG%', 'r_FGA', 'FT%', 'r_FTA', 'r_TO'] + ['z_' + c for c in CATS] + \
          ['z_total', 'ros_games', 'ros_value', 'value_per_week', 'vorp', 'trade_value', 'playoff_games', 'espn_rank_season', 'rotowire_ros_rank', 'trend', 'flags']
Z.sort_values('z_total', ascending=False)[pv_cols].to_csv(os.path.join(OUT, 'player_values.csv'), index=False, float_format='%.3f')
log('player values written; replacement z =', round(REPL, 2))

# =============================================================================== baseline
base = S.my_eval()
mc_base = S.monte_carlo()
my_roster = list(S.base[MY_TEAM_ID])
pre_fa_roster = list(my_roster)
pre_fa_base, pre_fa_mc = base, mc_base
log('baseline: reg cats', round(base['reg_cats'], 2), 'po cats', round(base['po_cats'], 2))
pp = pd.DataFrame(base['per_period'])
pp.to_csv(os.path.join(OUT, 'my_category_win_probs_by_week.csv'), index=False, float_format='%.3f')

# =============================================================================== identity
M = d.matchups[d.matchups.status == 'final']
mine = M[M.fantasy_team_id == MY_TEAM_ID]
h2h = {c: (mine['won_' + c] == 'W').sum() for c in CATS}
h2h_t = {c: (mine['won_' + c] == 'T').sum() for c in CATS}
allp = {c: [0, 0, 0] for c in CATS}
for mp, g in M.groupby('matchup_period'):
    me = g[g.fantasy_team_id == MY_TEAM_ID].iloc[0]
    for _, o in g[g.fantasy_team_id != MY_TEAM_ID].iterrows():
        for c in CATS:
            a, b = me[c], o[c]
            if c in ('FG%', 'FT%'):
                a = me['FGM'] / me['FGA'] if c == 'FG%' else me['FTM'] / me['FTA']
                b = o['FGM'] / o['FGA'] if c == 'FG%' else o['FTM'] / o['FTA']
            if a == b:
                allp[c][2] += 1
            elif (a > b) != (c == 'TO'):
                allp[c][0] += 1
            else:
                allp[c][1] += 1
SUM = d.summary.set_index('fantasy_team_id')
ap_me = S.allplay(MY_TEAM_ID)
reg_n, po_n = base['reg_weeks'], base['po_weeks']
ident = []
for c in CATS:
    preg = pre_fa_base['cat_reg'][c] / reg_n
    ppo = pre_fa_base['cat_po'][c] / po_n
    w, l, t = allp[c]
    act = (w + 0.5 * t) / (w + l + t)
    blend = 0.5 * preg + 0.5 * ppo
    grp = 'LOCK' if blend >= 0.70 else ('LOST CAUSE' if blend <= 0.30 else 'SWING')
    ident.append(dict(category=c, league_rank_wk1_3=int(SUM.loc[MY_TEAM_ID, 'rank_' + c]),
                      avg_week=SUM.loc[MY_TEAM_ID, 'avg_week_' + c], my_h2h_wins_wk1_3=f"{h2h[c]}/{len(mine)}",
                      allplay_wk1_3=f"{w}-{l}-{t}", allplay_win_pct=act, proj_win_reg=preg, proj_win_playoffs=ppo,
                      proj_vs_field=ap_me['cat'][c], group=grp))
ident = pd.DataFrame(ident)
log('identity done')

# ---- stats to target: add one good player's worth of a single stat
pool = Z.sort_values('z_total', ascending=False).head(150)
GPW = 3.5
units = {}
for c in COUNT_CATS:
    units[c] = pool['r_' + c].std() * GPW
units['FG%'] = pool.imp_FG.std() * GPW
units['FT%'] = pool.imp_FT.std() * GPW
target_rows = []
for c in CATS:
    b = np.zeros(len(STATS))
    if c in COUNT_CATS:
        b[SI[c]] = units[c] * (-1 if c == 'TO' else 1)
        label = f"{'-' if c == 'TO' else '+'}{units[c]:.1f} {c} per week"
    elif c == 'FG%':
        b[SI['FGM']] = units[c]
        label = f'+{units[c]:.1f} extra made FG on the same attempts per week'
    else:
        b[SI['FTM']] = units[c]
        label = f'+{units[c]:.1f} extra made FT on the same attempts per week'
    e = S.my_eval(bonus=b)
    nreg = reg_n - 1
    target_rows.append(dict(category=c, boost=label,
                            extra_cats_per_reg_week=(e['reg_cats'] - base['reg_cats']) / nreg,
                            extra_cats_per_playoff_week=(e['po_cats'] - base['po_cats']) / po_n,
                            extra_matchup_wins_ros=e['reg_mwins'] - base['reg_mwins'],
                            score_gain=e['score'] - base['score']))
targets = pd.DataFrame(target_rows).sort_values('score_gain', ascending=False)
log('stat targets done')

# =============================================================================== helpers for moves
fa_pool = Z[(Z.fantasy_team_id == 0) & (Z.ros_games > 5) & (~Z['flags'].str.contains('not projected'))]
fa_ids = list(fa_pool.sort_values('z_total', ascending=False).index)


def best_fa_for(tid, roster, k=1):
    """Highest-value healthy free agents by z (used to refill a roster spot)."""
    return [p for p in fa_ids if p not in roster][:k]


def eval_me(new_roster, override=None):
    ov = dict(override or {})
    ov[MY_TEAM_ID] = new_roster
    return S.my_eval(ov)


def summarize(e):
    return dict(reg_cats=e['reg_cats'] - base['reg_cats'], po_cats=e['po_cats'] - base['po_cats'],
                mwins=e['reg_mwins'] - base['reg_mwins'], score=e['score'] - base['score'],
                cat_moves={c: (e['cat_reg'][c] - base['cat_reg'][c]) + (e['cat_po'][c] - base['cat_po'][c]) for c in CATS})


# =============================================================================== punt vs balanced
G_full = S.gradient(MY_TEAM_ID)
droppable = [p for p in my_roster if name(p) != LUKA and m.avail[p][max(fut)] > 0 or (p in my_roster and m.Z.loc[p, 'injury_status'] == 'OUT' and name(p) != LUKA)]
droppable = [p for p in my_roster if name(p) != LUKA and m.Z.loc[p, 'lineup_slot'] != 'IR']


def greedy_swaps(exclude=(), n_swaps=2, n_fa=25):
    roster = list(my_roster)
    moves = []
    cur = S.my_eval({MY_TEAM_ID: roster}, exclude=exclude)
    for _ in range(n_swaps):
        G = S.gradient(MY_TEAM_ID, exclude=exclude, override={MY_TEAM_ID: roster})
        cands = sorted([p for p in fa_ids if p not in roster], key=lambda p: -S.lin_value(p, G))[:n_fa]
        best = None
        for a in cands:
            for dr in [p for p in roster if name(p) != LUKA and m.Z.loc[p, 'lineup_slot'] != 'IR']:
                nr = [p for p in roster if p != dr] + [a]
                e = S.my_eval({MY_TEAM_ID: nr}, exclude=exclude)
                if best is None or e['score_ex'] > best[0]['score_ex']:
                    best = (e, a, dr, nr)
        if best is None or best[0]['score_ex'] <= cur['score_ex'] + 1e-6:
            break
        cur, roster = best[0], best[3]
        moves.append(f"add {name(best[1])} / drop {name(best[2])}")
    return cur, moves


strat = []
e0 = base
strat.append(dict(strategy='Current roster (no moves)', moves='', exp_cats_per_reg_week=e0['reg_cats'] / reg_n,
                  exp_cats_per_playoff_week=e0['po_cats'] / po_n, matchup_win_pct=e0['reg_mwins'] / reg_n))
eb, mv = greedy_swaps()
strat.append(dict(strategy='Balanced (best 2 waiver moves for all 9 cats)', moves='; '.join(mv),
                  exp_cats_per_reg_week=eb['reg_cats'] / reg_n, exp_cats_per_playoff_week=eb['po_cats'] / po_n,
                  matchup_win_pct=eb['reg_mwins'] / reg_n))
for c in CATS:
    ep, mv = greedy_swaps(exclude=(c,))
    strat.append(dict(strategy=f'Punt {c} (best 2 waiver moves ignoring {c})', moves='; '.join(mv),
                      exp_cats_per_reg_week=ep['reg_cats'] / reg_n, exp_cats_per_playoff_week=ep['po_cats'] / po_n,
                      matchup_win_pct=ep['reg_mwins'] / reg_n,
                      punted_cat_win_pct=ep['cat_reg'][c] / reg_n))
strat = pd.DataFrame(strat)
log('punt analysis done')

# =============================================================================== my player fit (drop-only)
fit = {}
top_fa = sorted(fa_ids, key=lambda p: -S.lin_value(p, G_full))[:15]
for p in my_roster:
    if m.Z.loc[p, 'lineup_slot'] == 'IR':
        fit[p] = (float('nan'), float('nan'), '')
        continue
    best = None
    for a in top_fa:
        s_ = summarize(eval_me([q for q in my_roster if q != p] + [a]))
        if best is None or s_['score'] > best[0]['score']:
            best = (s_, a)
    fit[p] = (-best[0]['reg_cats'], -best[0]['po_cats'], name(best[1]))

# FA best-add delta
fa_eval = []
cands = sorted(fa_ids, key=lambda p: -S.lin_value(p, G_full))[:60]
for a in cands:
    best = None
    for dr in droppable:
        nr = [p for p in my_roster if p != dr] + [a]
        s_ = summarize(eval_me(nr))
        if best is None or s_['score'] > best[1]['score']:
            best = (dr, s_)
    fa_eval.append(dict(add=name(a), drop=name(best[0]), add_id=a, **{k: v for k, v in best[1].items() if k != 'cat_moves'},
                        cats_up=', '.join(c for c, v in best[1]['cat_moves'].items() if v > 0.15),
                        cats_down=', '.join(c for c, v in best[1]['cat_moves'].items() if v < -0.15),
                        z_total=m.Z.loc[a, 'z_total'], injury=m.Z.loc[a, 'injury_status'], gp=m.Z.loc[a, 's27_GP'],
                        status=m.Z.loc[a, 'roster_status'], flags=m.Z.loc[a, 'flags']))
fa_eval = pd.DataFrame(fa_eval).sort_values('score', ascending=False)
fa_eval.drop(columns=['add_id']).to_csv(os.path.join(OUT, 'free_agent_moves_evaluated.csv'), index=False, float_format='%.3f')
log('FA moves done')

# =============================================================================== trade baseline = after best FA move
fa_best = fa_eval.iloc[0]
pre_fa_base, pre_fa_mc = base, mc_base
if fa_best['score'] > 0:
    my_roster = [p for p in my_roster if name(p) != fa_best['drop']] + [int(fa_best['add_id'])]
    S.base[MY_TEAM_ID] = my_roster
    fa_ids = [p for p in fa_ids if p != int(fa_best['add_id'])]
    base = S.my_eval()
    mc_base = S.monte_carlo()
    G_full = S.gradient(MY_TEAM_ID)
log('trade baseline after FA move:', round(base['reg_cats'], 2), round(base['po_cats'], 2))

# =============================================================================== other teams
team_prof = {}
for t in d.teams:
    if t == MY_TEAM_ID:
        continue
    apt = ap_base[t] if t in ap_base else S.allplay(t)['per_week']
    catp = S.allplay(t)['cat']
    ranks = {c: int(SUM.loc[t, 'rank_' + c]) for c in CATS}
    strengths = [c for c, v in sorted(catp.items(), key=lambda x: -x[1]) if v >= 0.58]
    weaks = [c for c, v in sorted(catp.items(), key=lambda x: x[1]) if v <= 0.42]
    Gt = S.gradient(t, field=True)
    ros = [p for p in S.base[t] if m.Z.loc[p, 'lineup_slot'] != 'IR']
    lin = {p: S.lin_value(p, Gt) for p in ros}
    vor = {p: m.Z.loc[p, 'vorp'] for p in ros}
    # surplus: real trade value (VORP) but little use to this team's category needs
    vr = pd.Series(vor).rank(ascending=False)
    lr = pd.Series(lin).rank(ascending=False)
    surplus = sorted([p for p in ros if vor[p] > 0 and m.Z.loc[p, 'injury_status'] != 'OUT'],
                     key=lambda p: (vr[p] - lr[p]))[:3]
    team_prof[t] = dict(allplay=apt, cat=catp, ranks=ranks, strengths=strengths, weaks=weaks, G=Gt,
                        surplus=surplus, lin=lin)
log('team profiles done')

# =============================================================================== trades
G_me = G_full
just_added = {int(fa_best['add_id'])} if fa_best['score'] > 0 else set()
my_trade = [p for p in my_roster if p not in just_added and name(p) != LUKA and m.Z.loc[p, 'lineup_slot'] != 'IR' and m.Z.loc[p, 'injury_status'] != 'OUT']
lin_me = {p: S.lin_value(p, G_me) for p in set(list(m.rate.keys()))}


def their_tradeable(t):
    return [p for p in S.base[t] if m.Z.loc[p, 'lineup_slot'] != 'IR' and m.Z.loc[p, 'injury_status'] != 'OUT']


def their_drop(t, roster):
    cand = [p for p in roster if m.Z.loc[p, 'lineup_slot'] != 'IR']
    return min(cand, key=lambda p: m.Z.loc[p, 'z_total'])


def build(t, give, get):
    """Return my new roster, their new roster, who I drop/add, who they drop/add."""
    mine_new = [p for p in my_roster if p not in give] + list(get)
    their_new = [p for p in S.base[t] if p not in get] + list(give)
    my_drop = my_add = th_drop = th_add = None
    if len(get) > len(give):            # I must cut someone: pick the cut that hurts least
        opts = [p for p in mine_new if p not in get and name(p) != LUKA and m.Z.loc[p, 'lineup_slot'] != 'IR']
        my_drop = min(opts, key=lambda p: lin_me[p])
        mine_new.remove(my_drop)
    elif len(get) < len(give):          # open spot: add best free agent for my needs
        my_add = max([p for p in fa_ids[:40] if p not in mine_new and m.Z.loc[p, 's27_GP'] >= 5], key=lambda p: lin_me[p])
        mine_new.append(my_add)
    if len(give) > len(get):
        th_drop = their_drop(t, [p for p in their_new if p not in give])
        their_new.remove(th_drop)
    elif len(give) < len(get):
        th_add = best_fa_for(t, their_new + mine_new)[0]
        their_new.append(th_add)
    return mine_new, their_new, my_drop, my_add, th_drop, th_add


cands = []
for t in team_prof:
    Gt = team_prof[t]['G']
    lin_t = {p: S.lin_value(p, Gt) for p in set(their_tradeable(t) + my_trade)}
    nw = len(Gt)
    theirs = their_tradeable(t)
    shapes = []
    for a in my_trade:
        for b in theirs:
            shapes.append(((a,), (b,)))
    for a1, a2 in itertools.combinations(my_trade, 2):
        for b in theirs:
            shapes.append(((a1, a2), (b,)))
    for a in my_trade:
        for b1, b2 in itertools.combinations(theirs, 2):
            shapes.append(((a,), (b1, b2)))
    for give, get in shapes:
        vg = sum(m.Z.loc[p, 'trade_value'] for p in give)
        vr = sum(m.Z.loc[p, 'trade_value'] for p in get)
        mine_lin = sum(lin_me[p] for p in get) - sum(lin_me[p] for p in give)
        if len(get) > len(give):
            rest = [p for p in my_roster if p not in give and name(p) != LUKA and m.Z.loc[p, 'lineup_slot'] != 'IR']
            mine_lin -= min(lin_me[p] for p in rest)
        if len(get) < len(give):
            mine_lin += max(lin_me[p] for p in fa_ids[:40] if p not in my_roster and m.Z.loc[p, 's27_GP'] >= 5)
        th_lin = (sum(lin_t[p] for p in give) - sum(lin_t[p] for p in get)) / nw
        ratio = vg / vr if vr > 0 else (9.9 if vg > 0 else 1.0)
        if mine_lin > 0 and th_lin > -0.25 and ratio >= 0.6:
            cands.append((mine_lin, t, give, get, th_lin, ratio))
log('screened trade candidates:', len(cands))
cands.sort(key=lambda x: -x[0])
per_team_keep = {}
short = []
for c in cands:
    k = (c[1], len(c[2]), len(c[3]))
    if per_team_keep.get(k, 0) < 40:
        per_team_keep[k] = per_team_keep.get(k, 0) + 1
        short.append(c)
log('full-simulating', len(short), 'trades')

trade_rows = []
for mine_lin, t, give, get, th_lin, ratio in short:
    mine_new, their_new, my_drop, my_add, th_drop, th_add = build(t, give, get)
    ov = {MY_TEAM_ID: mine_new, t: their_new}
    s_ = summarize(S.my_eval(ov))
    their_ap = S.allplay(t, ov)
    d_them = their_ap['per_week'] - team_prof[t]['allplay']
    vg = sum(m.Z.loc[p, 'trade_value'] for p in give)
    vr = sum(m.Z.loc[p, 'trade_value'] for p in get)
    ratio = vg / vr if vr > 0 else 9.9
    their_cats = {c: their_ap['cat'][c] - team_prof[t]['cat'][c] for c in CATS}
    fair = (d_them >= -0.05 and ratio >= 0.85) or (d_them >= 0.10 and ratio >= 0.75)
    trade_rows.append(dict(partner=ab[t], partner_id=t, give=' + '.join(name(p) for p in give),
                           get=' + '.join(name(p) for p in get), shape=f'{len(give)}-for-{len(get)}',
                           i_drop=name(my_drop) if my_drop else '', i_add=name(my_add) if my_add else '',
                           they_drop=name(th_drop) if th_drop else '', they_add=name(th_add) if th_add else '',
                           my_reg_cats=s_['reg_cats'], my_playoff_cats=s_['po_cats'], my_matchup_wins=s_['mwins'],
                           my_score=s_['score'], their_cats_per_week=d_them, value_ratio_to_them=ratio,
                           fair=fair,
                           my_cats_up=', '.join(c for c, v in s_['cat_moves'].items() if v > 0.15),
                           my_cats_down=', '.join(c for c, v in s_['cat_moves'].items() if v < -0.15),
                           their_cats_up=', '.join(c for c, v in their_cats.items() if v > 0.01),
                           their_cats_down=', '.join(c for c, v in their_cats.items() if v < -0.01),
                           give_ids=give, get_ids=get, ov=ov))
trades = pd.DataFrame(trade_rows).sort_values('my_score', ascending=False)
trades.drop(columns=['give_ids', 'get_ids', 'ov', 'partner_id']).to_csv(
    os.path.join(OUT, 'trades_evaluated.csv'), index=False, float_format='%.3f')
log('trades simulated:', len(trades), 'fair & positive:', int(((trades.my_score > 0) & trades.fair).sum()))

good = trades[(trades.my_score > 0) & trades.fair]
top, used_team, used_in = [], {}, set()
for _, r in good.iterrows():
    if used_team.get(r.partner, 0) >= 2 or any(p in used_in for p in r['get_ids']):
        continue
    top.append(r)
    used_team[r.partner] = used_team.get(r.partner, 0) + 1
    used_in |= set(r['get_ids'])
    if len(top) == 15:
        break
mc_top = [S.monte_carlo(r.ov) for r in top]
# final order: title odds first (the goal), then the category score
order = sorted(range(len(top)), key=lambda i: (-(round(mc_top[i][MY_TEAM_ID]['title'], 2)), -top[i].my_score))
top = [top[i] for i in order]
mc_top = [mc_top[i] for i in order]
shortlist = pd.DataFrame([dict(partner=r.partner, give=r.give, get=r['get'], my_score=r.my_score,
                               title_odds=mc[MY_TEAM_ID]['title'], partner_cats_per_week=r.their_cats_per_week,
                               value_ratio=r.value_ratio_to_them) for r, mc in zip(top, mc_top)])
shortlist.to_csv(os.path.join(OUT, 'trade_shortlist_with_title_odds.csv'), index=False, float_format='%.3f')
top, mc_top = top[:5], mc_top[:5]
log('top trades MC done')

# =============================================================================== Kawhi scenario
kawhi = pid_by_name.get('Kawhi Leonard')
kawhi_row = None
if kawhi is not None and kawhi in my_roster:
    saved = dict(m.avail[kawhi])
    for mp in fut:
        m.avail[kawhi][mp] = m.Z.loc[kawhi, 'health'] if mp >= 8 else 0.0
    S._wk.clear()
    worst = min([p for p in my_roster if p != kawhi and name(p) != LUKA], key=lambda p: lin_me[p])
    ek = S.my_eval({MY_TEAM_ID: [p for p in my_roster if p != worst]})
    kawhi_row = dict(drop=name(worst), reg=ek['reg_cats'] - base['reg_cats'], po=ek['po_cats'] - base['po_cats'])
    m.avail[kawhi] = saved
    S._wk.clear()
    log('kawhi scenario', kawhi_row)

# =============================================================================== report
R = []
w = R.append
w('# Lukawhi: rest-of-season analysis')
w(f"\nBuilt from the ESPN export dated {d.league['current_date']} (scoring period {d.cur_sp}, week {d.cur_mp} in progress). "
  f"Re-run with `python3 analysis/run_analysis.py <export folder>`. All numbers come from the export only.\n"
  + (f"\n**Rate source for this run: Hashtag Basketball rest-of-season projections** ({rates.attrs['hbb_matched']} players matched; "
     "the rest use the blended ESPN rates). Injuries, schedule, lineups and variance are handled exactly as in the main run.\n" if HBB else ''))

# ---- Data checks
w('## Data checks\n')
w(f"- Game logs (`counts_for_team=1`) vs `matchups.csv`: **{len(checks) - n_bad} of {len(checks)} team-weeks match exactly** "
  f"(all 11 stat totals, games started, and FG%/FT% recomputed from makes/attempts)." +
  ('' if n_bad == 0 else f" **{n_bad} mismatches**: see data_checks.csv."))
w(f"- Completed weeks used for results: {', '.join(str(x) for x in d.completed)}. Week {d.cur_mp} is partial: its banked totals are "
  f"added to the projection for the {len(d.period_days[d.cur_mp])} remaining days (today's unfinished games count as final).")
w('- FG% and FT% are always summed makes / summed attempts.')
w(f"- Matchup periods 5-22 are derived, not confirmed by ESPN. Playoff weeks 20-22 = "
  f"{d.periods[20]['start_date']} to {d.periods[22]['end_date']}. Anything about playoff schedules (games per team in "
  f"weeks 20-22) depends on those boundaries and is flagged ⚠️.")
w(f"- Players in the export: {len(d.players)}; with usable rates: {len(rates)}. "
  f"Game-to-game noise was measured from {len(d.logs)} game-log rows; model noise vs real week-to-week swings:")
w('\n' + md_table(calib_tab) + '\n')
w('Ratios above 1 mean real weeks swing more than pure game-to-game noise; the model uses max(1, ratio).\n')

# ---- identity
w('## My team identity\n')
w(f"Record {SUM.loc[MY_TEAM_ID, 'cat_W']}-{SUM.loc[MY_TEAM_ID, 'cat_L']}-{SUM.loc[MY_TEAM_ID, 'cat_T']} (seed "
  f"{SUM.loc[MY_TEAM_ID, 'seed']}); all-play {SUM.loc[MY_TEAM_ID, 'allplay_cat_W']}-{SUM.loc[MY_TEAM_ID, 'allplay_cat_L']}-"
  f"{SUM.loc[MY_TEAM_ID, 'allplay_cat_T']} (best in the league).")
cw = base_week = pre_fa_base['per_period'][0]
w(f"\nThis week (week {cw['period']}, vs {cw['opponent']}, partly played): expected {cw['exp_cats']:.1f} categories, "
  f"{cw['match_win']:.0%} chance to win the matchup.")
w(f"\nModel outlook with the current roster: **{pre_fa_base['reg_cats'] / reg_n:.2f} categories per regular week**, "
  f"**{pre_fa_base['po_cats'] / po_n:.2f} per playoff week** vs the likely playoff field ({', '.join(ab[t] for t in strong)}). "
  f"Playoff odds {pre_fa_mc[MY_TEAM_ID]['playoffs']:.0%}, top-2 seed (bye) {pre_fa_mc[MY_TEAM_ID]['top2']:.0%}, "
  f"title {pre_fa_mc[MY_TEAM_ID]['title']:.0%}.\n")
odds = []
for t in sorted(d.teams, key=lambda t: -pre_fa_mc[t]['title']):
    odds.append({'team': tname(t), 'record': f"{SUM.loc[t, 'cat_W']}-{SUM.loc[t, 'cat_L']}-{SUM.loc[t, 'cat_T']}",
                 'proj final cat wins': pre_fa_mc[t]['exp_cat_wins'], 'playoffs': f"{pre_fa_mc[t]['playoffs']:.0%}",
                 'top-2 seed': f"{pre_fa_mc[t]['top2']:.0%}", 'title': f"{pre_fa_mc[t]['title']:.0%}"})
w('Season simulation (20,000 runs, current rosters):\n')
w(md_table(pd.DataFrame(odds), {'proj final cat wins': '{:.0f}'}) + '\n')
show = ident.copy()
show['allplay_win_pct'] = show.allplay_win_pct.map(lambda x: f'{x:.0%}')
for c in ['proj_win_reg', 'proj_win_playoffs', 'proj_vs_field']:
    show[c] = show[c].map(lambda x: f'{x:.0%}')
show = show.rename(columns={'league_rank_wk1_3': 'rank wk1-3', 'avg_week': 'my avg/week', 'my_h2h_wins_wk1_3': 'won in my matchups',
                            'allplay_wk1_3': 'all-play W-L-T', 'allplay_win_pct': 'all-play win%',
                            'proj_win_reg': 'proj win% (my schedule)', 'proj_win_playoffs': 'proj win% (playoffs)',
                            'proj_vs_field': 'proj win% vs field'})
w(md_table(show, {'my avg/week': '{:.3f}'}))
w('\nGroups use the average of the regular-season and playoff projections: LOCK ≥ 70%, LOST CAUSE ≤ 30%, otherwise SWING.\n')
# ---- auto-written identity paragraph (re-generated on every run)
idb = ident.assign(blend=0.5 * ident.proj_win_reg + 0.5 * ident.proj_win_playoffs).set_index('category')
locks = list(idb[idb.group == 'LOCK'].index)
lost = list(idb[idb.group == 'LOST CAUSE'].index)
weakest = list(idb.sort_values('blend').index[:2])
strongest = list(idb.sort_values('blend', ascending=False).index[:3])
tgt = list(targets.category)
gain = targets.set_index('category').extra_cats_per_reg_week
pct = lambda c: f"{idb.loc[c, 'blend']:.0%}"
para = (f"**Who we are:** a deep, balanced Luka team. Strongest categories: {', '.join(f'{c} ({pct(c)})' for c in strongest)}"
        + (f"; locks: {', '.join(locks)}" if locks else '') + f". Weakest: {', '.join(f'{c} ({pct(c)})' for c in weakest)}"
        + (f"; lost causes: {', '.join(lost)}" if lost else '; no category is a lost cause') + ". "
        f"The categories that move the most per unit of talent are **{tgt[0]}**, **{tgt[1]}** and **{tgt[2]}** "
        f"(one good specialist ≈ {gain[tgt[0]]:+.2f}, {gain[tgt[1]]:+.2f}, {gain[tgt[2]]:+.2f} categories a week). "
        f"**Aim for** players whose value comes from {tgt[0]}, {tgt[1]} and {tgt[2]}. "
        f"**Avoid paying for** {tgt[-1]} or {tgt[-2]} specialists: the same quality of player adds only "
        f"{gain[tgt[-1]]:+.2f} / {gain[tgt[-2]]:+.2f} a week there, because you already win them "
        f"{pct(tgt[-1])} / {pct(tgt[-2])} of the time. ")
fw = weakest[0]
if fw in ('FG%', 'FT%'):
    para += (f"Players who hurt {fw} are acceptable if they bring {tgt[0]} or {tgt[1]}: {fw} is already your weakest "
             f"category ({pct(fw)}), and an elite {fw} specialist only moves it {gain[fw]:+.2f} a week, "
             f"less than a specialist in {tgt[0]} ({gain[tgt[0]]:+.2f}).")
else:
    para += f"{fw} is your softest spot ({pct(fw)}); fix it only with players who also help {tgt[0]} or {tgt[1]}."
w(para + '\n')

w('### Punt or stay balanced?\n')
st = strat.copy()
for c in ['exp_cats_per_reg_week', 'exp_cats_per_playoff_week']:
    st[c] = st[c].map(lambda x: f'{x:.2f}')
st['matchup_win_pct'] = st.matchup_win_pct.map(lambda x: f'{x:.0%}')
st['punted_cat_win_pct'] = st.punted_cat_win_pct.map(lambda x: '' if pd.isna(x) else f'{x:.0%}')
w(md_table(st.rename(columns={'exp_cats_per_reg_week': 'cats/reg week', 'exp_cats_per_playoff_week': 'cats/playoff week',
                              'matchup_win_pct': 'matchup win %', 'punted_cat_win_pct': 'still win punted cat'})))
w('\nEach strategy gets the same tools (the two best waiver moves), chosen to maximise that strategy\'s target categories; '
  'the columns then count all 9 categories honestly.\n')
bal = strat.iloc[1]
punts = strat.iloc[2:].copy()
def norm(mv):   # final roster change: set of adds and set of drops
    parts = [x.split(' / ') for x in mv.split('; ') if x]
    return (frozenset(p[0] for p in parts), frozenset(p[1] for p in parts if len(p) > 1))
punts['same'] = [norm(x) == norm(bal.moves) for x in punts.moves]
real = punts[~punts.same]          # punts that actually change the roster
real = real if len(real) else punts
real = real.assign(tot=real.exp_cats_per_reg_week * reg_n + PLAYOFF_WEIGHT * real.exp_cats_per_playoff_week * po_n)
bp_ = real.sort_values('tot', ascending=False).iloc[0]
same = [r.strategy.split(' (')[0].replace('Punt ', '') for _, r in punts.iterrows() if r.same]
if bal.exp_cats_per_reg_week >= punts.exp_cats_per_reg_week.max() - 0.02 and bal.exp_cats_per_playoff_week >= punts.exp_cats_per_playoff_week.max() - 0.02:
    w(f"**Verdict: stay balanced.** No punt beats the balanced plan (best punt: {bp_.strategy.split(' (')[0]}, "
      f"{bp_.exp_cats_per_reg_week:.2f} vs {bal.exp_cats_per_reg_week:.2f} categories a regular week and "
      f"{bp_.exp_cats_per_playoff_week:.2f} vs {bal.exp_cats_per_playoff_week:.2f} in the playoffs). Your swing categories are close "
      "enough that giving one away costs more than it frees up."
      + (f" (For {', '.join(same)} the best 'punt' moves are the same as the balanced moves, so those aren't real punts.)" if same else '') + "\n")
else:
    w(f"**Verdict:** {bp_.strategy.split(' (')[0]} scores best ({bp_.exp_cats_per_reg_week:.2f} vs balanced "
      f"{bal.exp_cats_per_reg_week:.2f} per regular week). Consider it.\n")

# ---- stats to target
w('## Stats to target\n')
tg = targets.copy()
tg = tg[['category', 'boost', 'extra_cats_per_reg_week', 'extra_cats_per_playoff_week', 'extra_matchup_wins_ros']]
w(md_table(tg.rename(columns={'boost': 'boost tested (≈ one good specialist)', 'extra_cats_per_reg_week': 'extra cats / reg week',
                              'extra_cats_per_playoff_week': 'extra cats / playoff week', 'extra_matchup_wins_ros': 'extra matchup wins ROS'}),
           {'extra cats / reg week': '{:+.3f}', 'extra cats / playoff week': '{:+.3f}', 'extra matchup wins ROS': '{:+.2f}'}))
w('\nBoost = one standard deviation of that stat among the top 150 players, times 3.5 games a week.\n')
w('**Focus on, in order:** ' + ', '.join(f"{i}. {c} ({gain[c]:+.2f}/wk)" for i, c in enumerate(tgt[:4], 1)) + '.\n')

# ---- player rankings
w('## Player rankings\n')
w(f"Per-game values are rest-of-season blended rates. **z** = 9-cat value per game vs the top {150} players "
  f"(FG%/FT% weighted by attempts). **ROS games** = remaining NBA games × availability. **VORP** = value above the "
  f"10th-best healthy free agent (z {REPL:.2f}) × ROS games. **Cats vs best FA** = categories I'd lose (full simulation) "
  f"if I swapped him for the best free agent for my team; near zero or negative = replaceable. **Playoff games** = NBA games in "
  f"weeks 20-22 ⚠️ (derived week boundaries).\n")
w('### My roster\n')
rows = []
for p in sorted(pre_fa_roster, key=lambda p: -m.Z.loc[p, 'z_total']):
    r = m.Z.loc[p]
    rows.append({'player': r['name'], 'pos': r.eligible_pos, 'GP': r.s27_GP, 'PTS': r.r_PTS, 'REB': r.r_REB, 'AST': r.r_AST,
                 'STL': r.r_STL, 'BLK': r.r_BLK, '3PM': r.r_3PM, 'FG%': r['FG%'], 'FT%': r['FT%'], 'TO': r.r_TO,
                 'z': r.z_total, 'ROS games': r.ros_games, 'playoff games': r.playoff_games, 'VORP': r.vorp,
                 'cats vs best FA (reg)': fit[p][0], 'cats vs best FA (playoffs)': fit[p][1], 'best FA swap': fit[p][2],
                 'RotoWire': r.rotowire_ros_rank, 'notes': '; '.join(x for x in [r['flags'], r.trend] if x)})
w(md_table(pd.DataFrame(rows), {'FG%': '{:.3f}', 'FT%': '{:.3f}', 'ROS games': '{:.0f}', 'VORP': '{:.0f}',
                                'cats vs best FA (reg)': '{:+.2f}', 'cats vs best FA (playoffs)': '{:+.2f}'}))
w('\n### Top available players (free agents / waivers)\n')
rows = []
for p in fa_pool.sort_values('z_total', ascending=False).head(20).index:
    r = m.Z.loc[p]
    rows.append({'player': r['name'], 'status': r.roster_status, 'pos': r.eligible_pos, 'GP': r.s27_GP, 'PTS': r.r_PTS,
                 'REB': r.r_REB, 'AST': r.r_AST, 'STL': r.r_STL, 'BLK': r.r_BLK, '3PM': r.r_3PM, 'FG%': r['FG%'],
                 'FT%': r['FT%'], 'TO': r.r_TO, 'z': r.z_total, 'RotoWire': r.rotowire_ros_rank,
                 'notes': '; '.join(x for x in [r.injury_status if r.injury_status != 'ACTIVE' else '', r['flags'], r.trend] if x)})
w(md_table(pd.DataFrame(rows), {'FG%': '{:.3f}', 'FT%': '{:.3f}'}))

# ---- trades
w('\n## Trade recommendations\n')
w('### Other teams at a glance\n')
rows = []
for t, pr in sorted(team_prof.items(), key=lambda x: -x[1]['allplay']):
    rows.append({'team': tname(t), 'record': f"{SUM.loc[t, 'cat_W']}-{SUM.loc[t, 'cat_L']}-{SUM.loc[t, 'cat_T']}",
                 'proj cats/wk vs field': pr['allplay'], 'strong': ', '.join(pr['strengths']) or '-',
                 'weak': ', '.join(pr['weaks']) or '-',
                 'surplus (trade value they need least)': ', '.join(name(p) for p in pr['surplus'])})
w(md_table(pd.DataFrame(rows)))
w(f"\n{len(cands)} trade ideas passed the quick screen; the best {len(trades)} were fully simulated "
  f"({int(((trades.my_score > 0) & trades.fair).sum())} help me and look acceptable to the other side). All of them are in trades_evaluated.csv.\n")
if fa_best['score'] > 0:
    w(f"**Trades are measured after the free first move: add {fa_best['add']}, drop {fa_best['drop']}** (see Free-agent moves). "
      f"So every gain below is on top of that pickup. Title odds after the pickup alone: {mc_base[MY_TEAM_ID]['title']:.0%}.\n")
w('The 15 best acceptable trades by category score were each run through the full season simulation; the five below have the '
  'biggest title-odds gain, rounded to the nearest point; differences under about 1 point are simulation noise, so ties are '
  'ordered by category score (trade_shortlist_with_title_odds.csv has all 15).\n')
w('**Score** = extra categories over the remaining regular season + 3 × extra categories in playoff weeks 20-22. '
  '**Their gain** = change in their expected categories per week vs the whole league (their own needs). '
  '**Acceptable** = value ratio ≥ 0.85 and they lose no more than 0.05 categories a week, or they gain 0.10+ a week with ratio ≥ 0.75. **Value ratio** = trade value they receive ÷ value they give, where trade value = (value above replacement)^1.5 × games '
  '(so one star is worth more than two average players); ≥ 0.9 is roughly even.\n')
for i, (r, mc) in enumerate(zip(top, mc_top), 1):
    t = r.partner_id
    extra = []
    if r.i_drop:
        extra.append(f"I drop {r.i_drop}")
    if r.i_add:
        extra.append(f"I add {r.i_add} from waivers")
    if r.they_drop:
        extra.append(f"they drop {r.they_drop}")
    if r.they_add:
        extra.append(f"they pick up {r.they_add}")
    w(f"### {i}. Give {r.give} → get {r['get']} ({tname(t)})\n")
    w(f"- **Me:** {r.my_reg_cats:+.2f} categories over the regular season, {r.my_playoff_cats:+.2f} over playoff weeks, "
      f"{r.my_matchup_wins:+.2f} expected matchup wins. Title odds {mc_base[MY_TEAM_ID]['title']:.0%} → {mc[MY_TEAM_ID]['title']:.0%}.")
    w(f"- **Categories that move for me:** up {r.my_cats_up or '-'}; down {r.my_cats_down or '-'}.")
    w(f"- **Them:** {r.their_cats_per_week:+.2f} categories per week vs the league (up {r.their_cats_up or '-'}; down "
      f"{r.their_cats_down or '-'}); value ratio {r.value_ratio_to_them:.2f}. Their playoff odds "
      f"{mc_base[t]['playoffs']:.0%} → {mc[t]['playoffs']:.0%}, title odds {mc_base[t]['title']:.0%} → {mc[t]['title']:.0%}.")
    if extra:
        w(f"- **Roster:** {'; '.join(extra)}.")
    risks = []
    for nm in (r.give.split(' + ') + r['get'].split(' + ') + ([r.i_add] if r.i_add else [])):
        pid = pid_by_name.get(nm)
        if pid is None:
            continue
        rr = m.Z.loc[pid]
        bits = []
        if rr.injury_status != 'ACTIVE':
            bits.append(rr.injury_status)
        if rr.s27_GP < 6:
            bits.append(f'only {rr.s27_GP} games this season')
        if rr.health < 0.8:
            bits.append(f'ESPN projects {rr.health:.0%} of games')
        if rr.trend:
            bits.append(rr.trend)
        if bits:
            risks.append(f"{nm}: {', '.join(bits)}")
    w(f"- **Risks:** {'; '.join(risks) if risks else 'no injury flags; normal projection uncertainty'}.")
    up = r.their_cats_up.split(', ') if r.their_cats_up else []
    need = [c for c in up if c in team_prof[t]['weaks']]
    rest_up = [c for c in up if c not in need][:2]
    they_get = r.give.replace(' + ', ' and ')
    if len(r.give_ids) > len(r.get_ids):
        hook = f"You'd get two starters ({they_get}) for {r['get']}"
    else:
        hook = f"I'd send you {they_get} for {r['get']}"
    why = ''
    if need:
        why = f" It fixes your {', '.join(need)}" + (f" and adds {', '.join(rest_up)}" if rest_up else '') + '.'
    elif rest_up:
        why = f" It adds {', '.join(rest_up)} to your team."
    pitch = f'"{hook}.{why} By my numbers your team comes out ahead in weekly categories. Interested?"'
    w(f"- **Pitch:** {pitch}\n")

# ---- FA
w('## Free-agent moves\n')
fa_show = fa_eval.head(5).copy()
rows = []
for _, r in fa_show.iterrows():
    rows.append({'add': r['add'], 'status': r.status, 'drop': r['drop'], 'reg cats': r.reg_cats, 'playoff cats': r.po_cats,
                 'matchup wins': r.mwins, 'cats up': r.cats_up or '-', 'cats down': r.cats_down or '-',
                 'notes': '; '.join(x for x in [r.injury if r.injury != 'ACTIVE' else '', r['flags']] if x)})
w(md_table(pd.DataFrame(rows), {'reg cats': '{:+.2f}', 'playoff cats': '{:+.2f}', 'matchup wins': '{:+.2f}'}))
w('\nEach pickup is paired with the drop that leaves my team strongest. Waiver claims process on Sundays (24h waivers).\n')

# ---- assumptions
w('## Assumptions and limits\n')
w(f"- **Rates:** this season gets weight GP/(GP+{K_GAMES}) (10 games → 45%, 20 → 63%, 40 → 77%). The rest comes from a prior "
  f"= {int(PRIOR_PROJ_W * 100)}% ESPN 2026-27 projection + {int((1 - PRIOR_PROJ_W) * 100)}% last season (last season's share "
  f"shrinks if he played under 40 games). FG% and FT% shrink by attempts (prior worth {FG_PRIOR_ATT} FGA / {FT_PRIOR_ATT} FTA). "
  "Last-15/30-day splits are reported as trends, not used in the rates, to avoid overreacting to 5-7 game samples.")
w(f"- **Availability:** each player plays ESPN-projected GP/82 of remaining games (capped 60-95%; {int(DEFAULT_HEALTH * 100)}% if no projection). "
  f"OUT players have no return date in the export, so they are assumed out for the rest of week {d.cur_mp} and week {d.cur_mp + 1}. "
  f"OUT with zero games this season, and anyone in an IR slot, are not projected at all. DAY_TO_DAY = {int(DTD_AVAIL * 100)}% for the rest of this week.")
if kawhi_row:
    w(f"- **Kawhi Leonard (my IR):** not counted anywhere above. If he returned in week 8 at his blended rates and I dropped "
      f"{kawhi_row['drop']}, the model adds {kawhi_row['reg']:+.2f} regular-season categories and {kawhi_row['po']:+.2f} playoff "
      "categories. That is a scenario, not a forecast: the export has no return date.")
w("- **Lineups:** every day the 10 slots are filled by position eligibility, best players first; bench players only count "
  "on days a slot is open. Opponents are assumed to set optimal lineups and keep their current rosters.")
w("- **Week-to-week noise:** game-to-game variance from the game logs, scaled up where real weekly swings were larger. "
  "Categories are treated as independent when converting to matchup win odds.")
w(f"- **Playoffs:** opponent = average of the five strongest other teams by projection ({', '.join(ab[t] for t in strong)}). "
  "⚠️ Week 20-22 boundaries are derived, so games-per-team in those weeks may shift.")
w("- **Trades:** Luka is never offered. OUT and IR players are left out of trades (no return dates). When I receive more "
  "players than I send, the weakest fit on my roster is cut; when I send more, I add the best free agent for my needs. "
  "Acceptance uses the partner's own category gain plus a value check; real managers may value players differently.")
w("- **Small samples:** about 10 games into the season. Trends in the last 15 days are shown but not trusted on their own.")
w("- **RotoWire rankings** are shown for reference only and are not used in any calculation.")
open(os.path.join(OUT, 'report.md'), 'w').write('\n'.join(R) + '\n')

# extra csvs
ident.to_csv(os.path.join(OUT, 'my_category_identity.csv'), index=False, float_format='%.3f')
targets.to_csv(os.path.join(OUT, 'stats_to_target.csv'), index=False, float_format='%.3f')
strat.to_csv(os.path.join(OUT, 'punt_vs_balanced.csv'), index=False, float_format='%.3f')
pd.DataFrame([dict(team=ab[t], **v) for t, v in mc_base.items()]).to_csv(os.path.join(OUT, 'playoff_odds_baseline.csv'), index=False, float_format='%.3f')
log('report written')
