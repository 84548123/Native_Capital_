# ============================================================
# Google Cloud Platform (GCP) Cloud Run Deployment Script
# ============================================================
Write-Host "=== Deploying Native Capital to Google Cloud Run ===" -ForegroundColor Cyan

if (-not (Get-Command gcloud -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] gcloud CLI not found. Please install the Google Cloud SDK:" -ForegroundColor Red
    Write-Host "https://cloud.google.com/sdk/docs/install" -ForegroundColor Yellow
    exit 1
}

 = Read-Host "Enter your GCP Project ID (or press Enter to use current active project)"
if () {
    gcloud config set project 
}

Write-Host "Enabling Cloud Run and Cloud Build services..." -ForegroundColor Cyan
gcloud services enable run.googleapis.com cloudbuild.googleapis.com containerregistry.googleapis.com

Write-Host "Submitting build and deploying to Cloud Run..." -ForegroundColor Cyan
gcloud run deploy native-capital 
    --source . 
    --region us-central1 
    --platform managed 
    --allow-unauthenticated 
    --memory 2Gi 
    --cpu 1 
    --port 8080

Write-Host "=== Deployment Successful! ===" -ForegroundColor Green
