# Use the Base Image (Includes Python, PyTorch, CUDA) -> reduce time from heavy files download
FROM pytorch/pytorch:2.2.1-cuda12.1-cudnn8-runtime

# Install System Tools
# 'netcat' is required for the start script to check if the API is ready
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    curl \
    netcat-openbsd \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 1. Install Dependencies (Using the consolidated requirements.txt)
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip && \
    pip install --no-cache-dir --default-timeout=1000 -r requirements.txt

# 2. Copy the entire project structure
# This copies 'medical_api', 'vibert_pipeline', and everything else
COPY . .

# 3. Pre-download Vibert models (Optional but recommended)
# We try to run the setup script during build to save time later
RUN python vibert_pipeline/1_setup_models.py || echo "Vibert setup skipped during build"

# 4. Make the start script executable
RUN chmod +x start_services.sh

# 5. Create necessary data folders
RUN mkdir -p /app/models \
    /app/saved_transcripts \
    /app/processing_workspace \
    /app/vibert_cache

# 6. Expose Ports (8000 for API, 7860 for UI)
EXPOSE 8000
EXPOSE 7860

# 7. Start Command
CMD ["/bin/bash","./start_services.sh"]