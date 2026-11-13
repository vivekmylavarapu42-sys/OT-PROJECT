"""Entry point.

  python main.py                 # start web app at http://localhost:5000
  python main.py serve --port 8000
  python main.py match           # match data/dataset.json -> match_records.csv
  python main.py verify          # brute-force / SciPy / constraint checks + benchmark
"""
import argparse
import csv
import json
import os

ROOT = os.path.dirname(os.path.abspath(__file__))


def cmd_serve(a):
    from fleetmatch.server import app
    app.run(host=a.host, port=a.port, debug=True)


def cmd_match(a):
    from fleetmatch.config import SPEED
    from fleetmatch.geo import hav
    from fleetmatch.matching import alg_ours
    from fleetmatch.pricing import fare

    with open(a.dataset) as f:
        ds = json.load(f)
    R, D = ds['riders'], ds['drivers']
    ri = [i for i, r in enumerate(R) if r.get('on', True)]
    di = [j for j, d in enumerate(D) if d.get('on', True)]
    pairs = alg_ours([R[i] for i in ri], [D[j] for j in di])
    out = os.path.join(ROOT, 'match_records.csv')
    with open(out, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['rider_id', 'driver_id', 'trip_km', 'fare_inr', 'pickup_km', 'wait_min'])
        for a_, b_ in pairs:
            r, d = R[ri[a_]], D[di[b_]]
            pk = hav(r, d)
            w.writerow([r['id'], d['id'], r['dist'], fare(r['dist']), round(pk, 2), round(pk / SPEED * 60, 2)])
    print(f'{len(pairs)} matches written to match_records.csv')


def cmd_verify(a):
    from fleetmatch.verify import run
    run(a.riders, a.drivers, a.trials)


def main():
    ap = argparse.ArgumentParser(description='fleet.match')
    sub = ap.add_subparsers(dest='cmd')

    s = sub.add_parser('serve'); s.add_argument('--host', default='127.0.0.1'); s.add_argument('--port', type=int, default=5000)
    s.set_defaults(fn=cmd_serve)
    m = sub.add_parser('match'); m.add_argument('--dataset', default=os.path.join(ROOT, 'data', 'dataset.json'))
    m.set_defaults(fn=cmd_match)
    v = sub.add_parser('verify'); v.add_argument('--riders', type=int, default=25)
    v.add_argument('--drivers', type=int, default=20); v.add_argument('--trials', type=int, default=200)
    v.set_defaults(fn=cmd_verify)

    a = ap.parse_args()
    if not a.cmd:
        a = ap.parse_args(['serve'])
    a.fn(a)


if __name__ == '__main__':
    main()
