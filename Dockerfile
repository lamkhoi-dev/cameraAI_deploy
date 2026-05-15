FROM nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04

LABEL maintainer="Camera AI Team"
LABEL description="Camera Tracking AI Engine - Tesla P4 Optimized"
LABEL version="1.0-phase1"

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.10 \
    python3-pip \
    python3-dev \
    build-essential \
    git \
    wget \
    curl \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libglib2.0-0 \
    libtbb2 \
    libtbb-dev \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libdc1394-dev \
    libharfbuzz0b \
    libwebp7 \
    tesseract-ocr \
    libtesseract-dev \
    libgl1 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create app directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
# ⚠️ CRITICAL: Pin PyTorch 2.7 for Tesla P4 (Pascal GPU) compatibility
# CUDA 12.4 is the last version supporting Pascal GPUs
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Install PyTorch for CUDA 12.4 (last version supporting Tesla P4/Pascal)
RUN pip install --no-cache-dir --timeout=300 --retries=5 \
    torch==2.6.0 torchvision==0.21.0 \
    --index-url https://download.pytorch.org/whl/cu124 \
    && pip install --no-cache-dir --timeout=300 --retries=5 -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p ai_engine/models cropped_data/persons cropped_data/vehicles cropped_data/fire_alerts

# Verify installation
RUN python3 -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA: {torch.version.cuda}'); print(f'GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"None\"}')"

# Health check script
RUN echo '#!/bin/bash\n\
import sys\n\
try:\n\
    import torch\n\
    from ultralytics import YOLO\n\
    from paddleocr import PaddleOCR\n\
    print("All imports OK")\n\
    sys.exit(0)\n\
except Exception as e:\n\
    print(f"Import error: {e}")\n\
    sys.exit(1)\n\
' > /app/healthcheck.py

# Set default command — production multi-camera entry point
CMD ["python3", "run_engine.py"]

# Build instructions:
# docker build -t camera-ai:latest .
# docker build -t camera-ai:v1.0 .
#
# Run instructions (with GPU):
# docker run --gpus all --rm -v /data:/app/cropped_data -e VIDEO_SOURCE='rtsp://localhost:8554/cam_01' camera-ai:latest
# docker run --gpus device=0 --rm -e BACKEND_API_URL='http://localhost:8000' camera-ai:latest
#
# Run with environment file:
# docker run --gpus all --rm --env-file .env camera-ai:latest
#
# Docker compose (production):
# See: docker-compose.yml
