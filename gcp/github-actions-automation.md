# GitHub Actions Automation Investigation

**Date**: 2025-12-19
**Goal**: Automate RSS feed extraction and markdown generation using GitHub Actions

---

## Executive Summary

**Feasibility**: HIGH ✓

GitHub Actions automation is highly feasible with minor modifications to `extract.py`. The database should remain gitignored and excluded from automation using the existing `--skip-db` flag.

**Effort**: ~2 hours
**Key Blocker**: User approval prompts need bypass flag

---

## Current State Analysis

### Manual Workflow

1. Run `extract.py --type all` locally
2. Run `year_wrapped.py <year>` locally (as needed)
3. Commit modified markdown files in `docs/`
4. Push to GitHub → Jekyll builds Pages from `main` branch

### Key Components

- **RSS Feed**: `https://feeds.megaphone.fm/ridehome`
- **Python Dependencies**: feedparser, html2text, beautifulsoup4, html5lib
- **Database**: SQLite (`ridehome.db`) - currently gitignored, 3.3 MB
- **Outputs**: Markdown files in `docs/` directory
- **Deployment**: GitHub Pages via Jekyll (`.github/workflows/jekyll-gh-pages.yml`)

---

## Feasibility Assessment: HIGH ✓

GitHub Actions automation is highly feasible with some modifications needed.

---

## Required Changes

### 1. User Approval Bypass (BLOCKER)

**Issue**: `extract.py` lines 258 & 265 prompt for `[y/N]` approval:
```python
response = input(f"\nAdd them to {file_path}? [y/N] ").strip().lower()
```

**Solutions**:
- **Option A**: Add `--yes` flag to skip prompts in automation
- **Option B**: Use environment variable `CI=true` to auto-approve
- **Option C**: Modify `update_mode()` to accept `auto_approve` parameter

**Recommendation**: Add `--yes` flag for explicit automation control.

---

### 2. Requirements File (REQUIRED)

**Issue**: No `requirements.txt` exists for dependency installation.

**Solution**: Create `requirements.txt`:
```
feedparser==6.0.11
html2text==2024.2.26
beautifulsoup4==4.12.3
html5lib==1.1
```

---

### 3. Database Handling (DESIGN DECISION)

**Current**: Database is gitignored (not persisted between runs).

**Options**:

#### A. Use `--skip-db` flag (RECOMMENDED)
- Simplest approach
- Markdown files are source of truth
- Database becomes local-only optimization
- Command: `./extract.py --type all --skip-db --yes`

#### B. Commit database to git
- Remove `ridehome.db` from `.gitignore`
- Action commits both .md and .db files
- Increases repo size (~3.4 MB currently, grows ~100-200 MB/year)

#### C. GitHub Actions Artifacts
- Store database as workflow artifact
- Restore before each run
- Complex, requires artifact management

**Recommendation**: Use Option A (`--skip-db`) unless database queries are needed in Pages site.

---

## Proposed Workflow Design

### Schedule

**Weekdays at 6 AM PT** (after podcast typically publishes)

```yaml
name: Update Ride Home Links
on:
  schedule:
    - cron: '0 14 * * 1-5'  # 6 AM PT weekdays (14:00 UTC)
  workflow_dispatch:  # Manual trigger option

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run extraction
        run: ./extract.py --type all --skip-db --yes

      - name: Run tests
        run: python3 test_html_parser.py

      - name: Commit changes
        uses: stefanzweifel/git-auto-commit-action@v5
        with:
          commit_message: "Daily update: automated link extraction"
          file_pattern: "docs/*.md"
```

### Year Wrapped

Separate workflow, manual trigger only (or yearly schedule on Dec 31).

---

## Key Concerns & Mitigation

### 1. RSS Feed Availability
- **Risk**: External feed could be down
- **Mitigation**: Add retry logic, continue-on-error, alert on persistent failures

### 2. Empty Runs
- **Risk**: Action runs but no new episodes
- **Mitigation**: Check for changes before committing (git-auto-commit handles this)

### 3. Git Conflicts
- **Risk**: Local changes conflict with automated commits
- **Mitigation**: Work in `main` branch only for automation, avoid manual runs on publish days

