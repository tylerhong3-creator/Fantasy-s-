"""Player value-to-team ratings (out of 10), sell-high trade search, and a category rank breakdown.
Writes analysis/team_breakdown.md. Run hbb_crosscheck.py first (uses crosscheck_my_players.csv).

Usage (repo root): python3 analysis/team_breakdown.py [export_folder] [hbb_xlsx]
"""
import itertools
import math
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from fantasy import (CATS, COUNT_CATS, SI, STATS, MY_TEAM_ID, Data, Model, blend_rates, zscores, estimate_dispersion,
                     calibrate, apply_hbb_rates, load_hbb_sheet, norm_name)
from season import Season

ROOT = os.path.dirname(HERE)
FOLDER = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'espn_fantasy_2026-27_2026-11-11')
HBB = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, 'hbb', 'HBB_supplement_Lukawhi_2026-11-11.xlsx')
d = Data(FOLDER)
ab = d.abbrev
owner = {t['team_id']: t['owner'].split()[0] for t in d.league['teams']}
tname = lambda t: f"{ab[t]} ({owner[t]})"
LUKA = 'Luka Doncic'


def world(rates):
    Z = zscores(rates)
    m = Model(d, Z)
    m.disp = estimate_dispersion(d, m)
    m.calib, _ = calibrate(d, m)
    S = Season(m)
    S.set_strong()
    return dict(m=m, S=S, Z=m.Z)


base_rates = blend_rates(d)
W = {'ESPN-blend': world(base_rates), 'HBB': world(apply_hbb_rates(base_rates, HBB))}
Z0 = W['ESPN-blend']['Z']
pid = {r['name']: p for p, r in Z0.iterrows()}
name = lambda p: Z0.loc[p, 'name']
my0 = list(W['ESPN-blend']['S'].base[MY_TEAM_ID])
PM = load_hbb_sheet(HBB, 'Player_Master')
PM['key'] = PM.Player.map(norm_name)
PM = PM.drop_duplicates('key').set_index('key')


def hbb(nm, col):
    k = norm_name(nm)
    return PM.loc[k, col] if k in PM.index and PM.loc[k, col] is not None else np.nan


def md(df, fmt=None):
    cols = list(df.columns)
    out = ['| ' + ' | '.join(map(str, cols)) + ' |', '|' + '|'.join('---' for _ in cols) + '|']
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


# =============================================================================== 1. ratings out of 10
CP = pd.read_csv(os.path.join(HERE, 'crosscheck_my_players.csv')).set_index('player')
P = d.players.set_index('name')
rows = []
for nm in CP.index:
    r = CP.loc[nm]
    keep = np.nanmean([r['keep score ESPN-blend'], r['keep score HBB']])
    if nm == LUKA:
        rating = 10.0
    elif 'IR' in str(r.status):
        rating = np.nan
    else:
        rating = float(np.clip(3 + keep, 1, 9.5))   # 3 = waiver level; +1 per season-score point above the best free agent
    espn_rank = P.loc[nm, 'espn_rank_season'] if nm in P.index else np.nan
    rows.append(dict(player=nm, rating=rating, keep=keep, keepE=r['keep score ESPN-blend'], keepH=r['keep score HBB'],
                     espn_rank=espn_rank, hbb_ros_rank=hbb(nm, 'Rank ROS'), hbb_season_rank=hbb(nm, 'Rank Season'),
                     status=r.status))
R = pd.DataFrame(rows).sort_values('rating', ascending=False, na_position='last')


def market_note(r):
    if r.player == LUKA:
        return 'untouchable'
    best_mkt = np.nanmin([r.espn_rank, r.hbb_season_rank])
    if 'IR' in str(r.status):
        return 'hold'
    if best_mkt <= 50 and r.hbb_ros_rank >= best_mkt + 20:
        if r.rating >= 6:
            return 'SELL HIGH only for a clear upgrade: market loves him, but he drives a category for you'
        return 'SELL HIGH: market rates him far above his value to you'
    if r.rating <= 3.5:
        return 'replaceable from waivers'
    if r.rating >= 7:
        return 'keep'
    return 'keep unless he headlines a clear upgrade'


