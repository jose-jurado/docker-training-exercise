# Chatbot Service Dockerfile
FROM python:3.11-slim

ENV LLM_URL=http://llm:8080

ENV ENCODER_URL=http://encoder:8001

ENV VECTOR_DB_URL=http://vector-db:6333

WORKDIR /app

# Copy application code
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose REST API port
EXPOSE 8080

# Run the chatbot service
ENTRYPOINT ["python", "app.py"]
