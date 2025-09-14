# PDF Processing Microservice

A serverless microservice for analyzing and splitting PDF files, designed to run on Google Cloud Run with Workflow orchestration.

## Features

- **PDF Analysis**: Analyzes PDF structure and identifies chapters/sections
- **PDF Splitting**: Splits PDFs based on analysis results
- **Cloud Native**: Designed for Google Cloud Run and Workflows
- **Scalable**: Auto-scaling based on demand
- **RESTful API**: Easy integration with other services

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   GitHub        │    │   Cloud Run     │    │   GCS Bucket    │
│   Actions       │───▶│   Service       │───▶│   (Storage)     │
│   (CI/CD)       │    │   (Processing)  │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Workflows     │
                       │   (Orchestrator)│
                       └─────────────────┘
```

## Components

### 1. PDF Analyzer (`split_pdf/analyze_pdf.py`)
- Analyzes PDF structure using pattern matching
- Identifies chapters, sections, and page ranges
- Generates JSON configuration for splitting

### 2. PDF Splitter (`split_pdf/split_pdf.py`)
- Splits PDFs based on analysis results
- Organizes output into question papers and answer keys
- Handles various PDF formats and structures

### 3. Cloud Run Service (`split_pdf/main.py`)
- Flask-based REST API
- Handles PDF analysis and splitting requests
- Integrates with GCS for file storage

### 4. GCP Utilities (`utils/gcp/`)
- `bucket_manager.py`: GCS operations
- `cloud_run_manager.py`: Cloud Run deployment
- `workflow_manager.py`: Workflow orchestration

## Setup

### Prerequisites

1. Google Cloud Project with billing enabled
2. Docker installed locally
3. Google Cloud SDK installed
4. Python 3.11+

### 1. Configure GCP

```bash
# Set your project ID
export PROJECT_ID="book-qc-cf"
export REGION="us-central1"
export BUCKET_NAME="book-qc-cf-pdf-storage"

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable workflows.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable artifactregistry.googleapis.com

# Create GCS bucket
gsutil mb gs://$BUCKET_NAME

# Create Artifact Registry repository
gcloud artifacts repositories create pdf-processor \
    --repository-format=docker \
    --location=$REGION
```

### 2. Configure GitHub Secrets

Add the following secrets to your GitHub repository:

- `GCP_PROJECT_ID`: Your GCP project ID
- `GCP_SA_KEY`: Service account key JSON
- `BUCKET_NAME`: Your GCS bucket name

### 3. Deploy Service

#### Option A: Using GitHub Actions (Recommended)

1. Push code to main branch
2. GitHub Actions will automatically build and deploy

#### Option B: Manual Deployment

```bash
# Build and push Docker image
docker build -t $REGION-docker.pkg.dev/$PROJECT_ID/pdf-processor/pdf-processor:latest .
docker push $REGION-docker.pkg.dev/$PROJECT_ID/pdf-processor/pdf-processor:latest

# Deploy using deployment script
python deploy.py \
    --project-id $PROJECT_ID \
    --region $REGION \
    --image-uri $REGION-docker.pkg.dev/$PROJECT_ID/pdf-processor/pdf-processor:latest \
    --bucket-name $BUCKET_NAME
```

## API Usage

### Health Check

```bash
curl https://your-service-url/health
```

### Analyze PDF

```bash
curl -X POST https://your-service-url/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "pdf_path": "gs://your-bucket/path/to/file.pdf",
    "bucket_name": "your-bucket"
  }'
```

### Split PDF

```bash
curl -X POST https://your-service-url/split \
  -H "Content-Type: application/json" \
  -d '{
    "pdf_path": "gs://your-bucket/path/to/file.pdf",
    "analysis_path": "gs://your-bucket/path/to/file.pdf_analysis.json",
    "bucket_name": "your-bucket"
  }'
```

### Complete Processing (Analyze + Split)

```bash
curl -X POST https://your-service-url/process \
  -H "Content-Type: application/json" \
  -d '{
    "pdf_path": "gs://your-bucket/path/to/file.pdf",
    "bucket_name": "your-bucket"
  }'
```

## Workflow Usage

### Deploy Workflow

```bash
python deploy.py \
    --project-id $PROJECT_ID \
    --region $REGION \
    --workflow-name pdf-processing-workflow \
    --workflow-file workflows/pdf_processing_workflow.yaml
```

### Execute Workflow

```bash
gcloud workflows executions create pdf-processing-workflow \
    --location=$REGION \
    --argument='{"pdf_path":"gs://your-bucket/path/to/file.pdf","bucket_name":"your-bucket","project_id":"your-project-id"}'
```

## Configuration

Update `config.yaml` with your specific configuration:

```yaml
gcp:
  project_id: "your-project-id"
  region: "us-central1"
  bucket_name: "your-bucket-name"

cloud_run:
  service_name: "pdf-processor"
  memory: "2Gi"
  cpu: "2"
  max_instances: 10
```

## Development

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export PROJECT_ID="your-project-id"
export BUCKET_NAME="your-bucket-name"
export REGION="us-central1"

# Run locally
python split_pdf/main.py
```

### Testing

```bash
# Test health endpoint
curl http://localhost:8080/health

# Test with sample PDF
curl -X POST http://localhost:8080/analyze \
  -H "Content-Type: application/json" \
  -d '{"pdf_path": "gs://your-bucket/sample.pdf"}'
```

## Monitoring

### Cloud Run Metrics

- Request count and latency
- Memory and CPU usage
- Error rates

### Workflow Metrics

- Execution success/failure rates
- Execution duration
- Step-by-step execution logs

### Logs

```bash
# View Cloud Run logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=pdf-processor"

# View Workflow logs
gcloud logging read "resource.type=workflow_execution"
```

## Troubleshooting

### Common Issues

1. **Service not starting**: Check environment variables and GCS permissions
2. **PDF analysis failing**: Verify PDF format and file accessibility
3. **Splitting errors**: Check analysis JSON structure and page ranges
4. **Workflow failures**: Verify service URLs and authentication

### Debug Mode

Enable debug logging by setting environment variable:

```bash
export LOG_LEVEL=DEBUG
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review Cloud Run and Workflow logs
3. Create an issue in the repository
