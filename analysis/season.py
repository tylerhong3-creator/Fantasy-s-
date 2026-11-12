"""Season-level evaluation: weekly category win probabilities, playoff/title odds,
linear screening gradients. Built on fantasy.Model."""
import math

import numpy as np

from fantasy import (CATS, COUNT_CATS, SI, STATS, MY_TEAM_ID, PLAYOFF_PERIODS, PLAYOFF_WEIGHT,
                     matchup_win_prob, npdf)


class Season:
    def __init__(self, model):
        self.m = model
        self.d = model.d
        self.base = {tid: model.roster(tid) for tid in self.d.teams}
        self._wk = {}
        self.strong = None

    # ---------------------------------------------------------------- projections
    def wk(self, tid, mp, roster):
        key = (tid, mp, tuple(sorted(roster)))
        w = self._wk.get(key)
        if w is None:
            w = self.m.week(roster, mp, team_id=tid)
            self._wk[key] = w
        return w

    def rosters(self, override=None):
        r = dict(self.base)
        if override:
            r.update(override)
        return r

    def set_strong(self, n=5):
        """The playoff field: the n strongest other teams by projected all-play (baseline)."""
        ap = {tid: self.allplay(tid)['per_week'] for tid in self.d.teams if tid != MY_TEAM_ID}
        self.strong = sorted(ap, key=lambda t: -ap[t])[:n]
        return self.strong, ap

    # ---------------------------------------------------------------- my season
    def my_eval(self, override=None, bonus=None, team=MY_TEAM_ID, exclude=()):
        """Expected categories won / matchup win prob for `team` over every remaining week.
        Regular weeks: actual scheduled opponent. Playoff weeks: average over the strong field."""
        R = self.rosters(override)
        out = dict(per_period=[], reg_cats=0.0, reg_mwins=0.0, po_cats=0.0, po_mwin=0.0,
                   cat_reg={c: 0.0 for c in CATS}, cat_po={c: 0.0 for c in CATS})
        reg_n = po_n = 0
        for mp in self.d.future_periods:
            me = self.wk(team, mp, R[team])
            if bonus is not None and mp > self.d.cur_mp:
                me = dict(me)
                me['mean'] = me['mean'] + bonus
            if self.d.periods[mp]['type'] == 'regular':
                opps = [self.d.opponent(team, mp)]
            else:
                opps = [t for t in self.strong if t != team][:5]
            probs = {c: 0.0 for c in CATS}
            mw = 0.0
            for o in opps:
                pr = self.m.cat_probs(me, self.wk(o, mp, R[o]))
                for c in CATS:
                    probs[c] += pr[c] / len(opps)
                mw += matchup_win_prob(pr)[0] / len(opps)
            ec = sum(probs.values())
            rec = dict(period=mp, type=self.d.periods[mp]['type'],
                       opponent='/'.join(self.d.abbrev[o] for o in opps), exp_cats=ec, match_win=mw, **probs)
            out['per_period'].append(rec)
            if rec['type'] == 'regular':
                out['reg_cats'] += ec
                out['reg_mwins'] += mw
                reg_n += 1
                for c in CATS:
                    out['cat_reg'][c] += probs[c]
            else:
                out['po_cats'] += ec
                out['po_mwin'] += mw
                po_n += 1
                for c in CATS:
                    out['cat_po'][c] += probs[c]
        out['reg_weeks'], out['po_weeks'] = reg_n, po_n
        out['score'] = out['reg_cats'] + PLAYOFF_WEIGHT * out['po_cats']
        out['score_ex'] = out['score'] - sum(out['cat_reg'][c] + PLAYOFF_WEIGHT * out['cat_po'][c] for c in exclude)
        return out

    def allplay(self, tid, override=None, periods=None):
        """Team tid's expected category wins per week against every other team (league field)."""
        R = self.rosters(override)
        periods = periods or [mp for mp in self.d.future_periods if mp > self.d.cur_mp]
        tot = 0.0
        cat = {c: 0.0 for c in CATS}
        n = 0
        for mp in periods:
            me = self.wk(tid, mp, R[tid])
            for o in self.d.teams:
                if o == tid:
                    continue
                pr = self.m.cat_probs(me, self.wk(o, mp, R[o]))
                for c in CATS:
                    cat[c] += pr[c]
                tot += sum(pr.values())
                n += 1
        return dict(per_week=tot / n, cat={c: v / n for c, v in cat.items()})

    # ---------------------------------------------------------------- gradients
    def gradient(self, tid, field=False, exclude=(), override=None):
        """d(expected categories)/d(weekly stat totals) for each remaining period, used to
        screen thousands of trades quickly before the full simulation. Categories listed in
        `exclude` are ignored (used for punt strategies)."""
        R = self.rosters(override)
        G = {}
        for mp in self.d.future_periods:
            if mp == self.d.cur_mp:
                continue
            me = self.wk(tid, mp, R[tid])
            if field:
                opps, w = [o for o in self.d.teams if o != tid], 1.0
            elif self.d.periods[mp]['type'] == 'regular':
                opps, w = [self.d.opponent(tid, mp)], 1.0
            else:
                opps, w = [t for t in self.strong if t != tid][:5], PLAYOFF_WEIGHT
            g = np.zeros(len(STATS))
            for o in opps:
                op = self.wk(o, mp, R[o])
                for c in COUNT_CATS:
                    if c in exclude:
                        continue
                    i = SI[c]
                    sd = math.sqrt(me['var'][i] + op['var'][i]) * self.m.calib[c]
                    diff = me['mean'][i] - op['mean'][i]
                    sgn = 1.0
                    if c == 'TO':
                        diff, sgn = -diff, -1.0
                    g[i] += sgn * npdf(diff / sd) / sd / len(opps)
                for c, mk, at, rk in (('FG%', 'FGM', 'FGA', 'rfg'), ('FT%', 'FTM', 'FTA', 'rft')):
                    if c in exclude:
                        continue
                    Aa, Ab = me['mean'][SI[at]], op['mean'][SI[at]]
                    pa, pb = me['mean'][SI[mk]] / Aa, op['mean'][SI[mk]] / Ab
                    sd = math.sqrt(me[rk] / Aa ** 2 + op[rk] / Ab ** 2) * self.m.calib[c]
                    dens = npdf((pa - pb) / sd) / sd / len(opps)
                    g[SI[mk]] += dens / Aa
                    g[SI[at]] += -dens * pa / Aa
            G[mp] = g * w
        return G

    def games(self, pid, mp):
        teams = self.d.day_teams
        t = self.m.team[pid]
        return sum(1 for day in self.d.period_days[mp] if t in teams.get(day, ()))

    def lin_value(self, pid, G, start_frac=0.85):
        """Linear estimate of a player's contribution (weighted expected categories)."""
        if pid not in self.m.rate:
            return 0.0
        v = 0.0
        r = self.m.rate[pid]
        for mp, g in G.items():
            e = self.games(pid, mp) * self.m.avail[pid][mp] * start_frac
            v += e * float(g @ r)
        return v

    # ---------------------------------------------------------------- Monte Carlo
    def monte_carlo(self, override=None, n=20000, seed=7):
        """Playoff and title odds for every team. Regular season: each category of each
        scheduled matchup drawn independently from its win probability. Seeding by category
        win %. Bracket: 1 and 2 get byes; R1 3v6, 4v5; R2 1 v (4/5 winner), 2 v (3/6 winner)."""
        rng = np.random.default_rng(seed)
        R = self.rosters(override)
        tids = sorted(self.d.teams)
        idx = {t: i for i, t in enumerate(tids)}
        S = self.d.summary.set_index('fantasy_team_id')
        W = np.array([S.loc[t, 'cat_W'] for t in tids], float)[None, :].repeat(n, 0)
        L = np.array([S.loc[t, 'cat_L'] for t in tids], float)[None, :].repeat(n, 0)
        T = np.array([S.loc[t, 'cat_T'] for t in tids], float)[None, :].repeat(n, 0)
        for mp in self.d.regular_future:
            for s in self.d.schedule:
                if s['matchup_period'] != mp:
                    continue
                a, b = s['home_team_id'], s['away_team_id']
                pr = self.m.cat_probs(self.wk(a, mp, R[a]), self.wk(b, mp, R[b]))
                p = np.array([pr[c] for c in CATS])
                wins = (rng.random((n, 9)) < p).sum(1)
                W[:, idx[a]] += wins
                L[:, idx[a]] += 9 - wins
                W[:, idx[b]] += 9 - wins
                L[:, idx[b]] += wins
        pct = (W + 0.5 * T) / (W + L + T) + rng.random(W.shape) * 1e-6
        order = np.argsort(-pct, axis=1)
        seeds = order[:, :6]
        # matchup win prob matrices for playoff weeks
        M = {}
        for mp in PLAYOFF_PERIODS:
            mat = np.full((10, 10), 0.5)
            for a in tids:
                for b in tids:
                    if a < b:
                        pr = self.m.cat_probs(self.wk(a, mp, R[a]), self.wk(b, mp, R[b]))
                        pw = matchup_win_prob(pr)[0]
                        mat[idx[a], idx[b]], mat[idx[b], idx[a]] = pw, 1 - pw
            M[mp] = mat
        ar = np.arange(n)

        def play(mp, x, y):
            p = M[mp][x, y]
            return np.where(rng.random(n) < p, x, y)

        s1, s2, s3, s4, s5, s6 = (seeds[:, i] for i in range(6))
        w45 = play(20, s4, s5)
        w36 = play(20, s3, s6)
        f1 = play(21, s1, w45)
        f2 = play(21, s2, w36)
        champ = play(22, f1, f2)
        res = {}
        for t in tids:
            i = idx[t]
            res[t] = dict(playoffs=float((seeds == i).any(1).mean()),
                          top2=float(((s1 == i) | (s2 == i)).mean()),
                          title=float((champ == i).mean()),
                          exp_cat_wins=float(W[:, i].mean()))
        return res
