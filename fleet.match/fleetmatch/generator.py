"""Random rider / driver dataset generators."""
import math
import random

from .config import CENTER, NAMES


def generate(nr, nd, seed, radius=3.0):
    """Default generator used by generate_data.py and the verification suite."""
    rnd = random.Random(seed)
    pt = lambda: {'lat': CENTER[0] + rnd.uniform(-1, 1) * radius / 111,
                  'lng': CENTER[1] + rnd.uniform(-1, 1) * radius / (111 * math.cos(math.radians(CENTER[0])))}
    riders = [dict(id=f'R{i+1}', **pt(), dist=round(rnd.uniform(1, 12), 1), on=True) for i in range(nr)]
    drivers = []
    for i in range(nd):
        mn = round(rnd.uniform(1, 5), 1)
        drivers.append(dict(id=f'D{i+1}', name=f'Driver{i+1}', **pt(), minD=mn,
                            maxD=round(max(mn + 1, rnd.uniform(6, 15)), 1), on=True))
    return {'center': list(CENTER), 'riders': riders, 'drivers': drivers}


def generate_from_params(p):
    """Generator driven by the UI control parameters (POST /api/generate)."""
    rnd = random.Random(float(p['seed']) * 7919 + 1)
    clat, clng, R = float(p['clat']), float(p['clng']), float(p['rad'])
    u = lambda a, b: a + rnd.random() * (b - a)
    f = lambda x: round(x, 1)
    pt = lambda: {'lat': clat + (rnd.random() * 2 - 1) * R / 111,
                  'lng': clng + (rnd.random() * 2 - 1) * R / (111 * math.cos(math.radians(clat)))}
    riders = [dict(id=f'R{i+1}', **pt(), dist=f(u(float(p['tLo']), float(p['tHi']))),
                   on=rnd.random() * 100 < float(p['aR'])) for i in range(max(0, int(p['nR'])))]
    drivers = []
    for i in range(max(0, int(p['nD']))):
        mn = f(u(float(p['mnLo']), float(p['mnHi'])))
        drivers.append(dict(id=f'D{i+1}', name=rnd.choice(NAMES), **pt(), minD=mn,
                            maxD=f(max(mn + 1, u(float(p['mxLo']), float(p['mxHi'])))),
                            on=rnd.random() * 100 < float(p['aD'])))
    return {'center': [clat, clng], 'riders': riders, 'drivers': drivers}
