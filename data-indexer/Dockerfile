# Data Indexer Service Dockerfile
FROM python:3.11-slim

WORKDIR /app

# TODO: Copy application code
COPY requirements.txt .
# TODO: Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

COPY . . 

# Set entrypoint to run the data indexer script
ENTRYPOINT ["python", "app.py" ]