### 4. GitHub Actions Quotas
- **Usage**: ~5 runs/week × 2-3 minutes = minimal usage
- **Risk**: Low - well within free tier limits (2,000 minutes/month)

### 5. Testing Before Commit
- **Risk**: Broken updates get committed
- **Mitigation**: Run `python3 test_html_parser.py` before committing

---

## Implementation Complexity

### Effort Estimate

- Add `--yes` flag to extract.py: **30 minutes**
- Create requirements.txt: **5 minutes**
- Write GitHub Actions workflow: **20 minutes**
- Test & debug: **30-60 minutes**

**Total**: ~2 hours

---

## Database in Git: Trade-off Analysis

### Database Characteristics

**Current State**:
- **Size**: 3.3 MB (currently gitignored, never committed)
- **Records**: 6,827 links (6,178 showlinks + 649 longreads)
- **Time Span**: 4 years (Jan 2022 - Dec 2025)
- **Episodes**: 971 unique days

**Growth Rate**:
- **Per link**: ~500 bytes
- **Daily**: ~2.5 KB (assuming 5 links/episode)
- **Monthly**: ~50 KB
- **Yearly**: ~600-850 KB
- **5-year projection**: 3.3 MB → ~7 MB (database itself)

---

### POSITIVE Consequences

#### 1. Persistent State Across GitHub Actions Runs ✓
- Database grows continuously without manual intervention
- Duplicate prevention works correctly (unique index on url+date)
- No risk of data loss between runs

#### 2. Version Control as Backup ✓
- Full disaster recovery capability
- Can rollback to any historical state
- Implicit backup with every commit

#### 3. Enables Advanced Analytics ✓✓

The database structure supports queries markdown cannot:

```sql
-- Top sources by month
SELECT source, COUNT(*)
FROM links
WHERE date >= '2025-12-01'
GROUP BY source;

-- Link frequency trends over time
SELECT strftime('%Y-%m', date) as month, COUNT(*)
FROM links
GROUP BY month;

-- Most linked domains
SELECT substr(url, instr(url, '://') + 3,
              instr(substr(url, instr(url, '://') + 3), '/') - 1) as domain,
       COUNT(*) as count
FROM links
GROUP BY domain
ORDER BY count DESC;
```

**Could power GitHub Pages features like**:
- Monthly "Top Sources" widget
- Historical trend charts
- Search by source/domain
- Link recommendation engine

#### 4. Data Redundancy / Validation ✓
- Database becomes source of truth
- Can regenerate markdown files from database if needed
- Validates markdown parsing accuracy

#### 5. Offline Development ✓
- Clone repo = get full dataset
- No need to re-scrape RSS feed for local dev

---

### NEGATIVE Consequences

#### 1. Binary File in Git (SIGNIFICANT) ⚠️
- **Poor diff performance**: Git stores full copy each commit
- **Inefficient storage**: 3.3 MB × N commits = bloat
- **No meaningful diffs**: Can't see "what changed" in DB
- **Anti-pattern**: Git designed for text, not binary

**Impact**: Every commit that changes DB adds ~3.3 MB to repo history (compressed somewhat, but still substantial).

#### 2. Repository Growth ⚠️

**Projection assuming daily commits (weekdays only)**:
```
Year 1: 3.3 MB + (250 commits × 3.3 MB compressed ~30%) = ~250 MB
Year 5: ~1.2 GB repo size
```

**Reality check**: Git's delta compression helps, but binary files compress poorly. Estimate **~100-200 MB/year growth**.

**Consequences**:
- Slower `git clone` for new contributors
- Longer CI checkout times
- GitHub repo size warnings (1 GB soft limit)

#### 3. Merge Conflicts ⚠️

If multiple sources update database:
- Manual local runs while Actions is running
- Multiple branches both modifying DB
- SQLite binary conflicts are **unresolvable** without choosing one version

**Mitigation**: Only update from one source (Actions OR manual, not both).

#### 4. Database-Markdown Sync Risk ⚠️

Two sources of truth creates risk:
- Database could diverge from markdown
- Manual edits to markdown won't update DB
- Which is canonical?

