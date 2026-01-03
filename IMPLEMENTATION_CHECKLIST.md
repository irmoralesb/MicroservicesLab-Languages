# Prometheus Integration Implementation Checklist

Follow this checklist to implement Prometheus monitoring step-by-step.
Each section includes the files to modify and specific lines to uncomment.

## Phase 1: Install Dependencies ✓

- [ ] Run: `pip install prometheus-client prometheus-fastapi-instrumentator`
- [ ] Verify installation: `pip list | grep prometheus`

## Phase 2: Core Metrics Module (monitoring/metrics.py)

This file is the foundation - uncomment ALL code blocks in this file first.

- [ ] Uncomment lines 5-202 (entire file content)
- [ ] Verify no syntax errors: `python -c "from monitoring import metrics"`

Key components enabled:
- ✓ Centralized metrics definitions
- ✓ Helper functions for recording metrics
- ✓ Error handling in metric recording

## Phase 3: Main Application Setup (main.py)

Enable automatic HTTP metrics and configure Prometheus endpoint.

- [ ] Line 10: Uncomment `import os`
- [ ] Lines 12-13: Uncomment Instrumentator and metrics imports
- [ ] Lines 45-79: Uncomment entire Prometheus configuration block
  - Enables automatic HTTP request tracking
  - Configures /metrics endpoint
  - Adds environment-based configuration
- [ ] Lines 88-95: Uncomment updated health check

Test:
```bash
python main.py  Check for import errors
uvicorn main:app --reload
curl http://localhost:8000/metrics  Should return Prometheus metrics
```

## Phase 4: Router-Level Metrics (routers/translator.py)

Add business logic metrics for translation endpoint.

- [ ] Line 18: Uncomment `import time`
- [ ] Lines 20-25: Uncomment metrics imports from monitoring module
- [ ] Lines 61-94: Uncomment timing and LLM tracking in translate_endpoint
  - Adds translation timing
  - Tracks LLM API call duration
  - Records errors with proper metrics
- [ ] Lines 108-148: Uncomment database and response metrics
  - Database operation timing
  - Token usage tracking
  - Success/failure recording

Test:
```bash
Send a translation request
curl -X POST http://localhost:8000/api/v1/translator/translate \
  -H "Content-Type: application/json" \
  -d '{"text_to_translate": "Hello", "translate_to_language": "es"}'

Check metrics
curl http://localhost:8000/metrics | grep translation
```

## Phase 5: Database Monitoring (databases/database.py) [OPTIONAL]

Add connection pool monitoring. This is optional but recommended for production.

- [ ] Lines 7-11: Uncomment event and logging imports
- [ ] Lines 44-59: Uncomment pool event listeners
  - Tracks connection creation/closure
  - Monitors active connections
- [ ] Lines 63-78: Uncomment get_monitored_db_session context manager

Note: If you uncomment database monitoring, you'll need to update get_db() in translator.py:
```python
def get_db():
    from databases.database import get_monitored_db_session
    with get_monitored_db_session() as db:
        yield db
```

## Phase 6: Configuration Files

##Environment Configuration
- [ ] Copy `.env.metrics.example` to `.env`
- [ ] Uncomment all lines in `.env`
- [ ] Adjust `METRICS_ENABLED` as needed (default: true)

### Prometheus Configuration
- [ ] Rename `prometheus.yml.example` to `prometheus.yml`
- [ ] Uncomment all content
- [ ] Update targets if not using Docker (line 19)

### Docker Compose
- [ ] Rename `docker-compose.monitoring.yml` (remove .yml extension if needed)
- [ ] Uncomment all content
- [ ] Review ports and adjust if conflicts exist

### Grafana Datasource
- [ ] Uncomment `grafana/provisioning/datasources/prometheus.yml`
- [ ] Verify Prometheus URL matches your setup

## Phase 7: Start Monitoring Stack

##Option A: Docker Compose (Recommended)
```bash
Start all services
docker-compose -f docker-compose.monitoring.yml up -d

Verify all containers are running
docker ps

Check logs if issues occur
docker logs prometheus
docker logs grafana
```

### Option B: Manual Setup
```bash
Start Prometheus
docker run -d -p 9090:9090 \
  -v $(pwd)/prometheus.yml:/etc/prometheus/prometheus.yml \
  prom/prometheus

Start Grafana
docker run -d -p 3000:3000 grafana/grafana
```

## Phase 8: Verification & Testing

- [ ] Access Prometheus UI: http://localhost:9090
  - [ ] Check Status > Targets (should show translation-api as UP)
  - [ ] Run query: `up` (should return 1)
  - [ ] Run query: `translation_requests_total`

- [ ] Access Grafana UI: http://localhost:3000
  - [ ] Login with admin/admin
  - [ ] Navigate to Configuration > Data Sources
  - [ ] Verify Prometheus is connected (green checkmark)

