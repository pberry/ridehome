# ridehome

RSS feed parser for [The Ride Home](https://www.ridehome.info/podcast/techmeme-ride-home/) podcast.

Extracts daily show links and Friday longreads from the podcast RSS feed, generating static markdown pages and providing analytics capabilities.

**Live site**: [pberry.github.io/ridehome](https://pberry.github.io/ridehome/)

---

## Features

- **RSS Parsing**: Extracts links from podcast feed HTML content
- **Dual Content Types**: Show links (daily) + Weekend longreads (Fridays)
- **Robust HTML Parsing**: Handles 2,221+ episodes with inconsistent formatting
- **Analytics Database**: SQLite schema with 6,800+ links
- **Static Site Generation**: Markdown output for GitHub Pages
- **Year Wrapped Reports**: Spotify-style yearly summaries

---

## Quick Start

```bash
# Install dependencies
python3 -m venv env
source env/bin/activate
pip install feedparser html2text beautifulsoup4 html5lib

# Extract links
./extract.py --type all

# View output
ls docs/
```

---

## Deployment Options

### Local (Default)
Run manually on your machine.

```bash
./extract.py --type all
```

**Cost**: $0 | **Setup**: 5 minutes

---

### GitHub Actions (Automated)
Scheduled daily runs via GitHub Actions.

See [gcp/github-actions-automation.md](./gcp/github-actions-automation.md) for setup.

**Cost**: $0 (free tier) | **Setup**: ~2 hours

---

### Google Cloud Platform (Serverless)
Fully automated cloud deployment with BigQuery analytics and AI-powered natural language queries.

**Architecture**: Cloud Run + BigQuery + Gemini API

See **[gcp/](./gcp/)** directory for complete implementation guide.

**Cost**: ~$1.35/month | **Setup**: ~10 hours (educational)

**What you get**:
- Automatic daily updates
- BigQuery data warehouse
- Natural language queries (powered by Gemini)
- Static site hosting with CDN
- Analytics dashboard capabilities

---

## Project Structure

**Core Components** (platform-agnostic):
```
extract.py              # RSS parser and link extractor
html_parser.py          # HTML parsing logic
db_schema.py            # SQLite schema
db_writer.py            # Database writer
file_updater.py         # Markdown file updater
year_wrapped.py         # Yearly summary generator
```

**Deployment-Specific**:
```
gcp/                    # Google Cloud Platform deployment
docs/                   # GitHub Pages site output
test_*.py               # Test suites
```

---

## Testing

```bash
# Run all tests
python3 test_html_parser.py
python3 test_file_updater.py
python3 test_markdown_parser.py
```

Tests are based on real RSS feed edge cases and parsing bugs discovered over 4 years.

---

## Documentation

- **[CLAUDE.md](./CLAUDE.md)** - Project context and architecture
- **[CHANGELOG.md](./CHANGELOG.md)** - Version history
- **[gcp/](./gcp/)** - Cloud deployment guides

---

## Data

**Current Stats** (as of Dec 2025):
- **6,827 links** extracted (6,184 showlinks + 643 longreads)
- **971 episodes** parsed (Jan 2022 - Dec 2025)
- **450 unique sources** identified
- **4 years** of data

---

## Contributing

This is a personal learning project, but contributions are welcome!

**Areas for contribution**:
- Additional cloud deployments (AWS, Azure)
- Enhanced analytics queries
- UI improvements for GitHub Pages site
- Parser improvements for edge cases

---

## License

MIT (see LICENSE file)

