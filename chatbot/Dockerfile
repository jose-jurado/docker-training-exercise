# Chatbot Service Dockerfile
FROM python:3.11-slim

WORKDIR /app

# TODO: Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# TODO: Copy application code
COPY . . 

# TODO: Expose REST API port
EXPOSE 8080

# Run the chatbot service
# Esto garantiza que tu app 'app' (definida en app.py) se ejecute en el host 0.0.0.0 y puerto 8080.
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
#CMD ["python", "app.py"]
