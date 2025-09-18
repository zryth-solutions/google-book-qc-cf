# Question Analysis Service

A comprehensive service for analyzing CBSE Computer Applications question papers using AI. The service can process individual JSON files or batch process entire folders, storing analysis results in Qdrant vector database for search and retrieval.

## Features

- **AI-Powered Analysis**: Uses Google's Gemini AI to analyze question papers with extreme attention to detail
- **Batch Processing**: Process multiple JSON files from local folders or Google Cloud Storage
- **Vector Storage**: Store analysis results in Qdrant for semantic search and retrieval
- **REST API**: Cloud Run service with comprehensive REST endpoints
- **CLI Interface**: Command-line tool for local analysis and testing
- **Workflow Integration**: Argo Workflows support for automated processing

## Analysis Capabilities

The service performs comprehensive analysis of CBSE Computer Applications questions including:

1. **Grammar & Language**: Spelling, punctuation, grammar, vocabulary level
2. **Technical Accuracy**: Software names, hardware terminology, protocols
3. **Syllabus Alignment**: CBSE Class 10 Computer Applications curriculum compliance
4. **Question Clarity**: Unambiguous instructions, appropriate language
5. **MCQ Quality**: Option analysis, distractor evaluation
6. **Mark Allocation**: Appropriate difficulty-to-marks ratio
7. **CBSE Compliance**: Format and style adherence
8. **Software-Specific Accuracy**: MS Office, database, internet terminology

## Quick Start

### Prerequisites

- Python 3.11+
- Google Cloud Project with Cloud Storage and Cloud Run
- Qdrant Cloud account or self-hosted Qdrant
- Gemini API key

### Environment Variables

```bash
export GEMINI_API_KEY="your-gemini-api-key"
export QDRANT_API_KEY="your-qdrant-api-key"
export QDRANT_URL="your-qdrant-url"  # Optional for Qdrant Cloud
export GCP_PROJECT_ID="book-qc-cf"
export BUCKET_NAME="book-qc-cf-pdf-storage"
```

### Local Development

1. **Install dependencies**:
   ```bash
   cd question_analysis_service
   pip install -r requirements.txt
   ```

2. **Analyze a single file**:
   ```bash
   python cli_main.py single-file questions.json -o report.md -v
   ```

3. **Analyze a folder**:
   ```bash
   python cli_main.py folder ./question_files --verbose
   ```

4. **Analyze GCS folder**:
   ```bash
   python cli_main.py gcs-folder book_ip_sqp/extracted_questions --verbose
   ```

5. **Search analysis results**:
   ```bash
   python cli_main.py search "grammar errors" --limit 5
   ```

### Cloud Run Deployment

The service is automatically deployed to Google Cloud Run via GitHub Actions when changes are pushed to the main branch.

**Manual deployment**:
```bash
# Build and push image
gcloud builds submit --tag us-central1-docker.pkg.dev/book-qc-cf/question-analysis/question-analysis:latest

# Deploy to Cloud Run
gcloud run deploy question-analysis-service \
  --image us-central1-docker.pkg.dev/book-qc-cf/question-analysis/question-analysis:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 4Gi \
  --cpu 2 \
  --timeout 600
```

## API Endpoints

### Health Check
```http
GET /health
```

### Analyze Single File
```http
POST /analyze/file
Content-Type: application/json

{
  "file_path": "/path/to/questions.json",
  "verbose": false
}
```

### Analyze Local Folder
```http
POST /analyze/folder
Content-Type: application/json

{
  "folder_path": "/path/to/question/files",
  "file_pattern": "*.json",
  "batch_size": 5,
  "store_in_qdrant": true,
  "verbose": false
}
```

### Analyze GCS Folder
```http
POST /analyze/gcs-folder
Content-Type: application/json

{
  "gcs_folder_path": "book_ip_sqp/extracted_questions/",
  "local_temp_dir": "/tmp/question_analysis",
  "file_pattern": "*.json",
  "batch_size": 5,
  "store_in_qdrant": true,
  "verbose": false
}
```

### Search Analysis Results
```http
POST /search/analysis
Content-Type: application/json

{
  "query": "grammar errors in question 5",
  "limit": 10,
  "score_threshold": 0.7
}
```

### List Collections
```http
GET /collections
```

### Get Collection Info
```http
GET /collections/{collection_name}/info
```

## Workflow Integration

The service includes Argo Workflows configuration for automated batch processing:

```yaml
# Run workflow
argo submit question_analysis_workflow.yaml \
  -p gcs-folder-path="book_ip_sqp/extracted_questions" \
  -p batch-size=5 \
  -p store-in-qdrant=true \
  -p verbose=true
```

## Input Format

The service expects JSON files with the following structure:

```json
{
  "document_info": {
    "title": "Sample Question Paper",
    "class": "10",
    "subject": "Computer Applications"
  },
  "questions": [
    {
      "question_number": 1,
      "question_text": "What is the full form of CPU?",
      "section": "A",
      "marks": 1,
      "diagram_explain": null
    }
  ]
}
```

## Output Format

Analysis results are stored in Qdrant with the following metadata:

```json
{
  "file_name": "SQP-1-questions.json",
  "analysis_date": "2024-01-15T10:30:00",
  "analysis_id": "uuid-here",
  "total_questions": 25,
  "document_title": "Sample Question Paper",
  "document_class": "10",
  "status": "completed",
  "gcs_report_path": "gs://bucket/analysis_reports/SQP-1-questions_analysis.md",
  "chunk_type": "analysis_report"
}
```

## Configuration

### Batch Size
- Default: 5 questions per batch
- Larger batches: Faster processing, higher memory usage
- Smaller batches: More detailed analysis, slower processing

### Qdrant Collection
- Collection name: `question_analysis_results`
- Vector dimension: 768 (text-embedding-004)
- Distance metric: Cosine similarity

### GCS Integration
- Automatic upload of analysis reports
- Support for both local and GCS folder processing
- Configurable temporary directory for downloads

## Monitoring and Logging

- Structured logging with configurable levels
- Health check endpoint for monitoring
- Detailed error reporting and stack traces
- Processing metrics and statistics

## Development

### Running Tests
```bash
pytest tests/
```

### Code Formatting
```bash
black question_analysis_service/
flake8 question_analysis_service/
```

### Local Service
```bash
python question_analysis_service/main.py
```

## Troubleshooting

### Common Issues

1. **Gemini API Rate Limits**: Reduce batch size or add delays
2. **Qdrant Connection**: Verify API key and URL
3. **GCS Permissions**: Ensure service account has storage access
4. **Memory Issues**: Increase Cloud Run memory allocation

### Debug Mode
```bash
export LOG_LEVEL=DEBUG
python cli_main.py folder ./questions --verbose
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License.
