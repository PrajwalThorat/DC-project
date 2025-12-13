# Build stage
FROM python:3.9-slim as builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --user --no-cache-dir -r requirements.txt

# Final stage
FROM python:3.9-slim

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    curl \
    bash \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Copy application files
COPY app.py .
COPY init-db.sh .
COPY templates/ ./templates/
COPY static/ ./static/

# Create data directory
RUN mkdir -p data

# Make init script executable
RUN chmod +x /app/init-db.sh

# Default port
EXPOSE 5000

# Run database initialization on startup
RUN /app/init-db.sh || true

# Default command (can be overridden)
CMD ["python", "app.py"]
