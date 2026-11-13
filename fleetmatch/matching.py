"""Cost function, the three matching algorithms and evaluation metrics."""
import itertools
import random

from .config import BIG, MAXPICK, SPEED, W1, W2, W3
from .geo import hav
from .hungarian import hungarian
from .pricing import accepts, fare, fee


def cost(r, d):
    if not accepts(r, d):
        return BIG
    pk = hav(r, d)
    if pk > MAXPICK:
        return BIG
    f = fare(r['dist'])
    return W1 * pk / SPEED * 6 - W2 * (f - 20) / 100 - W3 * f / 100 - 1


def padded(riders, drivers):
    n = max(len(riders), len(drivers))
    return [[cost(riders[i], drivers[j]) if i < len(riders) and j < len(drivers) else 0
             for j in range(n)] for i in range(n)]


def alg_ours(riders, drivers):
    m = padded(riders, drivers)
    return [(i, j) for i, j in hungarian(m) if i < len(riders) and j < len(drivers) and m[i][j] < BIG / 2]


def alg_greedy(riders, drivers):
    used, out = set(), []
    for i, r in enumerate(riders):
        c = [(hav(r, d), j) for j, d in enumerate(drivers) if j not in used]
        if c:
            j = min(c)[1]; used.add(j); out.append((i, j))
    return out


def alg_random(riders, drivers, seed=0):
    rnd = random.Random(seed); free = list(range(len(drivers))); out = []
    for i in range(len(riders)):
        if free:
            out.append((i, free.pop(rnd.randrange(len(free)))))
    return out


def metrics(pairs, riders, drivers):
    served = [(i, j) for i, j in pairs if accepts(riders[i], drivers[j])]
    n = len(served)
    gmv = sum(fare(riders[i]['dist']) for i, _ in served)
    pk = sum(hav(riders[i], drivers[j]) for i, j in served)
    return dict(rides=n, gmv=gmv, driver_rev=gmv - fee(n) * n, platform=fee(n) * n,
                wait=(pk / n / SPEED * 60) if n else 0)


def total(pairs, riders, drivers):
    return sum(cost(riders[i], drivers[j]) for i, j in pairs)


def brute_force(riders, drivers):
    m = padded(riders, drivers); n = len(m)
    return min(sum(m[i][p[i]] for i in range(n)) for p in itertools.permutations(range(n)))
