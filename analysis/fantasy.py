"""Core library for the Lukawhi 9-cat H2H analysis.

Everything here reads only the ESPN export folder. Nothing is downloaded and no
stats are invented. Re-run run_analysis.py after dropping in a fresh export.
"""
import json
import math
import os
from functools import lru_cache

import numpy as np
import pandas as pd

STATS = ['FGM', 'FGA', 'FTM', 'FTA', '3PM', 'PTS', 'REB', 'AST', 'STL', 'BLK', 'TO']
SI = {s: i for i, s in enumerate(STATS)}
CATS = ['PTS', 'REB', 'AST', 'STL', 'BLK', '3PM', 'FG%', 'FT%', 'TO']
COUNT_CATS = ['PTS', 'REB', 'AST', 'STL', 'BLK', '3PM', 'TO']
SLOTS = ['PG', 'SG', 'SF', 'PF', 'C', 'G', 'F', 'UTIL', 'UTIL', 'UTIL']
MY_TEAM_ID = 5

# ---- modelling constants (explained in the report) ----
K_GAMES = 12          # s27 weight = GP / (GP + 12): 12 games played -> 50% this season
FG_PRIOR_ATT = 150    # FG% shrinks toward the prior as if the prior were 150 extra FGA
FT_PRIOR_ATT = 60     # FT% prior worth 60 FTA
PRIOR_PROJ_W = 0.6    # inside the prior: ESPN 2026-27 projection 60%, last season 40%
OUT_PERIODS = 2       # OUT (no date given) -> miss the rest of this week + next week
DTD_AVAIL = 0.75      # DAY_TO_DAY -> 75% chance to play each remaining game this week
DEFAULT_HEALTH = 0.85
PLAYOFF_PERIODS = [20, 21, 22]
PLAYOFF_WEIGHT = 3.0  # each playoff week counts 3x a regular week in the ranking score
Z_POOL = 150


