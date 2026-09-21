FROM python:3.13-slim-bookworm

# Install Chromium for server-side PDF generation
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium \
    fonts-liberation \
    fonts-dejavu \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install backend Python dependencies
COPY Backend/requirements.txt ./Backend/requirements.txt
RUN pip install --no-cache-dir -r Backend/requirements.txt

# Copy the complete project because Backend imports the root-level ai package
COPY . .

# Chromium used by report_service.py
ENV CHROME_BINARY=/usr/bin/chromium

# Start FastAPI from the Backend directory
CMD ["sh", "-c", "cd /app/Backend && PYTHONPATH=/app uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}"]