"""
Dataset generator + correctness proof for the multi-objective ride matching algorithm.

Usage:
  python verify_and_generate.py                      # defaults: 25 riders, 20 drivers
  python verify_and_generate.py --riders 40 --drivers 30 --seed 3
Outputs dataset.json (upload it in index.html) and prints:
  1. Brute-force check  : Hungarian optimum == exhaustive optimum on small instances
  2. SciPy check        : Hungarian optimum == scipy.optimize.linear_sum_assignment (if scipy installed)
  3. Constraint check   : every match respects driver min/max trip km and max pickup km
  4. Benchmark          : Ours vs Random vs Greedy over many random instances
"""
import argparse, itertools, json, math, random

FARE = [(0, 2, 40), (2, 5, 90), (5, 10, 180), (10, 15, 270), (15, 99, 380)]
FEE = [(1, 10, 20), (11, 25, 25), (26, 50, 30), (51, 9999, 35)]
SPEED, BIG = 25.0, 1e5
W1, W2, W3, MAXPICK = 1.5, 1.0, 1.0, 8.0
CENTER = (25.5355, 84.8520)  # Bihta / IIT Patna


def fare(d): return next(f for a, b, f in FARE if a <= d < b)
def fee(n): return next((f for a, b, f in FEE if a <= n <= b), 0) if n else 0
def hav(a, b):
    r = math.pi / 180
    x = math.sin((b['lat'] - a['lat']) * r / 2) ** 2 + math.cos(a['lat'] * r) * math.cos(b['lat'] * r) * math.sin((b['lng'] - a['lng']) * r / 2) ** 2
    return 12742 * math.asin(math.sqrt(x))
def accepts(r, d): return d['minD'] <= r['dist'] <= d['maxD']


def generate(nr, nd, seed, radius=3.0):
    rnd = random.Random(seed)
    pt = lambda: {'lat': CENTER[0] + rnd.uniform(-1, 1) * radius / 111,
                  'lng': CENTER[1] + rnd.uniform(-1, 1) * radius / (111 * math.cos(math.radians(CENTER[0])))}
    riders = [dict(id=f'R{i+1}', **pt(), dist=round(rnd.uniform(1, 12), 1), on=True) for i in range(nr)]
    drivers = []
    for i in range(nd):
        mn = round(rnd.uniform(1, 5), 1)
        drivers.append(dict(id=f'D{i+1}', name=f'Driver{i+1}', **pt(), minD=mn, maxD=round(max(mn + 1, rnd.uniform(6, 15)), 1), on=True))
    return {'center': list(CENTER), 'riders': riders, 'drivers': drivers}


def cost(r, d):
    if not accepts(r, d): return BIG
    pk = hav(r, d)
    if pk > MAXPICK: return BIG
    f = fare(r['dist'])
    return W1 * pk / SPEED * 6 - W2 * (f - 20) / 100 - W3 * f / 100 - 1


def hungarian(a):  # min-cost perfect assignment, square matrix, O(n^3)
    n = len(a); u = [0] * (n + 1); v = [0] * (n + 1); p = [0] * (n + 1); way = [0] * (n + 1)
    for i in range(1, n + 1):
        p[0] = i; j0 = 0; minv = [math.inf] * (n + 1); used = [False] * (n + 1)
        while True:
            used[j0] = True; i0 = p[j0]; d = math.inf; j1 = 0
            for j in range(1, n + 1):
                if not used[j]:
                    c = a[i0 - 1][j - 1] - u[i0] - v[j]
                    if c < minv[j]: minv[j] = c; way[j] = j0
                    if minv[j] < d: d = minv[j]; j1 = j
            for j in range(n + 1):
                if used[j]: u[p[j]] += d; v[j] -= d
                else: minv[j] -= d
            j0 = j1
            if p[j0] == 0: break
        while j0:
            j1 = way[j0]; p[j0] = p[j1]; j0 = j1
    return [(p[j] - 1, j - 1) for j in range(1, n + 1) if p[j]]


def padded(riders, drivers):
    n = max(len(riders), len(drivers))
    return [[cost(riders[i], drivers[j]) if i < len(riders) and j < len(drivers) else 0 for j in range(n)] for i in range(n)]


def alg_ours(riders, drivers):
    m = padded(riders, drivers)
    return [(i, j) for i, j in hungarian(m) if i < len(riders) and j < len(drivers) and m[i][j] < BIG / 2]