R['trade view'] = R.apply(market_note, axis=1)
why = {
    'Luka Doncic': 'Carries PTS, AST, 3PM, STL; nobody else on the roster is close.',
    'Karl-Anthony Towns': 'Your REB anchor with good FG%; one of few bigs who also scores.',
    'Donovan Clingan': 'REB + BLK + FG% specialist; hurts FT% (~.65-.67).',
    'Dyson Daniels': 'Steals engine (~2.5/g) plus AST/REB; no threes, FT% ~.60.',
    'Evan Mobley': 'BLK/REB/FG% with real scoring; FT% ~.64 is the cost.',
    'Jabari Smith Jr.': 'Stretch big: threes + some BLK/REB with solid FT%.',
    'Brandin Podziemski': 'Do-a-bit-of-everything guard; nothing elite.',
    'Payton Pritchard': 'Threes + FT% + low TO; thin elsewhere.',
    'OG Anunoby': 'STL/3PM/BLK wing; minutes down lately.',
    'Davion Mitchell': 'Assists specialist (7+/g); little else, FT% ~.66-.69.',
    'Norman Powell': 'Scorer (3PM/FT%) but OUT with no return date; takes a bench spot.',
    'Kyshawn George': 'Hot recent stretch; HBB projects a smaller role ahead (ROS rank 159).',
    'Jrue Holiday': 'Solid FT%/AST, but replaceable by a free agent in both projections.',
    'Rui Hachimura': 'Waiver-level; the planned drop for Kris Dunn.',
    'Kawhi Leonard': 'Elite when healthy (PTS/STL/FT%), on IR with no return date.',
}
R['what he does'] = R.player.map(why).fillna('')

# =============================================================================== 2. category ranks
M = d.matchups
fin = M[M.status == 'final'].copy()
fin['FG%c'] = fin.FGM / fin.FGA
fin['FT%c'] = fin.FTM / fin.FTA
col = {c: c for c in COUNT_CATS}
col.update({'FG%': 'FG%c', 'FT%': 'FT%c'})
wk_rank = {c: [] for c in CATS}
for mp, g in fin.groupby('matchup_period'):
    for c in CATS:
        asc = (c == 'TO')
        rk = g[col[c]].rank(ascending=asc, method='min')
        wk_rank[c].append(int(rk[g.fantasy_team_id == MY_TEAM_ID].iloc[0]))
# season totals (per week averages), percentages from summed makes
agg = fin.groupby('fantasy_team_id')[['FGM', 'FGA', 'FTM', 'FTA'] + COUNT_CATS].sum()
nweeks = fin.groupby('fantasy_team_id').size()
avg = agg[COUNT_CATS].div(nweeks, axis=0)
avg['FG%'] = agg.FGM / agg.FGA
avg['FT%'] = agg.FTM / agg.FTA
# per-game (normalises for games played)
games = fin.groupby('fantasy_team_id').starter_games.sum()
pg = agg[COUNT_CATS].div(games, axis=0)


# projected ROS weekly averages (both worlds)
def proj_table(w):
    S = w['S']
    tot = {}
    for t in d.teams:
        acc = np.zeros(len(STATS))
        n = 0
        for mp in d.regular_future:
            if mp == d.cur_mp:
                continue
            acc += S.wk(t, mp, S.base[t])['mean']
            n += 1
        acc /= n
        row = {c: acc[SI[c]] for c in COUNT_CATS}
        row['FG%'] = acc[SI['FGM']] / acc[SI['FGA']]
        row['FT%'] = acc[SI['FTM']] / acc[SI['FTA']]
        tot[t] = row
    return pd.DataFrame(tot).T


PJ = {k: proj_table(w) for k, w in W.items()}
evals = {k: w['S'].my_eval() for k, w in W.items()}
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


def rank_of(df, c, t=MY_TEAM_ID):
    return int(df[c].rank(ascending=(c == 'TO'), method='min')[t])


