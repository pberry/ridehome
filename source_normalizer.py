"""
Source name normalization for ridehome links database.

Provides canonical source mappings and normalization functions to:
1. Standardize source name variations (e.g., "Wall Street Journal" → "WSJ")
2. Extract sources from URLs for links with NULL sources
3. Remove author attributions (e.g., "Matt Levine/Bloomberg" → "Bloomberg")

User preferences:
- Keep sections separate (Bloomberg Opinion ≠ Bloomberg)
- Prefer abbreviations (WSJ, NYTimes, FT)
- Normalize authors to publication
- Social media = platform name
"""

from urllib.parse import urlparse
import re

# Maps website domains → canonical abbreviated source names
DOMAIN_TO_SOURCE = {
    # Major tech/business news
    'www.bloomberg.com': 'Bloomberg',
    'www.nytimes.com': 'NYTimes',
    'www.wsj.com': 'WSJ',
    'www.theverge.com': 'The Verge',
    'www.wired.com': 'Wired',
    'techcrunch.com': 'TechCrunch',
    'arstechnica.com': 'Ars Technica',
    'www.ft.com': 'FT',
    'www.cnbc.com': 'CNBC',
    'www.washingtonpost.com': 'Washington Post',
    'www.theatlantic.com': 'The Atlantic',
    'www.newyorker.com': 'The New Yorker',
    'www.forbes.com': 'Forbes',
    'www.vox.com': 'Vox',
    'www.reuters.com': 'Reuters',
    'apnews.com': 'AP',
    'www.bbc.com': 'BBC',
    'www.bbc.co.uk': 'BBC',

    # Social media
    'twitter.com': 'Twitter',
    'x.com': 'Twitter',
    'www.youtube.com': 'YouTube',
    'podcasts.apple.com': 'Apple Podcasts',

    # Additional news sites
    'www.rollingstone.com': 'Rolling Stone',
    'www.fastcompany.com': 'Fast Company',
    'restofworld.org': 'Rest of World',
    'www.technologyreview.com': 'MIT Technology Review',
    'www.quantamagazine.org': 'Quanta Magazine',
    'www.vice.com': 'Vice',
    'www.theguardian.com': 'The Guardian',
    'nymag.com': 'New York Magazine',
    'www.vulture.com': 'Vulture',
    'www.gq.com': 'GQ',
    'spectrum.ieee.org': 'IEEE Spectrum',
    'www.techmeme.com': 'Techmeme',
    'variety.com': 'Variety',
    'every.to': 'Every',
    'www.theinformation.com': 'The Information',
    'www.axios.com': 'Axios',
    'www.politico.com': 'Politico',
    'qz.com': 'Quartz',
    'www.economist.com': 'The Economist',
    'www.scientificamerican.com': 'Scientific American',
    'www.nature.com': 'Nature',
    'aeon.co': 'Aeon',
    'www.eff.org': 'EFF',
    '9to5mac.com': '9to5Mac',
    '9to5google.com': '9to5Google',
    'www.theinformation.com': 'The Information',
    'stratechery.com': 'Stratechery',
    'daringfireball.net': 'Daring Fireball',
}

# Maps all variations → canonical names
SOURCE_ALIASES = {
    # WSJ variations
    'Wall Street Journal': 'WSJ',
    'The Wall Street Journal': 'WSJ',
    'The WSJ': 'WSJ',
    'Wall Street Jounal': 'WSJ',  # typo

    # NYTimes variations
    'New York Times': 'NYTimes',
    'NY Times': 'NYTimes',
    'NyTimes': 'NYTimes',

    # The Verge
    'TheVerge': 'The Verge',

    # Bloomberg variations
    'BLoomberg': 'Bloomberg',
    'Bloomberg | Quint': 'Bloomberg',

    # Bloomberg sections - keep separate but normalize variations
    'Bloomberg Business Week': 'Bloomberg Businessweek',
    'Bloomberg BusinessWeek': 'Bloomberg Businessweek',
    'BloombergBusinessweek': 'Bloomberg Businessweek',

    # NYTimes sections - keep separate
    'Dealbook/NYT': 'NYTimes DealBook',
    'NYTimes/DealBook': 'NYTimes DealBook',

    # TechCrunch
    'Tech Crunch': 'TechCrunch',

    # Ars Technica
    'ArsTechnica': 'Ars Technica',
    'ArsTechica': 'Ars Technica',  # typo

    # Financial Times
    'Financial Times': 'FT',
    'FinancialTimes': 'FT',
    'The Financial Times': 'FT',

    # LA Times
    'LATimes': 'LA Times',
    'Los Angeles Times': 'LA Times',
    'The Los Angeles Times': 'LA Times',

    # Wired
    'WIRED': 'Wired',
    'Wired UK': 'Wired',
    'WiredUK': 'Wired',

    # Washington Post
    'WaPo': 'Washington Post',

    # Other common variations
    'The Guardian': 'The Guardian',
    'Ars': 'Ars Technica',
    'Techmeme': 'Techmeme',
}


def normalize_source(source_str: str) -> str:
    """
    Normalize a source string to canonical form.

    Handles:
    - Direct alias matches (case-insensitive)
    - Author attributions (e.g., "Matt Levine/Bloomberg" → "Bloomberg")
    - Whitespace cleanup

    Args:
        source_str: Raw source string from database or RSS feed

    Returns:
        Normalized source string, or original if no normalization applies
    """
    if not source_str:
        return source_str

    # Strip whitespace
    source = source_str.strip()

    # Check for direct alias match (case-insensitive)
    for alias, canonical in SOURCE_ALIASES.items():
        if source.lower() == alias.lower():
            return canonical

    # Check for author attribution patterns: "Author/Publication" or "Publication/Author"
    # Also handle "|" and " - " as separators
    author_patterns = [
        r'^([^/]+)/([^/]+)$',      # Author/Publication or Publication/Author
        r'^([^|]+)\|([^|]+)$',     # Author|Publication or Publication|Author
        r'^([^-]+)\s*-\s*([^-]+)$' # Author - Publication or Publication - Author
    ]

    for pattern in author_patterns:
        match = re.match(pattern, source)
        if match:
            part1, part2 = match.group(1).strip(), match.group(2).strip()

            # Try both parts as potential publication names
            for part in [part1, part2]:
                # Check if this part is a known publication (case-insensitive)
                for alias, canonical in SOURCE_ALIASES.items():
                    if part.lower() == alias.lower():
                        return canonical

                # Check if it's in domain mappings
                if part in DOMAIN_TO_SOURCE.values():
                    return part

            # If no match, default to first part (likely publication)
            return part1

    # No normalization needed
    return source


def extract_source_from_url(url: str) -> str | None:
    """
    Extract canonical source name from URL domain.

    Args:
        url: Full URL string

    Returns:
        Canonical source name, or None if domain not recognized
    """
    if not url:
        return None

    try:
        parsed = urlparse(url)
        domain = parsed.netloc

        if not domain:
            return None

        # Normalize domain (lowercase)
        domain = domain.lower()

        # Direct lookup
        if domain in DOMAIN_TO_SOURCE:
            return DOMAIN_TO_SOURCE[domain]

        # Try without www prefix
        if domain.startswith('www.'):
            domain_no_www = domain[4:]
            if domain_no_www in DOMAIN_TO_SOURCE:
                return DOMAIN_TO_SOURCE[domain_no_www]

        # Try with www prefix
        domain_with_www = f'www.{domain}'
        if domain_with_www in DOMAIN_TO_SOURCE:
            return DOMAIN_TO_SOURCE[domain_with_www]

        return None

    except Exception:
        # Malformed URL, return None
        return None
