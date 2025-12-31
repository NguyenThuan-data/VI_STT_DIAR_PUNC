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


# Copy setup script and download Vibert models

COPY 1_setup_models.py .

RUN python 1_setup_models.py || echo "Vibert setup will continue at runtime"


# Copy pipeline application

COPY 2_asr_pipeline.py .


# Create cache directory

RUN mkdir -p /app/vibert_cache


EXPOSE 7860


ENV GRADIO_SERVER_NAME=0.0.0.0

ENV GRADIO_SERVER_PORT=7860


CMD ["python", "2_asr_pipeline.py"]
