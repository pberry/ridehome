# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based RSS feed parser that extracts links from "The Ride Home" podcast feed and generates static markdown pages for a GitHub Pages site. The project parses inconsistent HTML content from RSS feeds and categorizes links into two types: daily show links and Friday "Weekend Longreads" suggestions.

**Status:** No longer actively updated. The podcast now has its own official website and RSS feed.

## Key Commands

### Environment Setup
```bash
# Activate virtual environment
source env/bin/activate

# Install dependencies (if needed)
pip install feedparser html2text beautifulsoup4 html5lib
```

### Running Scripts
```bash
# Extract show links for all episodes
./showlinks.py > docs/all-links-2025.md

# Extract Friday longreads
./longread.py > docs/longreads-2025.md

# Generate year-end Wrapped report (Spotify Wrapped style)
python3 year_wrapped.py 2025          # For 2025
python3 year_wrapped.py --year 2024   # For 2024
python3 year_wrapped.py 2023          # For any year with data
```

### Testing
```bash
# Run all tests
python3 test_html_parser.py

# Run specific test class
python3 test_html_parser.py TestLinksExtraction

# Run single test
python3 test_html_parser.py TestLinksExtraction.test_extracts_ul_after_links_paragraph
```

## Architecture

### Core Flow: RSS → HTML Parser → Markdown Output

1. **Feed Parsing** (`showlinks.py`, `longread.py`)
   - Fetches RSS from `https://feeds.megaphone.fm/ridehome`
   - Extracts HTML from `<content:encoded>` field (preferred) or falls back to `<summary>`
   - HTML content is **created by humans** and **highly inconsistent** across 2,221 episodes

2. **HTML Content Parsing** (`html_parser.py`)
   - **Shared module** used by both showlinks and longreads extractors
   - `find_section(html, pattern)`: Generalized section finder using regex pattern
   - `find_links_section(html)`: Specialized for show links with fallback behavior
   - Uses BeautifulSoup with html5lib parser for robustness

3. **Output Generation**
   - Converts extracted `<ul>` elements to markdown using html2text
   - Prepends headers from `docs/_includes/` directory
   - Outputs to `docs/` for GitHub Pages deployment

### Critical Parsing Logic

**The HTML parsing handles extreme variability:**
- 45% of episodes follow standard pattern: "Links:" header + `<ul>` list
- 26% have NO links at all (special episodes like "(BNS)" Behind the News Stories)
- 13% have both show links AND longreads sections
- 5% have `<ul>` lists with no explicit "Links:" header

**Pattern Matching Complexity:**
- Must distinguish between section **headers** (e.g., "Weekend Longreads:") vs **intro paragraphs** that mention longreads
- Must avoid matching timestamps (e.g., "15:35 Longreads")
- When multiple paragraphs match the pattern AND have `<ul>` next sibling, choose the shortest (headers are short, intros are long)
- Must handle structural variations: `<p>` → `<ul>` vs `<p>` → whitespace → `<ul>` (NavigableString handling)

**Two-Step Structural Check:**
1. Find all paragraphs matching the pattern regex
2. Filter to only paragraphs whose **next sibling** is a `<ul>` tag (skipping whitespace NavigableStrings)
3. Among candidates, choose **shortest paragraph** (distinguishes headers from intro paragraphs)

**Fallback Behavior for Show Links:**
- If no "Links:" header found, return **first `<ul>`** in the HTML (assumes it's show links)
- This handles episodes where the host forgot to add explicit "Links:" header

### Test-Driven Development Approach

**Test file:** `test_html_parser.py` - Comprehensive test suite based on real-world RSS feed bugs

**Key test categories:**
- Standard cases (explicit headers with `<ul>` lists)
- Edge cases (plain text content, no HTML tags)
- Structural ambiguity (multiple `<ul>` blocks, which is correct?)
- Pattern matching bugs (timestamps, intro paragraphs, period-ending sentences)

**Real bugs captured in tests:**
- September 5, 2025: Timestamp "15:35 Longreads" matched instead of "Weekend Longreads"
- August 29, 2025: Intro paragraph matched instead of standalone header
- November 26, 2025: Multiple paragraphs with `<ul>` next sibling (intro vs header)
- November 26, 2025: No "Links:" header broke showlinks extraction

## Working with HTML Parser

**When modifying `html_parser.py`:**
1. Check if there's already a test case for your scenario in `test_html_parser.py`
2. If not, add a test case FIRST (TDD approach)
3. Run tests after ANY changes: `python3 test_html_parser.py`
4. Verify against real RSS feed data: `python3 showlinks.py | head -50`

**Common pitfalls:**
- BeautifulSoup's `.next_sibling` can return `NavigableString` (whitespace) - must skip to find actual `Tag`
- Pattern matching can be too greedy (e.g., matching timestamps or intro text)
- Shortest-paragraph heuristic fails when intro has `<ul>` next sibling too → need structural check FIRST

## RSS Feed Analysis

**Feed statistics (2,221 episodes analyzed):**
- `links_and_sponsors`: 1,011 episodes (45.5%)
- `no_links_at_all`: 581 episodes (26.2%) - critical edge case
- `links_and_longreads`: 295 episodes (13.3%)
- `links_only`: 202 episodes (9.1%)
- `single_ul_no_header`: 111 episodes (5.0%)
- `longreads_only`: 14 episodes (0.6%)
- `multiple_ul_no_header`: 7 episodes (0.3%)

**Friday longreads pattern:** 299 Friday episodes have separate "Weekend Longreads Suggestions:" section that appears AFTER regular show links.

## Output Files

**Generated markdown files:**
- `docs/all-links-YYYY.md` - Show links by year
- `docs/longreads-YYYY.md` - Friday longreads by year
- Format: Date header + bulleted list of links converted from HTML

**Headers:**
- `docs/_includes/showlinks-header.md` - Prepended to show links output
- `docs/_includes/longreads-header.md` - Prepended to longreads output

## Development Workflow

**Making changes to parsing logic:**
1. Read CHANGELOG.md to understand bug history
2. Run existing tests: `python3 test_html_parser.py`
3. Add new test case if needed
4. Modify code
5. Run tests again
6. Verify against real RSS data
7. Update CHANGELOG.md with fix details

**Historical context:**
- Original test suite was scrapped and restarted from scratch using strict TDD
- Old tests are in `trash/` directory
- Current test suite is based on real RSS feed bugs, not hypothetical scenarios
