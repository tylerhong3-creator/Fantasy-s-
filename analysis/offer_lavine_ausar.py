import sys; sys.path.insert(0,'/home/user/Fantasy-s-/analysis')
import numpy as np, pandas as pd
from fantasy import *
from season import Season
d=Data('/home/user/Fantasy-s-/espn_fantasy_2026-27_2026-11-11')
HBB='/home/user/Fantasy-s-/analysis/hbb/HBB_supplement_Lukawhi_2026-11-11.xlsx'
br=blend_rates(d); hot=br.copy()
row=d.players[d.players.name=='Davion Mitchell'].iloc[0]; i=hot.index[hot.name=='Davion Mitchell'][0]
for s in STATS+['MIN']: hot.at[i,'r_'+s]=row['s27_'+s]/row.s27_GP
def world(rates):
    Z=zscores(rates); m=Model(d,Z); m.disp=estimate_dispersion(d,m); m.calib,_=calibrate(d,m); S=Season(m); S.set_strong(); return m,S
W={'ESPN-blend':world(br),'HBB':world(apply_hbb_rates(br,HBB)),'Davion hot start real':world(hot)}
P=d.players.set_index('name')
for nm in ['Davion Mitchell','Zach LaVine','Ausar Thompson']:
    r=P.loc[nm]; g=r.s27_GP
    print(f"{nm:16} {r.fantasy_team} {r.injury_status} GP {g:.0f} MIN {r.s27_MIN/g:.1f} PTS {r.s27_PTS/g:.1f} REB {r.s27_REB/g:.1f} AST {r.s27_AST/g:.1f} STL {r.s27_STL/g:.1f} BLK {r.s27_BLK/g:.1f} 3PM {r['s27_3PM']/g:.1f} TO {r.s27_TO/g:.1f} FG% {r.s27_FGM/r.s27_FGA:.3f} FT% {r.s27_FTM/r.s27_FTA:.3f} FTA {r.s27_FTA/g:.1f} | s26 GP {r.s26_GP} espn#{r.espn_rank_season}")
m0=W['ESPN-blend'][0]; pid={r['name']:p for p,r in m0.Z.iterrows()}
for k,(m,S) in W.items():
    for nm in ['Davion Mitchell','Zach LaVine','Ausar Thompson']:
        rr=m.rate[pid[nm]]; print(f"  [{k}] {nm:16} PTS {rr[SI['PTS']]:.1f} REB {rr[SI['REB']]:.1f} AST {rr[SI['AST']]:.1f} STL {rr[SI['STL']]:.1f} BLK {rr[SI['BLK']]:.1f} 3PM {rr[SI['3PM']]:.1f} TO {rr[SI['TO']]:.1f} FG% {rr[SI['FGM']]/rr[SI['FGA']]:.3f} FT% {rr[SI['FTM']]/rr[SI['FTA']]:.3f} avail {m.Z.loc[pid[nm],'health']}")
LS=[t for t,a in d.abbrev.items() if a=='LS'][0]
out=[]
for k,(m,S) in W.items():
    b=S.my_eval(); mc0=S.monte_carlo(n=30000); ap0=S.allplay(LS)['per_week']
    for get in ['Zach LaVine','Ausar Thompson']:
        mine=[p if p!=pid['Davion Mitchell'] else pid[get] for p in S.base[MY_TEAM_ID]]
        theirs=[p if p!=pid[get] else pid['Davion Mitchell'] for p in S.base[LS]]
        ov={MY_TEAM_ID:mine,LS:theirs}; e=S.my_eval(ov); mc=S.monte_carlo(ov,n=30000)
        cats={c:(e['cat_reg'][c]-b['cat_reg'][c]) for c in CATS}; catp={c:(e['cat_po'][c]-b['cat_po'][c]) for c in CATS}
        out.append(dict(world=k,get=get,reg_cat_wins=e['reg_cats']-b['reg_cats'],playoff_cat_wins=e['po_cats']-b['po_cats'],
            matchup_wins=e['reg_mwins']-b['reg_mwins'],po_match=(e['po_mwin']-b['po_mwin']),title0=mc0[MY_TEAM_ID]['title'],title=mc[MY_TEAM_ID]['title'],
            top2_0=mc0[MY_TEAM_ID]['top2'],top2=mc[MY_TEAM_ID]['top2'],them=S.allplay(LS,ov)['per_week']-ap0,
            **{'reg_'+c:v for c,v in cats.items()},**{'po_'+c:v for c,v in catp.items()}))
O=pd.DataFrame(out); pd.set_option('display.width',300)
print(O[['world','get','reg_cat_wins','playoff_cat_wins','matchup_wins','po_match','title0','title','top2_0','top2','them']].round(3).to_string())
print(O[['world','get']+['reg_'+c for c in CATS]].round(2).to_string())
print(O[['world','get']+['po_'+c for c in CATS]].round(2).to_string())
print('regular weeks left', len(d.regular_future))
O.to_csv('/home/user/Fantasy-s-/analysis/offer_lavine_ausar.csv',index=False,float_format='%.3f')
