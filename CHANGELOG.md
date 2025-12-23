# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

## [1.3.1] - 2025-12-23

### Added
- **Dynamic status section on homepage** - Auto-updating archive statistics and trends
  - **Real-time metrics:** Shows last update time, total archived links (showlinks + longreads)
  - **Top sources:** Displays 3 most-linked sources from last 6 months (Bloomberg, The Verge, WSJ)
  - **Trending topics:** Shows 3 most common topics from last 6 months using keyword categorization
    - 11 topic categories: AI/ML, Crypto, Gaming, Hardware/Chips, Security, Regulation, etc.
    - Keyword-based classification with word boundary matching for accuracy
  - **Automatic updates:** Status regenerates after every `extract.py` run
  - **Implementation:**
    - `status_generator.py` - Database queries, topic categorization, HTML generation
    - `test_status_generator.py` - 17 comprehensive tests (all passing)
    - Integration in `extract.py` to update homepage after successful runs
  - **Visual design:** 3-column responsive grid with cards matching Solarized theme

- **Redesigned homepage navigation** - Modern 3-column grid layout replacing bullet lists
  - **Recent Content section:** 3 featured cards for 2025 show links, longreads, and wrapped
    - Large clickable cards with titles and descriptions
    - Hover effects: 4px lift, animated arrow (→), blue border highlight
    - Full-width cards provide clear call-to-action
  - **Archive section:** Organized 3-column layout (Show Links | Longreads | Wrapped)
    - Consolidated from 2 separate sections (Older Stuff + Wrapped Archive)
    - Year-based lists (2024-2018) in compact columns
    - Cyan headings for visual distinction from Recent Content
    - Subtle hover effects: background highlight + left indent
  - **Responsive design:**
    - Desktop: 3 columns side-by-side
    - Tablet: Stacks to single column
    - Mobile: Optimized padding and font sizes

### Changed
- **Homepage structure:** Semantic HTML with proper `<nav>` elements and ARIA labels
  - `<section class="status-section" aria-labelledby="status-heading">`
  - `<nav class="recent-nav" aria-labelledby="recent-heading">`
  - `<nav class="archive-nav" aria-labelledby="archive-heading">`
  - Maintains WCAG AA accessibility with keyboard navigation and screen reader support

### Technical
- **CSS additions:** 375+ lines of responsive grid styles in `docs/assets/main.scss`
  - Status section: 3-column cards with hover effects and numbered lists
  - Recent nav: Featured cards with animations and pseudo-element arrows
  - Archive nav: 3-column list layout with background hover states
  - Full responsive breakpoints for tablet (768px) and mobile (480px)

### Fixed
- **WCAG 2.1 Level AA compliance achieved** - Critical accessibility improvements
  - **Color contrast fixes:** All text and links now meet WCAG AA requirements (4.5:1+ ratio)
    - Light theme body text: #556873 (5.0:1, was 4.13:1)
    - Light theme links: #1c6fa0 (4.8:1, was 3.41:1)
    - Light theme visited links: #5858a8 (4.6:1, was 4.06:1)
    - Dark theme links: #3ca0e6 (4.9:1, was 4.08:1)
    - Dark theme visited links: #8989d8 (4.6:1, was 3.43:1)
    - Focus indicators: High contrast colors for both themes (4.8:1+)
  - **Empty heading fix:** Added page titles to content pages to eliminate empty `<h1>` tags
    - Example: `all-links-2025.md` now has `title: Show Links 2025`
  - **Skip navigation link:** Added keyboard-accessible skip link for screen reader users
    - Appears on focus, jumps directly to main content
    - Hidden until focused (WCAG 2.4.1 compliance)
  - **Navigation landmarks:** Wrapped navigation lists in semantic `<nav>` elements with ARIA labels
    - Homepage now has three distinct nav regions: "Recent content", "Archive", "Wrapped reports"
  - **Improved ARIA states:** Theme toggle button now announces current state to screen readers
    - Added `aria-pressed` attribute to indicate dark mode on/off state
    - Dynamic label updates: "Switch to dark mode" / "Switch to light mode"

### Documentation
- **Accessibility audit report:** Added comprehensive `ACCESSIBILITY_AUDIT.md`
  - WCAG 2.1 Level AA compliance checklist
  - Color contrast calculations for all color combinations
  - Before/after contrast ratios with specific recommendations
  - Keyboard navigation testing results
  - Screen reader compatibility notes

