# GCP Implementation Plan: The Ride Home Migration

**Status**: Ready to implement
**Target Architecture**: Cloud Run + BigQuery + Gemini
**Estimated Cost**: $1.35/month
**Learning Approach**: Step-by-step with GCP concepts explained

---

## Architecture Overview

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Cloud      │────▶│  Cloud Run   │────▶│   BigQuery   │
│  Scheduler   │     │ RSS Parser   │     │ (links data) │
│  (6AM PT)    │     │              │     │              │
└──────────────┘     └──────────────┘     └──────┬───────┘
                                                  │
                                                  ▼
                                         ┌──────────────┐
                                         │  Cloud Run   │
                                         │Site Generator│
                                         └──────┬───────┘
                                                │
                                                ▼
                                         ┌──────────────┐
                                         │Cloud Storage │
                                         │   + CDN      │
                                         └──────────────┘
```

**What you'll learn**:
- GCP project management & IAM
- Cloud Run (serverless containers)
- BigQuery (data warehouse)
- Cloud Scheduler (cron jobs)
- Cloud Storage (object storage)
- Gemini API (AI/LLM integration)

---

## Prerequisites ✓ (Already Done)

- [x] GCP account created
- [x] Billing enabled with budget alerts
- [x] Core APIs enabled (Cloud Run, BigQuery, Cloud Scheduler, Cloud Storage)

---

## Phase 1: Infrastructure Foundation (Day 1 - 2 hours)

### 1.1 Complete Project Setup

**Commands**:
```bash
# Set your project ID (must be globally unique)
export PROJECT_ID="ridehome-poc"
export REGION="us-central1"  # Iowa datacenter (lowest cost)

# Configure gcloud CLI
gcloud config set project $PROJECT_ID
gcloud config set compute/region $REGION

# Verify configuration
gcloud config list
```

**What you're learning**:
- `gcloud` is the CLI for managing GCP resources
- Project ID is globally unique across all GCP
- Region choice affects cost and latency (us-central1 is cheapest)

---

### 1.2 Create BigQuery Dataset & Table

**What is BigQuery?**
BigQuery is Google's serverless data warehouse. Unlike traditional databases:
- No server to manage (fully serverless)
- Optimized for analytics queries (GROUP BY, aggregations)
- Pay only for data scanned (1 TB free/month)
- Automatically scales to petabytes

**Commands**:
```bash
# Create dataset (database equivalent)
bq mk \
  --dataset \
  --location=$REGION \
  --description="The Ride Home podcast links data" \
  $PROJECT_ID:ridehome

# Create links table
bq mk \
  --table \
  $PROJECT_ID:ridehome.links \
  id:STRING,date:DATE,date_unix:INT64,title:STRING,url:STRING,source:STRING,link_type:STRING,episode_date:DATE,episode_date_unix:INT64,created_at:TIMESTAMP
```

**Configure table partitioning** (for query optimization):
```bash
# Recreate table with partitioning (optimizes date-range queries)
bq rm -f -t $PROJECT_ID:ridehome.links

bq mk \
  --table \
  --time_partitioning_field=date \
  --clustering_fields=link_type,source \
  $PROJECT_ID:ridehome.links \
  schema.json
```

**Create schema.json**:
```bash
cat > schema.json <<EOF
[
  {"name": "id", "type": "STRING", "mode": "REQUIRED"},
  {"name": "date", "type": "DATE", "mode": "REQUIRED"},
  {"name": "date_unix", "type": "INT64", "mode": "REQUIRED"},
  {"name": "title", "type": "STRING", "mode": "REQUIRED"},
  {"name": "url", "type": "STRING", "mode": "REQUIRED"},
  {"name": "source", "type": "STRING", "mode": "NULLABLE"},
  {"name": "link_type", "type": "STRING", "mode": "REQUIRED"},
  {"name": "episode_date", "type": "DATE", "mode": "REQUIRED"},
  {"name": "episode_date_unix", "type": "INT64", "mode": "REQUIRED"},
  {"name": "created_at", "type": "TIMESTAMP", "mode": "NULLABLE"}
]
EOF

bq mk \
  --table \
  --time_partitioning_field=date \
  --clustering_fields=link_type,source \
  $PROJECT_ID:ridehome.links \
  schema.json
