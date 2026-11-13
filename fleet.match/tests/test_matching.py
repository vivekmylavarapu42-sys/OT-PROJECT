import pytest

from fleetmatch.config import MAXPICK
from fleetmatch.generator import generate
from fleetmatch.geo import hav
from fleetmatch.matching import alg_greedy, alg_ours, alg_random
from fleetmatch.pricing import accepts, fare, fee


def test_fare_slabs():
    assert [fare(x) for x in (1, 2, 5, 10, 15, 50)] == [40, 90, 180, 270, 380, 380]


def test_fee_slabs():
    assert [fee(n) for n in (0, 1, 10, 11, 25, 26, 50, 51)] == [0, 20, 20, 25, 25, 30, 30, 35]


def test_haversine_zero_and_symmetry():
    a, b = {'lat': 25.5, 'lng': 84.8}, {'lat': 25.6, 'lng': 84.9}
    assert hav(a, a) == 0
    assert hav(a, b) == pytest.approx(hav(b, a))


@pytest.mark.parametrize('seed', range(25))
def test_ours_respects_constraints(seed):
    d = generate(20, 15, 2000 + seed)
    pairs = alg_ours(d['riders'], d['drivers'])
    assert len({i for i, _ in pairs}) == len(pairs)
    assert len({j for _, j in pairs}) == len(pairs)
    for i, j in pairs:
        r, dr = d['riders'][i], d['drivers'][j]
        assert accepts(r, dr) and hav(r, dr) <= MAXPICK


def test_baselines_are_one_to_one():
    d = generate(25, 20, 7)
    for pairs in (alg_greedy(d['riders'], d['drivers']), alg_random(d['riders'], d['drivers'])):
        assert len({j for _, j in pairs}) == len(pairs) <= 20
