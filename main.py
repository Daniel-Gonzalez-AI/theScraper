import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import os
import time
import logging
import re
from datetime import datetime

# --- Configuration ---
ROOT_OUTPUT_DIR = "Web_Scrapes"
REQUEST_TIMEOUT = 15  # seconds
POLITENESS_DELAY = 0.5 # seconds (discovery uses POLITENESS_DELAY / 2)
MAX_DISCOVERY_DEPTH = 5 # Max depth for link discovery

# --- Global Logger ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# --- Helper Functions ---

def setup_session_logging(log_file_path):
    global logger
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    file_handler = logging.FileHandler(log_file_path, mode='w')
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'))
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.setLevel(logging.DEBUG)
    logger.info(f"Session logging initialized. Log file: {log_file_path}")


def get_user_urls():
    while True:
        urls_input = input(
            "\nEnter base URL(s) to scrape, separated by commas (e.g., https://site1.com, https://site2.com/docs)\n"
            "Type 'quit' to exit: "
        ).strip()

        if not urls_input:
            logger.warning("No URLs entered. Please provide at least one URL or type 'quit'.")
            continue
        if urls_input.lower() == 'quit':
            return None

        raw_urls = [url.strip() for url in urls_input.split(',')]
        valid_urls = []
        has_invalid = False
        for url in raw_urls:
            if not url: continue
            if url.startswith("http://") or url.startswith("https://"):
                valid_urls.append(url)
            else:
                logger.error(f"Invalid URL format: '{url}'. URLs must start with http:// or https://.")
                has_invalid = True
        
        if has_invalid and not valid_urls:
            logger.warning("No valid URLs provided. Please try again.")
            continue
        if has_invalid and valid_urls:
            logger.warning(f"Some URLs were invalid. Processing valid ones: {', '.join(valid_urls)}")

        if valid_urls:
            return valid_urls

def sanitize_filename(url_part):
    name = re.sub(r'^https?://', '', url_part)
    name = re.sub(r'[/:?*"<>|&%=#]', '_', name)
    name = re.sub(r'_+', '_', name)
    name = name.strip('_')
    max_len = 100
    if len(name) > max_len:
        name = name[:max_len] + '___TRUNCATED___'
    if not name:
        name = "unnamed_page"
    return name

def create_session_output_directory(base_url_for_naming):
    try:
        os.makedirs(ROOT_OUTPUT_DIR, exist_ok=True)
        
        parsed_url = urlparse(base_url_for_naming)
        domain = parsed_url.netloc.replace("www.", "")
        path_part = parsed_url.path.strip('/').replace('/', '_')
        folder_base_name = sanitize_filename(domain + ('_' + path_part if path_part else ''))

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        session_dir_name = f"{folder_base_name}_{timestamp}"
        session_output_dir = os.path.join(ROOT_OUTPUT_DIR, session_dir_name)
        os.makedirs(session_output_dir, exist_ok=True)
        # Logger may not be session-specific yet, so use print or ensure logger is configured
        print(f"Created session output directory: {session_output_dir}")
        return session_output_dir
    except OSError as e:
        logger.error(f"Failed to create output directories for {base_url_for_naming}: {e}", exc_info=True)
        raise

def discover_links_recursive(current_url, base_url_to_match, discovered_links_set, visited_discovery_urls, current_depth, discovery_stats):
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
        
        if current_url.startswith(base_url_to_match):
             if current_url not in discovered_links_set: # Check before adding to count new ones
                discovered_links_set.add(current_url)
                discovery_stats['found_count'] += 1
                if discovery_stats['found_count'] > 0 and discovery_stats['found_count'] % 20 == 0:
                    logger.info(f"  Discovery: Found {discovery_stats['found_count']} unique internal links so far...")

        soup = BeautifulSoup(response.content, 'html.parser')

        for link_tag in soup.find_all('a', href=True):
            href = link_tag['href']
            next_url_absolute = urljoin(current_url, href)
            
            parsed_next_url = urlparse(next_url_absolute)
            normalized_next_url = parsed_next_url._replace(fragment="").geturl()

            if normalized_next_url.startswith(base_url_to_match) and \
               normalized_next_url not in visited_discovery_urls and \
               normalized_next_url not in discovered_links_set: # Check discovered_links_set to avoid redundant processing of already found links
                
                discovered_links_set.add(normalized_next_url) # Add before recursion
                discovery_stats['found_count'] += 1
                if discovery_stats['found_count'] > 0 and discovery_stats['found_count'] % 20 == 0:
                    logger.info(f"  Discovery: Found {discovery_stats['found_count']} unique internal links so far...")
                logger.debug(f"  Discovery L{current_depth}: Added new link to explore: {normalized_next_url}")

                time.sleep(POLITENESS_DELAY / 2)
                discover_links_recursive(normalized_next_url, base_url_to_match, discovered_links_set, visited_discovery_urls, current_depth + 1, discovery_stats)
            elif normalized_next_url in discovered_links_set or normalized_next_url in visited_discovery_urls:
                 logger.debug(f"  Discovery: Skipping already known/visited link: {normalized_next_url}")
            elif not normalized_next_url.startswith(base_url_to_match):
                 logger.debug(f"  Discovery: Skipping external link: {normalized_next_url}")


    except requests.exceptions.RequestException as e:
        logger.warning(f"Discovery: Request failed for {current_url}: {e}")
    except Exception as e:
        logger.error(f"Discovery: An unexpected error occurred while processing {current_url}: {e}", exc_info=True)


