# This file is intentionally left blank.
# The main application logic has been moved to the webapp/ directory
# and is run via app.py (Flask application).
#
# For CLI-based operations, if any are reintroduced, they would be
# managed separately, possibly by a different script or by adding
# CLI commands to the Flask app.

# Original content included:
# - imports: requests, BeautifulSoup, urllib.parse, os, time, logging, re, datetime
# - Configuration: ROOT_OUTPUT_DIR, REQUEST_TIMEOUT, POLITENESS_DELAY, MAX_DISCOVERY_DEPTH
# - Global Logger setup
# - Helper Functions: setup_session_logging, get_user_urls, sanitize_filename, create_session_output_directory
# - Core Scraping Logic: discover_links_recursive, parse_page_selection, crawl_and_extract_single_page
# - Main Workflow: process_single_base_url, main_workflow
# - if __name__ == "__main__": block to run main_workflow()

# All relevant functionality has been refactored into:
# - webapp/app.py: Flask application, routes, and UI interaction.
# - webapp/scraper.py: Core scraping functions (discovery, page crawling).
# - webapp/utils.py: Helper utilities (logging, file/path management).

# To run the web application:
# Ensure Flask and other dependencies (requests, beautifulsoup4) are installed.
# Navigate to the project root in your terminal.
# Set the FLASK_APP environment variable: export FLASK_APP=webapp/app.py (Linux/macOS) or set FLASK_APP=webapp\app.py (Windows)
# Run Flask: flask run
# Open your browser to the address provided by Flask (usually http://127.0.0.1:5000/).
