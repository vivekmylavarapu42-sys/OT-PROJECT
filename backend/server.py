"""
Flask API for the ride-matching UI. Reuses the maths helpers from app.py.

  pip install -r requirements.txt
  python server.py          ->  open http://localhost:5000

Endpoints
  POST /api/generate   body: all control params   -> {center, riders, drivers}
  POST /api/simulate   body: {dataset, params}     -> {A, B, C, check}
"""
import math
import os
import random

from flask import Flask, jsonify, request, send_from_directory

from app import BIG, SPEED, accepts, fare, fee, hav, hungarian

NAMES = ['Amit', 'Priya', 'Rahul', 'Sneha', 'Vivek', 'Anjali', 'Rohit', 'Neha', 'Karan', 'Pooja', 'Ravi', 'Sita']
FRONTEND = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'frontend')

app = Flask(__name__, static_folder=FRONTEND, static_url_path='')


@app.after_request
def cors(resp):  # lets the page also work when opened from Live Server / another port
    resp.headers['Access-Control-Allow-Origin'] = '*'
    resp.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return resp


# ---------------- generation ----------------
def generate(p):
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


# ---------------- matching ----------------
def make_cost(P):
    w1, w2, w3, mp = float(P['w1']), float(P['w2']), float(P['w3']), float(P['mp'])

    def cost(r, d):
        if not accepts(r, d):
            return BIG
        pk = hav(r, d)
        if pk > mp:
            return BIG
        f = fare(r['dist'])
        return w1 * pk / SPEED * 6 - w2 * (f - 20) / 100 - w3 * f / 100 - 1
    return cost


def simulate(ds, P):
    R, D = ds['riders'], ds['drivers']
    RI = [i for i, r in enumerate(R) if r.get('on', True)]
    DI = [j for j, d in enumerate(D) if d.get('on', True)]
    cost = make_cost(P)

    def a_random():
        rnd, free = random.Random(float(P['seed']) + 99), list(DI)
        return [(i, free.pop(rnd.randrange(len(free)))) for i in RI if free]

    def b_greedy():
        used, out = set(), []
        for i in RI:
            c = [(hav(R[i], D[j]), j) for j in DI if j not in used]
            if c:
                j = min(c)[1]; used.add(j); out.append((i, j))
        return out

    def c_ours():
        n = max(len(RI), len(DI))
        if not n:
            return []
        m = [[cost(R[RI[a]], D[DI[b]]) if a < len(RI) and b < len(DI) else 0 for b in range(n)] for a in range(n)]
        return [(RI[a], DI[b]) for a, b in hungarian(m)
                if a < len(RI) and b < len(DI) and m[a][b] < BIG / 2]

    def evaluate(pairs):
        served = [q for q in pairs if accepts(R[q[0]], D[q[1]])]
        rej = [q for q in pairs if not accepts(R[q[0]], D[q[1]])]
        n = len(served); fe = fee(n); gmv = pk = 0; earn = {}
        for i, j in served:
            f = fare(R[i]['dist']); gmv += f; pk += hav(R[i], D[j]); earn[j] = f - fe
        nd = len(DI) or 1
        return dict(pairs=pairs, served=served, rej=rej, earn=earn, n=n, gmv=gmv, platform=fe * n,
                    avgDrv=(gmv - fe * n) / nd, avgPk=pk / n if n else 0,
                    avgWait=pk / n / SPEED * 60 if n else 0, rejN=len(rej))

    res = {'A': evaluate(a_random()), 'B': evaluate(b_greedy()), 'C': evaluate(c_ours())}
    res['check'] = opt_check(res['C']['pairs'], RI, DI, R, D, cost)
    return res


def opt_check(P, RI, DI, R, D, cost):
    """Local-optimality: no swap / replacement / extra match lowers total cost."""
    c = lambda i, j: cost(R[i], D[j])
    mr, md = {q[0] for q in P}, {q[1] for q in P}
    fr, ur = [j for j in DI if j not in md], [i for i in RI if i not in mr]
    n = bad = 0

    def chk(a, b):
        nonlocal n, bad
        n += 1
        bad += a < b - 1e-9

    for a in range(len(P)):
        for b in range(a + 1, len(P)):
            chk(c(P[a][0], P[b][1]) + c(P[b][0], P[a][1]), c(*P[a]) + c(*P[b]))
        for f in fr: chk(c(P[a][0], f), c(*P[a]))
        for u in ur: chk(c(u, P[a][1]), c(*P[a]))
    for u in ur:
        for f in fr: chk(c(u, f), 0)
    return {'n': n, 'bad': int(bad)}


# ---------------- routes ----------------
@app.get('/')
def index():
    return send_from_directory(FRONTEND, 'index.html')


@app.post('/api/generate')
def api_generate():
    try:
        return jsonify(generate(request.get_json(force=True)))
    except (KeyError, ValueError, TypeError) as e:
        return jsonify(error=f'bad parameters: {e}'), 400


@app.post('/api/simulate')
def api_simulate():
    try:
        body = request.get_json(force=True)
        return jsonify(simulate(body['dataset'], body['params']))
    except (KeyError, ValueError, TypeError) as e:
        return jsonify(error=f'bad request: {e}'), 400


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