def gaps(df, c):
    """my value, value of team one rank above, team one rank below (in that table's units)."""
    s = df[c].sort_values(ascending=(c == 'TO'))
    order = list(s.index)
    i = order.index(MY_TEAM_ID)
    up = s.iloc[i - 1] if i > 0 else np.nan
    dn = s.iloc[i + 1] if i + 1 < len(s) else np.nan
    return s.loc[MY_TEAM_ID], up, dn, (order[i - 1] if i > 0 else None)


cat_rows = []
for c in CATS:
    my, up, dn, upt = gaps(PJ['ESPN-blend'], c)
    gap = abs(up - my) if not np.isnan(up) else 0.0
    unit = '' if c in ('FG%', 'FT%') else ' /wk'
    gap_s = (f"{gap * 100:.2f} pct pts" if c in ('FG%', 'FT%') else f"{gap:.1f}") if upt else '- (1st)'
    rk_actual = [rank_of(avg, c)]
    cat_rows.append({
        'category': c,
        'wk1 / wk2 / wk3 rank': ' / '.join(map(str, wk_rank[c])),
        'avg weekly rank': np.mean(wk_rank[c]),
        'season rank (avg/week)': rank_of(avg, c),
        'per-game rank': rank_of(pg, c) if c in COUNT_CATS else rank_of(avg, c),
        'proj ROS rank (ESPN-blend)': rank_of(PJ['ESPN-blend'], c),
        'proj ROS rank (HBB)': rank_of(PJ['HBB'], c),
        'HBB profile rank': hbb_rank.get(c, ''),
        'win% reg': np.mean([evals[k]['cat_reg'][c] / evals[k]['reg_weeks'] for k in W]),
        'win% playoffs': np.mean([evals[k]['cat_po'][c] / evals[k]['po_weeks'] for k in W]),
        'gap to next rank up (proj)': gap_s + (unit if upt else ''),
    })
CR = pd.DataFrame(cat_rows)
CR['overall'] = CR[['avg weekly rank', 'proj ROS rank (ESPN-blend)', 'proj ROS rank (HBB)']].mean(axis=1)

# contributors per category (ESPN-blend rates × expected games)
contrib = {}
S0 = W['ESPN-blend']['S']
for c in CATS:
    vals = {}
    for p in my0:
        if Z0.loc[p, 'lineup_slot'] == 'IR':
            continue
        r = W['ESPN-blend']['m'].rate[p]
        if c in COUNT_CATS:
            vals[name(p)] = r[SI[c]]
        elif c == 'FG%':
            vals[name(p)] = r[SI['FGM']] - Z0.attrs.get('lg_fg', 0.48) * r[SI['FGA']]
        else:
            vals[name(p)] = r[SI['FTM']] - Z0.attrs.get('lg_ft', 0.80) * r[SI['FTA']]
    s = pd.Series(vals).sort_values(ascending=(c == 'TO'))
    contrib[c] = s

# =============================================================================== 3. sell-high trade search
E, H = W['ESPN-blend'], W['HBB']
for w in W.values():
    w['b'] = w['S'].my_eval()
    w['ap'] = {t: w['S'].allplay(t)['per_week'] for t in d.teams if t != MY_TEAM_ID}
chips = [x for x in ['Jabari Smith Jr.', 'Kyshawn George', 'Davion Mitchell', 'Jrue Holiday', 'OG Anunoby', 'Dyson Daniels',
                     'Brandin Podziemski', 'Payton Pritchard', 'Rui Hachimura'] if x in pid]
mkt = lambda nm: math.exp(-float(np.nanmin([P.loc[nm, 'espn_rank_season'] if P.loc[nm, 'espn_rank_season'] > 0 else 400,
                                             hbb(nm, 'Rank Season')])) / 40)
