"""Integer-unit scoring and seeded common-random-number evaluation."""
import numpy as np
from .rules import VALUES, PAYOUTS_UNITS
try:
    from numba import njit
except ImportError:
    def njit(*args, **kwargs):
        return lambda f: f


def validate_allocations(x):
    x = np.asarray(x)
    if x.shape[-1] != 5 or not np.issubdtype(x.dtype, np.integer) or np.any(x < 0) or np.any(x.sum(axis=-1) != 100):
        raise ValueError('Allocations must be five nonnegative integers summing to 100')
    return x


def score_g1_units(a, b):
    a, b = np.asarray(a), np.asarray(b)
    s = ((a > b) * 12 + (a == b) * 6) @ np.asarray(VALUES)
    return np.stack((s, 180-s), axis=-1)


def score_g2_units(groups):
    g = np.asarray(groups)
    wins = g == g.max(axis=-2, keepdims=True)
    points = (wins * (12 // wins.sum(axis=-2, keepdims=True)) * np.asarray(VALUES)).sum(axis=-1)
    above = (points[..., None, :] > points[..., :, None]).sum(axis=-1)
    ties = (points[..., None, :] == points[..., :, None]).sum(axis=-1)
    cumulative = np.array([0, 108, 156, 180, 180])
    pay = (cumulative[above+ties] - cumulative[above]) // ties
    return points, pay


def g1_marginals(pop):
    return np.array([np.bincount(pop.g1[:, j], weights=pop.w, minlength=101) for j in range(5)])


def g1_table(marginals):
    m = np.asarray(marginals)
    return (np.cumsum(m, axis=1) - 0.5*m) * np.asarray(VALUES)[:, None]


def g1_exact(x_batch, marginals):
    x = np.atleast_2d(x_batch)
    return g1_table(marginals)[np.arange(5), x].sum(axis=1)


def all_allocations(step=1):
    """Enumerate feasible allocations once, in lexicographic order."""
    n = 100 // step
    return np.asarray([(a,b,c,d,n-a-b-c-d) for a in range(n+1) for b in range(n-a+1)
                       for c in range(n-a-b+1) for d in range(n-a-b-c+1)], dtype=np.int16)*step


@njit(cache=True)
def g1_top(table, k=100):
    # Keep top-k partial sums for every budget. Backtracking stores whole 5-vectors.
    scores = np.full((101,k), -1e100)
    paths = np.zeros((101,k,5), np.int16)
    scores[0,0] = 0
    for j in range(5):
        nxt = np.full((101,k), -1e100)
        out = np.zeros((101,k,5), np.int16)
        for budget in range(101):
            for amount in range(budget+1):
                for r in range(k):
                    val = scores[budget-amount,r] + table[j,amount]
                    if val <= nxt[budget,k-1]:
                        break
                    pos = k-1
                    while pos > 0 and val > nxt[budget,pos-1]:
                        nxt[budget,pos] = nxt[budget,pos-1]
                        out[budget,pos] = out[budget,pos-1]
                        pos -= 1
                    nxt[budget,pos] = val
                    out[budget,pos] = paths[budget-amount,r]
                    out[budget,pos,j] = amount
        scores, paths = nxt, out
    return paths[100], scores[100]


def g2_sample_opponents(pop, n, seed):
    rng = np.random.default_rng(seed)
    return pop.g2[rng.choice(len(pop.w), size=(n,3), p=pop.w)]


@njit(cache=True)
def _payouts(x, opps):
    n = len(opps)
    pays = np.empty(n, np.int16)
    points_out = np.empty(n, np.int16)
    places = np.zeros((n,4), np.float32)
    payouts = np.array([108,48,24,0])
    for i in range(n):
        points = np.zeros(4, np.int16)
        for j in range(5):
            high = x[j]
            for p in range(3):
                high = max(high, opps[i,p,j])
            count = int(x[j] == high)
            for p in range(3):
                count += int(opps[i,p,j] == high)
            share = (12//count)*(j+1)
            if x[j] == high:
                points[0] += share
            for p in range(3):
                if opps[i,p,j] == high:
                    points[p+1] += share
        above, tied = 0, 0
        for p in range(4):
            above += int(points[p] > points[0])
            tied += int(points[p] == points[0])
        pay = 0
        for r in range(above, above+tied):
            pay += payouts[r]
            places[i,r] = 1.0/tied
        pays[i] = pay//tied
        points_out[i] = points[0]
    return pays, points_out, places


def g2_eval(x_batch, opps):
    means, ses, probs, points = [], [], [], []
    for x in np.atleast_2d(x_batch):
        p, q, r = _payouts(np.asarray(x), opps)
        means.append(p.mean()/12)
        ses.append(p.std(ddof=1)/12/np.sqrt(len(p)))
        probs.append(r.mean(axis=0, dtype=np.float64).tolist())
        points.append(q.mean()/12)
    return dict(mean=np.array(means), se=np.array(ses), place=np.array(probs), p_place=np.array(probs), mean_castle_points=np.array(points))


def g2_paired(x_a, x_b, opps):
    a = _payouts(np.asarray(x_a), opps)[0].astype(float)
    b = _payouts(np.asarray(x_b), opps)[0].astype(float)
    d = (a-b)/12
    return float(d.mean()), float(d.std(ddof=1)/np.sqrt(len(d)))


# Shared interfaces agreed with the independently written Claude reference.
g2_group_units = score_g2_units

def g1_pair_units(a, b):
    scores = score_g1_units(a, b)
    return scores[..., 0], scores[..., 1]