def ncdf(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def npdf(x):
    return math.exp(-0.5 * x * x) / math.sqrt(2 * math.pi)


# --------------------------------------------------------------------------- data
class Data:
    def __init__(self, folder):
        self.folder = folder
        rd = lambda f: pd.read_csv(os.path.join(folder, f))
        self.league = json.load(open(os.path.join(folder, 'league.json')))
        self.players = rd('players.csv')
        self.logs = rd('player_game_logs.csv')
        self.matchups = rd('matchups.csv')
        self.allplay = rd('all_play_matrix.csv')
        self.summary = rd('team_summary.csv')
        self.sched = rd('nba_schedule.csv')
        self.gpp = rd('nba_games_per_matchup_period.csv')
        L = self.league
        self.cur_sp = L['current_scoring_period']
        self.cur_mp = L['current_matchup_period']
        self.periods = {m['matchup_period']: m for m in L['matchup_periods']}
        self.teams = {t['team_id']: t for t in L['teams']}
        self.abbrev = {t['team_id']: t['abbrev'] for t in L['teams']}
        self.completed = sorted(self.matchups.loc[self.matchups.status == 'final', 'matchup_period'].unique())
        # days (scoring periods) per matchup period, with the NBA teams playing each day
        games_by_sp = self.sched.groupby('scoring_period')
        self.day_teams = {}
        for sp, g in games_by_sp:
            self.day_teams[int(sp)] = frozenset(g.home) | frozenset(g.away)
        self.period_days = {}
        for mp, m in self.periods.items():
            days = [sp for sp in range(m['first_scoring_period'], m['last_scoring_period'] + 1)]
            if mp == self.cur_mp:
                days = [d for d in days if d > self.cur_sp]   # today's games already in matchups.csv
            if mp < self.cur_mp:
                days = []
            self.period_days[mp] = days
        self.future_periods = [mp for mp in sorted(self.periods) if mp >= self.cur_mp]
        self.regular_future = [mp for mp in self.future_periods if self.periods[mp]['type'] == 'regular']
        self.schedule = L['schedule']

    def opponent(self, team_id, mp):
        for s in self.schedule:
            if s['matchup_period'] == mp and team_id in (s['home_team_id'], s['away_team_id']):
                return s['away_team_id'] if s['home_team_id'] == team_id else s['home_team_id']
        return None

    def current_partial(self):
        """Category totals already banked in the in-progress week, per team."""
        m = self.matchups[(self.matchups.matchup_period == self.cur_mp)]
        out = {}
        for _, r in m.iterrows():
            out[int(r.fantasy_team_id)] = np.array([r[s] for s in STATS], dtype=float)
        return out


# --------------------------------------------------------------------------- checks
def check_logs_vs_matchups(d):
    L = d.logs[d.logs.counts_for_team == 1]
    agg = L.groupby(['fantasy_team_id', 'matchup_period'])[['GP'] + STATS].sum().reset_index()
    m = d.matchups.merge(agg, on=['fantasy_team_id', 'matchup_period'], how='left', suffixes=('', '_log'))
    rows = []
    for _, r in m.iterrows():
        diffs = {}
        for s in STATS:
            if r[s] != r[s + '_log']:
                diffs[s] = (r[s], r[s + '_log'])
        if r['starter_games'] != r['GP']:
            diffs['games'] = (r['starter_games'], r['GP'])
        for pc, (mk, at) in {'FG%': ('FGM', 'FGA'), 'FT%': ('FTM', 'FTA')}.items():
            calc = r[mk] / r[at] if r[at] else 0
            if abs(calc - r[pc]) > 0.00051:
                diffs[pc] = (r[pc], round(calc, 4))
        rows.append(dict(matchup_period=r.matchup_period, team=r.fantasy_team, status=r.status,
                         ok=not diffs, mismatches=json.dumps({k: [float(x) for x in v] for k, v in diffs.items()})))
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- player rates
def _pg(row, pre):
    gp = row.get(pre + '_GP')
    if gp is None or pd.isna(gp) or gp <= 0:
        return None, 0
    v = {s: (row[pre + '_' + s] if not pd.isna(row[pre + '_' + s]) else 0.0) / gp for s in STATS + ['MIN']}
    return v, gp


def blend_rates(d):
    """Per-game rest-of-season rates for every player (see report for the weights)."""
    out = []
    for _, row in d.players.iterrows():
        s27, g27 = _pg(row, 's27')
        proj, gp_proj = _pg(row, 'proj27')
        s26, g26 = _pg(row, 's26')
        # prior = ESPN projection + last season
        if proj and s26:
            w26 = (1 - PRIOR_PROJ_W) * min(1.0, g26 / 40.0)
            wp = PRIOR_PROJ_W
            prior = {s: (wp * proj[s] + w26 * s26[s]) / (wp + w26) for s in proj}
            src = 'proj+s26'
        elif proj:
            prior, src = proj, 'proj'
        elif s26:
            prior, src = s26, 's26'
        else:
            prior, src = None, 'none'
        if s27 is None and prior is None:
            continue
        if prior is None:
            rate, w = dict(s27), 1.0
            src = 's27 only'
        elif s27 is None:
            rate, w = dict(prior), 0.0
        else:
            w = g27 / (g27 + K_GAMES)
            rate = {s: w * s27[s] + (1 - w) * prior[s] for s in s27}
            # shooting percentages: shrink by attempts, not games
            for mk, at, A in (('FGM', 'FGA', FG_PRIOR_ATT), ('FTM', 'FTA', FT_PRIOR_ATT)):
                p_prior = prior[mk] / prior[at] if prior[at] > 0 else 0.0
                made, att = row['s27_' + mk], row['s27_' + at]
                pct = (made + p_prior * A) / (att + A) if (att + A) > 0 else 0
                rate[mk] = rate[at] * pct
        l15, g15 = _pg(row, 'l15')
        trend = ''
        if l15 and g15 >= 3 and s27:
            dm = l15['MIN'] - rate['MIN']
            if dm >= 4:
                trend = f'minutes up (+{dm:.0f} last 15d)'
            elif dm <= -4:
                trend = f'minutes down ({dm:.0f} last 15d)'
        health = DEFAULT_HEALTH
        if not pd.isna(row['proj27_GP']) and row['proj27_GP'] > 0:
            health = float(np.clip(row['proj27_GP'] / 82.0, 0.6, 0.95))
        status = row['injury_status']
        flags = []
        if row['lineup_slot'] == 'IR':
            flags.append('on IR slot: not projected (no return date in data)')
        if status == 'OUT':
            if pd.isna(row['s27_GP']) or row['s27_GP'] == 0:
                flags.append('OUT, no games this season: not projected')
            else:
                flags.append(f'OUT: assumed back after week {d.cur_mp + OUT_PERIODS - 1} (no date in data)')
        if status == 'DAY_TO_DAY':
            flags.append('day-to-day: 75% for rest of this week')
        if g27 < 5:
            flags.append(f'small sample ({int(g27)} GP)')
        out.append(dict(player_id=int(row.player_id), name=row['name'], fantasy_team_id=int(row.fantasy_team_id),
                        fantasy_team=row.fantasy_team, roster_status=row.roster_status, lineup_slot=row.lineup_slot,
                        eligible_pos=row.eligible_pos, pro_team=row.pro_team, injury_status=status,
                        s27_GP=0 if pd.isna(row['s27_GP']) else int(row['s27_GP']), w_s27=round(w, 2), prior_src=src,
                        health=round(health, 2), trend=trend, flags='; '.join(flags),
                        espn_rank_season=row.espn_rank_season, pct_owned=row.pct_owned,
                        **{f'r_{s}': rate[s] for s in STATS + ['MIN']}))
    return pd.DataFrame(out)


def zscores(rates):
    R = rates.copy()
    pool = R.copy()
    for _ in range(4):
        lg_fg = pool.r_FGM.sum() / pool.r_FGA.sum()
        lg_ft = pool.r_FTM.sum() / pool.r_FTA.sum()
        R['imp_FG'] = R.r_FGM - lg_fg * R.r_FGA
        R['imp_FT'] = R.r_FTM - lg_ft * R.r_FTA
        pool = R.loc[pool.index]
        cols = {'PTS': 'r_PTS', 'REB': 'r_REB', 'AST': 'r_AST', 'STL': 'r_STL', 'BLK': 'r_BLK', '3PM': 'r_3PM',
                'FG%': 'imp_FG', 'FT%': 'imp_FT', 'TO': 'r_TO'}
        tot = 0
        for c, col in cols.items():
            mu, sd = pool[col].mean(), pool[col].std()
            z = (R[col] - mu) / sd
            if c == 'TO':
                z = -z
            R['z_' + c] = z
            tot = tot + z
        R['z_total'] = tot
        pool = R.sort_values('z_total', ascending=False).head(Z_POOL)
    R.attrs['lg_fg'], R.attrs['lg_ft'] = lg_fg, lg_ft
    return R


# --------------------------------------------------------------------------- simulator
def eligible_slots(pos):
    toks = set(pos.replace(' ', '').split('/'))
    s = set(['UTIL'])
    for t in toks:
        s.add(t)
        if t in ('PG', 'SG'):
            s.add('G')
        if t in ('SF', 'PF'):
            s.add('F')
    return [i for i, sl in enumerate(SLOTS) if sl in s]


def match_day(players, elig):
    """Max matching of players (already sorted by priority) to the 10 slots; returns started players."""
    slot_owner = [-1] * len(SLOTS)

    def tryp(p, seen):
        for s in elig[p]:
            if s in seen:
                continue
            seen.add(s)
            if slot_owner[s] == -1 or tryp(slot_owner[s], seen):
                slot_owner[s] = p
                return True
        return False

    if len(players) <= 3:
        return list(players)
    for p in players:
        tryp(p, set())
    return [p for p in slot_owner if p != -1]


class Model:
    def __init__(self, d, Z):
        self.d = d
        self.Z = Z.set_index('player_id', drop=False)
        self.rate = {pid: np.array([r['r_' + s] for s in STATS]) for pid, r in self.Z.iterrows()}
        self.elig = {pid: eligible_slots(r.eligible_pos) for pid, r in self.Z.iterrows()}
        self.prio = {pid: r.z_total for pid, r in self.Z.iterrows()}
        self.team = {pid: r.pro_team for pid, r in self.Z.iterrows()}
        self.partial = d.current_partial()
        # availability per player per period
        self.avail = {}
        for pid, r in self.Z.iterrows():
            a = {}
            for mp in d.future_periods:
                v = r.health
                if r.lineup_slot == 'IR' or ('not projected' in r['flags']):
                    v = 0.0
                elif r.injury_status == 'OUT' and mp < d.cur_mp + OUT_PERIODS:
                    v = 0.0
                elif r.injury_status == 'DAY_TO_DAY' and mp == d.cur_mp:
                    v = min(v, DTD_AVAIL)
                a[mp] = v
            self.avail[pid] = a
        self._day_cache = {}
        self.disp = None
        self.calib = {c: 1.0 for c in CATS}

    # ---- rosters
    def roster(self, team_id):
        P = self.Z
        return [pid for pid in P.index[(P.fantasy_team_id == team_id)]]

    def starts(self, roster, mp):
        """Expected started games per player in matchup period mp (daily slot filling)."""
        cnt = {}
        days = self.d.period_days[mp]
        act = [p for p in roster if p in self.rate and self.avail[p].get(mp, 0) > 0]
        act.sort(key=lambda p: -self.prio[p])
        for day in days:
            teams = self.d.day_teams.get(day, frozenset())
            playing = tuple(p for p in act if self.team[p] in teams)
            if not playing:
                continue
            key = playing
            st = self._day_cache.get(key)
            if st is None:
                st = match_day(playing, self.elig)
                self._day_cache[key] = st
            for p in st:
                cnt[p] = cnt.get(p, 0) + 1
        return cnt

    def week(self, roster, mp, team_id=None):
        """Projected totals (mean) and per-category variance for one team-week."""
        cnt = self.starts(roster, mp)
        mean = np.zeros(len(STATS))
        var = np.zeros(len(STATS))
        resid_fg = resid_ft = 0.0
        g = 0.0
        for p, n in cnt.items():
            e = n * self.avail[p][mp]
            r = self.rate[p]
            mean += e * r
            g += e
            var += e * self.disp['count'] * r
            pf = r[SI['FGM']] / r[SI['FGA']] if r[SI['FGA']] > 0 else 0
            pt = r[SI['FTM']] / r[SI['FTA']] if r[SI['FTA']] > 0 else 0
            resid_fg += e * self.disp['fg'] * r[SI['FGA']] * pf * (1 - pf)
            resid_ft += e * self.disp['ft'] * r[SI['FTA']] * pt * (1 - pt)
        if mp == self.d.cur_mp and team_id is not None and team_id in self.partial:
            mean = mean + self.partial[team_id]
        return dict(mean=mean, var=var, rfg=resid_fg, rft=resid_ft, games=g, starts=cnt)

    # ---- probabilities
    def cat_probs(self, a, b):
        """P(team a beats team b) in each category for one week."""
        out = {}
        ma, mb = a['mean'], b['mean']
        for c in COUNT_CATS:
            i = SI[c]
            sd = math.sqrt(a['var'][i] + b['var'][i] + 1e-9) * self.calib[c]
            diff = ma[i] - mb[i]
            if c == 'TO':
                diff = -diff
            out[c] = ncdf(diff / sd) if sd > 0 else (1.0 if diff > 0 else 0.0 if diff < 0 else 0.5)
        for c, mk, at, rk in (('FG%', 'FGM', 'FGA', 'rfg'), ('FT%', 'FTM', 'FTA', 'rft')):
            Aa, Ab = ma[SI[at]], mb[SI[at]]
            pa = ma[SI[mk]] / Aa if Aa > 0 else 0
            pb = mb[SI[mk]] / Ab if Ab > 0 else 0
            va = a[rk] / Aa ** 2 if Aa > 0 else 0
            vb = b[rk] / Ab ** 2 if Ab > 0 else 0
            sd = math.sqrt(va + vb + 1e-12) * self.calib[c]
            out[c] = ncdf((pa - pb) / sd)
        return out


def matchup_win_prob(probs):
    """P(winning >= 5 of 9 categories), categories treated as independent."""
    dist = np.zeros(10)
    dist[0] = 1.0
    for c in CATS:
        p = probs[c]
        dist = np.concatenate([dist[:1] * (1 - p), dist[1:] * (1 - p) + dist[:-1] * p])
    return float(dist[5:].sum()), dist


# --------------------------------------------------------------------------- variance
def estimate_dispersion(d, model):
    """Game-to-game noise from the game logs: variance = phi * mean (counting stats),
    binomial-with-overdispersion for FG/FT makes."""
    L = d.logs[d.logs.GP > 0]
    num = den = 0.0
    numf = denf = numt = dent = 0.0
    for pid, g in L.groupby('player_id'):
        if len(g) < 5:
            continue
        for s in ['PTS', 'REB', 'AST', 'STL', 'BLK', '3PM', 'TO']:
            x = g[s].values.astype(float)
            m = x.mean()
            if m <= 0:
                continue
            num += ((x - m) ** 2).sum() / m
            den += len(x) - 1
        p = g.FGM.sum() / g.FGA.sum() if g.FGA.sum() else 0
        numf += ((g.FGM - p * g.FGA) ** 2).sum()
        denf += (g.FGA * p * (1 - p)).sum()
        p = g.FTM.sum() / g.FTA.sum() if g.FTA.sum() else 0
        numt += ((g.FTM - p * g.FTA) ** 2).sum()
        dent += (g.FTA * p * (1 - p)).sum()
    phi_all = num / den
    # per-stat dispersion
    phis = {}
    for s in ['PTS', 'REB', 'AST', 'STL', 'BLK', '3PM', 'TO']:
        n = dd = 0.0
        for pid, g in L.groupby('player_id'):
            if len(g) < 5:
                continue
            x = g[s].values.astype(float)
            m = x.mean()
            if m <= 0:
                continue
            n += ((x - m) ** 2).sum() / m
            dd += len(x) - 1
        phis[s] = n / dd
    disp = np.ones(len(STATS)) * phi_all
    for s, v in phis.items():
        disp[SI[s]] = v
    return dict(count=disp, fg=numf / denf, ft=numt / dent, phis=phis)


def calibrate(d, model):
    """Compare model noise with the real week-to-week swings in matchups.csv (completed weeks),
    after removing each team's own average. Returns a multiplier per category (>= 1)."""
    M = d.matchups[d.matchups.status == 'final'].copy()
    disp = model.disp
    out, rows = {}, []
    for c in CATS:
        num = den = 0.0
        for tid, g in M.groupby('fantasy_team_id'):
            if len(g) < 2:
                continue
            G = g.starter_games.values.astype(float)
            if c in COUNT_CATS:
                x = g[c].values.astype(float)
                rate = x.sum() / G.sum()
                resid = x - rate * G             # remove team strength, scaled to games played
                pred = disp['count'][SI[c]] * rate * G
            else:
                mk, at = ('FGM', 'FGA') if c == 'FG%' else ('FTM', 'FTA')
                A = g[at].values.astype(float)
                p = g[mk].sum() / A.sum()
                resid = g[mk].values - p * A
                pred = (disp['fg'] if c == 'FG%' else disp['ft']) * A * p * (1 - p)
            n = len(g)
            num += (resid ** 2).sum() * n / (n - 1)
            den += pred.sum()
        k = math.sqrt(num / den) if den > 0 else 1.0
        rows.append(dict(category=c, empirical_to_model_sd_ratio=round(k, 2)))
        out[c] = float(np.clip(k, 1.0, 1.8))
    return out, pd.DataFrame(rows)
