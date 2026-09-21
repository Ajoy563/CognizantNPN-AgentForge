FROM python:3.13-slim

# Install Chromium and required system dependencies
RUN apt-get update && apt-get install -y \
    chromium \
    fonts-liberation \
    fonts-dejavu \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY . .

# Chromium location used by report_service.py
ENV CHROME_BINARY=/usr/bin/chromium

# Start FastAPI
CMD ["sh", "-c", "PYTHONPATH=/app/.. uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}"]