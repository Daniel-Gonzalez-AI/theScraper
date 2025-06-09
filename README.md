# Web Scraper UI

## Overview

Web Scraper UI is a Flask-based web application that allows users to scrape text content from websites. It features a user-friendly interface for entering multiple URLs, discovering internal links, selecting specific pages for scraping, and then extracting their content. Scraped data is saved into session-specific directories. The application is containerized using Docker and includes an integrated Filebrowser service for easy viewing, downloading, and management of the scraped files.

## Features

*   **Web-based Interface:** Modern UI for initiating and managing scraping tasks.
*   **Recursive Link Discovery:** Enter one or more base URLs, and the application will discover internal links up to a configurable depth.
*   **Selective Scraping:** Users can review the list of discovered links and select which ones to scrape.
*   **Text Content Extraction:** Extracts the main textual content from selected web pages.
*   **Organized Output:** Scraped content is saved in `.txt` files, organized into session-specific folders named after the target domain and timestamp.
*   **Integrated File Management:** Filebrowser service provides easy access to view, download, and manage scraped files directly in your browser.
*   **Dockerized:** Comes with `Dockerfile` and `docker-compose.yml` for quick and consistent setup and deployment.
*   **Persistent Storage:** Scraped data is stored in a Docker named volume, ensuring data persistence across container restarts.

## Prerequisites

*   [Docker](https://www.docker.com/get-started)
*   [Docker Compose](https://docs.docker.com/compose/install/) (usually included with Docker Desktop)

## Setup and Running

1.  **Clone the Repository:**
    ```bash
    git clone <repository_url>
    cd <repository_directory_name>
    ```

2.  **Build and Run with Docker Compose:**
    From the project root directory (where `docker-compose.yml` is located), run:
    ```bash
    docker-compose up --build -d
    ```
    *   The `--build` flag ensures the Docker image is built (or rebuilt if changes were made).
    *   The `-d` flag runs the containers in detached mode (in the background).

3.  **Access the Services:**
    *   **Web Scraper Application:** `http://localhost:5000`
    *   **Filebrowser (File Manager):** `http://localhost:8080/filebrowser/`

    *Note: It might take a few moments for the services to start up completely after running the `docker-compose up` command.*

## How to Use

1.  **Navigate to the Web App:** Open your browser and go to `http://localhost:5000`.
2.  **Enter Base URLs:** On the homepage, enter one or more full base URLs (e.g., `https://example.com/docs`) into the text area. You can separate multiple URLs by commas or newlines. Click "Discover Links".
3.  **Review and Select Links:** The application will display a list of links discovered under each base URL. Review these links and uncheck any you do not wish to scrape. By default, all discovered links are selected.
4.  **Initiate Scraping:** Once you've made your selection, click the "Scrape Selected Links" button.
5.  **View Results:** The next page will show a summary of the scraping process, including the location of the saved files within the container.
6.  **Access Scraped Files:**
    *   Click the "Access Scraped Files (File Manager)" link on the results page.
    *   Or, navigate directly to Filebrowser at `http://localhost:8080/filebrowser/`.
    *   Inside Filebrowser, you will see the `Web_Scrapes` directory (which is the root configured for Filebrowser). Your scraped files are organized in subdirectories usually named after the domain and a timestamp (e.g., `example_com_YYYY-MM-DD_HH-MM-SS/`).

## Project Structure

*   `Dockerfile`: Defines the Python environment and setup for the Flask web application.
*   `docker-compose.yml`: Orchestrates the deployment of the web application and Filebrowser services, including volume management.
*   `requirements.txt`: Lists Python dependencies for the web application.
*   `.dockerignore`: Specifies files to exclude from the Docker build context.
*   `webapp/`: Contains the Flask application source code.
    *   `app.py`: Main Flask application file (routes, views).
    *   `scraper.py`: Core link discovery and content scraping logic.
    *   `utils.py`: Utility functions (e.g., filename sanitization, directory creation).
    *   `static/`: Static assets (e.g., CSS files).
    *   `templates/`: HTML templates for the web interface.
*   `README.md`: This file.

## Configuration Notes

*   **Output Directory:** The web application saves scraped files to `/data/Web_Scrapes` inside its container. This path is mapped to the `scraper_data` Docker volume.
*   **Filebrowser Root:** Filebrowser is configured to use `/srv/Web_Scrapes` as its root directory. This path also maps to the `Web_Scrapes` folder within the shared `scraper_data` volume, effectively showing the same data as the scraper produces.
*   **Filebrowser Authentication:** For development purposes, Filebrowser authentication is currently disabled (`FB_NOAUTH=true`). For a production environment, you should enable authentication by setting `FB_NOAUTH=false` in `docker-compose.yml` and configuring users (refer to Filebrowser documentation).
*   **Scraping Depth:** The maximum depth for link discovery (`MAX_DISCOVERY_DEPTH`) is set as a constant in `webapp/scraper.py`.

## Netlify Deployment

The project can be deployed to [Netlify](https://www.netlify.com/) using Netlify Functions for the Flask backend. The repository includes a `netlify.toml` configuration and a function wrapper under `netlify/functions/`.
All incoming requests are redirected to the function via `webapp/static/_redirects`.

To deploy:

1. **Install the Netlify CLI** (optional for local testing):
   ```bash
   npm install -g netlify-cli
   ```
2. **Build and deploy**:
   ```bash
   netlify deploy --build
   ```
   Follow the CLI prompts to create or select a site. After the initial deploy, you can use `netlify deploy --prod` to publish.
   Ensure the `_redirects` file is included so all routes are served by the Flask function.

During the build, Netlify installs dependencies from `netlify/functions/requirements.txt` into the functions directory. This is configured in `netlify.toml` using `pip install -r netlify/functions/requirements.txt -t netlify/functions` so that the Flask app is properly packaged as a serverless function.

## Troubleshooting

*   **Port Conflicts:** Ensure ports `5000` and `8080` (or any other ports you configure) are not already in use by other applications on your host machine.
*   **Filebrowser Empty:** If Filebrowser shows an empty `/Web_Scrapes` directory, it means no scraping sessions have been completed yet, or there was an issue saving the files. Check the web application logs via `docker-compose logs web`.
*   **Permissions Issues (Volumes):** Docker named volumes generally handle permissions well. If you encounter issues with files not being written, check the container logs. Running Filebrowser as `user: root` in `docker-compose.yml` is a workaround for some permission complexities but consider refining permissions for production.
*   **Firewall:** Ensure your firewall is not blocking access to the specified ports if you are trying to access the application from another machine on your network. For local access, this is usually not an issue.

## License

This project is licensed under the [MIT License](LICENSE). See the LICENSE file for details.

---
ArtemisAI - Open Source Project - 2025
