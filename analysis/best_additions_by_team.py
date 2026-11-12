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

# value of ADDING each other-team player to my roster (I cut whichever of my bench pieces hurts least)
cut_pool = ['Rui Hachimura', 'Jrue Holiday', 'Norman Powell', 'Kyshawn George', 'Payton Pritchard']
rows = []
for t in d.teams:
    if t == MY_TEAM_ID: continue
    for p in W['ESPN-blend']['S'].base[t]:
        r = Z0.loc[p]
        if r.lineup_slot == 'IR' or 'not projected' in r['flags']: continue
        out = {}
        for k, w in W.items():
            S = w['S']; best = None
            for c in cut_pool:
                mine = [q for q in my0 if q != pid[c]] + [p]
                th = [q for q in S.base[t] if q != p]
                e = S.my_eval({MY_TEAM_ID: mine, t: th})
                if best is None or e['score'] > best[0]['score']: best = (e, c)
            e, c = best
            out[k] = dict(s=e['score'] - w['b']['score'], reg=e['reg_cats'] - w['b']['reg_cats'], po=e['po_cats'] - w['b']['po_cats'],
                          cut=c, cats={cc: e['cat_reg'][cc] + e['cat_po'][cc] - w['b']['cat_reg'][cc] - w['b']['cat_po'][cc] for cc in CATS})
        E, H = out['ESPN-blend'], out['HBB']
        rows.append(dict(team=d.abbrev[t], owner=[x['owner'].split()[0] for x in d.league['teams'] if x['team_id'] == t][0],
                         player=r['name'], status=r.injury_status, mkt_rank=round(mrank(r['name'])), espn=P.loc[r['name'], 'espn_rank_season'],
                         sE=E['s'], sH=H['s'], regE=E['reg'], regH=H['reg'], poE=E['po'], poH=H['po'], cut=E['cut'],
                         up=', '.join(c for c in CATS if E['cats'][c] > .25 and H['cats'][c] > .25)))
D = pd.DataFrame(rows); D['avg'] = D[['sE', 'sH']].mean(axis=1)
D.to_csv(os.path.join(HERE, 'best_additions_by_team.csv'), index=False, float_format='%.3f')
pd.set_option('display.width', 300)
for tm, g in D.groupby('team'):
    print(g.sort_values('avg', ascending=False).head(4)[['team','owner','player','status','espn','mkt_rank','sE','sH','regE','regH','poE','poH','cut','up']].round(2).to_string(header=False))
