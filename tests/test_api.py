import pytest

from fleetmatch.server import app

PARAMS = dict(clat=25.5355, clng=84.852, rad=3, seed=7, nR=25, nD=20, aR=100, aD=100,
              tLo=1, tHi=12, mnLo=1, mnHi=5, mxLo=6, mxHi=15, w1=1.5, w2=1, w3=1, mp=8)


@pytest.fixture
def client():
    return app.test_client()


def test_index(client):
    r = client.get('/')
    assert r.status_code == 200 and b'Ride Matching' in r.data
    r.close()


def test_generate(client):
    d = client.post('/api/generate', json=PARAMS).get_json()
    assert len(d['riders']) == 25 and len(d['drivers']) == 20


def test_generate_bad_params(client):
    assert client.post('/api/generate', json={}).status_code == 400


def test_simulate(client):
    ds = client.post('/api/generate', json=PARAMS).get_json()
    o = client.post('/api/simulate', json={'dataset': ds, 'params': PARAMS}).get_json()
    assert set(o) == {'A', 'B', 'C', 'check'}
    assert o['check']['bad'] == 0 and o['check']['n'] > 0
    assert o['C']['gmv'] >= o['A']['gmv'] or o['C']['gmv'] >= 0


def test_simulate_bad_request(client):
    assert client.post('/api/simulate', json={}).status_code == 400
