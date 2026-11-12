"""Trade ideas with LS (Sam) and 76Er (Andy) built around Davion, assuming Davion's
2026-27 production so far is his true level. Writes analysis/davion_partner_trades.csv."""
import sys, os, math, itertools
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import numpy as np, pandas as pd, openpyxl
from fantasy import *
from season import Season
ROOT = os.path.dirname(HERE)
d = Data(os.path.join(ROOT, 'espn_fantasy_2026-27_2026-11-11'))
HBBX = os.path.join(HERE, 'hbb', 'HBB_supplement_Lukawhi_2026-11-11.xlsx')

def hot(rates):
    R = rates.copy(); row = d.players[d.players.name == 'Davion Mitchell'].iloc[0]
    i = R.index[R.name == 'Davion Mitchell'][0]
    for s in STATS + ['MIN']: R.at[i, 'r_' + s] = row['s27_' + s] / row.s27_GP
    return R
def world(rates):
    Z = zscores(rates); m = Model(d, Z); m.disp = estimate_dispersion(d, m); m.calib, _ = calibrate(d, m)
    S = Season(m); S.set_strong(); return dict(m=m, S=S, Z=m.Z)
br = blend_rates(d)
W = {'ESPN-blend': world(hot(br)), 'HBB': world(hot(apply_hbb_rates(br, HBBX)))}
Z0 = W['ESPN-blend']['Z']; pid = {r['name']: p for p, r in Z0.iterrows()}; name = lambda p: Z0.loc[p, 'name']
# market ranks: HBB current + ROS rankings files, ESPN season rank
def load(f):
    rows = list(openpyxl.load_workbook(f, read_only=True, data_only=True).worksheets[0].iter_rows(values_only=True))
    df = pd.DataFrame(rows[1:], columns=rows[0]); df = df[df['R#'] != 'R#'].copy()
    df['R#'] = df['R#'].map(lambda x: int(str(x).split()[0])); df['key'] = df.PLAYER.map(norm_name)
    return df.drop_duplicates('key').set_index('key')['R#']
NOW = load(os.path.join(HERE, 'hbb', 'CurrentRankings.xlsx')); ROS = load(os.path.join(HERE, 'hbb', 'RestOfSeasonRankings.xlsx'))
P = d.players.set_index('name')
def mrank(nm):
    k = norm_name(nm); e = P.loc[nm, 'espn_rank_season']; e = e if e > 0 else 300
    return float(np.mean([e, NOW.get(k, 250), ROS.get(k, 250)]))
def mval(nm, premium=1.0):
    return premium * math.exp(-mrank(nm) / 40)
PREM = {'Davion Mitchell': 1.25}   # Sam and Andy both rate Davion highly

my0 = list(W['ESPN-blend']['S'].base[MY_TEAM_ID])
for w in W.values():
    w['b'] = w['S'].my_eval(); w['G'] = w['S'].gradient(MY_TEAM_ID)
    w['pool'] = sorted([p for p in w['Z'].index if w['Z'].loc[p, 'fantasy_team_id'] == 0 and w['Z'].loc[p, 's27_GP'] >= 5
                        and w['Z'].loc[p, 'injury_status'] != 'OUT'], key=lambda p: -w['S'].lin_value(p, w['G']))[:8]

import itertools
extras = ['Kyshawn George', 'Jrue Holiday', 'Rui Hachimura', 'Brandin Podziemski', 'Payton Pritchard', 'Jabari Smith Jr.']
gives = [('Davion Mitchell',) + c for c in itertools.combinations(extras, 2)]
TG = {'76Er': ['Michael Porter Jr.', 'VJ Edgecombe', 'Immanuel Quickley', 'Desmond Bane', 'Donovan Mitchell', 'Zion Williamson', 'Andrew Nembhard'],
      'LS': ['Ty Jerome', 'Ausar Thompson', 'Kyrie Irving', 'Deni Avdija', 'Wendell Carter Jr.', 'Zach LaVine', 'James Harden', 'CJ McCollum']}
