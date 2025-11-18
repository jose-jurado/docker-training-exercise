# UI Service Dockerfile
FROM node:18-alpine

WORKDIR /app

# TODO: Copy application code
COPY package*.json ./


# TODO: Install dependencies
RUN npm install
COPY . .
# TODO: Expose web server port
EXPOSE 3000

# Run the UI application
CMD ["npm", "start"]
