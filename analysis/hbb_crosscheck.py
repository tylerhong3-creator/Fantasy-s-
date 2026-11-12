"""Cross-check the recommended moves with Hashtag Basketball (HBB) data and write
analysis/moves_report.md.

Two "worlds" are simulated with the identical engine (lineups, schedule, injuries, variance):
  ESPN-blend : per-game rates blended from this season, ESPN projection, last season (main report)
  HBB        : per-game rates = HBB rest-of-season projection
A move is called ROBUST when it helps in both worlds.

Usage (repo root): python3 analysis/hbb_crosscheck.py [export_folder] [hbb_xlsx]
Run run_analysis.py first (normal run and the --hbb run into analysis/hbb_run) so the shortlists exist.
"""
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from fantasy import (CATS, MY_TEAM_ID, PLAYOFF_WEIGHT, Data, Model, blend_rates, zscores, estimate_dispersion,
                     calibrate, apply_hbb_rates, load_hbb_sheet, norm_name)
from season import Season

ROOT = os.path.dirname(HERE)
FOLDER = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'espn_fantasy_2026-27_2026-11-11')
HBB = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, 'hbb', 'HBB_supplement_Lukawhi_2026-11-11.xlsx')
LUKA = 'Luka Doncic'
MC_N = 20000

d = Data(FOLDER)
ab = d.abbrev
owner = {t['team_id']: t['owner'].split()[0] for t in d.league['teams']}
tname = lambda t: f"{ab[t]} ({owner[t]})"


def world(rates):
    Z = zscores(rates)
    m = Model(d, Z)
    m.disp = estimate_dispersion(d, m)
    m.calib, _ = calibrate(d, m)
    S = Season(m)
    S.set_strong()
    fut = d.future_periods
    m.Z['ros_games'] = [sum(S.games(p, mp) * m.avail[p][mp] for mp in fut) for p in m.Z.index]
    fa = m.Z[(m.Z.fantasy_team_id == 0) & (m.Z.injury_status != 'OUT') & (m.Z.ros_games > 20)].sort_values('z_total', ascending=False)
    repl = float(fa.z_total.iloc[9])
    m.Z['trade_value'] = np.maximum(0, m.Z.z_total - repl) ** 1.5 * m.Z.ros_games / 10
    return dict(m=m, S=S, Z=m.Z, base_roster=list(S.base[MY_TEAM_ID]))


base_rates = blend_rates(d)
W = {'ESPN-blend': world(base_rates), 'HBB': world(apply_hbb_rates(base_rates, HBB))}
pid_by_name = {r['name']: pid for pid, r in W['ESPN-blend']['Z'].iterrows()}
name = lambda pid: W['ESPN-blend']['Z'].loc[pid, 'name']
print('worlds ready')

# HBB sheets used directly
PM = load_hbb_sheet(HBB, 'Player_Master')
PM['key'] = PM.Player.map(norm_name)
PM = PM.drop_duplicates('key').set_index('key')
SCH = load_hbb_sheet(HBB, 'LK_Schedule')


def hbb(nm, col):
    k = norm_name(nm)
    if k in PM.index:
        v = PM.loc[k, col]
        return v if v is not None else np.nan
    return np.nan


def ev(w, roster, override=None):
    ov = dict(override or {})
    ov[MY_TEAM_ID] = roster
    return w['S'].my_eval(ov)


def delta(e, b):
    return dict(reg=e['reg_cats'] - b['reg_cats'], po=e['po_cats'] - b['po_cats'], mw=e['reg_mwins'] - b['reg_mwins'],
                score=e['score'] - b['score'],
                cats={c: (e['cat_reg'][c] - b['cat_reg'][c]) + (e['cat_po'][c] - b['cat_po'][c]) for c in CATS})


# =============================================================================== 1. baselines
for k, w in W.items():
    w['b0'] = w['S'].my_eval()
    w['mc0'] = w['S'].monte_carlo(n=MC_N)
    w['G'] = w['S'].gradient(MY_TEAM_ID)
    print(k, 'baseline', round(w['b0']['reg_cats'], 2), round(w['b0']['po_cats'], 2), w['mc0'][MY_TEAM_ID])

my0 = W['ESPN-blend']['base_roster']
droppable = [p for p in my0 if name(p) != LUKA and W['ESPN-blend']['Z'].loc[p, 'lineup_slot'] != 'IR']

