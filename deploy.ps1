$GCLOUD="C:\Users\DELL\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd"
$PROJECT_ID = & $GCLOUD config get-value project

Write-Host "Using Project ID: $PROJECT_ID"

# 2. Enable Required APIs
Write-Host "Enabling GCP APIs..."
& $GCLOUD services enable run.googleapis.com aiplatform.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com

# 3. Create Artifact Registry Repository (if not exists)
Write-Host "Creating Artifact Registry repository..."
& $GCLOUD artifacts repositories create gemini-storyteller-repo --repository-format=docker --location=us-central1 --description="Docker repository for Gemini Storyteller" 2>$null

# 4. Create Service Account (if not exists)
Write-Host "Setting up Service Account..."
$SA_EMAIL = "storyteller-sa@$PROJECT_ID.iam.gserviceaccount.com"
$SA_EXISTS = & $GCLOUD iam service-accounts list --filter="email:$SA_EMAIL" --format="value(email)"
if (-not $SA_EXISTS) {
    & $GCLOUD iam service-accounts create storyteller-sa --display-name="Gemini Storyteller Service Account"
}

# 5. Grant IAM Roles
Write-Host "Granting IAM roles to Service Account..."
& $GCLOUD projects add-iam-policy-binding $PROJECT_ID --member="serviceAccount:$SA_EMAIL" --role="roles/aiplatform.user"
& $GCLOUD projects add-iam-policy-binding $PROJECT_ID --member="serviceAccount:$SA_EMAIL" --role="roles/ml.developer"

# 6. Submit Build to Cloud Build
Write-Host "Submitting build to Cloud Build..."
$SHORT_SHA = "latest"
try {
    $GIT_SHA = git rev-parse --short HEAD 2>$null
    if ($GIT_SHA) { $SHORT_SHA = $GIT_SHA }
} catch {
    $SHORT_SHA = "latest"
}

& $GCLOUD builds submit --config cloudbuild.yaml . --substitutions=_SHORT_SHA=$SHORT_SHA

# 7. Grant Public Access
Write-Host "Granting Public Access (unauthenticated)..."
& $GCLOUD run services add-iam-policy-binding gemini-storyteller --member="allUsers" --role="roles/run.invoker" --region=us-central1