```

**Verify**:
```bash
bq show $PROJECT_ID:ridehome.links
```

**What you learned**:
- **Dataset** = container for tables (like a database)
- **Partitioning** = splits table by date for faster queries
- **Clustering** = sorts data by columns for optimization
- **Schema** = defines column names and types

---

### 1.3 Migrate Existing SQLite Data to BigQuery

**Export SQLite to CSV**:
```bash
cd /Users/pberry/src/ridehome

# Export links table to CSV
sqlite3 ridehome.db <<EOF
.headers on
.mode csv
.output links_export.csv
SELECT
  hex(randomblob(16)) as id,
  date,
  date_unix,
  title,
  url,
  source,
  link_type,
  episode_date,
  episode_date_unix,
  datetime('now') as created_at
FROM links;
.quit
EOF
```

**Load CSV into BigQuery**:
```bash
# Load data into BigQuery
bq load \
  --source_format=CSV \
  --skip_leading_rows=1 \
  --replace \
  $PROJECT_ID:ridehome.links \
  links_export.csv \
  schema.json
```

**Verify data**:
```bash
# Count rows
bq query --use_legacy_sql=false \
  'SELECT COUNT(*) as total FROM `ridehome.links`'

# Check recent links
bq query --use_legacy_sql=false \
  'SELECT date, title, source FROM `ridehome.links` ORDER BY date DESC LIMIT 10'
```

**What you learned**:
- `bq load` imports data from CSV/JSON/Avro
- `--replace` overwrites table (vs `--append`)
- BigQuery uses backticks for table names in SQL

---

### 1.4 Create Cloud Storage Bucket (Static Site Hosting)

**What is Cloud Storage?**
Object storage similar to AWS S3. We'll use it to host static HTML/markdown files.

**Commands**:
```bash
# Create bucket (name must be globally unique)
export BUCKET_NAME="${PROJECT_ID}-static-site"

gsutil mb \
  -l $REGION \
  -c STANDARD \
  gs://$BUCKET_NAME/

# Make bucket publicly readable
gsutil iam ch allUsers:objectViewer gs://$BUCKET_NAME

# Enable website hosting
gsutil web set -m index.html -e 404.html gs://$BUCKET_NAME/
```

**Test upload**:
```bash
echo "<h1>The Ride Home</h1>" > test.html
gsutil cp test.html gs://$BUCKET_NAME/
gsutil rm gs://$BUCKET_NAME/test.html
```

**What you learned**:
- `gsutil` = CLI tool for Cloud Storage
- Buckets are globally unique (like domain names)
- IAM controls access (`allUsers:objectViewer` = public read)

---

## Phase 2: Containerize RSS Parser (Day 2 - 3 hours)

### 2.1 Create Requirements File

**What is this?**
Python dependencies needed in the container. We'll pin versions for reproducibility.

**Commands**:
```bash
cd /Users/pberry/src/ridehome

# Generate from current environment
source env/bin/activate
pip freeze | grep -E "(feedparser|html2text|beautifulsoup4|html5lib)" > requirements-gcp.txt

# Add BigQuery client library
echo "google-cloud-bigquery==3.14.1" >> requirements-gcp.txt
echo "google-cloud-storage==2.14.0" >> requirements-gcp.txt
```

**Expected requirements-gcp.txt**:
```
feedparser==6.0.11
html2text==2024.2.26
beautifulsoup4==4.12.3
html5lib==1.1
google-cloud-bigquery==3.14.1
google-cloud-storage==2.14.0
```

---

### 2.2 Create BigQuery Writer Module

**Why?**
We need to replace SQLite writes with BigQuery writes.

**Create `bigquery_writer.py`**:
```python
#!/usr/bin/env python3
"""BigQuery writer for The Ride Home links."""

from google.cloud import bigquery
from datetime import datetime
import hashlib