targets = []
for t in d.teams:
    if t == MY_TEAM_ID:
        continue
    for p in E['S'].base[t]:
        r = Z0.loc[p]
        if r.lineup_slot == 'IR' or r.injury_status == 'OUT':
            continue
        # archetype filter: scorer who also helps AST or BLK and is not an FT% disaster
        rr = E['m'].rate[p]
        ftp = rr[SI['FTM']] / rr[SI['FTA']] if rr[SI['FTA']] > 0 else 0
        if rr[SI['PTS']] >= 15 and (rr[SI['AST']] >= 4 or rr[SI['BLK']] >= 1.0) and ftp >= 0.74:
            targets.append((t, p))
print('targets', len(targets))


def try_trade(t, give, get):
    out = {}
    for k, w in W.items():
        S = w['S']
        mine = [p for p in my0 if p not in give] + list(get)
        theirs = [p for p in S.base[t] if p not in get] + list(give)
        note = ''
        if len(give) > len(get):
            pool = [p for p in w['Z'].index if w['Z'].loc[p, 'fantasy_team_id'] == 0 and w['Z'].loc[p, 's27_GP'] >= 5
                    and w['Z'].loc[p, 'injury_status'] != 'OUT' and p not in mine]
            G = S.gradient(MY_TEAM_ID)
            add = max(pool, key=lambda p: S.lin_value(p, G))
            mine.append(add)
            drp = min([p for p in theirs if p not in give and w['Z'].loc[p, 'lineup_slot'] != 'IR'],
                      key=lambda p: w['Z'].loc[p, 'z_total'])
            theirs.remove(drp)
            note = f'I add {name(add)}; they drop {name(drp)}'
        ov = {MY_TEAM_ID: mine, t: theirs}
        e = S.my_eval(ov)
        out[k] = dict(score=e['score'] - w['b']['score'], po=e['po_cats'] - w['b']['po_cats'],
                      them=S.allplay(t, ov)['per_week'] - w['ap'][t], note=note, ov=ov,
                      cats={c: e['cat_reg'][c] + e['cat_po'][c] - w['b']['cat_reg'][c] - w['b']['cat_po'][c] for c in CATS})
    return out


res = []
combos = [(c,) for c in chips] + list(itertools.combinations(chips, 2))
for t, p in targets:
    mv_get = mkt(name(p))
    for give in combos:
        mv_give = sum(mkt(x) for x in give)
        if mv_give < 0.85 * mv_get or mv_give > 2.2 * mv_get:   # realistic by public rankings
            continue
        gids = [pid[x] for x in give]
        o = try_trade(t, gids, [p])
        if min(o['ESPN-blend']['score'], o['HBB']['score']) <= 0:
            continue
        if max(o['ESPN-blend']['them'], o['HBB']['them']) < -0.05:
            continue
        res.append(dict(partner=t, give=' + '.join(give), get=name(p), mkt_ratio=mv_give / mv_get,
                        sE=o['ESPN-blend']['score'], sH=o['HBB']['score'], poE=o['ESPN-blend']['po'], poH=o['HBB']['po'],
                        thE=o['ESPN-blend']['them'], thH=o['HBB']['them'], note=o['ESPN-blend']['note'],
                        catsE=o['ESPN-blend']['cats'], catsH=o['HBB']['cats'], ovE=o['ESPN-blend']['ov'], ovH=o['HBB']['ov']))
TRD = pd.DataFrame(res)
TRD['robust'] = TRD[['sE', 'sH']].min(axis=1)
TRD = TRD.sort_values('robust', ascending=False)
pick, seen_get, per_team = [], set(), {}
for _, r in TRD.iterrows():
    if r['get'] in seen_get or per_team.get(r.partner, 0) >= 2:
        continue
    pick.append(r)
    seen_get.add(r['get'])
    per_team[r.partner] = per_team.get(r.partner, 0) + 1
    if len(pick) == 8:
        break
mc0 = {k: w['S'].monte_carlo(n=20000)[MY_TEAM_ID]['title'] for k, w in W.items()}
for r in pick:
    r['titleE'] = E['S'].monte_carlo(r.ovE, n=20000)[MY_TEAM_ID]['title']
    r['titleH'] = H['S'].monte_carlo(r.ovH, n=20000)[MY_TEAM_ID]['title']
