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
4. Use the centralized metric definitions in `monitoring/metrics.py` for custom counters/histograms (e.g., `record_translation_metrics`, `record_llm_metrics`, `record_database_metrics`). Import and call these helpers from routers or services when recording domain-specific metrics.
5. Start the service normally and hit the metrics endpoint to verify collection:
	```
	uvicorn main:app --reload
	# then browse http://localhost:8000/metrics (or your custom METRICS_ENDPOINT)
	```
	Make sure your Prometheus server scrapes this same metrics endpoint (default `/metrics` on the app host/port) in its scrape config.

## Docker

### Build the image

```
docker image build -t <tag> .
```

**Parameters:**
- `docker image build`: Docker command to build an image from a Dockerfile
- `-t <tag>`: Tag the image with a name (replace `<tag>` with your desired image name, e.g., `microserviceslab-languages`)
- `.`: The build context (current directory containing the Dockerfile)

### Run the container

```
docker container run -i -t --rm -p 8000:8000 <tag>:latest
```

**Parameters:**
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