class BigQueryWriter:
    def __init__(self, project_id, dataset_id="ridehome"):
        """Initialize BigQuery client."""
        self.client = bigquery.Client(project=project_id)
        self.dataset_id = dataset_id
        self.table_id = f"{project_id}.{dataset_id}.links"

    def generate_id(self, url, date):
        """Generate deterministic ID from URL + date."""
        combined = f"{url}{date}"
        return hashlib.sha256(combined.encode()).hexdigest()[:32]

    def insert_links(self, links):
        """
        Insert links into BigQuery.

        Args:
            links: List of dicts with keys: date, title, url, source,
                   link_type, episode_date

        Returns:
            Number of rows inserted
        """
        if not links:
            return 0

        # Prepare rows
        rows_to_insert = []
        for link in links:
            # Convert date strings to date objects if needed
            date = link['date']
            episode_date = link['episode_date']

            row = {
                "id": self.generate_id(link['url'], link['date']),
                "date": date,
                "date_unix": int(datetime.strptime(date, "%Y-%m-%d").timestamp()),
                "title": link['title'],
                "url": link['url'],
                "source": link.get('source'),
                "link_type": link['link_type'],
                "episode_date": episode_date,
                "episode_date_unix": int(datetime.strptime(episode_date, "%Y-%m-%d").timestamp()),
                "created_at": datetime.utcnow().isoformat()
            }
            rows_to_insert.append(row)

        # Insert into BigQuery
        errors = self.client.insert_rows_json(self.table_id, rows_to_insert)

        if errors:
            print(f"BigQuery insert errors: {errors}")
            return 0

        print(f"✓ Inserted {len(rows_to_insert)} rows into BigQuery")
        return len(rows_to_insert)
```

**What you learned**:
- `google-cloud-bigquery` Python client
- `insert_rows_json()` for streaming inserts
- Deterministic IDs prevent duplicates

---

### 2.3 Create Cloud Run Entrypoint

**What is Cloud Run?**
Serverless container platform. You give it a Docker image, it runs it on-demand and scales to zero when idle.

**Create `cloud_run_parser.py`**:
```python
#!/usr/bin/env python3
"""Cloud Run entrypoint for RSS parser."""

import os
import sys
from flask import Flask, request
from extract import extract_and_format, CONFIGS
from bigquery_writer import BigQueryWriter

app = Flask(__name__)

# Get project ID from environment
PROJECT_ID = os.environ.get('GCP_PROJECT_ID')
if not PROJECT_ID:
    raise ValueError("GCP_PROJECT_ID environment variable required")


@app.route('/', methods=['POST', 'GET'])
def parse_rss():
    """Parse RSS feed and insert into BigQuery."""
    try:
        # Parse both showlinks and longreads
        bq_writer = BigQueryWriter(PROJECT_ID)

        total_inserted = 0
        for entry_type in ['showlinks', 'longreads']:
            print(f"Processing {entry_type}...")

            # Use existing extract logic
            entries = extract_and_format(
                feed_url='https://feeds.megaphone.fm/ridehome',
                entry_type=entry_type,
                config=CONFIGS[entry_type]
            )

            # Convert to BigQuery format
            links = []
            for entry in entries:
                links.append({
                    'date': entry['date'],
                    'title': entry['title'],
                    'url': entry['url'],
                    'source': entry.get('source'),
                    'link_type': entry_type.rstrip('s'),  # 'showlinks' -> 'showlink'
                    'episode_date': entry['episode_date']
                })

            # Insert into BigQuery
            inserted = bq_writer.insert_links(links)
            total_inserted += inserted

        return {
            'status': 'success',
            'inserted': total_inserted,
            'message': f'Inserted {total_inserted} links into BigQuery'
        }, 200

    except Exception as e:
        print(f"Error: {str(e)}")
        return {'status': 'error', 'message': str(e)}, 500


if __name__ == '__main__':
    # Cloud Run sets PORT environment variable
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
```

**What you learned**:
- Cloud Run expects HTTP server (Flask, FastAPI, etc.)
- `PORT` environment variable set by Cloud Run
- Container must listen on 0.0.0.0 (not localhost)

---

### 2.4 Create Dockerfile

**What is Docker?**
Packages your code + dependencies into a container image that runs anywhere.

**Create `Dockerfile`**:
```dockerfile
# Use official Python runtime
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements-gcp.txt .
RUN pip install --no-cache-dir -r requirements-gcp.txt

# Copy application code
COPY extract.py .
COPY html_parser.py .
COPY file_updater.py .
COPY bigquery_writer.py .
COPY cloud_run_parser.py .
COPY docs/_includes/ ./docs/_includes/

# Set environment variable
ENV PYTHONUNBUFFERED=1

