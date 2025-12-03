# Chatbot Service Dockerfile
FROM python:3.11-slim

ENV LLM_URL=http://llm:8080

ENV ENCODER_URL=http://encoder:8001

ENV VECTOR_DB_URL=http://vector-db:6333

WORKDIR /app

# TODO: Copy application code
COPY . .

# TODO: Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# TODO: Expose REST API port
EXPOSE 8080

# Run the chatbot service
CMD ["python", "app.py"]
