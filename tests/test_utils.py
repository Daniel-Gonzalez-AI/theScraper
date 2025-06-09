import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from webapp.utils import sanitize_filename, create_session_output_directory
import os


def test_sanitize_filename():
    assert sanitize_filename('https://example.com/page?query=1') == 'example.com_page_query_1'


def test_create_session_output_directory(tmp_path):
    d = create_session_output_directory('https://example.com', root_output_dir=tmp_path)
    assert os.path.isdir(d)
    assert str(d).startswith(str(tmp_path))
