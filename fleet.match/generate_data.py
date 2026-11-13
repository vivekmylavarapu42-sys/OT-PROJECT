"""Generate sample data.

  python generate_data.py                       # 25 riders, 20 drivers, seed 7
  python generate_data.py --riders 40 --drivers 30 --seed 3

Writes:
  data/dataset.json        -> upload in the web UI ("Upload dataset")
  data/ride_requests.csv   -> riders asking for a ride
  available_drivers.csv    -> drivers currently available
"""
import argparse
import csv
import json
import os

from fleetmatch.generator import generate

ROOT = os.path.dirname(os.path.abspath(__file__))


def write_csv(path, rows, fields):
    with open(path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r[k] for k in fields})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--riders', type=int, default=25)
    ap.add_argument('--drivers', type=int, default=20)
    ap.add_argument('--seed', type=int, default=7)
    a = ap.parse_args()

    ds = generate(a.riders, a.drivers, a.seed)
    os.makedirs(os.path.join(ROOT, 'data'), exist_ok=True)
    with open(os.path.join(ROOT, 'data', 'dataset.json'), 'w') as f:
        json.dump(ds, f, indent=1)
    write_csv(os.path.join(ROOT, 'data', 'ride_requests.csv'), ds['riders'],
              ['id', 'lat', 'lng', 'dist', 'on'])
    write_csv(os.path.join(ROOT, 'available_drivers.csv'), ds['drivers'],
              ['id', 'name', 'lat', 'lng', 'minD', 'maxD', 'on'])
    print(f'Generated {a.riders} riders and {a.drivers} drivers (seed {a.seed}).')


if __name__ == '__main__':
    main()