# =============================================================================== 2. free agents (both worlds)
fa_cands = set()
for k, w in W.items():
    Z = w['Z']
    pool = [p for p in Z.index if Z.loc[p, 'fantasy_team_id'] == 0 and Z.loc[p, 'ros_games'] > 5
            and 'not projected' not in Z.loc[p, 'flags']]
    fa_cands |= set(sorted(pool, key=lambda p: -w['S'].lin_value(p, w['G']))[:14])
fa_rows = []
for a in fa_cands:
    for dr in droppable:
        row = dict(add=name(a), drop=name(dr), add_id=a, drop_id=dr)
        for k, w in W.items():
            dd = delta(ev(w, [p for p in my0 if p != dr] + [a]), w['b0'])
            row[f'{k} score'] = dd['score']
            row[f'{k} reg'] = dd['reg']
            row[f'{k} po'] = dd['po']
        fa_rows.append(row)
FA = pd.DataFrame(fa_rows)
FA['robust'] = FA[['ESPN-blend score', 'HBB score']].min(axis=1)
FA = FA.sort_values('robust', ascending=False)
FA.drop(columns=['add_id', 'drop_id']).to_csv(os.path.join(HERE, 'crosscheck_free_agents.csv'), index=False, float_format='%.3f')
best_fa = FA.iloc[0]
print('best robust FA', best_fa['add'], best_fa['drop'], best_fa.robust)
# best move per add (one line each) for the report
fa_top = FA.drop_duplicates('add').head(8)

# =============================================================================== 3. trades (both worlds, common baseline)
my1 = [p for p in my0 if p != best_fa.drop_id] + [int(best_fa.add_id)]
for k, w in W.items():
    w['b1'] = ev(w, my1)
    w['S'].base[MY_TEAM_ID] = my1
    w['mc1'] = w['S'].monte_carlo(n=MC_N)
    w['G1'] = w['S'].gradient(MY_TEAM_ID)
    w['ap'] = {t: w['S'].allplay(t)['per_week'] for t in d.teams if t != MY_TEAM_ID}

cands = []
for f in [os.path.join(HERE, 'trade_shortlist_with_title_odds.csv'), os.path.join(HERE, 'hbb_run', 'trade_shortlist_with_title_odds.csv')]:
    if os.path.exists(f):
        cands += [(r.partner, r.give, r['get']) for _, r in pd.read_csv(f).iterrows()]
cands = list(dict.fromkeys(cands))
abbr2id = {v: k for k, v in ab.items()}


def build(w, t, give, get):
    Z, S = w['Z'], w['S']
    mine = [p for p in my1 if p not in give] + list(get)
    theirs = [p for p in S.base[t] if p not in get] + list(give)
    note = []
    if len(get) > len(give):
        opts = [p for p in mine if p not in get and name(p) != LUKA and Z.loc[p, 'lineup_slot'] != 'IR']
        dr = min(opts, key=lambda p: S.lin_value(p, w['G1']))
        mine.remove(dr)
        note.append(f'I drop {name(dr)}')
    elif len(get) < len(give):
        pool = [p for p in Z.index if Z.loc[p, 'fantasy_team_id'] == 0 and Z.loc[p, 's27_GP'] >= 5
                and Z.loc[p, 'injury_status'] != 'OUT' and p not in mine]
        pool = sorted(pool, key=lambda p: -S.lin_value(p, w['G1']))[:6]
        best = max(pool, key=lambda p: ev(w, mine + [p], {t: theirs})['score'])
        mine.append(best)
        note.append(f'I add {name(best)}')
    if len(give) > len(get):
        cand = [p for p in theirs if p not in give and Z.loc[p, 'lineup_slot'] != 'IR']
        drp = min(cand, key=lambda p: Z.loc[p, 'z_total'])
        theirs.remove(drp)
        note.append(f'they drop {name(drp)}')
    return mine, theirs, note


