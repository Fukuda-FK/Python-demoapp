FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including gettext for envsubst
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    gettext-base \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and New Relic config template
COPY . .
COPY newrelic.ini.template /app/newrelic.ini.template
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Expose port
EXPOSE 3000

# Set New Relic config file location
ENV NEW_RELIC_CONFIG_FILE=/app/newrelic.ini

# Run the application with New Relic via entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]
