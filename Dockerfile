FROM python:3.11-slim

# Install system dependencies and Android platform tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    android-tools-adb \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy application source
COPY . /app

# Expose AirADB web port
EXPOSE 8765

# Launch AirADB server
CMD ["python", "server.py", "--port", "8765", "--no-browser"]
