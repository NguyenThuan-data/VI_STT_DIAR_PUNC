#!/bin/bash

echo "================================================"
echo "Medical ASR System - Starting API Service"
echo "================================================"

# Start the FastAPI service (foreground)
echo "Starting Medical ASR API on port 8000..."
echo "Frontend will be served by Nginx on port 443"
echo ""

# Run uvicorn in foreground (keeps container alive)
uvicorn medical_api.api:app --host 0.0.0.0 --port 8000

