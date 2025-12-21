# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Changed
- **Standardized date format in longreads files** - All 8 longreads-*.md files (2018-2025) now use consistent date format
  - **New format:** `**Friday, December 28 2018 - Fri. 12/28**` (matches all-links files)
  - **Previous formats were inconsistent:**
    - 2018-2021: `**Friday, December 28**` (missing year and abbreviated suffix)
    - 2022-2025: `## December 22, 2022` (heading format, missing day of week)
  - **Updated:** 393 dates across 8 files using automated Python script (`update_longreads_dates.py`)
  - **Benefits:** Improved consistency across all documentation, easier date parsing

### Added
- **SQLite Database + Datasette Support** - Complete dual-output system (markdown + database)
  - **One-time import:** `load_db.py` script imports existing markdown into SQLite
    - 6,152 showlinks imported from all-links-*.md files (2022-2025)
    - 649 longreads imported from longreads-*.md files (2022-2025)
    - Total: 6,801 links in database
  - **Schema:** Single `links` table with hybrid date storage
    - TEXT dates (ISO format: YYYY-MM-DD) for human-readable queries
    - INTEGER dates (Unix timestamps) for efficient calculations
    - Columns: date, title, url, source, link_type, episode_date
    - Unique index on (url, date) prevents duplicates
  - **Database modules:**
    - `db_schema.py` - Schema creation with indexes
    - `markdown_parser.py` - Parse markdown bullets into structured data
    - `db_writer.py` - Insert with duplicate detection & date conversion
    - `load_db.py` - CLI for one-time imports
  - **Extract.py integration:** Dual output to markdown AND SQLite
    - `./extract.py` now writes to both docs/*.md and ridehome.db
    - `--skip-db` flag to update markdown only (backward compatibility)
    - Works for both showlinks and longreads
    - Graceful error handling (markdown updates succeed even if DB fails)
  - **Testing:** 11 unit tests for markdown parsing (100% pass rate)
  - **Documentation:** Detailed requirements in `.claude/requirements-sqlite-datasette.md`
  - **Next step:** Datasette configuration (metadata, canned queries) - manual setup

## [1.2.0] - 2025-12-09

### Changed
- **Merged duplicate scripts into unified `extract.py`** - Eliminated 90%+ code duplication
  - **New unified script:** `extract.py` replaces both `showlinks.py` and `longread.py`
  - **Breaking change:** Old scripts deleted; use `extract.py` instead
  - **Backward compatible output:** Print mode produces identical output to old scripts
  - **New CLI interface:**
    - `./extract.py` - Update showlinks (default behavior)
    - `./extract.py --type longreads` - Update longreads
    - `./extract.py --type all` - Update both in single run
    - `./extract.py --print` - Print showlinks to stdout (legacy pipe behavior)
    - `./extract.py --type longreads --print` - Print longreads to stdout
  - **Configuration-driven design:** Type-specific behavior defined in `CONFIGS` dict
    - Output file prefix (`all-links` vs `longreads`)
    - Header template file (`showlinks-header.md` vs `longreads-header.md`)
    - Entry type for parsing (`showlinks` vs `longreads`)
    - Format options (podcast title inclusion, year display, spacing)
  - **Shared functions:**
    - `extract_html_content()` - HTML extraction from feed entries
    - `format_entry()` - Type-agnostic entry formatting
    - `print_mode()` - Stdout output
    - `update_mode()` - File update workflow
    - `insert_entries()` - Markdown file insertion
  - **Type-specific behavior:**
    - Show links: Uses `find_links_section()`, includes podcast title, double newline spacing
    - Longreads: Uses `find_section()` with pattern, date-only header, single newline spacing
  - **Testing:** Validated output matches old scripts byte-for-byte in print mode
  - **Documentation:** Updated CHANGELOG.md and CLAUDE.md to reference `extract.py` throughout

### Removed
- **Deleted duplicate scripts:** `showlinks.py` and `longread.py`
  - Replaced by unified `extract.py` with `--type` flag
  - All functionality preserved with improved interface

## [1.1.0] - 2025-12-09

### Added
- **Automated Markdown File Updates** - Eliminated manual copy/paste workflow
  - New `--update` flag for both `showlinks.py` and `longread.py`
  - **Usage:** `./showlinks.py --update` and `./longread.py --update`
  - **What it does:**
    - Detects new episodes since last update by comparing to top date in existing file
    - Prompts user with preview of new entries before writing
    - Automatically inserts new entries in reverse chronological order
    - Maintains file structure (preserves headers, markers, manual edits)
    - Idempotent - safe to run multiple times per day
  - **New module:** `file_updater.py` with shared utilities
    - `parse_top_date()` - Extracts most recent date from markdown files
    - `find_new_entries()` - Filters feed entries to only new ones (date-only comparison, ignores timestamps)
    - `infer_year_from_context()` - Extracts year from file path (e.g., `all-links-2025.md` → 2025)
    - `group_entries_by_year()` - Groups entries by year for multi-year support
  - **Multi-year file handling:**
    - Automatically detects year boundaries (e.g., Dec 2025 → Jan 2026)
    - Creates new yearly files when needed (e.g., `all-links-2026.md`)
    - Updates multiple year files in single run
    - Proper headers for new files (Jekyll includes, deprecation notice, marker)
  - **Longreads enhancement:** Year now added to date format
    - Old format: `**Friday, December 05**`
    - New format: `**Friday, December 05 2025**`
    - Year inferred from RSS feed `published_parsed` data
    - Backward compatible - stdout mode preserves old format
  - **File markers:** Added `<!-- AUTO-GENERATED CONTENT BELOW -->` to delineate safe insertion zones
  - **Test coverage:** 16 passing unit tests in `test_file_updater.py`
    - Date parsing (showlinks with year, longreads with/without year)
    - New entry detection and filtering
    - Year inference and multi-year grouping
    - Edge cases (missing files, missing markers, malformed dates)
  - **Backward compatibility:** Original stdout behavior preserved
    - `./showlinks.py` → outputs all entries to stdout (unchanged)
    - `./longread.py` → outputs all entries to stdout without year (unchanged)

### Technical Implementation
- **Date comparison fix:** Compares dates only (ignores timestamps)
  - Problem: File stores midnight (00:00:00), feed has specific times (17:31:00)
  - Solution: Convert to `.date()` before comparison
  - Prevents false positives (same-day entries at different times)
- **Shared module pattern:** Follows existing `html_parser.py` approach
  - DRY principle - both scripts use same detection logic
  - Easier to maintain and test
  - Consistent behavior across showlinks and longreads

## [1.0.0] - 2025-12-09

### Added
- **Year Wrapped Report Generator** (`year_wrapped.py`)
  - Spotify Wrapped-style year-end statistics report for any year
  - Command-line interface: `python3 year_wrapped.py 2025` or `python3 year_wrapped.py --year 2024`
  - Supports years 2022-2025 (all available data files)
  - **Dual output format:**
    - Console output with colored ASCII report
    - Automatically generates markdown file at `docs/{year}-wrapped.md`
  - Statistics generated:
    - Episode counts and year coverage percentage (accounts for leap years)
    - Total links shared with per-episode averages
    - Top 10 sources for daily links and longreads with medal emojis (🥇🥈🥉)
    - Big tech company mention counts with ASCII bar charts
  - Tracks 10 major tech companies: Apple, Meta, Google, Netflix, OpenAI, Amazon, Anthropic, Microsoft, Tesla, Nvidia
  - Error handling for missing files and invalid years
  - Year-specific insights in markdown (e.g., "2024 saw Apple dominate headlines", "2025 was the year of AI dominance")
  - Generated all historical wrapped reports: 2022, 2023, 2024, 2025
  - Cross-year analysis: 2024 dominated by Apple (458 mentions) → 2025 shifted to OpenAI (364 mentions) showing AI narrative takeover
- New test file `test_html_parser.py` with test-driven approach for HTML content parsing
- Implemented `find_links_section()` function to extract links from HTML content
  - Handles standard pattern: "Links:" paragraph followed by `<ul>` element
  - Fallback behavior: returns first `<ul>` when no "Links:" paragraph exists (assumes it's show links)
- Comprehensive test coverage for HTML parsing edge cases:
  - Test for explicit "Links:" section extraction
  - Test for single `<ul>` fallback behavior
  - Test for multiple `<ul>` blocks (returns first `<ul>` as showlinks)
  - Test for plain text content (no HTML tags)
  - Test for timestamp pattern matching (ensures "15:35 Longreads" doesn't match)
  - Test for intro paragraph vs standalone header (ensures standalone header is matched)
  - Test for paragraphs ending with period (filters out intro paragraphs)
  - Test for structural matching (paragraph followed by `<ul>`, not just shortest text)
  - Test for multiple paragraphs with `<ul>` next sibling (chooses shortest)
  - Test for no "Links:" header but has "Weekend Longreads" header (returns first `<ul>`)
  - Test for Weekend Longreads section extraction
  - Test for Friday episodes with both regular links AND Weekend Longreads (ensures correct section is found)
- **RSS Pattern Extraction Script** (`extract_rss_patterns.py`)
  - Analyzes entire RSS archive (2,221 episodes) to identify HTML patterns
  - Categorizes episodes by content structure
  - Extracts representative samples for test fixtures
  - Generates `rss_pattern_samples.json` with real-world examples
- **Friday Longreads Analysis Script** (`extract_friday_longreads.py`)
  - Analyzes 299 Friday episodes with Weekend Longreads sections
  - Confirms pattern: Friday episodes have separate "Weekend Longreads Suggestions:" header
  - Generates `friday_longreads_samples.json` with real Friday episode examples
  - Validates that `find_section()` correctly identifies longreads section (not regular links)

### Changed
- Moved old test suite (`test_showlinks.py`, `test_fixtures.py`, `test_integration.py`) to `trash/` folder
- Restarted testing approach from scratch using strict TDD methodology

### Technical Notes
- Using BeautifulSoup with html5lib parser for HTML processing
- Properly handles NavigableString vs Tag distinction in DOM traversal
- All tests passing (12/12)
- Test coverage focuses on `<content:encoded>` HTML parsing, which is created by humans and highly inconsistent

### RSS Analysis Findings
**2,221 episodes analyzed from ridehome.rss:**
- `links_and_sponsors`: 1,011 episodes (45.5%) - most common pattern
- `no_links_at_all`: 581 episodes (26.2%) - **critical edge case**
- `links_and_longreads`: 295 episodes (13.3%)
- `links_only`: 202 episodes (9.1%)
- `single_ul_no_header`: 111 episodes (5.0%)
- `longreads_only`: 14 episodes (0.6%)
- `multiple_ul_no_header`: 7 episodes (0.3%)

**Key insight:** 26% of episodes have no structured links - primarily special episodes like "(BNS)" (Behind the News Stories) and "(Portfolio Profile)". This validates the importance of the "no links found" edge case.

### Refactoring
- Created shared `html_parser.py` module for HTML content parsing
- Generalized `find_section()` function accepts pattern parameter for flexible section finding
- Refactored `showlinks.py` to use shared HTML parser module
  - Removed duplicate HTML parsing logic
  - Simplified code from ~17 lines to ~7 lines
  - Maintained identical output behavior
- Refactored `longread.py` to use shared HTML parser module
  - Now uses `find_section(html, pattern="Weekend Longreads|Longreads Suggestions")`
  - Removed BeautifulSoup and re imports (handled by shared module)
  - Removed unused config.cfg dependency
  - Updated to use same feed URL and content extraction as showlinks.py
  - Simplified from ~15 lines to ~4 lines of parsing logic
  - **Verified working** - successfully extracts all Weekend Longreads sections
- All existing functionality preserved and tested

### Fixed
- **September 5, 2025 Episode Bug** - Timestamp pattern matching issue
  - Problem: Pattern `"Longreads|Suggestions"` incorrectly matched timestamp paragraphs like `"15:35 Longreads"`
  - This caused `longread.py` to extract the wrong section (regular links instead of Weekend Longreads)
  - Solution: Updated pattern to `"Weekend Longreads|Longreads Suggestions"` to be more specific
  - Added test case `test_timestamp_does_not_match_longreads_pattern` to prevent regression
  - Verified fix extracts correct Weekend Longreads section for September 5, 2025 episode

- **August 29, 2025 Episode Bug** - Intro paragraph pattern matching issue
  - Problem: Pattern matched intro paragraphs that mentioned "Weekend Longreads Suggestions" in text, not just standalone headers
  - Example: Intro "...And, of course, the Weekend Longreads Suggestions." was matched instead of header "Weekend Longreads Suggestions"
  - This caused `find_section()` to extract the wrong section (regular links instead of longreads)
  - Initial solution: Choose shortest matching paragraph (headers are short, intro paragraphs are long)
  - Improved solution: Use structural check - choose paragraph whose next sibling is a `<ul>` (more robust than length heuristic)
  - Added test cases: `test_intro_paragraph_does_not_match_when_standalone_header_exists` and `test_chooses_paragraph_followed_by_ul_not_just_shortest`
  - Verified fix extracts correct Weekend Longreads section for August 29, 2025 episode (2 longreads, not 5 regular links)

- **November 26, 2025 Episode Bug** - Multiple paragraphs with `<ul>` next sibling
  - Problem: Both intro paragraph and header paragraph had `<ul>` as next sibling
  - Intro "...the Weekend Longreads Suggestions." → `<ul>` with 6 regular links
  - Header "Weekend Longreads Suggestions:" → `<ul>` with 3 longreads
  - Previous structural-only check returned FIRST paragraph with `<ul>` (intro with 6 links)
  - Solution: Combine both approaches - find paragraphs with `<ul>` next sibling, then choose shortest
  - Added test case: `test_multiple_paragraphs_with_ul_chooses_shortest`
  - Verified fix extracts correct Weekend Longreads section for November 26, 2025 episode (3 longreads, not 6 regular links)

- **November 26, 2025 Showlinks Bug** - No "Links:" header regression
  - Problem: Previous fix for longreads broke showlinks for episodes without explicit "Links:" header
  - November 26 has no "Links:" paragraph, just intro followed by first `<ul>` with 6 regular links
  - Old `find_links_section()` fallback only returned `<ul>` if exactly 1 exists → returned None for multiple `<ul>`
  - This caused "No show links for this episode" message when 6 links actually existed
  - Solution: Changed fallback to return first `<ul>` when no "Links:" header (assumes it's show links)
  - Period filtering: Intro paragraphs ending with '.' are naturally filtered out by shortest-paragraph heuristic
  - Added test cases: `test_paragraph_ending_with_period_is_not_section_header`, `test_returns_first_ul_when_multiple_ul_blocks_and_no_links_paragraph`, `test_returns_first_ul_when_no_links_header_but_has_longreads_header`
  - Verified fix: November 26 now correctly shows 6 showlinks AND 3 longreads

---

**Release Highlights:** This major release represents a complete overhaul of the HTML parsing system with comprehensive test coverage, bug fixes for real-world RSS feed edge cases, and a brand new Year Wrapped report generator. The project now has proper documentation (CLAUDE.md) and follows strict TDD methodology.
