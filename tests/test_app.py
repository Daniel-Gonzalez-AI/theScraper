import os, sys
import http.server
import socket
import threading
import functools

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from webapp.app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

class ThreadedHTTPServer:
    def __init__(self, host, port, directory):
        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=directory)
        self.server = http.server.ThreadingHTTPServer((host, port), handler)
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.daemon = True

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.server.shutdown()
        self.thread.join()

@pytest.fixture
def local_site(tmp_path):
    index = tmp_path / 'index.html'
    page2 = tmp_path / 'page2.html'
    index.write_text('<html><body><a href="page2.html">Next</a></body></html>')
    page2.write_text('<html><body><p>Page 2</p></body></html>')

    sock = socket.socket()
    sock.bind(("localhost", 0))
    host, port = sock.getsockname()
    sock.close()

    with ThreadedHTTPServer(host, port, str(tmp_path)):
        yield f"http://{host}:{port}"

def test_index_route(client):
    resp = client.get('/')
    assert resp.status_code == 200
    assert b'Scrape' in resp.data or b'URL' in resp.data
    assert b'Developed by Artemis Applied Research 2025' in resp.data
    assert b'mode-toggle' in resp.data

def test_discover_no_urls(client):
    resp = client.post('/discover', data={'urls': ''}, follow_redirects=False)
    assert resp.status_code == 302


def test_discover_valid_url(client, local_site):
    resp = client.post('/discover', data={'urls': local_site})
    assert resp.status_code == 200
    assert b'Select links to scrape' in resp.data
    assert b'Developed by Artemis Applied Research 2025' in resp.data
    assert b'mode-toggle' in resp.data

def test_scrape_selected_footer(client, local_site):
    links = [f"{local_site}/index.html", f"{local_site}/page2.html"]
    resp = client.post('/scrape_selected', data={'selected_links': links})
    assert resp.status_code == 200
    assert b'Developed by Artemis Applied Research 2025' in resp.data
    assert b'mode-toggle' in resp.data