rows = []
for ab_, names in TG.items():
    t = [k for k, v in d.abbrev.items() if v == ab_][0]
    for w in W.values(): w['ap'] = w['S'].allplay(t)['per_week']
    gets = [tuple(pid[n] for n in c) for c in itertools.combinations(names, 2)] + [tuple(pid[n] for n in c) for c in itertools.combinations(names, 3)]
    for g in gives:
        gi = [pid[x] for x in g]
        vg = sum(mval(x, PREM.get(x, 1)) for x in g)
        for ge in gets:
            vr = sum(mval(name(p)) for p in ge)
            ratio = vg / vr
            if ratio < 1.0 or ratio > 1.8:
                continue
            res = {}
            for k, w in W.items():
                S, Z = w['S'], w['Z']
                mine = [p for p in my0 if p not in gi] + list(ge)
                th = [p for p in S.base[t] if p not in ge] + gi
                note = []
                while len(mine) < len(my0):
                    a = max([p for p in w['pool'] if p not in mine], key=lambda p: S.lin_value(p, w['G'])); mine.append(a); note.append(f'I add {name(a)}')
                while len(th) > len(S.base[t]):
                    dr = min([p for p in th if p not in gi and Z.loc[p, 'lineup_slot'] != 'IR'], key=lambda p: Z.loc[p, 'z_total']); th.remove(dr); note.append(f'they drop {name(dr)}')
                ov = {MY_TEAM_ID: mine, t: th}; e = S.my_eval(ov)
                res[k] = dict(reg=e['reg_cats'] - w['b']['reg_cats'], po=e['po_cats'] - w['b']['po_cats'], mw=e['reg_mwins'] - w['b']['reg_mwins'],
                              s=e['score'] - w['b']['score'], th=S.allplay(t, ov)['per_week'] - w['ap'], note='; '.join(note), ov=ov,
                              cats={c: e['cat_reg'][c] + e['cat_po'][c] - w['b']['cat_reg'][c] - w['b']['cat_po'][c] for c in CATS})
            E, H = res['ESPN-blend'], res['HBB']
            rows.append(dict(team=ab_, give=' + '.join(g), get=' + '.join(name(p) for p in ge), market_ratio=ratio,
                             regE=E['reg'], regH=H['reg'], poE=E['po'], poH=H['po'], mwE=E['mw'], mwH=H['mw'], sE=E['s'], sH=H['s'],
                             themE=E['th'], themH=H['th'], note=E['note'],
                             up=', '.join(c for c in CATS if E['cats'][c] > .15 and H['cats'][c] > .15),
                             down=', '.join(c for c in CATS if E['cats'][c] < -.15 and H['cats'][c] < -.15), ovE=E['ov'], ovH=H['ov']))
    print(ab_, 'done', len(rows))
D = pd.DataFrame(rows); D['robust'] = D[['sE', 'sH']].min(axis=1); D['they_ok'] = D[['themE', 'themH']].max(axis=1) >= -0.05
D.drop(columns=['ovE', 'ovH']).to_csv(os.path.join(HERE, 'davion_partner_trades_3for2.csv'), index=False, float_format='%.3f')
pd.set_option('display.width', 320)
for ab_ in TG:
    x = D[(D.team == ab_) & (D.robust > 0) & D.they_ok].sort_values('robust', ascending=False)
    print(f'===== {ab_}: {len(x)} good')
    seen = set(); n = 0
    for _, r in x.iterrows():
        if r['get'] in seen: continue
        seen.add(r['get']); n += 1
        tE = W['ESPN-blend']['S'].monte_carlo(r.ovE, n=20000)[MY_TEAM_ID]['title']; tH = W['HBB']['S'].monte_carlo(r.ovH, n=20000)[MY_TEAM_ID]['title']
        print(f"{r.give:56} -> {r['get']:52} mkt {r.market_ratio:.2f} | reg {r.regE:+.2f}/{r.regH:+.2f} po {r.poE:+.2f}/{r.poH:+.2f} mw {r.mwE:+.2f}/{r.mwH:+.2f} title {tE:.0%}/{tH:.0%} | them {r.themE:+.2f}/{r.themH:+.2f} | up {r.up} | down {r.down} | {r.note}")
        if n == 7: break
