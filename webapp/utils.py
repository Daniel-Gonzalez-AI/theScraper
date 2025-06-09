import os
import logging
import re
from datetime import datetime
from urllib.parse import urlparse

# Global Logger - This might be reconfigured for Flask app context later
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Output directory can be overridden with SCRAPER_OUTPUT_DIR.
# Default to a writable location within the container/CI environment.
ROOT_OUTPUT_DIR = os.getenv("SCRAPER_OUTPUT_DIR", "/tmp/Web_Scrapes")

def setup_session_logging(log_file_path):
    # This function might need changes for a web app context,
    # especially if multiple users are making requests concurrently.
    # For now, it's a direct move.
    global logger
    # Clear existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # File handler for the specific session
    file_handler = logging.FileHandler(log_file_path, mode='w')
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'))

    # Console handler (might be less relevant for a web server, but good for debugging)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.setLevel(logging.DEBUG) # Or INFO, depending on desired verbosity
    logger.info(f"Session-specific logging initialized. Log file: {log_file_path}")


def sanitize_filename(url_part):
    name = re.sub(r'^https?://', '', url_part)
    name = re.sub(r'[/:?*"<>|&%=#]', '_', name)
    name = re.sub(r'_+', '_', name)
    name = name.strip('_')
    max_len = 100  # Max length for a filename segment
    if len(name) > max_len:
        # Attempt to preserve the end of the name if it's a common file extension
        parts = name.split('.')
        if len(parts) > 1 and len(parts[-1]) < 10: # e.g. .html, .txt
            ext = parts[-1]
            name = name[:max_len - len(ext) - 4] + "..." + ext
        else:
            name = name[:max_len - 3] + '...'
    if not name:
        name = "unnamed_page"
    return name

def create_session_output_directory(base_url_for_naming, root_output_dir=ROOT_OUTPUT_DIR):
    """
    Creates a session-specific output directory.
    The root_output_dir parameter is used, defaulting to the global ROOT_OUTPUT_DIR.
    """
    try:
        # Ensure the root_output_dir from the parameter is used
        os.makedirs(root_output_dir, exist_ok=True)

        parsed_url = urlparse(base_url_for_naming)
        domain = parsed_url.netloc.replace("www.", "")
        path_part = parsed_url.path.strip('/').replace('/', '_')

        # Sanitize domain and path parts separately before combining
        sane_domain = sanitize_filename(domain)
        sane_path = sanitize_filename(path_part) if path_part else ""

        folder_base_name = sane_domain + ('_' + sane_path if sane_path else '')
        # Further sanitize the combined name in case it's too long or problematic
        folder_base_name = sanitize_filename(folder_base_name)


        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        session_dir_name = f"{folder_base_name}_{timestamp}"

        # Ensure session_dir_name is also a valid directory name (though sanitize_filename should handle most)
        session_dir_name = sanitize_filename(session_dir_name)

        # Ensure the correct root directory is used for joining
        session_output_dir = os.path.join(root_output_dir, session_dir_name)
        os.makedirs(session_output_dir, exist_ok=True)

        logger.info(f"Created session output directory: {session_output_dir}")
        return session_output_dir
    except OSError as e:
        logger.error(f"Failed to create output directories for {base_url_for_naming}: {e}", exc_info=True)
        # In a web app, we might want to raise this to be handled by the route
        raise
    except Exception as e:
        logger.error(f"An unexpected error occurred in create_session_output_directory for {base_url_for_naming}: {e}", exc_info=True)
        raise

# Example of how logging might be used from other modules:
# from .utils import logger
# logger.info("This is a log message from another module")
