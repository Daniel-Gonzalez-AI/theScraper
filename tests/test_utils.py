import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from webapp.utils import sanitize_filename, create_session_output_directory, LogBufferHandler
import os
import logging


def test_sanitize_filename():
    assert sanitize_filename('https://example.com/page?query=1') == 'example.com_page_query_1'


def test_create_session_output_directory(tmp_path):
    d = create_session_output_directory('https://example.com', root_output_dir=tmp_path)
    assert os.path.isdir(d)
    assert str(d).startswith(str(tmp_path))


def test_log_buffer_handler_cap_limit():
    handler = LogBufferHandler(max_lines=10)
    handler.setFormatter(logging.Formatter('%(message)s'))
    test_logger = logging.getLogger('test_log_buffer')
    test_logger.addHandler(handler)
    test_logger.setLevel(logging.INFO)

    for i in range(12):
        test_logger.info(f'line {i}')

    assert len(handler.buffer) == 10
    assert handler.buffer[0] == 'line 2'
    assert handler.buffer[-1] == 'line 11'