tr_rows = []
for partner, give_s, get_s in cands:
    t = abbr2id[partner]
    give = [pid_by_name[x] for x in give_s.split(' + ')]
    get = [pid_by_name[x] for x in get_s.split(' + ')]
    row = dict(partner=partner, partner_id=t, give=give_s, get=get_s)
    for k, w in W.items():
        mine, theirs, note = build(w, t, give, get)
        ov = {MY_TEAM_ID: mine, t: theirs}
        e = w['S'].my_eval(ov)
        dd = delta(e, w['b1'])
        th = w['S'].allplay(t, ov)['per_week'] - w['ap'][t]
        vg = sum(w['Z'].loc[p, 'trade_value'] for p in give)
        vr = sum(w['Z'].loc[p, 'trade_value'] for p in get)
        row.update({f'{k} score': dd['score'], f'{k} reg': dd['reg'], f'{k} po': dd['po'], f'{k} mw': dd['mw'],
                    f'{k} them': th, f'{k} ratio': vg / vr if vr > 0 else np.nan, f'{k} note': '; '.join(note),
                    f'{k} cats': dd['cats'], f'{k} ov': ov})
    hv_give = sum(hbb(x, 'Value ROS proj') for x in give_s.split(' + '))
    hv_get = sum(hbb(x, 'Value ROS proj') for x in get_s.split(' + '))
    row['HBB value they get'] = hv_give
    row['HBB value they give'] = hv_get
    tr_rows.append(row)
TR = pd.DataFrame(tr_rows)
TR['robust'] = TR[['ESPN-blend score', 'HBB score']].min(axis=1)
TR['fair'] = ((TR['ESPN-blend ratio'] >= 0.85) & (TR[['ESPN-blend them', 'HBB them']].max(axis=1) >= -0.05)) & \
             (TR['HBB value they get'] >= TR['HBB value they give'] - 1.5)
TR = TR.sort_values(['fair', 'robust'], ascending=[False, False])
top = TR[(TR.robust > 0) & TR.fair].head(6).copy()
for k, w in W.items():
    top[f'{k} title'] = [w['S'].monte_carlo(r[f'{k} ov'], n=MC_N)[MY_TEAM_ID]['title'] for _, r in top.iterrows()]
TR.drop(columns=[c for c in TR.columns if c.endswith(' ov') or c.endswith(' cats')]).to_csv(
    os.path.join(HERE, 'crosscheck_trades.csv'), index=False, float_format='%.3f')
print('trades evaluated', len(TR), 'robust+fair', len(TR[(TR.robust > 0) & TR.fair]))

# =============================================================================== 4. category picture
SUM = d.summary.set_index('fantasy_team_id')
import openpyxl
raw = [list(r) for r in openpyxl.load_workbook(HBB, read_only=True, data_only=True)['Lukawhi'].iter_rows(values_only=True)]
hbb_rank = {}
for i, r in enumerate(raw):
    if r and r[0] == 'Category ranks (1 = best)':
        hdr = raw[i + 1]
        for rr in raw[i + 2:]:
            if rr and rr[0] == 'LK':
                hbb_rank = dict(zip(hdr[2:11], rr[2:11]))
                break
        break
cat_rows = []
for c in CATS:
    e, h = W['ESPN-blend']['b0'], W['HBB']['b0']
    rg = lambda x: x['cat_reg'][c] / x['reg_weeks']
    pg = lambda x: x['cat_po'][c] / x['po_weeks']
    avg = np.mean([rg(e), pg(e), rg(h), pg(h)])
    verdict = 'SOLIDIFY (strength)' if avg >= 0.62 else ('IMPROVE (swing)' if avg >= 0.40 else 'WEAK: soft-concede')
    cat_rows.append({'category': c, 'actual rank wk1-3': int(SUM.loc[MY_TEAM_ID, 'rank_' + c]),
                     'HBB rank (ROS z, top-10)': hbb_rank.get(c, ''),
                     'win% reg (ESPN-blend)': f"{rg(e):.0%}", 'win% reg (HBB)': f"{rg(h):.0%}",
                     'win% playoffs (ESPN-blend)': f"{pg(e):.0%}", 'win% playoffs (HBB)': f"{pg(h):.0%}",
                     'avg': avg, 'verdict': verdict})
CATDF = pd.DataFrame(cat_rows)


# =============================================================================== 5. my players
def fit_vs_fa(w, p):
    pool = [q for q in w['Z'].index if w['Z'].loc[q, 'fantasy_team_id'] == 0 and w['Z'].loc[q, 'ros_games'] > 5
            and 'not projected' not in w['Z'].loc[q, 'flags'] and w['Z'].loc[q, 's27_GP'] >= 5]
    pool = sorted(pool, key=lambda q: -w['S'].lin_value(q, w['G']))[:10]
    best = max(ev(w, [x for x in my0 if x != p] + [q])['score'] for q in pool)
    return w['b0']['score'] - best


