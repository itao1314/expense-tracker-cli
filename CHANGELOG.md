# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v1.0.0] - 2026-04-14

### Added
- Initial release of the Expense Tracker CLI with terminal-first expense management.
- `add` command for recording expenses with amount, description, and category.
- `list` command for viewing saved expenses with configurable result limits.
- `report` command for monthly reporting and category-based spending analysis.
- CSV export support via the `export` command.
- `delete` command for removing expenses by ID.
- `edit` command for updating expense amount, description, and category fields.
- Category summary output in reports, including total spend by category sorted in descending order.
- Local SQLite-backed storage with automatic database initialization.
- PyInstaller-based packaging workflow for producing a single-file executable at `dist/expense`.

### Changed
- Packaged executable startup flow was finalized with a dedicated top-level entrypoint so the built binary runs correctly outside a package context.

