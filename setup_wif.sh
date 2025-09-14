#!/bin/bash

# Setup Workload Identity Federation for GitHub Actions
# This script sets up WIF to allow GitHub Actions to authenticate with GCP

set -e

PROJECT_ID="book-qc-cf"
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
GITHUB_REPO="kushagraagarwal/google-book-qc-cf"  # Update this with your actual GitHub repo
SERVICE_ACCOUNT="pdf-processor-sa@$PROJECT_ID.iam.gserviceaccount.com"
WORKLOAD_IDENTITY_POOL="github-actions-pool"
WORKLOAD_IDENTITY_PROVIDER="github-provider"

echo "🔐 Setting up Workload Identity Federation for GitHub Actions"
echo "Project ID: $PROJECT_ID"
echo "Project Number: $PROJECT_NUMBER"
echo "GitHub Repo: $GITHUB_REPO"
echo "Service Account: $SERVICE_ACCOUNT"
echo "=========================================="

# Enable required APIs
echo "🔧 Enabling required APIs..."
gcloud services enable iamcredentials.googleapis.com

# Create Workload Identity Pool
echo "🏊 Creating Workload Identity Pool..."
gcloud iam workload-identity-pools create $WORKLOAD_IDENTITY_POOL \
    --project=$PROJECT_ID \
    --location="global" \
    --display-name="GitHub Actions Pool"

# Get the pool ID
POOL_ID=$(gcloud iam workload-identity-pools describe $WORKLOAD_IDENTITY_POOL \
    --project=$PROJECT_ID \
    --location="global" \
    --format="value(name)")

echo "Pool ID: $POOL_ID"

# Create Workload Identity Provider
echo "🔑 Creating Workload Identity Provider..."
gcloud iam workload-identity-pools providers create-oidc $WORKLOAD_IDENTITY_PROVIDER \
    --project=$PROJECT_ID \
    --location="global" \
    --workload-identity-pool=$WORKLOAD_IDENTITY_POOL \
    --display-name="GitHub Provider" \
    --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
    --issuer-uri="https://token.actions.githubusercontent.com"

# Get the provider ID
PROVIDER_ID=$(gcloud iam workload-identity-pools providers describe $WORKLOAD_IDENTITY_PROVIDER \
    --project=$PROJECT_ID \
    --location="global" \
    --workload-identity-pool=$WORKLOAD_IDENTITY_POOL \
    --format="value(name)")

echo "Provider ID: $PROVIDER_ID"

# Allow GitHub Actions to impersonate the service account
echo "🔓 Granting GitHub Actions permission to impersonate service account..."
gcloud iam service-accounts add-iam-policy-binding $SERVICE_ACCOUNT \
    --project=$PROJECT_ID \
    --role="roles/iam.workloadIdentityUser" \
    --member="principalSet://iam.googleapis.com/$POOL_ID/attribute.repository/$GITHUB_REPO"

# Grant additional roles to the service account for Cloud Run deployment
echo "🔑 Granting additional roles to service account..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/iam.serviceAccountUser"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/cloudbuild.builds.builder"

echo ""
echo "✅ Workload Identity Federation setup completed!"
echo ""
echo "📋 Configuration for GitHub Actions:"
echo "  WORKLOAD_IDENTITY_PROVIDER: $PROVIDER_ID"
echo "  SERVICE_ACCOUNT: $SERVICE_ACCOUNT"
echo "  PROJECT_ID: $PROJECT_ID"
echo ""
echo "🔧 Next steps:"
echo "1. Add these secrets to your GitHub repository:"
echo "   - WORKLOAD_IDENTITY_PROVIDER: $PROVIDER_ID"
echo "   - SERVICE_ACCOUNT: $SERVICE_ACCOUNT"
echo "2. Push your code to trigger the GitHub Actions workflow"
echo ""
echo "🧪 Test the setup:"
echo "   git add ."
echo "   git commit -m 'Add WIF support'"
echo "   git push origin main"
