FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy Locust configuration
COPY locustfile.py .
COPY users.list .

# Expose ports
# 8089 for web UI
# 5557 for master communication
# 5558 for worker communication
EXPOSE 8089 5557 5558

# Default command runs Locust
# Can be overridden to run as master or worker
CMD ["locust", "-f", "locustfile.py", "--host", "http://localhost"]
