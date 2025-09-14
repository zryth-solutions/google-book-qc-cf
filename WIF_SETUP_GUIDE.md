# Workload Identity Federation Setup Guide

## Manual Setup via Google Cloud Console

Since the CLI approach is having issues, let's set up WIF manually through the Google Cloud Console:

### 1. Create Workload Identity Pool

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select project `book-qc-cf`
3. Navigate to **IAM & Admin** → **Workload Identity Federation**
4. Click **"Create Pool"**
5. Fill in:
   - **Pool ID**: `github-actions-pool`
   - **Display name**: `GitHub Actions Pool`
   - **Description**: `Pool for GitHub Actions authentication`
6. Click **"Continue"**

### 2. Create OIDC Provider

1. In the pool, click **"Add Provider"**
2. Select **"OpenID Connect (OIDC)"**
3. Fill in:
   - **Provider ID**: `github-provider`
   - **Display name**: `GitHub Provider`
   - **Issuer (URL)**: `https://token.actions.githubusercontent.com`
4. Click **"Continue"**

### 3. Configure Attribute Mapping

1. In **Attribute mapping** section:
   - **Google subject**: `assertion.sub`
   - **Additional attributes**:
     - `actor`: `assertion.actor`
     - `repository`: `assertion.repository`
2. Click **"Save"**

### 4. Grant Access to Service Account

1. Go to **IAM & Admin** → **IAM**
2. Find the service account: `pdf-processor-sa@book-qc-cf.iam.gserviceaccount.com`
3. Click **"Edit"** (pencil icon)
4. Click **"Add Principal"**
5. Add: `principalSet://iam.googleapis.com/projects/282136454082/locations/global/workloadIdentityPools/github-actions-pool/attribute.repository/kushagraagarwal/google-book-qc-cf`
6. Select role: **Workload Identity User**
7. Click **"Save"**

### 5. Get Provider Resource Name

After setup, you'll get a provider resource name like:
```
projects/282136454082/locations/global/workloadIdentityPools/github-actions-pool/providers/github-provider
```

## Alternative: Use Service Account Key (Temporary)

If WIF setup is complex, we can use the service account key approach temporarily:

1. Create a service account key:
   ```bash
   gcloud iam service-accounts keys create pdf-processor-sa-key.json \
       --iam-account=pdf-processor-sa@book-qc-cf.iam.gserviceaccount.com
   ```

2. Add the key content as `GCP_SA_KEY` secret in GitHub

## Next Steps

Once WIF is set up:
1. Add GitHub secrets:
   - `WORKLOAD_IDENTITY_PROVIDER`: The provider resource name
   - `SERVICE_ACCOUNT`: `pdf-processor-sa@book-qc-cf.iam.gserviceaccount.com`
2. Push code to trigger deployment
