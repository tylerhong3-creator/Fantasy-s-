import sys; sys.path.insert(0,'/home/user/Fantasy-s-/analysis')
import pandas as pd, numpy as np, openpyxl
from fantasy import norm_name, load_hbb_sheet
pd.set_option('display.width',250); pd.set_option('display.max_rows',200)
def load(f):
    rows=list(openpyxl.load_workbook(f,read_only=True,data_only=True).worksheets[0].iter_rows(values_only=True))
    df=pd.DataFrame(rows[1:],columns=rows[0]); df=df[df['R#']!='R#'].copy(); df['R#']=df['R#'].map(lambda x: str(x).split()[0])
    for c in ['R#','GP','TOTAL','PTS']: df[c]=pd.to_numeric(df[c])
    df['key']=df.PLAYER.map(norm_name); return df.drop_duplicates('key').set_index('key')
R=load('analysis/hbb/RestOfSeasonRankings.xlsx'); N=load('analysis/hbb/CurrentRankings.xlsx')
old=load_hbb_sheet('analysis/hbb/HBB_supplement_Lukawhi_2026-11-11.xlsx','Proj_ROS'); old['key']=old.Player.map(norm_name); old=old.drop_duplicates('key').set_index('key')
P=pd.read_csv('espn_fantasy_2026-27_2026-11-11/players.csv'); P['key']=P.name.map(norm_name); P=P.set_index('key')
com=R.index.intersection(old.index)
print(len(R),len(N),'ROS rank corr vs Nov11 proj:', round(np.corrcoef(R.loc[com,'R#'].astype(float),old.loc[com,'Rank'].astype(float))[0,1],3), 'same PTS frac', (R.loc[com,'PTS']==old.loc[com,'PTS'].astype(float)).mean())
print('now GP max', N.GP.max())
def g(D,k,c): return D.loc[k,c] if k in D.index else np.nan
rows=[]
for k,r in P.iterrows():
    rows.append(dict(player=r['name'],team=r.fantasy_team,inj=r.injury_status,espn=r.espn_rank_season,
                     ros=g(R,k,'R#'),ros_val=g(R,k,'TOTAL'),now=g(N,k,'R#'),now_val=g(N,k,'TOTAL'),gp=g(N,k,'GP')))
T=pd.DataFrame(rows); T['gap']=T.ros-T.now
T.to_csv('analysis/hbb_rank_compare.csv',index=False)
print('\nMY ROSTER'); print(T[T.team=='LK'].sort_values('ros').to_string())
tg=['Miles Bridges','Derrick White','Jaylen Brown','Trae Young','Michael Porter Jr.','Cameron Boozer','Devin Booker','Cade Cunningham','Cooper Flagg','LeBron James','Desmond Bane','Tyler Herro','Jalen Johnson','Dejounte Murray','LaMelo Ball','Domantas Sabonis','Naz Reid','Brandon Miller','Kris Dunn','Collin Gillespie']
print('\nTARGETS'); print(T[T.player.isin(tg)].sort_values('ros').to_string())
o=T[(T.team!='LK')&(T.team!='FA')&(T.inj!='OUT')]
print('\nBUY-LOW other teams (ROS top 90)'); print(o[(o.ros<=90)].sort_values('gap').head(20).to_string())
print('\nFA by ROS'); print(T[T.team=='FA'].sort_values('ros').head(12).to_string())
