#!/bin/bash

# GCP Resource Setup Script for PDF Processing Microservice
# Run this script after enabling billing for the project

set -e

PROJECT_ID="book-qc-cf"
REGION="us-central1"
BUCKET_NAME="book-qc-cf-pdf-storage"
SERVICE_ACCOUNT_NAME="pdf-processor-sa"
REPOSITORY_NAME="pdf-processor"

echo "🚀 Setting up GCP resources for PDF Processing Microservice"
echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"
echo "Bucket: $BUCKET_NAME"
echo "=========================================="

# Set the project
echo "📋 Setting project..."
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "🔧 Enabling required APIs..."
gcloud services enable run.googleapis.com
gcloud services enable workflows.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable artifactregistry.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable workflowexecutions.googleapis.com

# Create GCS bucket
echo "🪣 Creating GCS bucket..."
gsutil mb gs://$BUCKET_NAME

# Create Artifact Registry repository
echo "📦 Creating Artifact Registry repository..."
gcloud artifacts repositories create $REPOSITORY_NAME \
    --repository-format=docker \
    --location=$REGION \
    --description="Docker repository for PDF processing microservice"

# Create service account
echo "🔐 Creating service account..."
gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME \
    --display-name="PDF Processor Service Account" \
    --description="Service account for PDF processing microservice"

# Grant required roles to service account
echo "🔑 Granting permissions to service account..."
SERVICE_ACCOUNT_EMAIL="$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/run.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/storage.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/workflows.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/artifactregistry.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/cloudbuild.builds.builder"

# Create service account key
echo "🔑 Creating service account key..."
gcloud iam service-accounts keys create pdf-processor-sa-key.json \
    --iam-account=$SERVICE_ACCOUNT_EMAIL

# Configure Docker authentication
echo "🐳 Configuring Docker authentication..."
gcloud auth configure-docker $REGION-docker.pkg.dev

echo ""
echo "✅ GCP resources setup completed successfully!"
echo ""
echo "📋 Summary:"
echo "  Project ID: $PROJECT_ID"
echo "  Region: $REGION"
echo "  Bucket: gs://$BUCKET_NAME"
echo "  Artifact Registry: $REGION-docker.pkg.dev/$PROJECT_ID/$REPOSITORY_NAME"
echo "  Service Account: $SERVICE_ACCOUNT_EMAIL"
echo "  Service Account Key: pdf-processor-sa-key.json"
echo ""
echo "🔑 Next steps:"
echo "1. Add the service account key (pdf-processor-sa-key.json) as GCP_SA_KEY secret in GitHub"
echo "2. Push your code to trigger the GitHub Actions deployment"
echo "3. Or run manual deployment:"
echo "   python deploy.py --project-id $PROJECT_ID --image-uri $REGION-docker.pkg.dev/$PROJECT_ID/$REPOSITORY_NAME/pdf-processor:latest --bucket-name $BUCKET_NAME"
echo ""
echo "🧪 Test the deployment:"
echo "   python test_service.py https://your-service-url.run.app"
