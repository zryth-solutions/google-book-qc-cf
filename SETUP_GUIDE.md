# PDF Processing Microservice - Setup Guide

## 🚀 Quick Setup

Your GCP project `book-qc-cf` has been created and all configuration files have been updated with the correct project details.

### Current Status
- ✅ GCP Project: `book-qc-cf` (created)
- ✅ Configuration files updated
- ⚠️ Billing required for full setup

## 📋 Prerequisites

1. **Enable Billing** (Required)
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Select project `book-qc-cf`
   - Go to Billing → Link a billing account
   - Enable billing for the project

2. **Required Tools**
   - Google Cloud SDK (`gcloud`)
   - Docker
   - Python 3.11+

## 🔧 Complete Setup (After Billing is Enabled)

### Option 1: Automated Setup (Recommended)

Run the automated setup script:

```bash
./setup_gcp_resources.sh
```

This script will:
- Enable all required APIs
- Create GCS bucket: `book-qc-cf-pdf-storage`
- Create Artifact Registry repository
- Create service account with proper permissions
- Generate service account key

### Option 2: Manual Setup

If you prefer to run commands manually:

```bash
# Set project
gcloud config set project book-qc-cf

# Enable APIs
gcloud services enable run.googleapis.com workflows.googleapis.com storage.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com

# Create bucket
gsutil mb gs://book-qc-cf-pdf-storage

# Create Artifact Registry
gcloud artifacts repositories create pdf-processor \
    --repository-format=docker \
    --location=us-central1

# Create service account
gcloud iam service-accounts create pdf-processor-sa \
    --display-name="PDF Processor Service Account"

# Grant permissions
SERVICE_ACCOUNT_EMAIL="pdf-processor-sa@book-qc-cf.iam.gserviceaccount.com"

gcloud projects add-iam-policy-binding book-qc-cf \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/run.admin"

gcloud projects add-iam-policy-binding book-qc-cf \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/storage.admin"

gcloud projects add-iam-policy-binding book-qc-cf \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/workflows.admin"

gcloud projects add-iam-policy-binding book-qc-cf \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/artifactregistry.admin"

# Create service account key
gcloud iam service-accounts keys create pdf-processor-sa-key.json \
    --iam-account=$SERVICE_ACCOUNT_EMAIL
```

## 🚀 Deployment

### Option 1: GitHub Actions (Recommended)

1. **Add GitHub Secrets**:
   - Go to your GitHub repository → Settings → Secrets and variables → Actions
   - Add these secrets:
     - `GCP_SA_KEY`: Contents of `pdf-processor-sa-key.json`
     - `BUCKET_NAME`: `book-qc-cf-pdf-storage`

2. **Push to main branch**:
   ```bash
   git add .
   git commit -m "Initial commit with GCP project setup"
   git push origin main
   ```

### Option 2: Manual Deployment

```bash
# Build and push Docker image
docker build -t us-central1-docker.pkg.dev/book-qc-cf/pdf-processor/pdf-processor:latest .
docker push us-central1-docker.pkg.dev/book-qc-cf/pdf-processor/pdf-processor:latest

# Deploy to Cloud Run
python deploy.py \
    --project-id book-qc-cf \
    --image-uri us-central1-docker.pkg.dev/book-qc-cf/pdf-processor/pdf-processor:latest \
    --bucket-name book-qc-cf-pdf-storage
```

## 🧪 Testing

Once deployed, test the service:

```bash
# Test with the deployed service URL
python test_service.py https://pdf-processor-xxx.run.app

# Or test locally
python split_pdf/main.py
```

## 📊 Project Configuration Summary

| Component | Value |
|-----------|-------|
| Project ID | `book-qc-cf` |
| Region | `us-central1` |
| GCS Bucket | `book-qc-cf-pdf-storage` |
| Artifact Registry | `us-central1-docker.pkg.dev/book-qc-cf/pdf-processor/` |
| Service Account | `pdf-processor-sa@book-qc-cf.iam.gserviceaccount.com` |
| Cloud Run Service | `pdf-processor` |
| Workflow | `pdf-processing-workflow` |

## 🔍 Verification

After setup, verify everything is working:

```bash
# Check project
gcloud config get-value project

# Check bucket
gsutil ls gs://book-qc-cf-pdf-storage

# Check Artifact Registry
gcloud artifacts repositories list --location=us-central1

# Check service account
gcloud iam service-accounts list --filter="email:pdf-processor-sa@book-qc-cf.iam.gserviceaccount.com"

# Check Cloud Run service (after deployment)
gcloud run services list --region=us-central1
```

## 🆘 Troubleshooting

### Common Issues

1. **Billing not enabled**: Enable billing in Google Cloud Console
2. **Permission denied**: Ensure service account has proper roles
3. **API not enabled**: Run the API enablement commands
4. **Docker push fails**: Configure Docker authentication with `gcloud auth configure-docker us-central1-docker.pkg.dev`

### Getting Help

- Check Cloud Run logs: `gcloud logging read "resource.type=cloud_run_revision"`
- Check Workflow logs: `gcloud logging read "resource.type=workflow_execution"`
- View service status: `gcloud run services describe pdf-processor --region=us-central1`

## 📝 Next Steps

1. Enable billing for the project
2. Run `./setup_gcp_resources.sh`
3. Add GitHub secrets
4. Push code to trigger deployment
5. Test the service

Your PDF processing microservice will be ready to analyze and split PDFs at scale! 🎉
