FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1

WORKDIR /app

# System dependencies for pyodbc and SSL certs
RUN apt-get update \
	&& DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
		build-essential \
		libodbc1 \
		unixodbc \
		unixodbc-dev \
		ca-certificates \
		curl \
	&& rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip \
	&& pip install --no-cache-dir -r requirements.txt

COPY . .

# Create non-root user for runtime
RUN useradd --create-home appuser \
	&& chown -R appuser /app
USER appuser

EXPOSE 8000
CMD ["uvicorn","main:app", "--host", "0.0.0.0", "--port", "8000"]