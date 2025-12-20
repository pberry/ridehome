# GCP Deployment

Serverless cloud deployment using Google Cloud Platform.

## Architecture

```
Cloud Scheduler → Cloud Run (Parser) → BigQuery → Cloud Run (Site Gen) → Cloud Storage
                                            ↓
                                    Gemini Query API
```

**Components**:
- **BigQuery**: Data warehouse for 6,800+ links (analytics-ready)
- **Cloud Run**: Serverless containers (RSS parser, site generator, query API)
- **Cloud Scheduler**: Cron trigger (6 AM PT weekdays)
- **Cloud Storage**: Static site hosting with CDN
- **Gemini 2.0 Flash**: Natural language queries (FREE tier)

**Monthly Cost**: ~$1.35

---

## Quick Start

**Prerequisites**:
- GCP account with billing enabled
- `gcloud` CLI installed ([install guide](https://cloud.google.com/sdk/docs/install))
- Docker Desktop ([install guide](https://www.docker.com/products/docker-desktop))

**Setup**:
```bash
# Set project variables
export PROJECT_ID="ridehome-poc"
export REGION="us-central1"

# Configure gcloud
gcloud config set project $PROJECT_ID
gcloud config set compute/region $REGION

# Follow the implementation plan
cat GCP-IMPLEMENTATION-PLAN.md
```

---

## Documentation

- **[GCP-IMPLEMENTATION-PLAN.md](./GCP-IMPLEMENTATION-PLAN.md)** - Complete step-by-step guide (5 phases)
- **[cloud-migration-analysis.md](./cloud-migration-analysis.md)** - AWS vs GCP vs Azure analysis
- **[github-actions-automation.md](./github-actions-automation.md)** - Alternative: GitHub Actions deployment

---

## Cost Breakdown

```
Component               Monthly Cost
──────────────────────────────────
Cloud Scheduler         FREE (3 jobs in free tier)
Cloud Run (parser)      $0.50
BigQuery Storage        FREE (under 10 GB limit)
BigQuery Queries        FREE (under 1 TB limit)
Cloud Run (site gen)    $0.25
Cloud Storage           $0.05
Cloud CDN               $0.50
Gemini API              FREE (under 2M tokens/day)
Cloud Run (query API)   $0.05
──────────────────────────────────
TOTAL                   $1.35/month
```

---

## File Structure

```
gcp/
├── README.md                           # This file
├── GCP-IMPLEMENTATION-PLAN.md          # Step-by-step setup guide
├── cloud-migration-analysis.md         # Cloud provider comparison
├── github-actions-automation.md        # Alternative deployment
│
├── gcp.sh                              # Initial project setup commands
├── billing.sh                          # Billing setup commands
│
└── (Future: implementation files)
    ├── bigquery_writer.py              # BigQuery adapter
    ├── cloud_run_parser.py             # Cloud Run entrypoint
    ├── site_generator.py               # Static site generator
    ├── nl_query_api.py                 # Query API
    ├── Dockerfile                      # Container image
    ├── requirements-gcp.txt            # Python dependencies
    └── deploy.sh                       # Deployment automation
```

---

## Implementation Status

**Phase 1**: Infrastructure Setup
- [ ] BigQuery dataset created
- [ ] SQLite data migrated
- [ ] Cloud Storage bucket configured

**Phase 2**: RSS Parser
- [ ] Containerized parser
- [ ] Deployed to Cloud Run
- [ ] BigQuery integration working

**Phase 3**: Automation
- [ ] Cloud Scheduler configured
- [ ] Site generator deployed
- [ ] Pipeline end-to-end tested

**Phase 4**: Natural Language Queries
- [ ] Gemini API enabled
- [ ] Query API deployed
- [ ] Sample queries tested

**Phase 5**: Monitoring
- [ ] Logging configured
- [ ] Cost alerts set up
- [ ] Dashboards created

---

## Key Learning Outcomes

By completing this migration, you'll learn:

- **Serverless architecture** - Cloud Run, BigQuery, Cloud Scheduler
- **Container deployment** - Docker, GCR, Cloud Run
- **Data warehousing** - BigQuery schema design, partitioning, clustering
- **Event-driven systems** - Scheduler → Parser → Generator workflow
- **AI/LLM integration** - Gemini API for text-to-SQL
- **Infrastructure as Code** - Declarative cloud resources
- **Cost optimization** - Free tiers, scaling to zero

---

## Comparison to Other Deployments

| Deployment | Cost/Month | Setup | Maintenance | Scalability | NL Queries |
|------------|------------|-------|-------------|-------------|------------|
| **Local** | $0 | Easy | Manual runs | Single machine | No |
| **GitHub Actions** | $0 | Medium | Automated | Free tier limits | No |
| **GCP** | $1.35 | Complex | Fully automated | Unlimited | YES (free) |
| **AWS** | $50 | Complex | Fully automated | Unlimited | YES ($5/mo) |
| **Azure** | $13 | Complex | Fully automated | Unlimited | YES ($6/mo) |

---

## Support

**Questions?** Check:
1. [GCP-IMPLEMENTATION-PLAN.md](./GCP-IMPLEMENTATION-PLAN.md) troubleshooting section
2. [GCP Documentation](https://cloud.google.com/docs)
3. [Cloud Run Docs](https://cloud.google.com/run/docs)
4. [BigQuery Docs](https://cloud.google.com/bigquery/docs)

---

## Next Steps

1. **Read the implementation plan**: [GCP-IMPLEMENTATION-PLAN.md](./GCP-IMPLEMENTATION-PLAN.md)
2. **Complete Phase 1**: Infrastructure setup (2 hours)
3. **Test locally**: Verify parser works with BigQuery
4. **Deploy to Cloud Run**: Containerize and deploy
5. **Set up automation**: Cloud Scheduler + workflow
6. **Add NL queries**: Gemini integration

**Ready?** Start with Phase 1, step 1.1 in the implementation plan.
