import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import os
import time
from datetime import datetime

# Import logger and utility functions from utils.py
from .utils import logger, sanitize_filename, create_session_output_directory, ROOT_OUTPUT_DIR

# --- Configuration Constants (moved from main.py) ---
REQUEST_TIMEOUT = 15  # seconds
POLITENESS_DELAY = 0.5 # seconds (discovery uses POLITENESS_DELAY / 2)
MAX_DISCOVERY_DEPTH = 5 # Max depth for link discovery
# ROOT_OUTPUT_DIR is now imported from utils

# --- Core Scraping Logic (adapted from main.py) ---

def discover_links_recursive(current_url, base_url_to_match, discovered_links_set, visited_discovery_urls, current_depth, discovery_stats):
    """
    Recursively discovers links starting from current_url, staying within base_url_to_match.
    Modifies discovered_links_set and visited_discovery_urls in place.
    discovery_stats is a dict {'checked_count': 0, 'found_count': 0} to track progress.
    """
    if current_url in visited_discovery_urls or current_depth > MAX_DISCOVERY_DEPTH:
        if current_depth > MAX_DISCOVERY_DEPTH:
            logger.debug(f"Max discovery depth ({MAX_DISCOVERY_DEPTH}) reached for path from {current_url}")
        return

    discovery_stats['checked_count'] += 1
    logger.info(f"Discovery L{current_depth} (Checked: {discovery_stats['checked_count']}): Visiting {current_url}")
    visited_discovery_urls.add(current_url)

    try:
        response = requests.get(current_url, timeout=REQUEST_TIMEOUT, allow_redirects=True)
        response.raise_for_status()

        # Add to discovered_links_set if it's within the base URL scope, even if it's the starting page
        if current_url.startswith(base_url_to_match):
             if current_url not in discovered_links_set:
                discovered_links_set.add(current_url)
                discovery_stats['found_count'] += 1
                if discovery_stats['found_count'] > 0 and discovery_stats['found_count'] % 20 == 0:
                    logger.info(f"  Discovery: Found {discovery_stats['found_count']} unique internal links so far...")

        soup = BeautifulSoup(response.content, 'html.parser')

        for link_tag in soup.find_all('a', href=True):
            href = link_tag['href']
            next_url_absolute = urljoin(current_url, href)

            parsed_next_url = urlparse(next_url_absolute)
            normalized_next_url = parsed_next_url._replace(fragment="").geturl() # Remove fragments

            if normalized_next_url.startswith(base_url_to_match) and \
               normalized_next_url not in visited_discovery_urls:
                # Check discovered_links_set again; it might have been added by a parallel path
                if normalized_next_url not in discovered_links_set:
                    discovered_links_set.add(normalized_next_url)
                    discovery_stats['found_count'] += 1
                    logger.debug(f"  Discovery L{current_depth}: Added new link to explore: {normalized_next_url}")
                    if discovery_stats['found_count'] > 0 and discovery_stats['found_count'] % 20 == 0:
                        logger.info(f"  Discovery: Found {discovery_stats['found_count']} unique internal links so far...")

                # Small delay before recursive call
                time.sleep(POLITENESS_DELAY / 2)
                discover_links_recursive(normalized_next_url, base_url_to_match, discovered_links_set, visited_discovery_urls, current_depth + 1, discovery_stats)

            elif normalized_next_url in visited_discovery_urls:
                 logger.debug(f"  Discovery: Skipping already visited link: {normalized_next_url}")
            elif not normalized_next_url.startswith(base_url_to_match):
                 logger.debug(f"  Discovery: Skipping external link: {normalized_next_url}")

    except requests.exceptions.RequestException as e:
        logger.warning(f"Discovery: Request failed for {current_url}: {e}")
    except Exception as e:
        logger.error(f"Discovery: An unexpected error occurred while processing {current_url}: {e}", exc_info=True)