# Run the web service
CMD ["python", "cloud_run_parser.py"]
```

**What you learned**:
- `FROM` = base image (Python 3.11)
- `COPY` = add files to image
- `RUN` = execute commands during build
- `CMD` = command to run when container starts

---

### 2.5 Build and Test Locally

**Install Docker Desktop** (if not already):
- Download from https://www.docker.com/products/docker-desktop

**Build image**:
```bash
cd /Users/pberry/src/ridehome

# Build container
docker build -t ridehome-parser:latest .

# Verify image
docker images | grep ridehome-parser
```

**Test locally**:
```bash
# Run container locally
docker run -p 8080:8080 \
  -e GCP_PROJECT_ID=$PROJECT_ID \
  -e GOOGLE_APPLICATION_CREDENTIALS=/tmp/keys/key.json \
  -v ~/.config/gcloud/application_default_credentials.json:/tmp/keys/key.json:ro \
  ridehome-parser:latest

# In another terminal, test HTTP endpoint
curl -X POST http://localhost:8080/
```

**What you learned**:
- `docker build` creates image
- `docker run` starts container
- `-p 8080:8080` maps ports (host:container)
- `-e` sets environment variables
- `-v` mounts files into container

---

### 2.6 Deploy to Cloud Run

**Enable Container Registry**:
```bash
gcloud services enable containerregistry.googleapis.com
```

**Push image to Google Container Registry**:
```bash
# Tag image for GCR
docker tag ridehome-parser:latest gcr.io/$PROJECT_ID/ridehome-parser:latest

# Configure Docker auth
gcloud auth configure-docker

# Push to GCR
docker push gcr.io/$PROJECT_ID/ridehome-parser:latest
```

**Deploy to Cloud Run**:
```bash
gcloud run deploy ridehome-parser \
  --image gcr.io/$PROJECT_ID/ridehome-parser:latest \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars GCP_PROJECT_ID=$PROJECT_ID \
  --memory 512Mi \
  --timeout 300s \
  --max-instances 1 \
  --min-instances 0
```

**What each flag means**:
- `--platform managed` = fully serverless (vs GKE)
- `--allow-unauthenticated` = public endpoint (change later for security)
- `--memory 512Mi` = RAM allocation
- `--timeout 300s` = max 5 minutes per request
- `--min-instances 0` = scales to zero (no cost when idle)

**Test deployed service**:
```bash
# Get service URL
SERVICE_URL=$(gcloud run services describe ridehome-parser \
  --region $REGION \
  --format='value(status.url)')

echo "Service URL: $SERVICE_URL"

# Test endpoint
curl -X POST $SERVICE_URL
```

**What you learned**:
- GCR (Google Container Registry) stores Docker images
- Cloud Run auto-scales based on traffic
- Pay only when container is processing requests

---

## Phase 3: Automation (Day 3 - 2 hours)

### 3.1 Create Cloud Scheduler Job

**What is Cloud Scheduler?**
Managed cron service. Triggers HTTP endpoints on a schedule.

**Create job**:
```bash
# Enable Cloud Scheduler API
gcloud services enable cloudscheduler.googleapis.com

# Create service account for scheduler
gcloud iam service-accounts create ridehome-scheduler \
  --display-name="Ride Home Scheduler"

# Grant Cloud Run Invoker role
gcloud run services add-iam-policy-binding ridehome-parser \
  --region=$REGION \
  --member="serviceAccount:ridehome-scheduler@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/run.invoker"

# Create scheduler job (6 AM PT weekdays = 2 PM UTC)
gcloud scheduler jobs create http ridehome-daily-parse \
  --location=$REGION \
  --schedule="0 14 * * 1-5" \
  --uri="$SERVICE_URL" \
  --http-method=POST \
  --oidc-service-account-email="ridehome-scheduler@${PROJECT_ID}.iam.gserviceaccount.com" \
  --oidc-token-audience="$SERVICE_URL"
```

**Cron schedule explained**:
- `0 14 * * 1-5` = minute 0, hour 14 (2 PM UTC), every day, every month, Mon-Fri
- Converts to 6 AM Pacific Time (UTC-8)

**Test manually**:
```bash
# Trigger job immediately (for testing)
gcloud scheduler jobs run ridehome-daily-parse --location=$REGION
```

**What you learned**:
- Cloud Scheduler uses cron syntax
- OIDC authentication for secure triggers
- Service accounts for service-to-service auth

---

### 3.2 Build Site Generator

**Create `site_generator.py`**:
```python
#!/usr/bin/env python3
"""Generate static markdown files from BigQuery data."""

