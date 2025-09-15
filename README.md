# Google Book QC Cloud Functions - Microservices Architecture

A comprehensive microservices architecture for PDF processing and content extraction using Google Cloud Platform. This project consists of multiple serverless services that work together to process educational PDFs.

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   GCS Bucket    │    │  Split PDF      │    │  Book Extractor │
│   (PDFs)        │───▶│  Service        │───▶│  Service        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   GCS Bucket    │    │   GCS Bucket    │
                       │   (Split PDFs)  │    │   (JSON Data)  │
                       └─────────────────┘    └─────────────────┘
```

## 📁 Project Structure

```
google-book-qc-cf/
├── split_pdf_service/          # PDF splitting microservice
│   ├── main.py                 # Flask application
│   ├── analyze_pdf.py          # PDF analysis logic
│   ├── split_pdf.py            # PDF splitting logic
│   ├── Dockerfile              # Container configuration
│   ├── deploy.yml              # GitHub Actions workflow
│   ├── pdf_processing_workflow.yaml  # GCP Workflow
│   └── update_workflow_urls.py # URL update script
├── book_extractor_service/     # Content extraction microservice
│   ├── main.py                 # Flask application
│   ├── vertex/                 # Vertex AI integration
│   │   ├── extractor.py        # Core extraction logic
│   │   ├── subject_mapper.py   # Subject factory pattern
│   │   └── subjects/           # Subject-specific prompts
│   │       ├── computer_application/
│   │       └── math/
│   ├── Dockerfile              # Container configuration
│   ├── deploy-book-extractor.yml  # GitHub Actions workflow
│   ├── book_extraction_workflow.yaml  # GCP Workflow
│   └── update_book_extractor_urls.py  # URL update script
├── utils/                      # Shared utilities
│   └── gcp/                    # GCP service integrations
│       ├── bucket_manager.py   # GCS operations
│       ├── cloud_run_manager.py # Cloud Run operations
│       └── workflow_manager.py # Workflow operations
├── config.yaml                 # Global configuration
├── requirements.txt            # Python dependencies
└── .github/workflows/          # CI/CD pipelines
    └── deploy-all-services.yml # Main deployment workflow
```

## 🚀 Services

### 1. Split PDF Service
**Purpose**: Analyzes and splits PDFs into smaller, manageable files

**Features**:
- PDF structure analysis
- Chapter-based splitting
- GCS integration for file management
- Serverless Cloud Run deployment

**Endpoints**:
- `GET /health` - Health check
- `POST /analyze` - Analyze PDF structure
- `POST /split` - Split PDF based on analysis
- `POST /process` - Complete analyze + split workflow

### 2. Book Extractor Service
**Purpose**: Extracts questions and answers from PDFs using Vertex AI

**Features**:
- Multi-subject support (Computer Applications, Mathematics)
- Vertex AI integration with Gemini 2.5 Pro
- Subject-specific prompt engineering
- Batch processing for large documents
- Factory pattern for extensibility

**Endpoints**:
- `GET /health` - Health check
- `POST /extract-questions` - Extract questions from question papers
- `POST /extract-answers` - Extract answers from answer keys
- `POST /extract-all` - Extract both questions and answers
- `GET /subjects` - Get available subjects

## 🔧 Configuration

### Environment Variables
- `GOOGLE_CLOUD_PROJECT`: GCP project ID (default: book-qc-cf)
- `BUCKET_NAME`: GCS bucket name (default: book-qc-cf-pdf-storage)
- `VERTEX_AI_LOCATION`: Vertex AI region (default: us-central1)
- `PORT`: Service port (default: 8080)

### Subject Configuration
Each subject has its own configuration and prompts:

#### Computer Applications
- **Batch Size**: 8 items per batch
- **Expected Total**: 39 questions/answers
- **Special Features**: Code snippet extraction, diagram analysis

#### Mathematics
- **Batch Size**: 10 items per batch
- **Expected Total**: 30 questions/answers
- **Special Features**: Mathematical expression preservation, graph analysis

## 🚀 Deployment

### Automatic Deployment
The project uses GitHub Actions for automated deployment:

1. **Push to main branch** triggers deployment
2. **Service-specific changes** deploy only affected services
3. **Workflow URLs** are automatically updated after deployment

### Manual Deployment
```bash
# Deploy Split PDF Service
cd split_pdf_service
docker build -t gcr.io/book-qc-cf/pdf-processor .
gcloud run deploy pdf-processor --image gcr.io/book-qc-cf/pdf-processor

