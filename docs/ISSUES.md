# Issue Tracker

This file documents notable issues and their resolutions.

## Resolved
- **2025-06-09**: Results page crashed with `UndefinedError` for `loop.parent` after Jinja upgrade. Fixed by capturing the outer loop index in a variable.

## Open
- **Netlify Deployment Failure**: Deploys succeed locally but fail on Netlify. Suspect missing dependencies in the function bundle. Investigate packaging during the build step.
