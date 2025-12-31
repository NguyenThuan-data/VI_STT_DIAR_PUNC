#!/bin/bash

# 1. Start the ASR API (Background Process)
echo "Starting Medical ASR API..."
# We use 'medical_api.api:app' because the file is inside the folder
uvicorn medical_api.api:app --host 0.0.0.0 --port 8000 &

# 2. Wait for the API to wake up
echo "Waiting for API to launch on port 8000..."
while ! nc -z localhost 8000; do   
  sleep 1
done
echo "API is ready!"

# 3. Start the Gradio Interface (Foreground Process)
echo "Starting Gradio Pipeline..."
python vibert_pipeline/2_asr_pipeline.py 

