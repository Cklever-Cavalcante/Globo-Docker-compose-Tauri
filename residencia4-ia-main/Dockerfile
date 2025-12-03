# Multi-stage build for IA Service
FROM python:3.10-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies (CPU-only versions for smaller image)
RUN pip install --no-cache-dir --user -r requirements.txt

# Final stage
FROM python:3.10-slim

WORKDIR /app

# Install runtime dependencies for ML, FFmpeg, and OpenCV
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsm6 \
    libxext6 \
    libglib2.0-0 \
    libgomp1 \
    libgl1 \
    libxrender-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 appuser

# Copy Python packages from builder to appuser's home
COPY --from=builder --chown=appuser:appuser /root/.local /home/appuser/.local

# Make sure scripts in .local are usable
ENV PATH=/home/appuser/.local/bin:$PATH

# Copy YOLO model first (better caching if code changes)
COPY --chown=appuser:appuser yolov8n.pt .

# Copy application code
COPY --chown=appuser:appuser . .

# Create temp directory and ensure ownership
RUN mkdir -p temp_videos_ia && \
    chown -R appuser:appuser /app

# Expose port
EXPOSE 8001

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8001/ || exit 1

# Switch to non-root user
USER appuser

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]