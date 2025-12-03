# Data Indexer Service Dockerfile
FROM python:3.11-slim

WORKDIR /app

# TODO: Copy application code
COPY . .

# TODO: Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set entrypoint to run the data indexer script
ENTRYPOINT ["python", "app.py"]