import os
from google.cloud import bigquery, storage
from datetime import datetime


def generate_markdown_files(project_id, bucket_name):
    """Query BigQuery and generate markdown files."""

    bq_client = bigquery.Client(project=project_id)
    storage_client = storage.Client(project=project_id)
    bucket = storage_client.bucket(bucket_name)

    # Query for showlinks by year
    query = """
    SELECT
      EXTRACT(YEAR FROM date) as year,
      date,
      title,
      url,
      source
    FROM `ridehome.links`
    WHERE link_type = 'showlink'
    ORDER BY date DESC
    """

    results = bq_client.query(query).to_dataframe()

    # Group by year
    for year, group in results.groupby('year'):
        markdown = f"# The Ride Home - Show Links {int(year)}\n\n"

        current_date = None
        for _, row in group.iterrows():
            if row['date'] != current_date:
                markdown += f"\n## {row['date'].strftime('%B %d, %Y')}\n\n"
                current_date = row['date']

            source = f" ({row['source']})" if row['source'] else ""
            markdown += f"- [{row['title']}]({row['url']}){source}\n"

        # Upload to Cloud Storage
        blob = bucket.blob(f'all-links-{int(year)}.md')
        blob.upload_from_string(markdown, content_type='text/markdown')
        print(f"✓ Generated all-links-{int(year)}.md")

    # Query for longreads
    query = """
    SELECT
      date,
      title,
      url,
      source
    FROM `ridehome.links`
    WHERE link_type = 'longread'
    ORDER BY date DESC
    """

    results = bq_client.query(query).to_dataframe()

    markdown = f"# Weekend Longreads\n\n"
    current_date = None
    for _, row in results.iterrows():
        if row['date'] != current_date:
            markdown += f"\n## {row['date'].strftime('%B %d, %Y')}\n\n"
            current_date = row['date']

        markdown += f"- [{row['title']}]({row['url']})\n"

    blob = bucket.blob('longreads-all.md')
    blob.upload_from_string(markdown, content_type='text/markdown')
    print("✓ Generated longreads-all.md")


if __name__ == '__main__':
    project_id = os.environ['GCP_PROJECT_ID']
    bucket_name = os.environ['BUCKET_NAME']

    generate_markdown_files(project_id, bucket_name)
```

**Deploy as Cloud Run service**:
```bash
# Create Dockerfile for site generator
cat > Dockerfile.sitegen <<EOF
FROM python:3.11-slim
WORKDIR /app
RUN pip install google-cloud-bigquery google-cloud-storage pandas flask
COPY site_generator.py .
CMD ["python", "site_generator.py"]
EOF

# Build and deploy
docker build -f Dockerfile.sitegen -t gcr.io/$PROJECT_ID/ridehome-sitegen:latest .
docker push gcr.io/$PROJECT_ID/ridehome-sitegen:latest

gcloud run deploy ridehome-sitegen \
  --image gcr.io/$PROJECT_ID/ridehome-sitegen:latest \
  --region $REGION \
  --platform managed \
  --no-allow-unauthenticated \
  --set-env-vars GCP_PROJECT_ID=$PROJECT_ID,BUCKET_NAME=$BUCKET_NAME \
  --memory 256Mi \
  --timeout 60s
```

**What you learned**:
- BigQuery results export to Pandas DataFrame
- Cloud Storage client for uploading files
- `--no-allow-unauthenticated` = private service (internal only)

---

### 3.3 Trigger Site Generator After Parser

**Option 1: Pub/Sub (Recommended)**

Create event-driven workflow:
```bash
# Enable Pub/Sub
gcloud services enable pubsub.googleapis.com

# Create topic
gcloud pubsub topics create ridehome-links-updated

# Create Pub/Sub triggered Cloud Run
gcloud run deploy ridehome-sitegen \
  --image gcr.io/$PROJECT_ID/ridehome-sitegen:latest \
  --region $REGION \
  --platform managed \
  --no-allow-unauthenticated
```

Update `cloud_run_parser.py` to publish Pub/Sub message after insert:
```python
from google.cloud import pubsub_v1

