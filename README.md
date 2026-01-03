# MicroservicesLab-Languages
Services to Enable Learning Language


## Dependencies installation

```
pip install -r requirements.txt
```

## Running the Service

```
uvicorn main:app --reload
```

## Prometheus Metrics (internal setup)

1. Install monitoring dependencies:
	```
	pip install prometheus-client prometheus-fastapi-instrumentator
	```
	(they are expected to be present in `requirements.txt` for full installs).
2. Enable metrics via environment variables (e.g. in a `.env` file):
	```
	METRICS_ENABLED=true
	METRICS_ENDPOINT=/api/v1/metrics
	```
3. Ensure the app imports metrics instrumentation in `main.py` and exposes the endpoint. The existing setup uses `prometheus_fastapi_instrumentator.Instrumentator` to auto-collect HTTP metrics and then calls `instrumentator.instrument(app).expose(app, endpoint=METRICS_ENDPOINT)`.
4. Use the centralized metric definitions in `monitoring/metrics.py` for custom counters/histograms. Available helpers:
	- `record_translation_metrics`
	- `record_llm_metrics`
	- `record_database_metrics`
	- `database_connections_activating`
	- `database_connections_deactivating`
	Import and call these helpers from routers or services when recording domain-specific metrics.
5. Start the service normally and hit the metrics endpoint to verify collection:
	```
	uvicorn main:app --reload
	# then browse http://localhost:8000/api/v1/metrics (or your custom METRICS_ENDPOINT)
	```
	Make sure your Prometheus server scrapes this same metrics endpoint (default `/api/v1/metrics` on the app host/port) in its scrape config.

### Example To See Metrics in Grafana

Import the following json in Grafana Dashboard to see the metrics

```json
{
  "dashboard": {
    "title": "Translation API Monitoring",
    "tags": ["microservices", "translation", "api"],
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "Translation Requests per Second",
        "type": "graph",
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
        "targets": [
          {
            "expr": "rate(translation_requests_total[5m])",
            "legendFormat": "{{status}} - {{target_language}}"
          }
        ]
      },
      {
        "id": 2,
        "title": "Success Rate",
        "type": "gauge",
        "gridPos": {"h": 8, "w": 6, "x": 12, "y": 0},
        "targets": [
          {
            "expr": "sum(rate(translation_requests_total{status=\"success\"}[5m])) / sum(rate(translation_requests_total[5m])) * 100"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "percent",
            "min": 0,
            "max": 100,
            "thresholds": {
              "steps": [
                {"value": 0, "color": "red"},
                {"value": 90, "color": "yellow"},
                {"value": 99, "color": "green"}
              ]
            }
          }
        }
      },
      {
        "id": 3,
        "title": "P95 Translation Latency",
        "type": "graph",
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8},
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(translation_duration_seconds_bucket[5m]))",
            "legendFormat": "{{target_language}}"
          }
        ],
        "yaxes": [
          {"format": "s", "label": "Latency"}
        ]
      },
      {
        "id": 4,
        "title": "Token Consumption Rate",
        "type": "graph",
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8},
        "targets": [
          {
            "expr": "rate(llm_tokens_used_total[5m])",
            "legendFormat": "{{model_name}} - {{token_type}}"
          }
        ]
      },
      {
        "id": 5,
        "title": "Active Database Connections",
        "type": "stat",
        "gridPos": {"h": 4, "w": 6, "x": 0, "y": 16},
        "targets": [
          {
            "expr": "database_connections_active"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "thresholds": {
              "steps": [
                {"value": 0, "color": "green"},
                {"value": 8, "color": "yellow"},
                {"value": 15, "color": "red"}
              ]
            }
          }
        }
      },
      {
        "id": 6,
        "title": "Error Rate",
        "type": "graph",
        "gridPos": {"h": 8, "w": 12, "x": 6, "y": 16},
        "targets": [
          {
            "expr": "rate(application_errors_total[5m])",
            "legendFormat": "{{error_type}} - {{endpoint}}"
          }
        ]
      },
      {
        "id": 7,
        "title": "HTTP Request Duration (P50, P95, P99)",
        "type": "graph",
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 24},
        "targets": [
          {
            "expr": "histogram_quantile(0.50, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "P50"
          },
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "P95"
          },
          {
            "expr": "histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "P99"
          }
        ]
      },
      {
        "id": 8,
        "title": "Total Requests by Status Code",
        "type": "piechart",
        "gridPos": {"h": 8, "w": 6, "x": 12, "y": 24},
        "targets": [
          {
            "expr": "sum by (status_code) (http_requests_total)",
            "legendFormat": "{{status_code}}"
          }
        ]
      }
    ],
    "refresh": "10s",
    "time": {
      "from": "now-1h",
      "to": "now"
    }
  }
}
```

### Grafana datasource configuration for auto-provisioning Prometheus
This file automatically configures Prometheus as a datasource when Grafana starts

```
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
    jsonData:
      timeInterval: "15s"
      queryTimeout: "60s"
      httpMethod: POST
```


## Docker

### Build the image

```
docker image build -t <tag> .
```

### Run the container

```
docker container run -i -t --rm -p 8000:8000 <tag>:latest
```

**Parameters:**
- `docker image build`: Docker command to build an image from a Dockerfile
- `-t <tag>`: Tag the image with a name (replace `<tag>` with your desired image name, e.g., `microserviceslab-languages`)
- `.`: The build context (current directory containing the Dockerfile)
- `docker container run`: Docker command to run a container from an image
- `-i`: Interactive mode - keeps STDIN open even if not attached
- `-t`: Allocate a pseudo-TTY - provides an interactive terminal
- `--rm`: Automatically remove the container when it exits
- `-p 8000:8000`: Port mapping - maps port 8000 on the host to port 8000 in the container (format: `host_port:container_port`)
- `<tag>:latest`: The image name and tag to run (replace `<tag>` with the same tag used when building the image)

## Database

**Connection string example**

```
mssql+pyodbc://<user>:<password>@localhost:1433/<db_name>?driver=SQL+Server&TrustServerCertificate=yes
```

## API Endpoints

- `GET /` — Root welcome message
- `GET /api/v1/health` — Health check endpoint
- `GET /api/v1/metrics` — Prometheus metrics endpoint
- Other endpoints under `/api/v1/translator` (see source for details)

## Environment Variables

- `METRICS_ENABLED` — Enable Prometheus metrics (`true` or `false`)
- `METRICS_ENDPOINT` — Path for metrics endpoint (default: `/api/v1/metrics`)

## Contributing & Testing

Contributions are welcome! Please ensure new endpoints follow the `/api/v1/...` pattern and use centralized metrics helpers from `monitoring/metrics.py`.