pl_rows = []
sched = {r.Player.replace(' (IR)', ''): r for _, r in SCH.iterrows() if isinstance(r.Player, str)}
for p in sorted(my0, key=lambda p: -W['ESPN-blend']['Z'].loc[p, 'z_total']):
    nm = name(p)
    ir = W['ESPN-blend']['Z'].loc[p, 'lineup_slot'] == 'IR'
    f_e = np.nan if ir else fit_vs_fa(W['ESPN-blend'], p)
    f_h = np.nan if ir else fit_vs_fa(W['HBB'], p)
    sc = sched.get(nm)
    pl_rows.append({'player': nm, 'status': W['ESPN-blend']['Z'].loc[p, 'injury_status'] + (' (IR)' if ir else ''),
                    'z (ESPN-blend)': W['ESPN-blend']['Z'].loc[p, 'z_total'],
                    'HBB ROS value': hbb(nm, 'Value ROS proj'), 'HBB last-14 value': hbb(nm, 'Value L14'),
                    'HBB season value': hbb(nm, 'Value Season'),
                    'MPG chg (L7)': hbb(nm, 'MPG chg (L7-season)'),
                    'keep score ESPN-blend': f_e, 'keep score HBB': f_h,
                    'P8 games (Dec 7-13)': sc['P8 Dec 7-13'] if sc is not None else np.nan,
                    'playoff games': sc['Playoffs total'] if sc is not None else np.nan,
                    'off-night games left': sc['Off-night games reg left (≤7 NBA games that day)'] if sc is not None else np.nan})
PL = pd.DataFrame(pl_rows)


def tag(r):
    if 'IR' in r.status:
        return 'HOLD (IR)'
    k = np.nanmin([r['keep score ESPN-blend'], r['keep score HBB']])
    kx = np.nanmax([r['keep score ESPN-blend'], r['keep score HBB']])
    if r.player == LUKA:
        return 'CORE'
    if k >= 2.0:
        return 'CORE'
    if kx <= 0.3:
        return 'DROP/REPLACE'
    if k <= 0.8:
        return 'TRADE CHIP / replaceable'
    return 'KEEP'


PL['verdict'] = PL.apply(tag, axis=1)
PL.to_csv(os.path.join(HERE, 'crosscheck_my_players.csv'), index=False, float_format='%.2f')

# FA list from HBB with minutes trends (only players actually unrostered in the ESPN export)
FAH = load_hbb_sheet(HBB, 'FA_Targets')
fa_names = set(W['ESPN-blend']['Z'].loc[W['ESPN-blend']['Z'].fantasy_team_id == 0, 'name'].map(norm_name))
FAH = FAH[FAH.Player.map(norm_name).isin(fa_names)]


# =============================================================================== report
def pct(x):
    return f'{x:.0%}'


def md(df, fmt=None):
    cols = list(df.columns)
    out = ['| ' + ' | '.join(cols) + ' |', '|' + '|'.join('---' for _ in cols) + '|']
    for _, r in df.iterrows():
        cells = []
        for c in cols:
            v = r[c]
            if isinstance(v, (float, np.floating)):
                cells.append('' if np.isnan(v) else (fmt or {}).get(c, '{:.2f}').format(v))
            else:
                cells.append(str(v))
        out.append('| ' + ' | '.join(cells) + ' |')
    return '\n'.join(out)


E, H = W['ESPN-blend'], W['HBB']
L = []
w = L.append
w('# Lukawhi: moves report (ESPN export + Hashtag Basketball cross-check)')
w(f"\nData: ESPN export {d.league['current_date']} (week {d.cur_mp} in progress) and the HBB supplement pulled the same day. "
  "Every move below was simulated twice with the same engine (daily lineups, real schedule, injuries, week-to-week noise): "
  "once with my blended ESPN rates and once with HBB's rest-of-season projections. **ROBUST** = helps in both. "
  "The HBB file confirmed the ESPN matchup weeks (P7 Nov 30-Dec 6, P8 Dec 7-13, P18 Feb 15-28, playoffs Mar 8-28), "
  "so the week-boundary warning in report.md no longer applies.\n")

