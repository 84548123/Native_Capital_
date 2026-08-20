#!/bin/bash
set -e
echo "=== Deploying Native Capital to Google Cloud Run ==="

if ! command -v gcloud &> /dev/null; then
    echo "[ERROR] gcloud CLI not found. Please install Google Cloud SDK."
    exit 1
fi

gcloud services enable run.googleapis.com cloudbuild.googleapis.com containerregistry.googleapis.com

gcloud run deploy native-capital \
    --source . \
    --region us-central1 \
    --platform managed \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 1 \
    --port 8080

echo "=== Deployment Complete! ==="
