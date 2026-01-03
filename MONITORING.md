# This guide explains how to enable and configure Prometheus metrics for monitoring your Translation API with Grafana visualization.

##📋 Prerequisites

- Python 3.8+
- Docker and Docker Compose (for Prometheus/Grafana)
- Your FastAPI application running

## 🚀 Quick Start

### Step 1: Install Dependencies

```bash
pip install prometheus-client prometheus-fastapi-instrumentator
```

### Step 2: Enable Metrics in Code

Uncomment all commented blocks in these files (in order):

1. **monitoring/metrics.py** - Core metrics definitions
2. **main.py** - Application-level instrumentation
3. **routers/translator.py** - Endpoint-level metrics
4. **databases/database.py** - Database connection monitoring (optional)

### Step 3: Configure Environment

Add to your `.env` file:
```bash
METRICS_ENABLED=true
METRICS_ENDPOINT=/metrics
```

### Step 4: Start Your Application

```bash
uvicorn main:app --reload
```

Verify metrics endpoint: http://localhost:8000/metrics

### Step 5: Start Prometheus & Grafana

```bash
First, uncomment docker-compose.monitoring.yml
docker-compose -f docker-compose.monitoring.yml up -d
```

Access:
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)

#📊 Available Metrics

### HTTP Metrics (Automatic)
- `http_requests_total` - Total HTTP requests by method, endpoint, status
- `http_request_duration_seconds` - Request duration histogram
- `http_requests_inprogress` - Current requests being processed

### Translation Metrics
- `translation_requests_total{source_language, target_language, status}` - Total translations
- `translation_duration_seconds{target_language, status}` - Translation duration
- `translation_text_length_characters{target_language}` - Input text length distribution

### LLM Metrics
- `llm_tokens_used_total{model_name, token_type}` - Token consumption (input/output)
- `llm_api_calls_total{model_name, status}` - API call count
- `llm_api_duration_seconds{model_name}` - LLM API latency

### Database Metrics
- `database_connections_active` - Active database connections
- `database_operations_total{operation_type, table, status}` - DB operation count
- `database_operation_duration_seconds{operation_type, table}` - DB operation latency

### Error Tracking
- `application_errors_total{error_type, endpoint}` - Application errors

## 🎨 Grafana Dashboard Setup

### Import Pre-built Dashboard (Recommended)

1. Log into Grafana (http://localhost:3000)
2. Click **+** → **Import**
3. Enter dashboard ID: **1860** (Node Exporter) or **6417** (Prometheus 2.0)
4. Select Prometheus datasource
5. Click **Import**

### Create Custom Dashboard for Translation API

1. **Create New Dashboard**
2. **Add Panel** with these queries:

#### Translation Request Rate
```promql
rate(translation_requests_total[5m])
```

#### Average Translation Duration
```promql
rate(translation_duration_seconds_sum[5m]) / rate(translation_duration_seconds_count[5m])
```

#### Success Rate
```promql
sum(rate(translation_requests_total{status="success"}[5m])) / 
sum(rate(translation_requests_total[5m])) * 100
```

#### Token Usage
```promql
rate(llm_tokens_used_total[5m])
```

#### Active Database Connections
```promql
database_connections_active
```

#### Error Rate
```promql
rate(application_errors_total[5m])
```

## 🔍 Prometheus Query Examples

### Find slow translations (> 5 seconds)
```promql
translation_duration_seconds_bucket{le="5.0"} / 
translation_duration_seconds_count < 0.95
```

### Monitor token consumption by model
```promql
sum by (model_name, token_type) (llm_tokens_used_total)
```

### Track error rate by endpoint
```promql
rate(application_errors_total[5m]) > 0
```

### Database connection pool saturation
```promql
database_connections_active > 8  Adjust threshold
```

## 🎯 Production Best Practices

### 1. Metric Cardinality Control
- ✅ Use labels for dimensions you need to query
- ❌ Don't use high-cardinality labels (user IDs, transaction IDs)
- ✅ Limit label values to predefined sets

### 2. Performance Optimization
- Keep metrics collection lightweight (< 1ms overhead)
- Use `try/except` blocks to prevent metric failures from breaking app
- Consider sampling for high-volume metrics

### 3. Security
- Protect `/metrics` endpoint in production:
  ```python
  from fastapi import Depends, HTTPException, status
  from fastapi.security import HTTPBasic, HTTPBasicCredentials
  
  security = HTTPBasic()
  
  @app.get("/metrics")
  async def metrics(credentials: HTTPBasicCredentials = Depends(security)):
      if credentials.username != "metrics_user":
          raise HTTPException(status_code=401)
      Return metrics
  ```

### 4. Alert Configuration

Create `alerts.yml`:
```yaml
groups:
  - name: translation_api_alerts
    interval: 30s
    rules:
      - alert: HighErrorRate
        expr: rate(application_errors_total[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
      
      - alert: SlowTranslations
        expr: histogram_quantile(0.95, rate(translation_duration_seconds_bucket[5m])) > 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "95th percentile latency > 10s"
```

### 5. Data Retention
- Default: 15 days
- Adjust in prometheus.yml: `--storage.tsdb.retention.time=30d`
- Consider remote storage for long-term retention (Thanos, Cortex)

## 🧪 Testing Metrics

### 1. Generate test traffic
```bash
Send sample translation requests
curl -X POST "http://localhost:8000/api/v1/translator/translate" \
  -H "Content-Type: application/json" \
  -d '{"text_to_translate": "Hello World", "translate_to_language": "es"}'
```

### 2. Query Prometheus
```bash
Check if metrics are being collected
curl http://localhost:9090/api/v1/query?query=translation_requests_total
```

### 3. Verify in Grafana
- Navigate to Explore
- Run sample queries
- Create test visualizations

## 🐛 Troubleshooting

### Metrics endpoint returns 404
- ✅ Check `METRICS_ENABLED=true` in .env
- ✅ Verify instrumentation is uncommented in main.py
- ✅ Restart application

### Prometheus can't scrape metrics
- ✅ Check prometheus.yml targets configuration
- ✅ Verify network connectivity: `docker network inspect monitoring-network`
- ✅ Check Prometheus targets page: http://localhost:9090/targets

### Grafana shows "No data"
- ✅ Verify Prometheus datasource is configured
- ✅ Check time range in Grafana
- ✅ Generate test traffic to create metrics

### High memory usage
- ✅ Reduce metric cardinality (fewer labels/values)
- ✅ Decrease retention time
- ✅ Enable Prometheus remote write

## 📚 Additional Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [prometheus-fastapi-instrumentator](https://github.com/trallnag/prometheus-fastapi-instrumentator)
- [Prometheus Best Practices](https://prometheus.io/docs/practices/naming/)

## 🤝 Contributing Dashboards

If you create useful Grafana dashboards:
1. Export as JSON
2. Save to `grafana/dashboards/`
3. Document in this README

## 📞 Support

For issues or questions:
- Check application logs: `docker logs translation-api`
- Check Prometheus logs: `docker logs prometheus`
- Check Grafana logs: `docker logs grafana`