def parse_page_selection(selection_str, num_options):
    selected_indices = set()
    if not selection_str or selection_str.lower() == 'all':
        return list(range(num_options))

    parts = selection_str.split(',')
    for part in parts:
        part = part.strip()
        if not part: continue
        try:
            if '-' in part:
                start, end = map(int, part.split('-'))
                if not (1 <= start <= end <= num_options):
                    raise ValueError("Range out of bounds.")
                selected_indices.update(range(start - 1, end))
            else:
                num = int(part)
                if not (1 <= num <= num_options):
                    raise ValueError("Number out of bounds.")
                selected_indices.add(num - 1)
        except ValueError as e:
            logger.error(f"Invalid selection part: '{part}'. {e}. Please use numbers or ranges (e.g., 1,3,5-7).")
            return None
    return sorted(list(selected_indices))


def crawl_and_extract_single_page(page_url, output_dir, visited_scraping_urls_set):
    try:
        if page_url in visited_scraping_urls_set:
            logger.debug(f"Skipping already scraped URL in this session: {page_url}")
            return False

        logger.info(f"Scraping content from: {page_url}")
        visited_scraping_urls_set.add(page_url)

        response = requests.get(page_url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        logger.debug(f"Successfully retrieved URL: {page_url} (Status: {response.status_code})")

        soup = BeautifulSoup(response.content, 'html.parser')
        content_element = None
        possible_selectors = [
            'article.main-content', 'div.markdown-body', 'article', 'main',
            'div.content', 'div#content', 'section.content', 'body'
        ]
        for selector in possible_selectors:
            content_element = soup.select_one(selector)
            if content_element:
                logger.debug(f"Content found for {page_url} using selector: '{selector}'")
                break
        
        if content_element:
            for noisy_tag in content_element.select('nav, footer, script, style, .noprint, .no-export, header, aside'):
                noisy_tag.decompose()
            text = content_element.get_text(separator='\n', strip=True)
        else:
            text = "Content not found (no specific selectors matched or body tag missing)."
            logger.warning(f"No primary content element found for URL: {page_url}. Text might be incomplete.")

        url_path_part = urlparse(page_url).path
        filename_base = "index" if not url_path_part or url_path_part == '/' else url_path_part.strip('/')
        sanitized_name = sanitize_filename(filename_base)
        # Handle cases where sanitized_name might still be very long or create deep paths
        # For simplicity here, just use it directly. Complex paths might need os.path.basename()
        filename = os.path.join(output_dir, f"{sanitized_name}.txt")
        
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        with open(filename, "w", encoding="utf-8") as file:
            file.write(f"URL: {page_url}\n")
            file.write(f"Scraped_At: {datetime.now().isoformat()}\n\n")
            file.write(text)
        logger.info(f"Saved content from {page_url} to {filename}")
        return True

    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error for {page_url}: {e.response.status_code} {e.response.reason}. Message: {e}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed for {page_url}: {e}", exc_info=False)
    except IOError as e:
        logger.error(f"IOError writing file for {page_url}: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"An unexpected error occurred while processing {page_url}: {e}", exc_info=True)
    return False

# --- Main Workflow Functions ---

def process_single_base_url(base_url, round_stats_list):
    logger.info(f"\n--- Processing Base URL: {base_url} ---")

    # 1. Discovery Phase
    print(f"\nDiscovering links for {base_url} (max depth {MAX_DISCOVERY_DEPTH}).")
    print(f"This can take several minutes for large sites or if the network is slow. Please be patient...")
    logger.info(f"Starting link discovery for {base_url}. Max depth: {MAX_DISCOVERY_DEPTH}. Politeness delay between discovery requests: {POLITENESS_DELAY / 2:.2f}s.")
    
    discovered_links_set = set()
    visited_discovery_urls = set()
    discovery_stats = {'checked_count': 0, 'found_count': 0} # To provide better feedback
    
    discover_links_recursive(base_url, base_url, discovered_links_set, visited_discovery_urls, 0, discovery_stats)
    
    logger.info(f"Discovery phase for {base_url} complete. Checked {discovery_stats['checked_count']} URLs, found {len(discovered_links_set)} unique internal links.")
    discovered_urls_list = sorted(list(discovered_links_set))

    if not discovered_urls_list:
        logger.warning(f"No links found for {base_url} (or initial page failed to load). Skipping.")
        print(f"No discoverable internal pages found for {base_url}.")
        return

    print(f"\nFound {len(discovered_urls_list)} potential pages for {base_url}:")
    for i, link in enumerate(discovered_urls_list):
        print(f"  {i+1}. {link}")

    # 2. User Confirmation Phase
    while True:
        selection_prompt = (
            f"\nWhich pages do you want to scrape for {base_url}?\n"
            "  - Enter numbers/ranges (e.g., '1,3,5-8')\n"
            "  - 'all' (or press Enter) to scrape all listed pages\n"
            "  - 'none' or 'skip' to scrape nothing for this base URL\n"
            "  - 'back' to cancel processing this base URL\n"
            "Your choice: "
        )
        user_choice = input(selection_prompt).strip().lower()

        if user_choice == 'back':
            logger.info(f"User chose 'back'. Cancelling processing for {base_url}.")
            print(f"Cancelled processing for {base_url}.")
            return
        if user_choice in ['none', 'skip']:
            logger.info(f"User chose to skip scraping for {base_url}.")
            print(f"Skipping scraping for {base_url}.")
            return

        selected_indices = parse_page_selection(user_choice, len(discovered_urls_list))
        if selected_indices is not None:
            urls_to_scrape = [discovered_urls_list[i] for i in selected_indices]
            if not urls_to_scrape:
                 logger.info(f"User selection resulted in no pages to scrape for {base_url}.")
                 print(f"No pages selected for scraping from {base_url}.")
                 return
            break
        else:
            print("Invalid selection. Please try again.")

    logger.info(f"User selected {len(urls_to_scrape)} pages to scrape for {base_url}.")
    print(f"Proceeding to scrape {len(urls_to_scrape)} selected page(s) for {base_url}.")

    # 3. Scraping Phase
    try:
        session_output_dir = create_session_output_directory(base_url) # Uses print for now
        log_file_path = os.path.join(session_output_dir, "scraping_log.txt")
        setup_session_logging(log_file_path) # Reconfigures logger for this session
    except OSError:
        print(f"Critical error: Could not create output directory for {base_url}. Skipping this URL.")
        return

    pages_scraped_count = 0
    visited_scraping_urls_set = set()

    for page_url in urls_to_scrape:
        time.sleep(POLITENESS_DELAY)
        if crawl_and_extract_single_page(page_url, session_output_dir, visited_scraping_urls_set):
            pages_scraped_count += 1
    
    logger.info(f"Scraping for {base_url} completed. {pages_scraped_count} page(s) saved in '{session_output_dir}'.")
    print(f"\nScraping for {base_url} finished.")
    print(f"  {pages_scraped_count} page(s) processed.")
    print(f"  Output saved to: {session_output_dir}")
    
    round_stats_list.append({
        "base_url": base_url,
        "pages_scraped": pages_scraped_count,
        "output_dir": session_output_dir
    })

def main_workflow():
    print("--- Web Scraper Initialized ---")
    print(f"Output will be saved in subfolders under ./{ROOT_OUTPUT_DIR}/")
    print(f"Set MAX_DISCOVERY_DEPTH to {MAX_DISCOVERY_DEPTH}. Adjust in script if needed for deeper crawls (can be very slow).")

    while True:
        current_round_stats = []
        
        # Ensure logger is set for general console output before asking for URLs
        for handler in logger.handlers[:]: logger.removeHandler(handler)
        console_handler_main = logging.StreamHandler()
        console_handler_main.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(console_handler_main)
        logger.setLevel(logging.INFO)

        base_urls_to_process = get_user_urls()

        if base_urls_to_process is None:
            break
        
        if not base_urls_to_process:
            continue

        for base_url in base_urls_to_process:
            # Reset logger to general INFO console for this specific base_url's pre-session phase
            # (discovery and prompts) Session logging will take over if scraping starts.
            for handler in logger.handlers[:]: logger.removeHandler(handler)
            ch = logging.StreamHandler()
            ch.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            logger.addHandler(ch)
            logger.setLevel(logging.INFO)

            process_single_base_url(base_url, current_round_stats)
            print("-" * 40)

        if current_round_stats:
            print("\n===== Summary of this Run =====")
            for stat in current_round_stats:
                print(f"  Base URL: {stat['base_url']}")
                print(f"    Pages Scraped: {stat['pages_scraped']}")
                print(f"    Output Directory: {stat['output_dir']}")
            print("=============================\n")
        else:
            print("\nNo scraping tasks were completed in this round.\n")

        while True:
            more_work = input("Do you want to scrape more URLs? (yes/no): ").strip().lower()
            if more_work in ['yes', 'y']:
                break
            elif more_work in ['no', 'n']:
                return
            else:
                print("Invalid input. Please type 'yes' or 'no'.")
                
    print("\nExiting scraper. Goodbye!")

if __name__ == "__main__":
    try:
        main_workflow()
    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user (Ctrl+C). Exiting.")
        print("\nScraping interrupted. Exiting.")
    except Exception as e:
        logger.critical(f"An unhandled critical error occurred in the main workflow: {e}", exc_info=True)
        print(f"A critical error occurred. Please check the logs. Error: {e}")
