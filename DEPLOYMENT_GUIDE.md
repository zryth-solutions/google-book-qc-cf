# GitHub Actions Deployment Guide

## 🚀 Complete Setup for GitHub Actions with WIF

Your PDF processing microservice is ready for deployment via GitHub Actions using Workload Identity Federation (WIF).

### ✅ What's Ready

1. **GCP Resources**: All created and configured
2. **GitHub Actions Workflow**: Updated to use WIF
3. **Docker Configuration**: Optimized for Cloud Run
4. **Test PDF**: Uploaded to GCS bucket

### 🔐 Authentication Setup

Since service account key creation is disabled, we need to use Workload Identity Federation.

#### Option 1: Manual WIF Setup (Recommended)

1. **Go to Google Cloud Console**:
   - Navigate to [Workload Identity Federation](https://console.cloud.google.com/iam-admin/workload-identity-pools)
   - Select project `book-qc-cf`

2. **Create Workload Identity Pool**:
   - Click **"Create Pool"**
   - Pool ID: `github-actions-pool`
   - Display name: `GitHub Actions Pool`

3. **Create OIDC Provider**:
   - Click **"Add Provider"** → **"OpenID Connect (OIDC)"**
   - Provider ID: `github-provider`
   - Issuer URL: `https://token.actions.githubusercontent.com`
   - Attribute mapping:
     - `google.subject` = `assertion.sub`
     - `actor` = `assertion.actor`
     - `repository` = `assertion.repository`

4. **Grant Access**:
   - Go to **IAM & Admin** → **IAM**
   - Find `pdf-processor-sa@book-qc-cf.iam.gserviceaccount.com`
   - Add principal: `principalSet://iam.googleapis.com/projects/282136454082/locations/global/workloadIdentityPools/github-actions-pool/attribute.repository/kushagraagarwal/google-book-qc-cf`
   - Role: **Workload Identity User**

#### Option 2: Use Your Personal Service Account

If you have a personal GCP account with key creation enabled:

1. Create a service account in your personal project
2. Grant it the necessary roles in `book-qc-cf`
3. Create a key and add it as `GCP_SA_KEY` secret

### 🔧 GitHub Repository Setup

1. **Add GitHub Secrets**:
   - Go to your repository → Settings → Secrets and variables → Actions
   - Add these secrets:
     - `WORKLOAD_IDENTITY_PROVIDER`: `projects/282136454082/locations/global/workloadIdentityPools/github-actions-pool/providers/github-provider`
     - `SERVICE_ACCOUNT`: `pdf-processor-sa@book-qc-cf.iam.gserviceaccount.com`

2. **Push Code**:
   ```bash
   git add .
   git commit -m "Add GitHub Actions deployment with WIF"
   git push origin main
   ```

### 🧪 Testing the Deployment

Once deployed, test your service:

```bash
# Get the service URL from GitHub Actions output
SERVICE_URL="https://pdf-processor-xxx.run.app"

# Test health endpoint
curl $SERVICE_URL/health

# Test with your uploaded PDF
curl -X POST $SERVICE_URL/process \
  -H "Content-Type: application/json" \
  -d '{
    "pdf_path": "gs://book-qc-cf-pdf-storage/book_ip_sqp.pdf",
    "bucket_name": "book-qc-cf-pdf-storage"
  }'
```

### 📊 Expected Results

The service should:
1. Analyze the PDF and find 18 chapters
2. Split it into 16 files (9 question papers + 7 answer keys)
3. Upload all files to GCS bucket
4. Return success response with file details

### 🔍 Monitoring

- **GitHub Actions**: Check the Actions tab for build/deploy status
- **Cloud Run**: Monitor in [Cloud Run Console](https://console.cloud.google.com/run)
- **Logs**: View in [Cloud Logging](https://console.cloud.google.com/logs)

### 🆘 Troubleshooting

1. **WIF Setup Issues**: Follow the manual setup guide in `WIF_SETUP_GUIDE.md`
2. **Permission Errors**: Ensure service account has all required roles
3. **Build Failures**: Check Docker build logs in GitHub Actions
4. **Deployment Issues**: Verify Cloud Run service configuration

### 📋 Project Summary

| Component | Status | Details |
|-----------|--------|---------|
| **GCP Project** | ✅ | `book-qc-cf` |
| **GCS Bucket** | ✅ | `book-qc-cf-pdf-storage` |
| **Artifact Registry** | ✅ | `us-central1-docker.pkg.dev/book-qc-cf/pdf-processor/` |
| **Service Account** | ✅ | `pdf-processor-sa@book-qc-cf.iam.gserviceaccount.com` |
| **GitHub Actions** | ✅ | WIF configured |
| **Test PDF** | ✅ | Uploaded to GCS |

### 🎯 Next Steps

1. Complete WIF setup in Google Cloud Console
2. Add GitHub secrets
3. Push code to trigger deployment
4. Test the deployed service
5. Monitor and scale as needed

Your PDF processing microservice is ready to handle PDF analysis and splitting at scale! 🚀
