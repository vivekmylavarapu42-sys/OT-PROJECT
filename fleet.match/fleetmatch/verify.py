"""Correctness proof + benchmark for the multi-objective matching algorithm.

  1. Brute-force check : Hungarian optimum == exhaustive optimum on small instances
  2. SciPy check       : Hungarian optimum == scipy.optimize.linear_sum_assignment
  3. Constraint check  : every match respects driver min/max trip km and max pickup km
  4. Benchmark         : Ours vs Random vs Greedy over many random instances
"""
import random

from .config import MAXPICK
from .generator import generate
from .geo import hav
from .hungarian import hungarian
from .matching import (alg_greedy, alg_ours, alg_random, brute_force, metrics,
                       padded)
from .pricing import accepts


def run(riders=25, drivers=20, trials=200, T=60):
    # 1. brute force (exhaustive) on small instances
    ok_bf = 0
    for s in range(T):
        d = generate(random.Random(s).randint(3, 7), random.Random(s + 1).randint(3, 7), s, radius=1.5)
        m = padded(d['riders'], d['drivers'])
        ours = sum(m[i][j] for i, j in hungarian(m))  # raw assignment cost incl. forbidden-pair penalties
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
    for s in range(trials):
        d = generate(riders, drivers, 5000 + s); R, D = d['riders'], d['drivers']
        res = {'Random': metrics(alg_random(R, D, s), R, D),
               'Greedy': metrics(alg_greedy(R, D), R, D),
               'Ours': metrics(alg_ours(R, D), R, D)}
        for k, m in res.items():
            for f in agg[k]:
                agg[k][f] += m[f] / trials
        wins += res['Ours']['gmv'] >= max(res['Random']['gmv'], res['Greedy']['gmv'])
    print(f'\n[4] Benchmark over {trials} random instances (averages)')
    print(f'{"Algorithm":<8}{"Rides":>8}{"GMV":>10}{"DriverRev":>11}{"Wait(min)":>11}')
    for k, m in agg.items():
        print(f'{k:<8}{m["rides"]:>8.1f}{m["gmv"]:>10.0f}{m["driver_rev"]:>11.0f}{m["wait"]:>11.2f}')
    print(f'Ours had GMV >= both baselines in {wins}/{trials} instances')
    return dict(brute_force=ok_bf, constraint_violations=viol, wins=wins, trials=trials)
