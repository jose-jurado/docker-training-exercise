# UI Service Dockerfile
FROM node:18-alpine

WORKDIR /app

# Copy application code

COPY . .

# Install dependencies
RUN npm install

# Expose web server port
EXPOSE 3000

# Run the UI application
CMD ["npm", "start"]
