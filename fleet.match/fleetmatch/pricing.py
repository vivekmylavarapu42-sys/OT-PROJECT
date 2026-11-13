"""Fare, platform fee and driver-acceptance rules."""
from .config import FARE, FEE


def fare(d):
    return next(f for a, b, f in FARE if a <= d < b)


def fee(n):
    return next((f for a, b, f in FEE if a <= n <= b), 0) if n else 0


def accepts(r, d):
    """A driver accepts a ride only if its length is inside [minD, maxD]."""
    return d['minD'] <= r['dist'] <= d['maxD']
