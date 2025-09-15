# Book Extractor Microservice

A serverless microservice that extracts questions and answers from PDF documents using Google Cloud Vertex AI. This service is designed to work as part of a larger pipeline for processing educational content.

## Features

- **Multi-Subject Support**: Factory pattern implementation for different subjects (Computer Applications, Mathematics, etc.)
- **Vertex AI Integration**: Uses Google Cloud Vertex AI with Gemini 2.5 Pro for intelligent PDF processing
- **Batch Processing**: Efficiently processes large documents in batches
- **GCS Integration**: Seamlessly works with Google Cloud Storage for file management
- **Serverless Architecture**: Runs on Google Cloud Run with automatic scaling
- **Workflow Integration**: Can be orchestrated with Google Cloud Workflows

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   GCS Bucket    │    │  Cloud Run      │    │   Vertex AI     │
│   (PDFs)        │───▶│  (Extractor)    │───▶│   (Gemini 2.5)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   GCS Bucket    │
                       │   (JSON Results)│
                       └─────────────────┘
```

## API Endpoints

### Health Check
- **GET** `/health` - Service health status

### Question Extraction
- **POST** `/extract-questions` - Extract questions from question paper PDF
  ```json
  {
    "pdf_path": "gs://bucket-name/question-paper.pdf",
    "subject": "computer_applications",
    "bucket_name": "book-qc-cf-pdf-storage"
  }
  ```

### Answer Extraction
- **POST** `/extract-answers` - Extract answers from answer key PDF
  ```json
  {
    "pdf_path": "gs://bucket-name/answer-key.pdf",
    "subject": "computer_applications",
    "bucket_name": "book-qc-cf-pdf-storage"
  }
  ```

### Combined Extraction
- **POST** `/extract-all` - Extract both questions and answers
  ```json
  {
    "question_pdf_path": "gs://bucket-name/question-paper.pdf",
    "answer_pdf_path": "gs://bucket-name/answer-key.pdf",
    "subject": "computer_applications"
  }
  ```

### Available Subjects
- **GET** `/subjects` - Get list of supported subjects

## Supported Subjects

- **Computer Applications**: CBSE Class 10 Computer Applications
- **Mathematics**: General mathematics questions and answers
- **Extensible**: Easy to add new subjects using the factory pattern

## Configuration

### Environment Variables
- `GOOGLE_CLOUD_PROJECT`: GCP project ID (default: book-qc-cf)
- `BUCKET_NAME`: GCS bucket name (default: book-qc-cf-pdf-storage)
- `VERTEX_AI_LOCATION`: Vertex AI region (default: us-central1)
- `PORT`: Service port (default: 8080)

### Subject Configuration
Each subject has its own extraction configuration:

```python
ExtractionConfig(
    content_type="questions",
    item_name="question",
    batch_size=8,
    expected_total=39,
    fields={
        "question_number": "exact question number as it appears",
        "question_text": "complete question text word-for-word",
        "diagram_explain": "detailed description of diagrams",
        "section": "exact section name",
        "marks": "exact marks notation"
    }
)
```

## Local Development

### Prerequisites
- Python 3.11+
- Google Cloud SDK
- Vertex AI API enabled
- GCS bucket access

### Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export GOOGLE_CLOUD_PROJECT=book-qc-cf
export BUCKET_NAME=book-qc-cf-pdf-storage
export VERTEX_AI_LOCATION=us-central1
```

### Running Locally
```bash
# Run the service
python book_extractor/main.py

# Run tests
python book_extractor/test_local.py
```

## Deployment

### Docker Build
```bash
cd book_extractor
docker build -t book-extractor .
```

### Cloud Run Deployment
```bash
# Build and push to Artifact Registry
gcloud builds submit --tag gcr.io/book-qc-cf/book-extractor

# Deploy to Cloud Run
gcloud run deploy book-extractor \
  --image gcr.io/book-qc-cf/book-extractor \
  --platform managed \
  --region us-central1 \
  --service-account pdf-processor-sa@book-qc-cf.iam.gserviceaccount.com
```

### GitHub Actions
The service is automatically deployed via GitHub Actions when changes are pushed to the main branch.

## Usage Examples

### Extract Questions
```python
import requests

response = requests.post(
    "https://book-extractor-xxx.run.app/extract-questions",
    json={
        "pdf_path": "gs://book-qc-cf-pdf-storage/question-paper.pdf",
        "subject": "computer_applications"
    }
)

result = response.json()
print(f"Extracted {result['total_questions']} questions")
```

### Extract Answers
```python
response = requests.post(
    "https://book-extractor-xxx.run.app/extract-answers",
    json={
        "pdf_path": "gs://book-qc-cf-pdf-storage/answer-key.pdf",
        "subject": "computer_applications"
    }
)

result = response.json()
print(f"Extracted {result['total_answers']} answers")
```

## Workflow Integration

The service can be integrated with Google Cloud Workflows:

```yaml
main:
  params: [pdf_path, subject]
  steps:
    - extract_questions:
        call: http.post
        args:
          url: "https://book-extractor-xxx.run.app/extract-questions"
          headers:
            Content-Type: "application/json"
          body:
            pdf_path: "${pdf_path}"
            subject: "${subject}"
        result: questions_result
```

## Error Handling

The service includes comprehensive error handling:
- Input validation
- PDF processing errors
- Vertex AI API errors
- GCS upload/download errors
- JSON parsing errors

## Monitoring

- Health check endpoint for service monitoring
- Structured logging for debugging
- Cloud Run metrics and logs
- Error tracking and reporting

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License.
