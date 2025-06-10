# TODO List

This file outlines planned enhancements for the Web Scraper UI.

## Core Features

- [x] **Dark/Light Mode Toggle**: Basic JavaScript-powered theme switcher with persistent preference.
- **Tailwind CSS Styling**: Apply a clean Tailwind-based design throughout the interface.
- **Processing Spinner & Log View**:
  - Show a spinner while scraping is in progress.
  - Include a log dropdown (collapsed initially) that displays live status updates. When collapsed, show only the latest log line.
- [x] **Attribution & Licensing**: Display "Developed by Artemis Applied Research 2025" in the footer and add an open-source license suitable for this project.
- **Concatenate Files**: After scraping, provide a button to concatenate selected or all text files into a single `.txt` download.
- **Export Formats**: Offer options to convert concatenated results to PDF or other formats.

## Suggested Enhancements

- **Keyboard Shortcuts** for common actions (start scraping, toggle dark mode, etc.).
- **Search & Filter** within the discovered links list to quickly locate specific pages.
- **Session History** page showing previous scrapes with quick access to their results.
- **Error Reporting** with clearer messages and links to troubleshooting docs.

## Deployment

- **Netlify Build Fix**: Investigate failing deploys on Netlify. Verify Python dependency packaging and adjust `netlify.toml` if needed.

