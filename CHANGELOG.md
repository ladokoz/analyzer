# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

### Versioning Rules for Future Updates
- **Major (X.0.0)**: Massive architectural overhauls, rewriting core modules, or completely restructuring the UI.
- **Minor (1.X.0)**: Adding new features, new endpoints, new visible buttons, or significant enhancements to existing systems (backwards-compatible).
- **Patch (1.0.X)**: Small bug fixes, caching/performance tweaks, typo corrections, or minor adjustments to CSS styling.

---

## [Unreleased]
*Any work-in-progress features will be tracked here before receiving a version bump.*

---

## [1.1.0] - 2026-04-21

### Added
- Implemented environment variable-based security (`.env`) using `python-dotenv`.
- Separated API keys, Vimeo credentials, and default admin login parameters securely onto the server rather than the web UI.

### Changed
- Removed vulnerable key inputs for Gemini and Vimeo from the web UI settings modal.
- Cleaned up application config (`data/settings.json`) schema so credentials are no longer persisted structurally to local files.
- `README.md` created to document setup and `.env` initialization logic.

### Fixed
- Fixed critical Cloudflare and browser caching mismatches by injecting explicit `Cache-Control: no-cache` server headers for the frontend payload endpoints.
- Bumped frontend script `v` string parameters to forcefully bypass stale cache buffers.

---

## [1.0.0] - Initial Tracking State

*Historical base of Ahub Video Analyzer before formalized changelog tracking. Includes batch background worker architecture, Gemini payload processing capabilities, and foundational UI queue interfaces.*
