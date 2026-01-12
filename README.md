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
	METRICS_ENDPOINT=/metrics
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
	# then browse http://localhost:8000/metrics (or your custom METRICS_ENDPOINT)
	```
	Make sure your Prometheus server scrapes this same metrics endpoint (default `/metrics` on the app host/port) in its scrape config.

### Example To See Metrics in Grafana

Import the following json in Grafana Dashboard to see the metrics

```json
{
  "__inputs": [],
  "__requires": [],
  "annotations": {
    "list": []
  },
  "editable": true,
  "gnetId": null,
  "graphTooltip": 0,
  "id": null,
  "links": [],
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
    "schemaVersion": 27,
    "style": "dark",
    "tags": ["microservices", "translation", "api"],
    "templating": {
      "list": []
    },
    "time": {
      "from": "now-1h",
      "to": "now"
    },
    "timepicker": {},
    "timezone": "browser",
    "title": "Translation API Monitoring",
    "uid": null,
    "version": 0
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

The Docker image installs `unixodbc`/`unixodbc-dev` so `pyodbc` can connect, and runs as an unprivileged user. If you need the Microsoft SQL Server ODBC driver inside the image, add the Microsoft repository and install `msodbcsql18` during the build (see Appendix for host instructions).

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

For Database Migrations read: `alembic/README.md` file.

## API Endpoints

- `GET /` — Root welcome message
- `GET /api/v1/health` — Health check endpoint
- `GET /api/v1/metrics` — Prometheus metrics endpoint (requires router, default endpoint is `/metrics`)
- `POST /api/v1/translator/translate` — Translation endpoint (translates text between languages)

## Environment Variables

- `METRICS_ENABLED` — Enable Prometheus metrics (`true` or `false`, default: `true`)
- `METRICS_ENDPOINT` — Path for metrics endpoint (default: `/metrics`)
- `LOG_LEVEL` — Logging level (e.g., `INFO`, `DEBUG`; default: `INFO`)
- `CORS_ALLOW_ORIGINS` — Comma-separated list of allowed origins for CORS (default: `*`)

## About This Project

This is a personal learning lab project created for educational purposes. While I'm not accepting pull requests or contributions at this time, you are absolutely welcome to:

- **View** the code and explore the implementation
- **Comment** with suggestions, questions, or feedback
- **Fork** the repository for your own learning and experimentation

Feel free to use this project as a reference or starting point for your own microservices journey. If you have questions or ideas, I'd be happy to discuss them in the issues section!

---

## Appendix: Installing Microsoft ODBC Driver 18 for SQL Server on Kubuntu 25.10

This guide provides step-by-step instructions for installing the Microsoft ODBC Driver 18 for SQL Server on Kubuntu 25.10.

## Prerequisites

- Kubuntu 25.10 (officially supported)
- Terminal access with sudo privileges
- Internet connection

## Installation Steps

### 1. Download and Install Microsoft Repository Configuration

Download the package to configure the Microsoft repository:

```bash
curl -sSL -O https://packages.microsoft.com/config/ubuntu/25.10/packages-microsoft-prod.deb
```

Install the repository configuration package:

```bash
sudo dpkg -i packages-microsoft-prod.deb
```

Clean up the downloaded file:

```bash
rm packages-microsoft-prod.deb
```

### 2. Update Package Lists

Update your system's package lists:

```bash
sudo apt-get update
```

### 3. Install MSSQL ODBC Driver 18

Install the ODBC driver (accepting the EULA automatically):

```bash
sudo ACCEPT_EULA=Y apt-get install -y msodbcsql18
```

### 4. Optional: Install SQL Server Command-Line Tools

If you need `bcp` and `sqlcmd` utilities:

```bash
sudo ACCEPT_EULA=Y apt-get install -y mssql-tools18
```

Add the tools to your PATH:

```bash
echo 'export PATH="$PATH:/opt/mssql-tools18/bin"' >> ~/.bashrc
source ~/.bashrc
```

### 5. Optional: Install unixODBC Development Headers

For development purposes:

```bash
sudo apt-get install -y unixodbc-dev
```

## Verification

To verify the installation was successful, check the installed ODBC drivers:

```bash
odbcinst -q -d
```

You should see "ODBC Driver 18 for SQL Server" in the output.

## Troubleshooting

### Error: Malformed line in source list

If you encounter an error like:
```
E: Malformed line 1 in source list /etc/apt/sources.list.d/mssql-release.list (type)
```

Remove the malformed file and reinstall the repository configuration:

```bash
sudo rm /etc/apt/sources.list.d/mssql-release.list
curl -sSL -O https://packages.microsoft.com/config/ubuntu/25.10/packages-microsoft-prod.deb
sudo dpkg -i packages-microsoft-prod.deb
rm packages-microsoft-prod.deb
sudo apt-get update
```

### Alternative EULA Acceptance Method

Instead of using the `ACCEPT_EULA=Y` environment variable, you can set the debconf variable:

```bash
echo msodbcsql18 msodbcsql/ACCEPT_EULA boolean true | sudo debconf-set-selections
sudo apt-get install -y msodbcsql18
```

## Additional Resources

- [Official Microsoft Documentation](https://learn.microsoft.com/en-us/sql/connect/odbc/linux-mac/installing-the-microsoft-odbc-driver-for-sql-server)
- [ODBC Driver Release Notes](https://learn.microsoft.com/en-us/sql/connect/odbc/linux-mac/release-notes-odbc-sql-server-linux-mac)

## License

The Microsoft ODBC Driver for SQL Server is subject to Microsoft's End-User License Agreement (EULA). By installing this software, you accept the terms of the EULA.
