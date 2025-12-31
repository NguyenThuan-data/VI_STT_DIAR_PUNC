FROM pytorch/pytorch:2.1.0-cuda11.8-cudnn8-runtime

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --default-timeout=1000 -r requirements.txt

# Copy API code
COPY api.py .

# Note: ALL models are mounted as volumes at runtime (no need to download)
# - dia_seg: ./medical_api/models/dia_seg:/app/models/dia_seg
# - dia_embed: ./medical_api/models/dia_embed:/app/models/dia_embed
# - vi_offline: ./medical_api/models/vi_offline:/app/models/vi_offline

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["python", "api.py"]