def crawl_and_extract_single_page(page_url, output_dir):
    """
    Crawls a single page, extracts its text content, and saves it to a file.
    Returns True if successful, False otherwise.
    output_dir is the session-specific directory where the file should be saved.
    """
    try:
        logger.info(f"Scraping content from: {page_url}")

        response = requests.get(page_url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        logger.debug(f"Successfully retrieved URL: {page_url} (Status: {response.status_code})")

        soup = BeautifulSoup(response.content, 'html.parser')
        content_element = None
        # Common selectors for main content areas
        possible_selectors = [
            'article.main-content', 'div.markdown-body', 'article', 'main',
            'div.content', 'div#content', 'section.content',
            'div[role="main"]', 'div.main', 'div.post-content', 'body'
        ]
        for selector in possible_selectors:
            content_element = soup.select_one(selector)
            if content_element:
                logger.debug(f"Content found for {page_url} using selector: '{selector}'")
                break

        text_content = ""
        if content_element:
            # Remove common noisy elements like nav, footer, scripts, styles, etc.
            for noisy_tag_selector in ['nav', 'footer', 'script', 'style', '.noprint', '.no-export', 'header', 'aside', 'form', '.sidebar', '#sidebar']:
                for tag in content_element.select(noisy_tag_selector):
                    tag.decompose()
            text_content = content_element.get_text(separator='\n', strip=True)
        else:
            text_content = "Content not found (no specific selectors matched or body tag missing)."
            logger.warning(f"No primary content element found for URL: {page_url}. Extracted text might be from the whole body or incomplete.")

        # Determine filename
        url_path_part = urlparse(page_url).path
        # If path is empty or just '/', use 'index' or a sanitized version of the domain
        if not url_path_part or url_path_part == '/':
            filename_base = sanitize_filename(urlparse(page_url).netloc) + "_index"
        else:
            filename_base = url_path_part.strip('/')

        sanitized_name = sanitize_filename(filename_base)

        # Ensure filename isn't empty after sanitization
        if not sanitized_name:
            sanitized_name = "unnamed_page"

        filename = os.path.join(output_dir, f"{sanitized_name}.txt")

        # Ensure the directory for the file exists (e.g., if sanitized_name created subpaths, though sanitize_filename aims to prevent this)
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        with open(filename, "w", encoding="utf-8") as file:
            file.write(f"URL: {page_url}\n")
            file.write(f"Scraped_At: {datetime.now().isoformat()}\n\n")
            file.write(text_content)
        logger.info(f"Saved content from {page_url} to {filename}")
        return True

    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error for {page_url}: {e.response.status_code} {e.response.reason}. Message: {e}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed for {page_url}: {e}", exc_info=False) # Set exc_info=False for less verbose request errors
    except IOError as e:
        logger.error(f"IOError writing file for {page_url}: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"An unexpected error occurred while processing {page_url}: {e}", exc_info=True)
    return False


# --- Functions to be called by the Flask app ---

def start_link_discovery(base_url):
    """
    Initiates link discovery for a given base_url.
    Returns a sorted list of unique discovered URLs.
    """
    logger.info(f"Starting link discovery for base URL: {base_url}. Max depth: {MAX_DISCOVERY_DEPTH}.")

    discovered_links_set = set()
    visited_discovery_urls = set() # URLs visited during this discovery session
    discovery_stats = {'checked_count': 0, 'found_count': 0}

    # Ensure base_url itself is added if it's valid and discoverable
    # The discover_links_recursive function will handle adding it.

    discover_links_recursive(base_url, base_url, discovered_links_set, visited_discovery_urls, 0, discovery_stats)

    logger.info(f"Discovery phase for {base_url} complete. Checked {discovery_stats['checked_count']} URLs, found {len(discovered_links_set)} unique internal links.")

    if not discovered_links_set:
        logger.warning(f"No links found for {base_url} (or initial page failed to load).")
        return []

    return sorted(list(discovered_links_set))


def scrape_selected_pages(base_url_for_naming, urls_to_scrape, existing_session_dir=None):
    """
    Scrapes a list of selected URLs.
    - base_url_for_naming: Used for creating the session directory name.
    - urls_to_scrape: A list of URLs to be scraped.
    - existing_session_dir: If provided, use this directory. Otherwise, create a new one.
    Returns a tuple: (session_output_dir, pages_scraped_count, total_pages_selected, errors_occurred_list)
    """
    if not urls_to_scrape:
        logger.info("No URLs provided to scrape.")
        return None, 0, 0, []

    try:
        if existing_session_dir:
            session_output_dir = existing_session_dir
            logger.info(f"Using existing session directory: {session_output_dir}")
        else:
            # Creates a directory like /data/Web_Scrapes/domain_com_YYYY-MM-DD_HH-MM-SS
            # The ROOT_OUTPUT_DIR from utils is used by default by create_session_output_directory
            session_output_dir = create_session_output_directory(base_url_for_naming)

        # Session-specific logging can be set up here if desired, using utils.setup_session_logging
        # For now, we'll rely on the global logger configured in utils.py
        # log_file_path = os.path.join(session_output_dir, "scraping_log.txt")
        # setup_session_logging(log_file_path) # This would reconfigure the global logger

    except OSError:
        logger.critical(f"Critical error: Could not create/access output directory for {base_url_for_naming}. Skipping scraping.")
        # In a web app, this should be reported back to the user.
        return None, 0, len(urls_to_scrape), [f"Failed to create output directory for {base_url_for_naming}"]
    except Exception as e:
        logger.critical(f"Unexpected error during session setup for {base_url_for_naming}: {e}", exc_info=True)
        return None, 0, len(urls_to_scrape), [f"Unexpected error during session setup: {str(e)}"]


    pages_scraped_count = 0
    errors_occurred = [] # To collect URLs that failed

    logger.info(f"Starting scraping for {len(urls_to_scrape)} selected page(s) related to {base_url_for_naming}.")
    logger.info(f"Output will be saved to: {session_output_dir}")

    for page_url in urls_to_scrape:
        time.sleep(POLITENESS_DELAY) # Politeness delay between each scrape
        if not crawl_and_extract_single_page(page_url, session_output_dir):
            errors_occurred.append(page_url)
            logger.warning(f"Failed to scrape or save: {page_url}")
        else:
            pages_scraped_count += 1

    logger.info(f"Scraping for {base_url_for_naming} completed. {pages_scraped_count}/{len(urls_to_scrape)} page(s) saved in '{session_output_dir}'.")
    if errors_occurred:
        logger.warning(f"There were errors scraping the following URLs: {', '.join(errors_occurred)}")

    return session_output_dir, pages_scraped_count, len(urls_to_scrape), errors_occurred

# Example usage (for testing, not part of Flask app flow directly):
# if __name__ == '__main__':
# logger.info("Testing scraper functions...")
# test_base_url = "http://example.com" # Replace with a suitable test URL

# discovered = start_link_discovery(test_base_url)
# if discovered:
# logger.info(f"\nDiscovered {len(discovered)} links for {test_base_url}:")
# for i, link in enumerate(discovered):
# logger.info(f"  {i+1}. {link}")

# # Simulate selecting a few links to scrape
#       pages_to_scrape_test = discovered[:2] # Scrape the first 2 discovered links
# if pages_to_scrape_test:
#           logger.info(f"\nSimulating scraping of {len(pages_to_scrape_test)} links from {test_base_url}...")
#           output_dir, scraped_count, total_selected, errors = scrape_selected_pages(test_base_url, pages_to_scrape_test)
# if output_dir:
#               logger.info(f"Test scraping complete. {scraped_count}/{total_selected} saved to {output_dir}")
# if errors:
#                   logger.warning(f"Test scraping errors for: {errors}")
# else:
#               logger.warning(f"No pages selected or an error occurred before scraping could start for {test_base_url}.")
# else:
# logger.warning(f"No links discovered for {test_base_url}, cannot test scraping.")
#
#   # Test with a non-existent site to see error handling
#   # test_bad_url = "http://thissitedefinitelydoesnotexist12345.com"
#   # logger.info(f"\nTesting discovery for a non-existent site: {test_bad_url}")
#   # discovered_bad = start_link_discovery(test_bad_url)
#   # if not discovered_bad:
#   #    logger.info(f"Correctly found no links for {test_bad_url}")
#   # else:
#   #    logger.error(f"Incorrectly found links for non-existent site: {discovered_bad}")