TRD.drop(columns=['catsE', 'catsH', 'ovE', 'ovH']).assign(partner=lambda x: x.partner.map(ab)).to_csv(
    os.path.join(HERE, 'sell_high_trades.csv'), index=False, float_format='%.3f')
print('sell-high trades found', len(TRD))

# =============================================================================== report
L = []
w = L.append
w('# Lukawhi: player ratings, trade targets, category breakdown')
w(f"\nESPN export {d.league['current_date']} + Hashtag Basketball supplement. Every number is from those two files; "
  "every simulation was run with both projection sets (my ESPN-blend and HBB) and averaged.\n")

w('## 1. Every player, rated for YOUR team (out of 10)\n')
w('**Scale:** 3 = what you could get off waivers today. Each point above 3 ≈ one extra category win over the rest of the season '
  '(playoff weeks count triple) compared with swapping him for the best free agent. Luka is set to 10. '
  '"ESPN rank" = ESPN season-to-date rank (what other managers see); "HBB ROS rank" = Hashtag Basketball rest-of-season projection rank.\n')
tab = R[['player', 'rating', 'espn_rank', 'hbb_ros_rank', 'what he does', 'trade view']].copy()
tab['rating'] = [('~8 when healthy (IR, no return date)' if np.isnan(x) else f'{x:.1f}') for x in tab.rating]
tab['espn_rank'] = tab.espn_rank.map(lambda x: '' if np.isnan(x) else int(x))
tab['hbb_ros_rank'] = tab.hbb_ros_rank.map(lambda x: '' if np.isnan(x) else int(x))
w(md(tab.rename(columns={'rating': 'value to you /10', 'espn_rank': 'ESPN rank', 'hbb_ros_rank': 'HBB ROS rank'})))
sh = list(R[R['trade view'].str.startswith('SELL')].player)
w(f"\n**Sell-high list:** {', '.join(sh)}. Other managers see these players near the top of ESPN's season rankings, "
  "but they're worth less to your team (or HBB projects them to fade), so they buy more in a trade than they give you on the court.")
w("**Never trade:** Luka, KAT. **Hold:** Kawhi on IR. **Free roster spots:** Rui (drop for Kris Dunn), then Jrue/Powell.\n")

w('## 2. What to trade for\n')
w("**The target:** a scorer (15+ points) who also brings **assists or blocks**, with an FT% that won't sink you further (.74+). "
  "Those are your swing categories, and points are the one that most often decides playoff weeks. "
  "Pay with sell-high players and the guards who overlap (Jrue, Davion, Pritchard, Podziemski), not with KAT, Mobley or Clingan "
  "(they make REB/BLK/FG% strengths).\n")
w(f"I tested every target on other teams that fits that profile ({len(targets)} players) against 1- and 2-player packages of your chips, "
  "kept trades that are realistic by public rankings (what you send is worth 0.85-2.2× what you get by ESPN/HBB season rank) "
  f"and that the other team doesn't lose categories on. {len(TRD)} passed and helped you under both projections. "
  f"Current title odds: {mc0['ESPN-blend']:.0%} (ESPN-blend) / {mc0['HBB']:.0%} (HBB).\n")
rows = []
for r in pick:
    up = [c for c in CATS if r.catsE[c] > 0.15 and r.catsH[c] > 0.15]
    dn = [c for c in CATS if r.catsE[c] < -0.15 and r.catsH[c] < -0.15]
    rows.append({'give': r.give, 'get': r['get'], 'team': tname(r.partner),
                 'my gain (ESPN-blend / HBB)': f"{r.sE:+.1f} / {r.sH:+.1f}",
                 'title odds': f"{mc0['ESPN-blend']:.0%}→{r.titleE:.0%} / {mc0['HBB']:.0%}→{r.titleH:.0%}",
                 'their cats/wk': f"{r.thE:+.2f} / {r.thH:+.2f}",
                 'cats up / down': f"{', '.join(up) or '-'} / {', '.join(dn) or '-'}",
                 'roster': r.note or '-'})