def alg_greedy(riders, drivers):
    used, out = set(), []
    for i, r in enumerate(riders):
        c = [(hav(r, d), j) for j, d in enumerate(drivers) if j not in used]
        if c: j = min(c)[1]; used.add(j); out.append((i, j))
    return out

def alg_random(riders, drivers, seed=0):
    rnd = random.Random(seed); free = list(range(len(drivers))); out = []
    for i in range(len(riders)):
        if free: out.append((i, free.pop(rnd.randrange(len(free)))))
    return out


def metrics(pairs, riders, drivers):
    served = [(i, j) for i, j in pairs if accepts(riders[i], drivers[j])]
    n = len(served); gmv = sum(fare(riders[i]['dist']) for i, _ in served)
    pk = sum(hav(riders[i], drivers[j]) for i, j in served)
    return dict(rides=n, gmv=gmv, driver_rev=gmv - fee(n) * n, platform=fee(n) * n, wait=(pk / n / SPEED * 60) if n else 0)


def total(pairs, riders, drivers): return sum(cost(riders[i], drivers[j]) for i, j in pairs)


def brute_force(riders, drivers):
    m = padded(riders, drivers); n = len(m)
    return min(sum(m[i][p[i]] for i in range(n)) for p in itertools.permutations(range(n)))


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--riders', type=int, default=25); ap.add_argument('--drivers', type=int, default=20)
    ap.add_argument('--seed', type=int, default=7); ap.add_argument('--trials', type=int, default=200); a = ap.parse_args()

    ds = generate(a.riders, a.drivers, a.seed)
    json.dump(ds, open('dataset.json', 'w'), indent=1)
    print(f'dataset.json written ({a.riders} riders, {a.drivers} drivers) -> upload it in index.html\n')

    # 1. brute force (exhaustive) on small instances
    ok_bf = 0; T = 60
    for s in range(T):
        d = generate(random.Random(s).randint(3, 7), random.Random(s + 1).randint(3, 7), s, radius=1.5)
        ours = total(alg_ours(d['riders'], d['drivers']), d['riders'], d['drivers'])
        ok_bf += abs(ours - brute_force(d['riders'], d['drivers'])) < 1e-6
    print(f'[1] Brute-force check : Hungarian == exhaustive optimum on {ok_bf}/{T} instances')

    # 2. scipy cross-check
    try:
        import numpy as np
        from scipy.optimize import linear_sum_assignment
        ok_sp = 0
        for s in range(T):
            d = generate(15, 12, 1000 + s)
            m = np.array(padded(d['riders'], d['drivers'])); r_, c_ = linear_sum_assignment(m)
            ok_sp += abs(m[r_, c_].sum() - sum(m[i][j] for i, j in hungarian(m.tolist()))) < 1e-6
        print(f'[2] SciPy check       : matches linear_sum_assignment on {ok_sp}/{T} instances')
    except ImportError:
        print('[2] SciPy check       : skipped (pip install scipy numpy to enable)')

    # 3. constraints
    viol = 0
    for s in range(T):
        d = generate(20, 15, 2000 + s)
        for i, j in alg_ours(d['riders'], d['drivers']):
            r, dr = d['riders'][i], d['drivers'][j]
            viol += (not accepts(r, dr)) or hav(r, dr) > MAXPICK
    print(f'[3] Constraint check  : {viol} violations of driver min/max trip km or max pickup km')

    # 4. benchmark
    agg = {k: dict(rides=0, gmv=0, driver_rev=0, wait=0) for k in ('Random', 'Greedy', 'Ours')}; wins = 0
    for s in range(a.trials):
        d = generate(a.riders, a.drivers, 5000 + s); R, D = d['riders'], d['drivers']
        res = {'Random': metrics(alg_random(R, D, s), R, D), 'Greedy': metrics(alg_greedy(R, D), R, D), 'Ours': metrics(alg_ours(R, D), R, D)}
        for k, m in res.items():
            for f in agg[k]: agg[k][f] += m[f] / a.trials
        wins += res['Ours']['gmv'] >= max(res['Random']['gmv'], res['Greedy']['gmv'])
    print(f'\n[4] Benchmark over {a.trials} random instances (averages)')
    print(f'{"Algorithm":<8}{"Rides":>8}{"GMV":>10}{"DriverRev":>11}{"Wait(min)":>11}')
    for k, m in agg.items(): print(f'{k:<8}{m["rides"]:>8.1f}{m["gmv"]:>10.0f}{m["driver_rev"]:>11.0f}{m["wait"]:>11.2f}')
    print(f'Ours had GMV >= both baselines in {wins}/{a.trials} instances')