## [1.3.0] - 2024-12-23

### Added
- **Dark mode theme toggle** - Solarized Dark theme with persistent user preference
  - **Theme switcher button:** Toggle button in top-right of header (☀️/🌙 icons)
  - **CSS custom properties:** Complete theme system using CSS variables for runtime theme switching
  - **Solarized Dark palette:** Authentic dark theme with inverted Solarized colors
    - Background: Deep blue-black (#002b36)
    - Secondary background: Dark blue-gray (#073642)
    - Text: Light gray-blue (#839496)
    - Links: Same blue/cyan/violet accent colors (optimized for both themes)
  - **Smooth transitions:** 0.3s color transitions for seamless theme switching
  - **Persistent preference:** Uses localStorage to remember user's theme choice across sessions
  - **Accessibility:** Proper ARIA labels, keyboard focus states, respects user preferences
  - **Implementation files:**
    - `docs/assets/main.scss` - Theme variables and complete stylesheet (replaces style.scss)
    - `docs/assets/js/theme-toggle.js` - Vanilla JS theme switcher with no dependencies
    - `docs/_includes/header.html` - Updated header with toggle button
  - **No flash of unstyled content:** Theme applied immediately on page load before render

- **Solarized Light theme for GitHub Pages** - Custom visual design replacing default Jekyll styling
  - **Base theme:** minima (clean, technical foundation)
  - **Color scheme:** Solarized Light palette for readability and technical aesthetic
    - Background: Warm off-white (#fdf6e3)
    - Text: Muted gray-blue (#657b83)
    - Links: Blue (#268bd2) with distinct visited state (violet #6c71c4)
    - Accent colors: Full Solarized palette for code, tables, emphasis
  - **Typography:** System font stack for performance, generous line-height (1.6-1.8) for readability
  - **Link-focused design:** Clear visual hierarchy, underlines with transparency, hover states
  - **Table styling:** Clean borders and alternating rows for Wrapped stats pages
  - **Configuration:**
    - `docs/_config.yml` - Jekyll theme configuration
    - `docs/assets/css/style.scss` - Complete Solarized Light stylesheet
    - `docs/Gemfile` - Local development dependencies
  - **Benefits:** Distinctive identity, improved readability, maintains focus on links content
  - **No animations or images** - Clean, technical presentation

## [1.2.1] - 2025-12-21

### Changed
- **Standardized date format in longreads files** - All 8 longreads-*.md files (2018-2025) now use consistent date format
  - **New format:** `**Friday, December 28 2018 - Fri. 12/28**` (matches all-links files)
  - **Previous formats were inconsistent:**
    - 2018-2021: `**Friday, December 28**` (missing year and abbreviated suffix)
    - 2022-2025: `## December 22, 2022` (heading format, missing day of week)
  - **Updated:** 393 dates across 8 files using automated Python script (`update_longreads_dates.py`)
  - **Benefits:** Improved consistency across all documentation, easier date parsing
- **Normalized bullet format in longreads files** - Fixed database parsing compatibility
  - **Previous issue:** 2022-2025 longreads used dash bullets (`-`) while 2018-2021 used asterisks (`*`)
  - **Fix:** Converted 649 dash bullets to asterisks for consistency
  - **Impact:** `markdown_parser.py` now successfully parses ALL longreads files
    - Before: 781 links parseable (2018-2021 only)
    - After: 1,430 links parseable (2018-2025 complete)
  - **Script:** `normalize_longreads_bullets.py`
- **Deprecated master archive file** - Eliminated redundant all-links.md
  - **Previous:** Master archive (all-links.md) contained 2018-2021 data + yearly files for 2022-2025
  - **Now:** All data in yearly files (all-links-2018.md through all-links-2025.md)
  - **Moved:** all-links.md → trash/ (archived)
  - **Updated:** load_db.py now loads only yearly files
  - **Benefits:** No duplicate processing, cleaner import (8 files vs 9), same total data (12,058 showlinks)

### Added
- **SQLite Database + Datasette Support** - Complete dual-output system (markdown + database)
  - **One-time import:** `load_db.py` script imports existing markdown into SQLite
    - 12,058 showlinks imported from all-links-*.md files (2018-2025)
    - 1,736 longreads imported from longreads-*.md files (2018-2025)
    - Total: 13,794 links in database
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
