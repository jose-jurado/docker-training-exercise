# Data Indexer Service Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy application code
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set entrypoint to run the data indexer script
ENTRYPOINT ["python", "app.py"]
