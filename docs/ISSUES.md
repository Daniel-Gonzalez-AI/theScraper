# Issue Tracker

This file documents notable issues and their resolutions.

## Resolved
- **2025-06-09**: Results page crashed with `UndefinedError` for `loop.parent` after Jinja upgrade. Fixed by capturing the outer loop index in a variable.
