# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added
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

### In Progress
- Additional test coverage for edge cases (Sponsors section, more real-world samples)
- Integration tests for complete end-to-end workflow
