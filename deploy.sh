#!/bin/bash
set -e

PROJECT_ID=${GOOGLE_CLOUD_PROJECT:-"forgeminiliveagent"}
REGION=${REGION:-"us-central1"}
SERVICE_NAME="drishti"

# If GOOGLE_API_KEY is not set locally, pull from existing Cloud Run service
if [ -z "$GOOGLE_API_KEY" ]; then
    echo "GOOGLE_API_KEY not set locally, fetching from existing service..."
    GOOGLE_API_KEY=$(gcloud run services describe $SERVICE_NAME --region $REGION --project $PROJECT_ID --format='value(spec.template.spec.containers[0].env[0].value)' 2>/dev/null)
    if [ -z "$GOOGLE_API_KEY" ]; then
        echo "ERROR: Could not retrieve GOOGLE_API_KEY. Set it manually."
        exit 1
    fi
fi

echo "Deploying Drishti to Cloud Run..."
echo "  Project: $PROJECT_ID"
echo "  Region:  $REGION"

# Build and push container image
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME --project $PROJECT_ID

# Deploy to Cloud Run
gcloud run deploy $SERVICE_NAME \
    --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
    --platform managed \
    --region $REGION \
    --project $PROJECT_ID \
    --allow-unauthenticated \
    --set-env-vars="GOOGLE_API_KEY=$GOOGLE_API_KEY,DEFAULT_PLUGIN=blind_navigation" \
    --memory=512Mi \
    --cpu=1 \
    --timeout=300 \
    --min-instances=0 \
    --max-instances=3

echo ""
echo "Deployed!"
URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --project $PROJECT_ID --format='value(status.url)')
echo "URL: $URL"
