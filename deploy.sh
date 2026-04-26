#!/bin/bash
# ─────────────────────────────────────────────────────────────
# RouteCare — Google Cloud Run Deployment Script
# ─────────────────────────────────────────────────────────────
# Usage:
#   chmod +x deploy.sh
#   ./deploy.sh
#
# Prerequisites:
#   1. Google Cloud SDK installed: https://cloud.google.com/sdk/docs/install
#   2. Run once: gcloud auth login
#   3. Set your GEMINI_API_KEY in this script OR use Secret Manager
# ─────────────────────────────────────────────────────────────

set -e   # Exit on any error

# ── CONFIGURE THESE ──────────────────────────────────────────
PROJECT_ID="your-gcp-project-id"       # ← CHANGE THIS
REGION="asia-south1"                    # Mumbai — closest to India
SERVICE_NAME="routecare"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"
GEMINI_API_KEY="${GEMINI_API_KEY:-your-gemini-api-key-here}"   # ← CHANGE THIS or export env var
# ─────────────────────────────────────────────────────────────

echo "🚑 RouteCare Cloud Run Deployment"
echo "   Project : ${PROJECT_ID}"
echo "   Region  : ${REGION}"
echo "   Service : ${SERVICE_NAME}"
echo ""

# Step 1: Set GCP project
echo "📋 Step 1: Setting GCP project..."
gcloud config set project "${PROJECT_ID}"

# Step 2: Enable required APIs
echo "🔌 Step 2: Enabling required APIs..."
gcloud services enable \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    secretmanager.googleapis.com \
    --quiet

# Step 3: Store Gemini API key in Secret Manager (more secure than env var)
echo "🔐 Step 3: Storing Gemini API key in Secret Manager..."
echo -n "${GEMINI_API_KEY}" | gcloud secrets create gemini-api-key \
    --data-file=- \
    --replication-policy="automatic" 2>/dev/null || \
echo -n "${GEMINI_API_KEY}" | gcloud secrets versions add gemini-api-key \
    --data-file=-
echo "   Secret stored: gemini-api-key"

# Step 4: Build and push container image
echo "🏗️  Step 4: Building container image..."
gcloud builds submit \
    --tag "${IMAGE_NAME}" \
    --timeout=300 \
    .
echo "   Image built: ${IMAGE_NAME}"

# Step 5: Deploy to Cloud Run
echo "🚀 Step 5: Deploying to Cloud Run..."
gcloud run deploy "${SERVICE_NAME}" \
    --image "${IMAGE_NAME}" \
    --region "${REGION}" \
    --platform managed \
    --allow-unauthenticated \
    --memory 512Mi \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 10 \
    --concurrency 80 \
    --timeout 60 \
    --set-secrets "GEMINI_API_KEY=gemini-api-key:latest" \
    --set-env-vars "FLASK_ENV=production" \
    --quiet

# Step 6: Get the deployed URL
echo ""
echo "✅ Deployment complete!"
SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" \
    --region "${REGION}" \
    --format="value(status.url)")
echo "   🌐 Live URL: ${SERVICE_URL}"
echo ""
echo "   Test Gemini: ${SERVICE_URL}/api/gemini_status"
echo "   Login page : ${SERVICE_URL}/login"
echo ""
echo "Demo credentials:"
echo "   Ambulance : AMB001 / pass123"
echo "   Hospital  : HSP001 / hosp123"
