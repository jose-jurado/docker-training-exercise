# Chatbot Service Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy application code
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose REST API port
EXPOSE 8080

# Run the chatbot service
ENTRYPOINT ["python", "app.py"]
