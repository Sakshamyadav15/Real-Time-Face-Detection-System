FROM python:3.12-slim AS base

# Install system dependencies for Pillow and MediaPipe
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY alembic.ini .
COPY alembic/ ./alembic/
COPY app/ ./app/

# Run Alembic migrations and start server
CMD alembic upgrade head && \
    uvicorn app.main:app --host 0.0.0.0 --port 8000