w(md(pd.DataFrame(rows)))
w('\n"My gain" = extra category wins over the season (playoff weeks ×3). Full list: sell_high_trades.csv. '
  'The earlier best deal, Daniels + Jrue for Devin Booker (NYX2), remains a top option (see moves_report.md).\n')

w('## 3. Category breakdown\n')
crs = CR.copy()
crs['win% reg'] = crs['win% reg'].map(lambda x: f'{x:.0%}')
crs['win% playoffs'] = crs['win% playoffs'].map(lambda x: f'{x:.0%}')
crs = crs.sort_values('overall')
w(md(crs.drop(columns=['overall']), {'avg weekly rank': '{:.1f}'}))
w(f"\n**Average rank across all 9 categories:** actual weeks 1-3 {np.mean([np.mean(v) for v in wk_rank.values()]):.1f}; "
  f"projected rest of season {CR['proj ROS rank (ESPN-blend)'].mean():.1f} (ESPN-blend) / {CR['proj ROS rank (HBB)'].mean():.1f} (HBB). "
  "Win% = chance to win that category in a given week (regular season vs your real opponents; playoffs vs the strongest teams), averaged over both projections. "
  "Gap = how much more per week you'd need to pass the team just above you in the projection.\n")

w('### What to do with each category\n')
for _, r in CR.sort_values('overall').iterrows():
    c = r.category
    s = contrib[c]
    top3 = ', '.join(f"{n} ({v:+.2f})" if c in ('FG%', 'FT%') else f"{n} ({v:.1f})" for n, v in s.head(3).items())
    bot = ', '.join((f"{n} ({v:.1f})" if c == 'TO' else f"{n} ({v:+.2f})") for n, v in s.tail(2).items()) if c in ('FG%', 'FT%', 'TO') else ''
    wr, wp = float(r['win% reg']), float(r['win% playoffs'])
    if wr >= 0.62 and wp >= 0.55:
        plan = 'SOLIDIFY: a strength. Keep the players who drive it; don\'t trade them away for help elsewhere.'
    elif wr >= 0.45 and wp >= 0.40:
        plan = 'IMPROVE: a true swing category. Small upgrades flip weeks here.'
    elif wp < 0.40 and wr >= 0.45:
        plan = 'IMPROVE FOR THE PLAYOFFS: fine in the regular season, but the playoff teams beat you here.'
    else:
        plan = 'SOFT: weakest category. Don\'t spend assets on it; just avoid making it worse.'
    line = f"- **{c}** ({plan}) Rank now {r['season rank (avg/week)']}, projected {r['proj ROS rank (ESPN-blend)']}/{r['proj ROS rank (HBB)']}; " \
           f"wins {wr:.0%} of regular weeks, {wp:.0%} of playoff weeks. Top contributors: {top3}."
    if bot:
        line += f" Biggest drags: {bot}."
    w(line)
w('\nContributor numbers are per game (FG%/FT%: makes above a league-average shooter on the same attempts; TO: fewer is better, so the list starts with the lowest).\n')

w('### Priorities\n')
w("1. **PTS (playoffs).** The biggest gap against playoff teams. Every trade above adds points.")
w("2. **AST.** HBB ranks you 9th on projected top-10 players; one assist-heavy scorer moves it most per unit of talent.")
w("3. **BLK and FG%.** Swing categories. Your bigs (Mobley, Clingan, KAT, Jabari) carry both, so keep them.")
w("4. **Solidify REB, STL, 3PM, TO** by keeping KAT/Clingan (REB) and Luka/Pritchard (3PM). Daniels is most of your steals: "
  "if he goes (e.g. in the Booker deal), make sure the return or a pickup like Kris Dunn covers STL.")
w("5. **FT% stays soft.** Last in both projections; an elite FT% specialist only moves it ~0.07 categories a week. Don't chase it.")
open(os.path.join(HERE, 'team_breakdown.md'), 'w').write('\n'.join(L) + '\n')
print('team_breakdown.md written')
