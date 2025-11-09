FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (curl for healthcheck)
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create models directory and make startup script executable
RUN mkdir -p /app/models && \
    chmod +x start.sh

# Expose port
EXPOSE 3000

# Run the application via startup script
CMD ["/bin/bash", "start.sh"]