# At end of parse_rss():
publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(PROJECT_ID, 'ridehome-links-updated')
publisher.publish(topic_path, b'Links updated')
```

**Option 2: Direct HTTP Call (Simpler)**

Add to end of `cloud_run_parser.py`:
```python
import requests

# Call site generator
sitegen_url = os.environ.get('SITEGEN_URL')
if sitegen_url:
    requests.post(sitegen_url)
```

**What you learned**:
- Pub/Sub = message queue for async communication
- Event-driven architecture decouples services
- Direct HTTP calls are simpler but tightly coupled

---

## Phase 4: Natural Language Query API (Day 4 - 3 hours)

### 4.1 Enable Gemini API

```bash
# Enable Vertex AI API (includes Gemini)
gcloud services enable aiplatform.googleapis.com
```

**Test Gemini access**:
```python
from google.cloud import aiplatform

aiplatform.init(project=PROJECT_ID, location=REGION)

# Test Gemini 2.0 Flash
from vertexai.preview.generative_models import GenerativeModel

model = GenerativeModel("gemini-2.0-flash-exp")
response = model.generate_content("Say hello!")
print(response.text)
```

---

### 4.2 Create Query API

**Create `nl_query_api.py`**:
```python
#!/usr/bin/env python3
"""Natural language query API using Gemini."""

import os
from flask import Flask, request, jsonify
from google.cloud import bigquery, aiplatform
from vertexai.preview.generative_models import GenerativeModel

app = Flask(__name__)

PROJECT_ID = os.environ['GCP_PROJECT_ID']
REGION = os.environ.get('REGION', 'us-central1')

aiplatform.init(project=PROJECT_ID, location=REGION)
bq_client = bigquery.Client(project=PROJECT_ID)
gemini_model = GenerativeModel("gemini-2.0-flash-exp")

# Schema for Gemini
SCHEMA = """
Table: ridehome.links
Columns:
- id (STRING)
- date (DATE)
- title (STRING)
- url (STRING)
- source (STRING)
- link_type (STRING: 'showlink' or 'longread')
- episode_date (DATE)
- created_at (TIMESTAMP)
"""


@app.route('/query', methods=['POST'])
def query():
    """Process natural language query."""
    data = request.get_json()
    question = data.get('question')

    if not question:
        return jsonify({'error': 'Missing question'}), 400

    # Generate SQL with Gemini
    prompt = f"""
You are a SQL expert. Given this BigQuery table schema:

{SCHEMA}

Convert this natural language question to a SQL query:
"{question}"

Return ONLY the SQL query, no explanation.
"""

    response = gemini_model.generate_content(prompt)
    sql = response.text.strip()

    # Remove markdown code blocks if present
    if sql.startswith('```'):
        sql = sql.split('```')[1].strip()
        if sql.startswith('sql'):
            sql = sql[3:].strip()

    # Execute query
    try:
        results = bq_client.query(sql).to_dataframe()

        return jsonify({
            'question': question,
            'sql': sql,
            'results': results.to_dict(orient='records'),
            'row_count': len(results)
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'sql': sql
        }), 500


@app.route('/health', methods=['GET'])
def health():
    return {'status': 'healthy'}, 200


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
```

---

### 4.3 Deploy Query API

```bash
# Create requirements
cat > requirements-query.txt <<EOF
flask==3.0.0
google-cloud-bigquery==3.14.1
google-cloud-aiplatform==1.38.1
pandas==2.1.4
EOF

# Create Dockerfile
cat > Dockerfile.query <<EOF
FROM python:3.11-slim
WORKDIR /app
COPY requirements-query.txt .
RUN pip install --no-cache-dir -r requirements-query.txt
COPY nl_query_api.py .
CMD ["python", "nl_query_api.py"]
EOF

# Build and deploy
docker build -f Dockerfile.query -t gcr.io/$PROJECT_ID/ridehome-query:latest .
docker push gcr.io/$PROJECT_ID/ridehome-query:latest

gcloud run deploy ridehome-query \
  --image gcr.io/$PROJECT_ID/ridehome-query:latest \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars GCP_PROJECT_ID=$PROJECT_ID,REGION=$REGION \
  --memory 512Mi \
  --timeout 60s
```

**Test**:
```bash
QUERY_URL=$(gcloud run services describe ridehome-query \
  --region $REGION \
  --format='value(status.url)')

