# Frontend Branding Roadmap

This document outlines the steps required to align the Web Scraper UI with the
**ArtemisAI Branding Guidelines** and ensure visual consistency with other
services.

## Goals

- Adopt Tailwind CSS for all styling to match the design system used across
  ArtemisAI projects.
- Update colours, fonts and spacing according to the branding guide.
- Replace the existing footer text with: `Developed as an open source resource by
  Daniel Gonzalez at ArtemisAI`.
- Review the layout of all templates so that components mirror the style of the
  main ArtemisAI website (see `astroWeb` repository for reference).
- Remove unused custom CSS once Tailwind covers the required styles.

## Steps

1. **Audit Current Styles**
   - Catalogue all custom CSS rules in `webapp/static/style.css`.
   - Identify which rules can be replaced with Tailwind classes.

2. **Introduce Tailwind**
   - Load Tailwind via CDN during development.
   - Migrate templates to use Tailwind utility classes.
   - Keep a minimal custom stylesheet for the spinner and dark mode toggle.

3. **Apply Branding**
   - Update colour palette and typography to match the
     ArtemisAI Branding Guidelines.
   - Ensure logos and imagery follow the approved assets.

4. **Consistency Review**
   - Compare each page against the `astroWeb` project to confirm alignment.
   - Perform accessibility checks and responsive testing.

5. **Finalize**
   - Remove deprecated CSS.
   - Document the new design choices in this `docs` directory.
   - Verify all tests pass and update screenshots if visual regression tests
     exist.

