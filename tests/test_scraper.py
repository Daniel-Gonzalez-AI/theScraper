import http.server
import socket
import threading
import os
import functools
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest

from webapp.scraper import start_link_discovery, scrape_selected_pages

# Utility to start a simple HTTP server serving files from a directory
class ThreadedHTTPServer(object):
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
    # Create simple HTML pages
    index = tmp_path / 'index.html'
    page2 = tmp_path / 'page2.html'
    index.write_text('<html><body><a href="page2.html">Next</a></body></html>')
    page2.write_text('<html><body><p>Page 2</p></body></html>')

    # Bind to an available port
    sock = socket.socket()
    sock.bind(("localhost", 0))
    host, port = sock.getsockname()
    sock.close()

    with ThreadedHTTPServer(host, port, str(tmp_path)) as server:
        base_url = f"http://{host}:{port}"
        yield base_url, port


def test_start_link_discovery(local_site):
    base_url, _ = local_site
    links = start_link_discovery(base_url)
    # Should discover both pages
    assert any('page2.html' in url for url in links)
    assert base_url.rstrip('/') in [u.rstrip('/') for u in links]


def test_scrape_selected_pages(tmp_path, local_site):
    base_url, port = local_site
    links = [f"{base_url}/index.html", f"http://localhost:{port}/page2.html"]
    output_dir, scraped, total, errors = scrape_selected_pages(
        base_url_for_naming='localhost',
        urls_to_scrape=links,
        existing_session_dir=str(tmp_path)
    )
    assert output_dir == str(tmp_path)
    assert scraped == 2
    assert total == 2
    assert not errors
    # Verify files exist
    files = os.listdir(tmp_path)
    assert any('index' in f for f in files)
    assert any('page2' in f for f in files)