curl -X POST $QUERY_URL/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What were the top 5 sources in December 2024?"}'
```

**What you learned**:
- Gemini 2.0 Flash = free tier (2M tokens/day)
- Vertex AI = GCP's AI/ML platform
- Text-to-SQL via LLM prompt engineering

---

## Phase 5: Monitoring & Cost Control (Day 5 - 1 hour)

### 5.1 Set Up Logging

**View Cloud Run logs**:
```bash
gcloud logging read "resource.type=cloud_run_revision" \
  --limit 50 \
  --format="table(timestamp,textPayload)"
```

**Create log-based alert**:
```bash
# Alert on errors
gcloud alpha monitoring policies create \
  --notification-channels=YOUR_EMAIL \
  --display-name="Ridehome Parser Errors" \
  --condition-display-name="Error rate > 10%" \
  --condition-threshold-value=10
```

---

### 5.2 Cost Monitoring Dashboard

**View current costs**:
```bash
gcloud billing accounts list
gcloud billing projects describe $PROJECT_ID
```

**Set budget alert** (already done, but verify):
```bash
# List budgets
gcloud billing budgets list --billing-account=YOUR_BILLING_ACCOUNT
```

---

### 5.3 Enable Cloud Monitoring

```bash
# View dashboards
gcloud monitoring dashboards list

# Create custom dashboard for ridehome
# (Do this in Cloud Console: Monitoring > Dashboards > Create)
```

---

## Summary: What You Built

### Components
1. **BigQuery** - Data warehouse (6,827 links, analytics-ready)
2. **Cloud Run (Parser)** - Serverless RSS parser (runs daily)
3. **Cloud Run (Site Gen)** - Markdown generator (triggered after parse)
4. **Cloud Run (Query API)** - Gemini-powered natural language queries
5. **Cloud Scheduler** - Cron trigger (6 AM PT weekdays)
6. **Cloud Storage** - Static file hosting

### Cost Breakdown (Monthly)
```
Cloud Scheduler:      FREE (3 jobs free tier)
Cloud Run (parser):   $0.50 (20 runs × 2 min)
BigQuery:             FREE (under free tier limits)
Cloud Run (sitegen):  $0.25 (20 runs × 1 min)
Cloud Storage:        $0.05 (10 MB)
Cloud CDN:            $0.50 (cache hits)
Gemini API:           FREE (< 2M tokens/day)
Cloud Run (query):    $0.05 (100 queries)
──────────────────────────────
TOTAL:                $1.35/month
```

### Key GCP Concepts Learned
- **Serverless** - No servers to manage, auto-scaling
- **IAM** - Identity and Access Management (service accounts)
- **Regional resources** - Location affects cost and latency
- **Container deployment** - Docker → GCR → Cloud Run
- **Event-driven architecture** - Scheduler → Parser → Pub/Sub → Site Gen
- **Managed services** - BigQuery, Cloud Scheduler, Cloud Storage

---

## Next Steps (Optional Enhancements)

1. **Add HTTPS custom domain** - Point ridehome.com to Cloud Storage
2. **CI/CD with Cloud Build** - Auto-deploy on git push
3. **Enhanced NL query UI** - Web interface for queries
4. **Weekly digest email** - Gemini-generated newsletter
5. **Public API** - RESTful endpoints for developers
6. **Recommendation engine** - "Similar links" feature

---

## Troubleshooting

**Cloud Run deployment fails**:
```bash
gcloud run services describe ridehome-parser --region=$REGION
gcloud logging read "resource.type=cloud_run_revision" --limit 20
```

**BigQuery insert errors**:
```bash
bq show --format=prettyjson $PROJECT_ID:ridehome.links
```

**Cost exceeds expectations**:
```bash
gcloud billing accounts describe YOUR_BILLING_ACCOUNT
# Check: Monitoring > Dashboards > Cost breakdown
```

---

## Resources

- [Cloud Run Docs](https://cloud.google.com/run/docs)
- [BigQuery Docs](https://cloud.google.com/bigquery/docs)
- [Gemini API Docs](https://cloud.google.com/vertex-ai/docs/generative-ai/model-reference/gemini)
- [GCP Free Tier](https://cloud.google.com/free/docs/free-cloud-features)

---

**Ready to start?** Begin with Phase 1, step 1.1. Each step builds on the previous one.
