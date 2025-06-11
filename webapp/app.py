from flask import Flask, render_template, request, url_for, redirect, Response, stream_with_context
import re
from urllib.parse import urlparse # Added for /scrape_selected
from .scraper import start_link_discovery, scrape_selected_pages
from .utils import logger, LogBufferHandler
import logging
import time

app = Flask(__name__)

# Log buffer handler keeps the last 10 log lines for streaming
log_buffer_handler = LogBufferHandler()
log_buffer_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(log_buffer_handler)

# Keep a simple global store for discovered links for now.
# In a real app, this would be per-session or use a database.
discovered_links_store = {}


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/discover', methods=['POST'])
def discover():
    urls_input = request.form.get('urls', '')
    # Split by newlines or commas, then strip whitespace and filter out empty strings
    raw_urls = re.split(r'[,\n]', urls_input)
    base_urls = [url.strip() for url in raw_urls if url.strip()]

    if not base_urls:
        # Redirect back to index with an error message (or handle more gracefully)
        logger.warning("No URLs provided for discovery.")
        return redirect(url_for('index')) # Consider adding flash messages for errors

    # Clear previous discovery results for this session/store
    # For simplicity, clearing the global store. If multiple users, this needs to be session-based.
    discovered_links_store.clear()

    for base_url in base_urls:
        if not (base_url.startswith("http://") or base_url.startswith("https://")):
            logger.warning(f"Skipping invalid URL (must start with http/https): {base_url}")
            # Store an error message for this URL or skip
            discovered_links_store[base_url] = {"error": "Invalid URL format. Must start with http:// or https://."}
            continue

        logger.info(f"Starting link discovery for: {base_url}")
        try:
            links = start_link_discovery(base_url)
            discovered_links_store[base_url] = {"links": links, "error": None}
            logger.info(f"Found {len(links)} links for {base_url}")
        except Exception as e:
            logger.error(f"Error during discovery for {base_url}: {e}", exc_info=True)
            discovered_links_store[base_url] = {"error": str(e), "links": []}

    # Pass the whole store to results.html, which will iterate through it
    return render_template('results.html', discovery_results=discovered_links_store)

@app.route('/scrape_selected', methods=['POST'])
def scrape_selected():
    selected_links = request.form.getlist('selected_links')

    # The form also submitted 'base_url_for_grouping' for each group.
    # For now, we'll treat all selected links as one batch and use the
    # first one's domain for naming the output directory, or a generic name.
    # A more sophisticated approach might group them by original base_url.

    if not selected_links:
        logger.warning("No links selected for scraping.")
        # Redirect to results or index, perhaps with a flash message
        return redirect(url_for('index')) # Or back to 'results' if state is preserved

    # Determine a base name for the session directory.
    # Using the first selected URL's domain, or a generic name.
    # This is a simplification. A robust app might handle multiple sources better.
    try:
        first_url_parsed = urlparse(selected_links[0])
        session_name_base = first_url_parsed.netloc if first_url_parsed.netloc else "general_scrape"
    except Exception:
        session_name_base = "general_scrape"

    logger.info(f"Received {len(selected_links)} links for scraping. Session base: {session_name_base}")

    # logs are automatically captured by log_buffer_handler

    # Call the scraper function (ensure it's imported)
    # from .scraper import scrape_selected_pages (should be at the top of the file)
    # For now, assuming scrape_selected_pages is ready and imported.
    # It should handle creation of the session directory using utils.create_session_output_directory
    # which will use the ROOT_OUTPUT_DIR (to be updated to /data/Web_Scrapes).

    # The scrape_selected_pages function from previous subtask returns:
    # (session_output_dir, pages_scraped_count, total_pages_selected, errors_occurred_list)
    # We need to import it: from .scraper import scrape_selected_pages

    # Let's ensure the import is there (mentally, as I can't check current file state without reading it again)
    # Assuming: from .scraper import start_link_discovery, scrape_selected_pages

    try:
        # We pass session_name_base to help name the directory within ROOT_OUTPUT_DIR
        # scrape_selected_pages will call create_session_output_directory
        output_dir, num_scraped, num_selected, errors = scrape_selected_pages(
            base_url_for_naming=session_name_base,
            urls_to_scrape=selected_links
        )

        if output_dir: # If None, it means directory creation failed critically
            logger.info(f"Scraping session complete. Output directory: {output_dir}")
            return render_template('scraped.html',
                                   output_directory=output_dir,
                                   num_scraped=num_scraped,
                                   num_selected=num_selected,
                                   errors=errors,
                                   selected_links=selected_links)
        else:
            logger.error("Scraping failed critically: No output directory was created/returned.")
            # Handle this critical error, maybe show a different template or an error message
            # For now, redirecting to index with a conceptual error state.
            # A flash message would be good here.
            return redirect(url_for('index')) # Simplified error handling

    except Exception as e:
        logger.error(f"An unexpected error occurred during scraping process: {e}", exc_info=True)
        # Generic error feedback
        return render_template('scraped.html', error_message=str(e), selected_links=selected_links)


@app.route('/logs_stream')
def logs_stream():
    def event_stream():
        last = 0
        while True:
            while len(log_buffer_handler.buffer) > last:
                line = log_buffer_handler.buffer[last]
                last += 1
                yield f"data: {line}\n\n"
            time.sleep(1)
    return Response(stream_with_context(event_stream()), mimetype='text/event-stream')


if __name__ == '__main__':
    # Make sure to run in a way that the development server can be accessed.
    # host='0.0.0.0' makes it accessible on the network, useful for Docker.
    app.run(debug=True, host='0.0.0.0')