**Mitigation**: Make database source of truth, generate markdown from DB.

#### 5. Not Idiomatic ⚠️

Database in git is uncommon practice. Most developers expect:
- Database = runtime state
- Git = source code
- Violates "boring technology" principle

---

### Alternative: Git LFS (Large File Storage)

GitHub's LFS could mitigate some issues:

**Pros**:
- Designed for binary files
- Stores only deltas
- Keeps main repo light
- ~$5/month for 50 GB storage

**Cons**:
- Added complexity
- Monthly cost
- Still grows over time
- Requires LFS setup on all clones

---

### Data-Driven Recommendation

#### Recommendation: Keep Database OUT of Git (Current state)

**Rationale**:
1. **Markdown is sufficient source of truth** for current use case
2. **Growth rate is acceptable** (850 KB/year), but multiplied by commits becomes problematic
3. **No current analytics features** that require database queries
4. **Markdown files already committed** - provide full history
5. **Binary DB = anti-pattern** in git

#### When to Reconsider

**Commit database to git IF**:
- You plan to add database-powered features to GitHub Pages (search, trends, recommendations)
- You want to query historical data via SQL (not just display links)
- The markdown files become insufficient for your use case
- You're willing to accept ~100-200 MB/year repo growth

**Alternative architectures if analytics needed**:
- **Separate data repo**: Keep ridehome.db in dedicated `ridehome-data` repo
- **External database**: PostgreSQL/MySQL on external host, Actions connects to it
- **Static JSON**: Export database to `data.json`, commit that (text-based, better diffs)
- **Read-only replica**: Actions generates database, uploads as artifact/release asset (not committed)

---

### Summary Table

| Factor | Keep DB Out (Current) | Commit DB to Git |
|--------|----------------------|------------------|
| **Repo size growth** | ✓ None | ✗ ~100-200 MB/year |
| **Git performance** | ✓ Fast | ⚠️ Slower over time |
| **Data persistence in Actions** | ⚠️ Use --skip-db | ✓ Full persistence |
| **Advanced analytics** | ✗ Not possible | ✓ SQL queries enabled |
| **Merge conflicts** | ✓ None | ⚠️ High risk |
| **Idiomatic practice** | ✓ Standard | ⚠️ Anti-pattern |
| **Backup/recovery** | ⚠️ Markdown only | ✓ Full DB history |
| **Simplicity** | ✓ Simple | ⚠️ Complex |

**Final Answer**: For automated Actions workflow, **use `--skip-db` flag**. Database remains local development tool only. If you later want database-powered features on the site, revisit with alternative architecture (separate data repo or static JSON export).

---

## Recommended Next Steps

1. **Create requirements.txt** with exact dependency versions
2. **Add `--yes` flag to extract.py** to bypass approval prompts
3. **Create `.github/workflows/update-links.yml`** with schedule trigger
4. **Test manually** with `workflow_dispatch` before enabling schedule
5. **Monitor first week** to ensure reliability
6. **Optional**: Add Slack/email notifications on failure

---

## Questions to Resolve

1. Should the Action run automatically on schedule or only on manual trigger initially?
2. Do you want email notifications on workflow failures?
3. Should `year_wrapped.py` also be automated (yearly? manually triggered only)?
4. Should tests block the commit if they fail, or just warn?

---

## Appendix: Database Schema

```sql
CREATE TABLE links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    date_unix INTEGER NOT NULL,
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    source TEXT,
    link_type TEXT NOT NULL CHECK(link_type IN ('showlink', 'longread')),
    episode_date TEXT NOT NULL,
    episode_date_unix INTEGER NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_date ON links(date);
CREATE INDEX idx_date_unix ON links(date_unix);
CREATE INDEX idx_link_type ON links(link_type);
CREATE INDEX idx_source ON links(source);
CREATE UNIQUE INDEX idx_url_date ON links(url, date);
```

**Current Stats** (as of 2025-12-19):
- Total links: 6,827
- Showlinks: 6,178
- Longreads: 649
- Date range: 2022-01-03 to 2025-12-18
- Unique episodes: 971 days