# ---- bottom line
w('## Bottom line: moves in order\n')
bl = []
bl.append(f"1. **Waiver move: add {best_fa['add']}, drop {best_fa['drop']}.** "
          f"{best_fa['ESPN-blend score']:+.2f} (ESPN-blend) / {best_fa['HBB score']:+.2f} (HBB) on the season score "
          "(regular-season categories + 3× playoff categories). It is the best pickup that helps under both projections.")
if len(top):
    t0 = top.iloc[0]
    bl.append(f"2. **Trade: give {t0.give} to {tname(t0.partner_id)} for {t0['get']}.** "
              f"Score {t0['ESPN-blend score']:+.2f} / {t0['HBB score']:+.2f}; title odds "
              f"{E['mc1'][MY_TEAM_ID]['title']:.0%}→{t0['ESPN-blend title']:.0%} (ESPN-blend), "
              f"{H['mc1'][MY_TEAM_ID]['title']:.0%}→{t0['HBB title']:.0%} (HBB).")
    if len(top) > 1:
        alts = '; '.join(f"{r.give} → {r['get']} ({r.partner})" for _, r in top.iloc[1:4].iterrows())
        bl.append(f"3. **If that's declined**, in order: {alts}. Details below.")
p8 = d.sched[(d.sched.scoring_period >= d.periods[8]['first_scoring_period']) & (d.sched.scoring_period <= d.periods[8]['last_scoring_period'])]
p8_teams = set(p8.home) | set(p8.away)
p8_none = sorted(set(d.sched.home) - p8_teams)
p8_opp = ab[d.opponent(MY_TEAM_ID, 8)]
bl.append(f"4. **Week 8 (Dec 7-13) is a near-empty week:** only {len(p8)} NBA games ({', '.join(sorted(p8.date.unique()))}), no team plays twice, "
          f"and {', '.join(p8_none)} don't play at all, so **Luka has 0 games**. Your opponent is {p8_opp}. Every other player of yours has 1 game, "
          "so start everyone who plays; the week is mostly luck. Don't make long-term roster moves just for it.")
bl.append("5. **Don't punt FT%.** It is your weakest category in both projections, but punting it gains nothing measurable "
          "(see report.md). Treat it as soft: never pay for FT%, don't avoid good players because of it.")
for x in bl:
    w(x)

# ---- identity
w('\n## What the team is good and bad at\n')
w(f"Projected title odds now: **{E['mc0'][MY_TEAM_ID]['title']:.0%} (ESPN-blend) / {H['mc0'][MY_TEAM_ID]['title']:.0%} (HBB)**; "
  f"playoffs ~{E['mc0'][MY_TEAM_ID]['playoffs']:.0%}, top-2 seed {E['mc0'][MY_TEAM_ID]['top2']:.0%} / {H['mc0'][MY_TEAM_ID]['top2']:.0%}. "
  f"Main rival: BBB (title {E['mc0'][abbr2id['BBB']]['title']:.0%} / {H['mc0'][abbr2id['BBB']]['title']:.0%}).\n")
w(md(CATDF.drop(columns=['avg'])))
sol = list(CATDF[CATDF.verdict.str.startswith('SOLIDIFY')].category)
imp = list(CATDF[CATDF.verdict.str.startswith('IMPROVE')].category)
weak = list(CATDF[CATDF.verdict.str.startswith('WEAK')].category)
w(f"\n- **Strengths to keep (don't trade away the players who drive them):** {', '.join(sol) or '-'}.")
w(f"- **Swing categories, where upgrades pay off most:** {', '.join(imp) or '-'}. Per unit of talent, the simulator ranks AST and PTS "
  "as the highest-leverage adds in both projections, then REB/BLK.")
w(f"- **Weak spots:** {', '.join(weak) or '-'}. FT% is last in HBB's league profile (rank 10) and ~30-39% in the simulator. "
  "HBB also ranks you 9th in AST and TO on its projected top-10 players, while your actual weekly results were better (AST 5th, TO 5th): "
  "your depth plays more games than a top-10 snapshot counts.")
w("- **Biggest single swing: playoff PTS.** Against the likely playoff field you win PTS only ~28% (ESPN-blend) of weeks. "
  "A real scorer is the upgrade that matters most in March.\n")

