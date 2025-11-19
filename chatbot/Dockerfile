# Chatbot Service Dockerfile
FROM python:3.11-slim

WORKDIR /app

# TODO: Copy application code
COPY requirements.txt  .
# TODO: Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# copio el resto de la app
COPY . .
# TODO: Expose REST API port
EXPOSE 8080
# Run the chatbot service
CMD ["python", "app.py"]
