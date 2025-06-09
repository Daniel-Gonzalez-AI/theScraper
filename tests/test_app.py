import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pytest
from webapp.app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_index_route(client):
    resp = client.get('/')
    assert resp.status_code == 200
    assert b'Scrape' in resp.data or b'URL' in resp.data

def test_discover_no_urls(client):
    resp = client.post('/discover', data={'urls': ''}, follow_redirects=False)
    assert resp.status_code == 302