# ---- players
w('## My players\n')
w("**Keep score** = categories (season score: regular + 3× playoffs) I'd lose by swapping him for the best free agent. "
  "High = core; near zero or negative = replaceable. HBB values are HBB's 9-cat z totals (TO weighted ×1).\n")
w(md(PL, {'z (ESPN-blend)': '{:+.2f}', 'HBB ROS value': '{:+.2f}', 'HBB last-14 value': '{:+.2f}', 'HBB season value': '{:+.2f}',
          'MPG chg (L7)': '{:+.1f}', 'keep score ESPN-blend': '{:+.2f}', 'keep score HBB': '{:+.2f}',
          'P8 games (Dec 7-13)': '{:.0f}', 'playoff games': '{:.0f}', 'off-night games left': '{:.0f}'}))
dis = []
for _, r in PL.iterrows():
    if np.isnan(r['keep score ESPN-blend']) or np.isnan(r['keep score HBB']):
        continue
    if abs(r['keep score ESPN-blend'] - r['keep score HBB']) >= 1.5:
        dis.append(f"{r.player} ({r['keep score ESPN-blend']:+.1f} vs {r['keep score HBB']:+.1f})")
w('\n**Where the two projections disagree most:** ' + (', '.join(dis) if dis else 'nowhere by more than 1.5') + '. '
  "Usually this is HBB weighting a player's recent role differently: compare his HBB last-14 value and minutes change before acting.\n")

# ---- FA
w('## Free-agent moves\n')
show = fa_top[['add', 'drop', 'ESPN-blend reg', 'ESPN-blend po', 'HBB reg', 'HBB po', 'robust']].copy()
show['ROBUST?'] = np.where(show.robust > 0, 'yes', 'no')
for c in ['MPG chg (L7)', 'HBB L14']:
    pass
show['HBB last-14 value'] = [hbb(x, 'Value L14') for x in show['add']]
show['MPG chg (L7)'] = [hbb(x, 'MPG chg (L7-season)') for x in show['add']]
w(md(show.drop(columns=['robust']).rename(columns={'ESPN-blend reg': 'reg cats (ESPN-blend)', 'ESPN-blend po': 'playoff cats (ESPN-blend)',
                                                   'HBB reg': 'reg cats (HBB)', 'HBB po': 'playoff cats (HBB)'}),
     {'reg cats (ESPN-blend)': '{:+.2f}', 'playoff cats (ESPN-blend)': '{:+.2f}', 'reg cats (HBB)': '{:+.2f}',
      'playoff cats (HBB)': '{:+.2f}', 'HBB last-14 value': '{:+.2f}', 'MPG chg (L7)': '{:+.1f}'}))
w('\nEach add is paired with its best drop (the one that scores best in the worse of the two projections). All combinations: crosscheck_free_agents.csv.\n')

# ---- trades
w('## Trades\n')
w(f"{len(TR)} trade ideas (the shortlists from both full runs) were re-simulated in both worlds on top of the waiver move above. "
  f"{len(TR[(TR.robust > 0) & TR.fair])} help me in both and pass the fairness check (their own category change ≥ -0.05/week in at least one "
  "projection, my value ratio ≥ 0.85, and HBB's market value they receive within 1.5 of what they give).\n")
