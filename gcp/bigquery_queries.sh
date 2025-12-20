#!/bin/bash
#
# BigQuery Sample Queries for The Ride Home Dataset
# Interactive script to explore the ridehome.links table
#
# Usage: ./bigquery_queries.sh [query_number]
#        ./bigquery_queries.sh           (shows menu)
#        ./bigquery_queries.sh 1         (runs query #1)
#

set -e

# Colors for output
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

function print_header() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

function run_query() {
    local query_num=$1
    local query=$2
    local description=$3

    print_header "Query #$query_num: $description"
    echo ""

    bq query --use_legacy_sql=false "$query"

    echo ""
}

# Query 1: Top 10 Sources All-Time
function query_top_sources() {
    run_query 1 "
SELECT source, COUNT(*) as link_count
FROM \`ridehome.links\`
WHERE source IS NOT NULL
GROUP BY source
ORDER BY link_count DESC
LIMIT 10
" "Top 10 Sources All-Time"
}

# Query 2: Links Per Year Trend
function query_yearly_trend() {
    run_query 2 "
SELECT
  EXTRACT(YEAR FROM date) as year,
  COUNT(*) as total_links,
  COUNT(DISTINCT source) as unique_sources,
  COUNTIF(link_type = 'showlink') as showlinks,
  COUNTIF(link_type = 'longread') as longreads
FROM \`ridehome.links\`
GROUP BY year
ORDER BY year
" "Links Per Year Trend"
}

# Query 3: Big Tech Company Mentions
function query_big_tech() {
    run_query 3 "
SELECT
  CASE
    WHEN LOWER(title) LIKE '%openai%' THEN 'OpenAI'
    WHEN LOWER(title) LIKE '%google%' THEN 'Google'
    WHEN LOWER(title) LIKE '%meta%' OR LOWER(title) LIKE '%facebook%' THEN 'Meta/Facebook'
    WHEN LOWER(title) LIKE '%apple%' THEN 'Apple'
    WHEN LOWER(title) LIKE '%amazon%' THEN 'Amazon'
    WHEN LOWER(title) LIKE '%microsoft%' THEN 'Microsoft'
    WHEN LOWER(title) LIKE '%tesla%' THEN 'Tesla'
    WHEN LOWER(title) LIKE '%nvidia%' THEN 'Nvidia'
  END as company,
  COUNT(*) as mentions
FROM \`ridehome.links\`
WHERE LOWER(title) LIKE '%openai%'
   OR LOWER(title) LIKE '%google%'
   OR LOWER(title) LIKE '%meta%'
   OR LOWER(title) LIKE '%facebook%'
   OR LOWER(title) LIKE '%apple%'
   OR LOWER(title) LIKE '%amazon%'
   OR LOWER(title) LIKE '%microsoft%'
   OR LOWER(title) LIKE '%tesla%'
   OR LOWER(title) LIKE '%nvidia%'
GROUP BY company
ORDER BY mentions DESC
" "Big Tech Company Mentions in Titles"
}

# Query 4: Busiest Days
function query_busiest_days() {
    run_query 4 "
SELECT
  date,
  COUNT(*) as link_count,
  STRING_AGG(DISTINCT source, ', ' ORDER BY source LIMIT 5) as top_sources
FROM \`ridehome.links\`
GROUP BY date
ORDER BY link_count DESC
LIMIT 10
" "Busiest Days (Most Links Shared)"
}

# Query 5: Source Diversity by Year
function query_source_diversity() {
    run_query 5 "
SELECT
  EXTRACT(YEAR FROM date) as year,
  COUNT(DISTINCT source) as unique_sources,
  COUNT(*) as total_links,
  ROUND(COUNT(DISTINCT source) / COUNT(*) * 100, 2) as diversity_ratio
FROM \`ridehome.links\`
WHERE source IS NOT NULL
GROUP BY year
ORDER BY year
" "Source Diversity by Year"
}

# Query 6: Monthly Longreads (2022+)
function query_monthly_longreads() {
    run_query 6 "
SELECT
  FORMAT_DATE('%Y-%m', date) as month,
  COUNT(*) as longread_count
FROM \`ridehome.links\`
WHERE link_type = 'longread'
GROUP BY month
ORDER BY month DESC
LIMIT 20
" "Monthly Longreads Count (Recent 20 Months)"
}

# Query 7: Search for Specific Topic
function query_search_topic() {
    if [ -z "$1" ]; then
        echo -e "${YELLOW}Usage: $0 7 <search_term>${NC}"
        echo "Example: $0 7 chatgpt"
        exit 1
    fi

    local search_term=$1

    run_query 7 "
SELECT
  date,
  title,
  source,
  url
FROM \`ridehome.links\`
WHERE LOWER(title) LIKE '%${search_term}%'
   OR LOWER(url) LIKE '%${search_term}%'
ORDER BY date ASC
LIMIT 20
" "Search for '$search_term' (First 20 Mentions)"
}

# Query 8: Day of Week Analysis
function query_day_of_week() {
    run_query 8 "
SELECT
  FORMAT_DATE('%A', date) as day_of_week,
  COUNT(*) as total_links,
  ROUND(AVG(links_per_day), 2) as avg_links_per_episode
FROM (
  SELECT
    date,
    FORMAT_DATE('%A', date) as dow,
    COUNT(*) as links_per_day
  FROM \`ridehome.links\`
  GROUP BY date
)
GROUP BY day_of_week
ORDER BY
  CASE day_of_week
    WHEN 'Monday' THEN 1
    WHEN 'Tuesday' THEN 2
    WHEN 'Wednesday' THEN 3
    WHEN 'Thursday' THEN 4
    WHEN 'Friday' THEN 5
    WHEN 'Saturday' THEN 6
    WHEN 'Sunday' THEN 7
  END
" "Links by Day of Week"
}

# Query 9: AI/ML Topic Trend
function query_ai_trend() {
    run_query 9 "
SELECT
  EXTRACT(YEAR FROM date) as year,
  COUNTIF(LOWER(title) LIKE '%ai %' OR LOWER(title) LIKE '% ai%') as ai_mentions,
  COUNTIF(LOWER(title) LIKE '%chatgpt%') as chatgpt_mentions,
  COUNTIF(LOWER(title) LIKE '%openai%') as openai_mentions,
  COUNTIF(LOWER(title) LIKE '%machine learning%' OR LOWER(title) LIKE '%ml %') as ml_mentions,
  COUNT(*) as total_links
FROM \`ridehome.links\`
GROUP BY year
ORDER BY year
" "AI/ML Topic Trend Over Time"
}

# Query 10: Custom SQL
function query_custom() {
    echo -e "${YELLOW}Enter your SQL query (press Ctrl+D when done):${NC}"
    local custom_query=$(cat)

    print_header "Custom Query"
    echo ""

    bq query --use_legacy_sql=false "$custom_query"

    echo ""
}

# Menu
function show_menu() {
    print_header "The Ride Home - BigQuery Sample Queries"
    echo ""
    echo "Available queries:"
    echo ""
    echo "  1. Top 10 Sources All-Time"
    echo "  2. Links Per Year Trend"
    echo "  3. Big Tech Company Mentions"
    echo "  4. Busiest Days (Most Links)"
    echo "  5. Source Diversity by Year"
    echo "  6. Monthly Longreads Count"
    echo "  7. Search for Specific Topic (requires search term)"
    echo "  8. Links by Day of Week"
    echo "  9. AI/ML Topic Trend Over Time"
    echo " 10. Run Custom SQL Query"
    echo ""
    echo -e "${YELLOW}Usage:${NC}"
    echo "  ./bigquery_queries.sh [query_number] [args]"
    echo ""
    echo -e "${YELLOW}Examples:${NC}"
    echo "  ./bigquery_queries.sh 1              # Run query 1"
    echo "  ./bigquery_queries.sh 7 chatgpt      # Search for 'chatgpt'"
    echo "  ./bigquery_queries.sh                # Show this menu"
    echo ""
}

# Main
if [ $# -eq 0 ]; then
    show_menu
    exit 0
fi

case $1 in
    1) query_top_sources ;;
    2) query_yearly_trend ;;
    3) query_big_tech ;;
    4) query_busiest_days ;;
    5) query_source_diversity ;;
    6) query_monthly_longreads ;;
    7) query_search_topic "$2" ;;
    8) query_day_of_week ;;
    9) query_ai_trend ;;
    10) query_custom ;;
    *)
        echo -e "${YELLOW}Invalid query number: $1${NC}"
        echo ""
        show_menu
        exit 1
        ;;
esac