# Deploy Book Extractor Service
cd book_extractor_service
docker build -t gcr.io/book-qc-cf/book-extractor .
gcloud run deploy book-extractor --image gcr.io/book-qc-cf/book-extractor
```

## 📊 Usage Examples

### Split PDF Workflow
```python
import requests

# Analyze PDF
response = requests.post(
    "https://pdf-processor-xxx.run.app/analyze",
    json={
        "pdf_path": "gs://bucket-name/document.pdf",
        "bucket_name": "book-qc-cf-pdf-storage"
    }
)

# Split PDF
response = requests.post(
    "https://pdf-processor-xxx.run.app/split",
    json={
        "pdf_path": "gs://bucket-name/document.pdf",
        "analysis_path": "gs://bucket-name/analysis.json",
        "bucket_name": "book-qc-cf-pdf-storage"
    }
)
```

### Book Extraction Workflow
```python
# Extract questions
response = requests.post(
    "https://book-extractor-xxx.run.app/extract-questions",
    json={
        "pdf_path": "gs://bucket-name/question-paper.pdf",
        "subject": "computer_applications"
    }
)

# Extract answers
response = requests.post(
    "https://book-extractor-xxx.run.app/extract-answers",
    json={
        "pdf_path": "gs://bucket-name/answer-key.pdf",
        "subject": "computer_applications"
    }
)
```

## 🔄 Workflow Integration

### GCP Workflows
Both services can be orchestrated using Google Cloud Workflows:

#### PDF Processing Workflow
```yaml
main:
  params: [pdf_path]
  steps:
    - analyze_pdf: # Analyze PDF structure
    - split_pdf:   # Split PDF based on analysis
    - return_success
```

#### Book Extraction Workflow
```yaml
main:
  params: [pdf_path, subject]
  steps:
    - extract_questions: # Extract questions
    - extract_answers:   # Extract answers
    - return_success
```

## 🧪 Testing

### Local Testing
```bash
# Test Split PDF Service
cd split_pdf_service
python3 main.py

# Test Book Extractor Service
cd book_extractor_service
python3 main.py
```

### Service Testing
```bash
# Test Split PDF Service
curl -X POST https://pdf-processor-xxx.run.app/health

# Test Book Extractor Service
curl -X POST https://book-extractor-xxx.run.app/health
```

## 📈 Monitoring

### Health Checks
- All services expose `/health` endpoints
- Cloud Run provides built-in monitoring
- GCP Workflows show execution status

### Logging
- Structured logging for debugging
- Cloud Run logs integration
- Error tracking and reporting

## 🔧 Development

### Adding New Subjects
1. Create new subject folder in `book_extractor_service/vertex/subjects/`
2. Implement subject-specific prompts
3. Register in `SubjectExtractorFactory`
4. Deploy and test

### Adding New Services
1. Create service folder with required files
2. Add GitHub Actions workflow
3. Update main deployment workflow
4. Test and deploy

## 📋 Dependencies

### Core Dependencies
- **Flask**: Web framework
- **PyMuPDF**: PDF processing
- **PyPDF2**: PDF manipulation
- **Google Cloud AI Platform**: Vertex AI integration
- **Google Cloud Storage**: File management
- **Gunicorn**: Production server

### GCP Services
- **Cloud Run**: Serverless container platform
- **Cloud Storage**: Object storage
- **Vertex AI**: AI/ML platform
- **Workflows**: Orchestration service
- **Artifact Registry**: Container registry

## 🚀 Getting Started

1. **Clone the repository**
2. **Set up GCP project** with required services
3. **Configure GitHub Actions** with Workload Identity Federation
4. **Push to main branch** to trigger deployment
5. **Test the services** using the provided endpoints

## 📄 License

This project is licensed under the MIT License.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📞 Support

For questions or issues, please open a GitHub issue or contact the development team.