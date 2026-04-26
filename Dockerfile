# ─────────────────────────────────────────────────────────────
# RouteCare — Dockerfile for Google Cloud Run
# ─────────────────────────────────────────────────────────────
# Build:  docker build -t routecare .
# Run:    docker run -p 8080:8080 -e GEMINI_API_KEY=your-key routecare
# Deploy: gcloud run deploy routecare --source .
# ─────────────────────────────────────────────────────────────

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory (SQLite DB will be created here at runtime)
RUN mkdir -p /app/data

# Cloud Run requires the app to listen on PORT env var (default 8080)
ENV PORT=8080
ENV FLASK_ENV=production

# Use Gunicorn for production (not Flask dev server)
# 2 workers × 2 threads = handles 4 concurrent requests on free tier
CMD exec gunicorn \
    --bind 0.0.0.0:$PORT \
    --workers 2 \
    --threads 2 \
    --timeout 60 \
    --access-logfile - \
    --error-logfile - \
    app:app
