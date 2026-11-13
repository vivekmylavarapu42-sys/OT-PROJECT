# fleet.match

Multi-objective ride matching for **Bihta / IIT Patna**. Riders are matched to drivers with the **Hungarian algorithm** (O(n³)), optimising pickup wait, driver revenue and platform GMV at once, and compared against a Random/FIFO baseline and a Greedy nearest-driver baseline on an interactive map.

## Features

- Generate riders and drivers on a Leaflet map (satellite / street), or use your live location
- Drag markers, edit a rider's trip distance or a driver's min/max trip km and availability
- Compare **Random**, **Greedy** and **Hungarian (ours)**: rides, GMV, platform revenue, avg driver revenue, avg pickup km, avg wait, rejected rides
- Optimality check on the Hungarian result: no improving swap, replacement or extra match
- Dataset download/upload as JSON
- Flask API, plus CLI tools for data generation, matching and verification

## Project structure

```
fleet.match/
├── data/                    # dataset.json, ride_requests.csv
├── frontend/
│   └── index.html           # map UI (Leaflet, single page)
├── fleetmatch/
│   ├── config.py            # fare / fee slabs, weights, constants
│   ├── geo.py               # haversine distance
│   ├── pricing.py           # fare, platform fee, driver acceptance
│   ├── hungarian.py         # min-cost assignment
│   ├── matching.py          # cost function, Random / Greedy / Ours, metrics
│   ├── generator.py         # random dataset generators
│   ├── verify.py            # brute-force, SciPy, constraint checks, benchmark
│   └── server.py            # Flask API + static host
├── tests/                   # pytest suite
├── available_drivers.csv    # sample drivers (generated)
├── match_records.csv        # matches from `python main.py match`
├── generate_data.py         # sample-data generator
├── main.py                  # entry point: serve / match / verify
├── requirements.txt
└── README.md
```

## Setup

```bash
pip install -r requirements.txt
```

## Usage

```bash
python main.py                 # web app at http://localhost:5000
python main.py match           # match data/dataset.json -> match_records.csv
python main.py verify          # correctness checks + benchmark
python generate_data.py --riders 40 --drivers 30 --seed 3
python -m pytest               # run tests
```

## How matching works

For rider *r* and driver *d* (pickup distance `pk` in km, trip fare `f`):

```
cost(r, d) = W1 · pk / SPEED · 6  −  W2 · (f − 20) / 100  −  W3 · f / 100  −  1
```

- Defaults: `W1 = 1.5` (wait), `W2 = 1` (driver revenue), `W3 = 1` (GMV), `SPEED = 25 km/h`, `MAXPICK = 8 km`
- A pair costs `BIG` (forbidden) if the trip is outside the driver's `[minD, maxD]` km range or the pickup is beyond `MAXPICK`
- The matrix is padded to square and solved with the Hungarian algorithm; forbidden pairs are dropped from the result

**Fare (₹):** 0–2 km 40 · 2–5 km 90 · 5–10 km 180 · 10–15 km 270 · 15+ km 380
**Platform fee per match (₹):** 1–10 matches 20 · 11–25 matches 25 · 26–50 matches 30 · 51+ matches 35

## API

| Method | Endpoint | Body | Returns |
| --- | --- | --- | --- |
| POST | `/api/generate` | control params | `{center, riders, drivers}` |
| POST | `/api/simulate` | `{dataset, params}` | `{A, B, C, check}` |

## Verification

`python main.py verify` reports:

1. Hungarian cost equals the exhaustive (brute-force) optimum on small instances
2. Hungarian cost equals `scipy.optimize.linear_sum_assignment`
3. No match violates driver min/max trip km or max pickup km
4. Benchmark of Ours vs Random vs Greedy over 200 random instances (default 25 riders, 20 drivers)

Sample benchmark result (averages): Ours serves 20.0 rides with ₹3661 GMV, against 13.0 / ₹2146 (Random) and 12.9 / ₹2138 (Greedy); average wait 3.31 min vs 7.48 / 3.44 min.

## Deployment

Serve the backend with `gunicorn fleetmatch.server:app`. When the page is opened from a host other than `localhost`, set the `API` constant in `frontend/index.html` to your deployed backend URL.

## Tech stack

Python · Flask · NumPy / SciPy (verification) · Leaflet · Vanilla JS
