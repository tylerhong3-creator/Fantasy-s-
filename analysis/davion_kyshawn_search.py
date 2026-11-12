import sys, math, itertools
sys.path.insert(0, '/home/user/Fantasy-s-/analysis')
import numpy as np, pandas as pd
from fantasy import *
from season import Season
d = Data('/home/user/Fantasy-s-/espn_fantasy_2026-27_2026-11-11')
HBB = '/home/user/Fantasy-s-/analysis/hbb/HBB_supplement_Lukawhi_2026-11-11.xlsx'
def world(rates):
    Z = zscores(rates); m = Model(d, Z); m.disp = estimate_dispersion(d, m); m.calib, _ = calibrate(d, m)
    S = Season(m); S.set_strong(); return dict(m=m, S=S, Z=m.Z)
br = blend_rates(d)
W = {'E': world(br), 'H': world(apply_hbb_rates(br, HBB))}
Z0 = W['E']['Z']; pid = {r['name']: p for p, r in Z0.iterrows()}; name = lambda p: Z0.loc[p, 'name']
PM = load_hbb_sheet(HBB, 'Player_Master'); PM['key'] = PM.Player.map(norm_name); PM = PM.drop_duplicates('key').set_index('key')
hb = lambda n, c: PM.loc[norm_name(n), c] if norm_name(n) in PM.index else np.nan
P = d.players.set_index('name')
my0 = list(W['E']['S'].base[MY_TEAM_ID])
for w in W.values():
    w['b'] = w['S'].my_eval(); w['ap'] = {t: w['S'].allplay(t)['per_week'] for t in d.teams if t != MY_TEAM_ID}
    w['G'] = w['S'].gradient(MY_TEAM_ID)
DM, KG = pid['Davion Mitchell'], pid['Kyshawn George']
def run(t, give, get):
    o = {}
    for k, w in W.items():
        S, Z = w['S'], w['Z']
        mine = [p for p in my0 if p not in give] + list(get); theirs = [p for p in S.base[t] if p not in get] + list(give)
        note = []
        if len(give) > len(get):
            pool = [p for p in Z.index if Z.loc[p,'fantasy_team_id']==0 and Z.loc[p,'s27_GP']>=5 and Z.loc[p,'injury_status']!='OUT']
            add = max(pool, key=lambda p: S.lin_value(p, w['G'])); mine.append(add); note.append(f'I add {name(add)}')
            drp = min([p for p in theirs if p not in give and Z.loc[p,'lineup_slot']!='IR'], key=lambda p: Z.loc[p,'z_total'])
            theirs.remove(drp); note.append(f'they drop {name(drp)}')
        ov = {MY_TEAM_ID: mine, t: theirs}; e = S.my_eval(ov)
        o[k] = dict(s=e['score']-w['b']['score'], po=e['po_cats']-w['b']['po_cats'], th=S.allplay(t, ov)['per_week']-w['ap'][t],
                    cats={c: e['cat_reg'][c]+e['cat_po'][c]-w['b']['cat_reg'][c]-w['b']['cat_po'][c] for c in CATS}, ov=ov, note='; '.join(note))
    return o
rows = []
for t in d.teams:
    if t == MY_TEAM_ID: continue
    for p in W['E']['S'].base[t]:
        r = Z0.loc[p]
        if r.lineup_slot == 'IR' or r.injury_status == 'OUT': continue
        er = P.loc[r['name'], 'espn_rank_season']; hr = hb(r['name'], 'Rank Season'); hros = hb(r['name'], 'Rank ROS')
        mk = np.nanmin([er if er > 0 else 999, hr])
        for give, lab, lo in (((DM, KG), 'Davion + Kyshawn', 18), ((DM,), 'Davion', 30), ((KG,), 'Kyshawn', 30)):
            if mk < lo or mk > 160: continue     # realistic: 2-for-1 can reach ~top-20 by public rank; 1-for-1 ~top-30
            o = run(t, list(give), [p])
            rows.append(dict(give=lab, get=r['name'], team=d.abbrev[t], espn_rank=er, hbb_season=hr, hbb_ros=hros,
                             sE=o['E']['s'], sH=o['H']['s'], poE=o['E']['po'], poH=o['H']['po'], thE=o['E']['th'], thH=o['H']['th'],
                             up=', '.join(c for c in CATS if o['E']['cats'][c] > .15 and o['H']['cats'][c] > .15),
                             dn=', '.join(c for c in CATS if o['E']['cats'][c] < -.15 and o['H']['cats'][c] < -.15),
                             note=o['E']['note'], ovE=o['E']['ov'], ovH=o['H']['ov'],
                             pts=W['E']['m'].rate[p][SI['PTS']], ast=W['E']['m'].rate[p][SI['AST']], reb=W['E']['m'].rate[p][SI['REB']],
                             blk=W['E']['m'].rate[p][SI['BLK']], tpm=W['E']['m'].rate[p][SI['3PM']],
                             ft=W['E']['m'].rate[p][SI['FTM']]/max(W['E']['m'].rate[p][SI['FTA']],1e-9)))
D = pd.DataFrame(rows); D['robust'] = D[['sE','sH']].min(axis=1)
D['ok_them'] = D[['thE','thH']].max(axis=1) >= -0.05
G = D[(D.robust > 0) & D.ok_them].sort_values('robust', ascending=False)
mc0 = {k: w['S'].monte_carlo(n=20000)[MY_TEAM_ID]['title'] for k, w in W.items()}
print('baseline title', mc0, 'n good', len(G), 'of', len(D))
for lab in ['Davion + Kyshawn', 'Davion', 'Kyshawn']:
    g = G[G.give == lab].head(8)
    print(f'\n=== {lab} ===')
    for _, r in g.iterrows():
        tE = W['E']['S'].monte_carlo(r.ovE, n=20000)[MY_TEAM_ID]['title']; tH = W['H']['S'].monte_carlo(r.ovH, n=20000)[MY_TEAM_ID]['title']
        print(f"{r['get']:24} {r.team:5} espn#{r.espn_rank:>4.0f} hbbS#{r.hbb_season:>4.0f} hbbROS#{r.hbb_ros:>4.0f} | me {r.sE:+5.1f}/{r.sH:+5.1f} po {r.poE:+.2f}/{r.poH:+.2f} title {tE:.0%}/{tH:.0%} | them {r.thE:+.2f}/{r.thH:+.2f} | up {r.up} | down {r.dn} | {r.pts:.1f}p {r.ast:.1f}a {r.reb:.1f}r {r.blk:.1f}b {r.tpm:.1f}3 ft{r.ft:.3f} | {r.note}")
D.drop(columns=['ovE','ovH']).to_csv('/home/user/Fantasy-s-/analysis/davion_kyshawn_trades.csv', index=False, float_format='%.3f')
