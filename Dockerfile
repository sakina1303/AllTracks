cat > Dockerfile << 'EOF'
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies for OpenCV
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY api_track_c.py .
COPY track_c_final.h5 .

# Cloud Run sets PORT environment variable
ENV PORT=8888
EXPOSE 8888

# Run the application
CMD ["uvicorn", "api_track_c:app", "--host", "0.0.0.0", "--port", "8888"]
EOF
