#!/bin/bash

# Exit on error
set -e

# 1. Get Project ID
PROJECT_ID=$(gcloud config get-value project)
echo "Using Project ID: $PROJECT_ID"

# 2. Enable Required APIs
echo "Enabling GCP APIs..."
gcloud services enable \
    run.googleapis.com \
    aiplatform.googleapis.com \
    cloudbuild.googleapis.com \
    artifactregistry.googleapis.com

# 3. Create Artifact Registry Repository (if not exists)
echo "Creating Artifact Registry repository..."
gcloud artifacts repositories create gemini-storyteller-repo \
    --repository-format=docker \
    --location=us-central1 \
    --description="Docker repository for Gemini Storyteller" || true

# 4. Create Service Account (if not exists)
echo "Setting up Service Account..."
if ! gcloud iam service-accounts describe storyteller-sa@$PROJECT_ID.iam.gserviceaccount.com > /dev/null 2>&1; then
    gcloud iam service-accounts create storyteller-sa \
        --display-name="Gemini Storyteller Service Account"
fi

# 5. Grant IAM Roles
echo "Granting IAM roles to Service Account..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:storyteller-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:storyteller-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/ml.developer"

# 6. Submit Build to Cloud Build
echo "Submitting build to Cloud Build..."
gcloud builds submit --config cloudbuild.yaml .

# 7. Get the Service URL
SERVICE_URL=$(gcloud run services describe gemini-storyteller --region=us-central1 --format='value(status.url)')

echo "--------------------------------------------------"
echo "Deployment Complete!"
echo "Service URL: $SERVICE_URL"
echo "--------------------------------------------------"

# 8. Run a quick health check
echo "Running health check..."
curl -s "$SERVICE_URL/health"
echo -e "\n--------------------------------------------------"