- [ ] Generate test traffic:
  ```bash
  Run this 10 times to generate metrics
  for i in {1..10}; do
    curl -X POST http://localhost:8000/api/v1/translator/translate \
      -H "Content-Type: application/json" \
      -d "{\"text_to_translate\": \"Test $i\", \"translate_to_language\": \"es\"}"
    sleep 1
  done
  ```

- [ ] Verify metrics in Prometheus:
  - [ ] `translation_requests_total` should show counts
  - [ ] `translation_duration_seconds_count` should increment
  - [ ] `llm_tokens_used_total` should show token usage
  - [ ] `http_requests_total` should track HTTP traffic

## Phase 9: Create Grafana Dashboard

- [ ] In Grafana, click "+" > "Dashboard"
- [ ] Add panels for key metrics:

### Panel 1: Translation Request Rate
- [ ] Query: `rate(translation_requests_total[5m])`
- [ ] Visualization: Time series
- [ ] Title: "Translation Requests/sec"

### Panel 2: P95 Latency
- [ ] Query: `histogram_quantile(0.95, rate(translation_duration_seconds_bucket[5m]))`
- [ ] Visualization: Time series
- [ ] Title: "95th Percentile Latency"

### Panel 3: Success Rate
- [ ] Query: `sum(rate(translation_requests_total{status="success"}[5m])) / sum(rate(translation_requests_total[5m])) * 100`
- [ ] Visualization: Gauge
- [ ] Title: "Success Rate %"

### Panel 4: Token Usage
- [ ] Query: `sum by (token_type) (rate(llm_tokens_used_total[5m]))`
- [ ] Visualization: Time series
- [ ] Title: "Token Consumption Rate"

### Panel 5: Active Connections
- [ ] Query: `database_connections_active`
- [ ] Visualization: Stat
- [ ] Title: "Active DB Connections"

### Panel 6: Error Rate
- [ ] Query: `rate(application_errors_total[5m])`
- [ ] Visualization: Time series
- [ ] Title: "Errors/sec"

- [ ] Save dashboard with name: "Translation API Monitoring"

## Phase 10: Production Hardening [IMPORTANT]

### Security
- [ ] Add authentication to /metrics endpoint (see MONITORING.md)
- [ ] Configure Prometheus scrape authentication
- [ ] Use HTTPS for Grafana in production
- [ ] Change default Grafana admin password

### Performance
- [ ] Set appropriate metric retention: `--storage.tsdb.retention.time=30d`
- [ ] Monitor Prometheus memory usage
- [ ] Consider metric sampling for high-traffic endpoints

### Alerting
- [ ] Create alerts.yml for critical conditions
- [ ] Set up AlertManager for notifications
- [ ] Configure notification channels (Slack, email, PagerDuty)

### High Availability
- [ ] Consider Prometheus federation for multiple instances
- [ ] Set up remote storage (Thanos/Cortex) for long-term retention
- [ ] Implement Grafana HA setup for production

## Troubleshooting Guide

### Problem: /metrics returns 404
**Solution:**
- Verify METRICS_ENABLED=true in .env
- Check that Instrumentator().instrument(app).expose(app) is uncommented
- Restart the application

### Problem: Prometheus shows "DOWN" for targets
**Solution:**
- Check network connectivity: `docker network ls`
- Verify service name in prometheus.yml matches docker-compose service name
- Check application logs: `docker logs translation-api`

### Problem: No metrics appearing in Grafana
**Solution:**
- Verify Prometheus datasource is configured correctly
- Check time range (Last 15 minutes)
- Generate test traffic to create metrics
- Verify metrics exist in Prometheus: http://localhost:9090

### Problem: High memory usage
**Solution:**
- Reduce metric cardinality (limit label values)
- Decrease retention time in Prometheus
- Enable metric sampling for high-volume endpoints

## Validation Checklist

Before considering implementation complete:

- [ ] All metrics endpoints return 200
- [ ] Prometheus successfully scrapes metrics
- [ ] Grafana displays data from Prometheus
- [ ] Custom metrics appear after test traffic
- [ ] Dashboard visualizations work correctly
- [ ] Health check includes metrics status
- [ ] Documentation is updated (if needed)
- [ ] Team members trained on dashboard usage

## Success Criteria

✓ Application exposes /metrics endpoint
✓ Prometheus scrapes metrics every 15 seconds
✓ Grafana displays real-time data
✓ All custom metrics (translation, LLM, DB) visible
✓ Error tracking operational
✓ Dashboard created and saved
✓ Alerts configured (if required)
✓ Documentation complete

## Next Steps After Implementation

1. Monitor dashboard daily for first week
2. Adjust alert thresholds based on baseline
3. Create additional dashboards for specific use cases
4. Set up automated reports (Grafana feature)
5. Train team on troubleshooting with metrics
6. Document runbook for common scenarios

## Estimated Implementation Time

- Phase 1-4 (Basic setup): 30 minutes
- Phase 5-6 (Configuration): 15 minutes
- Phase 7-8 (Deploy & verify): 20 minutes
- Phase 9 (Dashboards): 45 minutes
- Phase 10 (Production hardening): 60 minutes

**Total: ~3 hours for complete implementation**
