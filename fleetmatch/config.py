"""Shared constants: fare slabs, platform-fee slabs and default weights."""

# (min_km, max_km, fare_inr) -- min inclusive, max exclusive
FARE = [(0, 2, 40), (2, 5, 90), (5, 10, 180), (10, 15, 270), (15, 99, 380)]

# (min_matches, max_matches, fee_per_match_inr) -- both inclusive
FEE = [(1, 10, 20), (11, 25, 25), (26, 50, 30), (51, 9999, 35)]

SPEED = 25.0   # average speed, km/h
BIG = 1e5      # cost of a forbidden rider-driver pair

W1, W2, W3 = 1.5, 1.0, 1.0   # wait, driver revenue, GMV weights
MAXPICK = 8.0                # max pickup distance, km

CENTER = (25.5355, 84.8520)  # Bihta / IIT Patna
NAMES = ['Amit', 'Priya', 'Rahul', 'Sneha', 'Vivek', 'Anjali',
         'Rohit', 'Neha', 'Karan', 'Pooja', 'Ravi', 'Sita']