for i, (_, r) in enumerate(top.iterrows(), 1):
    t = r.partner_id
    ce = r['ESPN-blend cats']
    ch = r['HBB cats']
    up = [c for c in CATS if ce[c] > 0.15 and ch[c] > 0.15]
    dn = [c for c in CATS if ce[c] < -0.15 and ch[c] < -0.15]
    w(f"### {i}. Give {r.give} → get {r['get']} ({tname(t)})\n")
    w(f"- **Me:** season score {r['ESPN-blend score']:+.2f} (ESPN-blend) / {r['HBB score']:+.2f} (HBB); playoff categories "
      f"{r['ESPN-blend po']:+.2f} / {r['HBB po']:+.2f}; title odds {E['mc1'][MY_TEAM_ID]['title']:.0%}→{r['ESPN-blend title']:.0%} / "
      f"{H['mc1'][MY_TEAM_ID]['title']:.0%}→{r['HBB title']:.0%}.")
    w(f"- **Categories (agreed by both):** up {', '.join(up) or '-'}; down {', '.join(dn) or '-'}.")
    w(f"- **Them:** {r['ESPN-blend them']:+.2f} / {r['HBB them']:+.2f} categories a week; HBB market value they get "
      f"{r['HBB value they get']:+.1f} vs give {r['HBB value they give']:+.1f}.")
    notes = r['ESPN-blend note'] or r['HBB note']
    if notes:
        w(f"- **Roster:** {notes}.")
    risk = []
    for nm in r.give.split(' + ') + r['get'].split(' + '):
        mp = hbb(nm, 'MPG chg (L7-season)')
        l14, ros = hbb(nm, 'Value L14'), hbb(nm, 'Value ROS proj')
        st = E['Z'].loc[pid_by_name[nm], 'injury_status']
        bits = []
        if st != 'ACTIVE':
            bits.append(st)
        if not np.isnan(mp) and abs(mp) >= 3:
            bits.append(f'minutes {mp:+.1f} last 7 days')
        if not np.isnan(l14) and not np.isnan(ros) and abs(l14 - ros) >= 4:
            bits.append(f'HBB last-14 {l14:+.1f} vs ROS {ros:+.1f}')
        if bits:
            risk.append(f"{nm}: {', '.join(bits)}")
    w(f"- **Risks:** {'; '.join(risk) if risk else 'no injury or role flags in either source'}.")
    w('')
w('All evaluated trades with both projections: crosscheck_trades.csv.\n')

# ---- schedule
w('## Schedule notes (from HBB, matches the ESPN export)\n')
lk = SCH[SCH.Player.astype(str).str.len() > 0].copy()
lk = lk[~lk.Player.astype(str).str.startswith('Roster total')]
w(f"- **Week 8 (Dec 7-13):** total roster games = {int(lk['P8 Dec 7-13'].fillna(0).sum())} (Luka 0; no NBA team plays more than once). "
  "With so few games every slot is open, so all your players who play will count.")
w(f"- **Playoff weeks (Mar 8-28):** roster games = {int(lk['Playoffs total'].fillna(0).sum())}. Fewest: "
  + ', '.join(f"{r.Player} {int(r['Playoffs total'])}" for _, r in lk.sort_values('Playoffs total').head(3).iterrows())
  + '. Most: ' + ', '.join(f"{r.Player} {int(r['Playoffs total'])}" for _, r in lk.sort_values('Playoffs total', ascending=False).head(4).iterrows()) + '.')
w("- **Off-night games** (days with ≤7 NBA games, when bench players actually get a slot): Pritchard, Jabari, Clingan and Jrue have the "
  "most; Davion Mitchell has the fewest. Players with many off-night games are worth more on a deep roster like yours.")
w('')

# ---- HBB FA list
w('## HBB free-agent radar (minutes trends)\n')
fr = FAH.copy()
fr = fr[['Player', 'Pos', 'NBA', 'GP', 'MPG', 'MPG chg L7', 'Value ROS proj', 'Value L14', 'Games left reg season', 'Playoff games (Mar 8-28)']]
fr = fr.sort_values('Value ROS proj', ascending=False).head(12)
w(md(fr, {'MPG': '{:.1f}', 'MPG chg L7': '{:+.1f}', 'Value ROS proj': '{:+.2f}', 'Value L14': '{:+.2f}', 'GP': '{:.0f}',
          'Games left reg season': '{:.0f}', 'Playoff games (Mar 8-28)': '{:.0f}'}))
w('\nOnly players listed as unrostered in the ESPN export are shown. Rising minutes plus a strong last-14 value are the '
  'pickups to watch if a roster spot opens (e.g. when Kawhi returns).\n')

w('## Assumptions and limits\n')
w("- HBB rates replace the ESPN-blend per-game rates for players matched by name; injury status, availability, lineups and "
  "schedule come from the ESPN export in both worlds. HBB's FG%/FT% z-scores and 'Value' are shown as HBB computes them.")
w("- Kawhi Leonard is on IR with no return date in either source and is not projected. Week 4 is partly played; its banked totals are included.")
w("- Trade acceptance is an estimate. HBB 'market value' is a proxy for how the other manager might rate the players.")
w("- RotoWire rankings were not used.")
open(os.path.join(HERE, 'moves_report.md'), 'w').write('\n'.join(L) + '\n')
print('moves_report.md written')
