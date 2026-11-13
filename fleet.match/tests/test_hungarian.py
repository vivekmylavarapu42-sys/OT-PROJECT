import random

import pytest

from fleetmatch.generator import generate
from fleetmatch.hungarian import hungarian
from fleetmatch.matching import brute_force, padded


def test_known_matrix():
    m = [[4, 1, 3], [2, 0, 5], [3, 2, 2]]
    assert sum(m[i][j] for i, j in hungarian(m)) == 5


@pytest.mark.parametrize('seed', range(30))
def test_matches_brute_force(seed):
    d = generate(random.Random(seed).randint(3, 7), random.Random(seed + 1).randint(3, 7), seed, radius=1.5)
    m = padded(d['riders'], d['drivers'])
    ours = sum(m[i][j] for i, j in hungarian(m))
    assert abs(ours - brute_force(d['riders'], d['drivers'])) < 1e-6


@pytest.mark.parametrize('seed', range(20))
def test_matches_scipy(seed):
    np = pytest.importorskip('numpy')
    lsa = pytest.importorskip('scipy.optimize').linear_sum_assignment
    d = generate(15, 12, 1000 + seed)
    m = np.array(padded(d['riders'], d['drivers']))
    r, c = lsa(m)
    assert abs(m[r, c].sum() - sum(m[i][j] for i, j in hungarian(m.tolist()))) < 1e-6
