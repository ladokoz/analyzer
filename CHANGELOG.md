# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.2.1] - 2026-04-22

### Fixed
- **Unicode Encoding**: Enforced UTF-8 encoding across all internal logging, stdout, and stderr streams to prevent crashes when processing films with non-ASCII characters (e.g., full-width quotation marks).
- **Excel CSV Compatibility**: Migrated CSV exports to `utf-8-sig` encoding, adding a Byte Order Mark (BOM) to ensure special characters (like Polish or accented letters) display correctly when opened in Microsoft Excel.
- **Settings Persistence**: Fixed potential encoding crashes when saving or loading application prompts containing international characters.

---

## [1.2.0] - 2026-04-21

### Added
- **Web-Based Updater**: A new "Check Updates" button inside Settings that allows pulling the latest code from GitHub directly from the browser.
- **Version Tracking**: Real-time app version display in the Settings modal header, parsed directly from this changelog.

### Fixed
- Improved version extraction regex to avoid "Unreleased" labels and properly target semantic numbers.
- Migrated primary repository remote URL to `https://github.com/ladokoz/analyzer/`.

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
