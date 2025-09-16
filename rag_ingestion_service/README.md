# RAG Ingestion Service

A comprehensive Cloud Run service for converting PDFs to markdown, performing semantic chunking, and storing in vector databases for RAG (Retrieval-Augmented Generation) applications.

## Features

- **PDF to Markdown Conversion**: Uses Marker API for high-quality PDF to markdown conversion with image descriptions
- **Semantic Chunking**: Intelligently chunks markdown content based on structure and meaning
- **Vector Embeddings**: Generates embeddings using Google Vertex AI
- **Vector Storage**: Stores chunks and embeddings in Qdrant vector database
- **Chapter-wise Processing**: Support for processing entire books or individual chapters
- **Collection Management**: Automatic collection creation and updates for each book
- **Fast Vector Search**: Optimized for accurate and fast vector searches

## Architecture

```
PDF → Marker API → Markdown → Semantic Chunking → Vertex AI Embeddings → Qdrant Vector DB
```

## Components

### Core Modules

- **`pdf_to_markdown.py`**: Handles PDF to markdown conversion using Marker API
- **`semantic_chunker.py`**: Performs intelligent chunking of markdown content
- **`embedding_generator.py`**: Generates embeddings using Google Vertex AI
- **`vector_store.py`**: Manages Qdrant vector database operations
- **`cli_main.py`**: Command-line interface for the service
- **`main.py`**: Flask web service for Cloud Run

### Configuration

- **`markdown_conversion_workflow.yaml`**: Google Cloud Workflows configuration
- **`Dockerfile`**: Container configuration
- **`requirements.txt`**: Python dependencies

## Usage

### CLI Interface

```bash
# Process a full book
python cli_main.py process --pdf-path gs://bucket/book.pdf --book-name "My Book"

# Process a specific chapter
python cli_main.py process --pdf-path gs://bucket/chapter.pdf --book-name "My Book" --chapter 1

# Search for content
python cli_main.py search --book-name "My Book" --query "machine learning algorithms"

# List collections
python cli_main.py list-collections
```

### Cloud Workflows

```bash
# Execute workflow
gcloud workflows execute rag-ingestion-workflow \
  --location=us-central1 \
  --data='{"pdf_path":"gs://bucket/book.pdf","book_name":"My Book","chapter":1}' \
  --project=book-qc-cf
```

### Web API

```bash
# Process PDF
curl -X POST https://your-service-url/process \
  -H "Content-Type: application/json" \
  -d '{"pdf_path":"gs://bucket/book.pdf","book_name":"My Book","chapter":1}'

# Search content
curl -X POST https://your-service-url/search \
  -H "Content-Type: application/json" \
  -d '{"book_name":"My Book","query":"machine learning","limit":10}'
```

## Environment Variables

- `PROJECT_ID`: Google Cloud project ID
- `BUCKET_NAME`: GCS bucket for storing markdown files (default: llm-books)
- `REGION`: Google Cloud region (default: us-central1)
- `MARKER_API_KEY`: Marker API key for PDF conversion
- `QDRANT_API_KEY`: Qdrant API key for vector database
- `QDRANT_URL`: Qdrant cluster URL (default: https://qdrant.tech)

## Setup

### 1. Create Secrets

```bash
# Create Marker API key secret
echo "your-marker-api-key" | gcloud secrets create marker-api-key --data-file=-

# Create Qdrant API key secret
echo "your-qdrant-api-key" | gcloud secrets create qdrant-api-key --data-file=-
```

### 2. Grant Permissions

```bash
# Grant access to secrets
gcloud secrets add-iam-policy-binding marker-api-key \
  --member="serviceAccount:markdown-converter-sa@book-qc-cf.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding qdrant-api-key \
  --member="serviceAccount:markdown-converter-sa@book-qc-cf.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### 3. Deploy Service

The service is automatically deployed via GitHub Actions when changes are pushed to the main branch.

## API Endpoints

### POST /process
Process a PDF file and store in vector database.

**Request Body:**
```json
{
  "pdf_path": "gs://bucket/file.pdf",
  "book_name": "Book Name",
  "chapter": 1,
  "update_existing": true
}
```

**Response:**
```json
{
  "status": "success",
  "book_name": "Book Name",
  "chapter": 1,
  "collection_name": "book_book_name_chapter_1",
  "chunks_created": 150,
  "embeddings_generated": 150,
  "markdown_gcs_path": "gs://llm-books/books/Book Name/chapter_01.md",
  "collection_info": {...}
}
```

### POST /search
Search for similar content in vector database.

**Request Body:**
```json
{
  "query": "machine learning algorithms",
  "book_name": "Book Name",
  "chapter": 1,
  "limit": 10,
  "score_threshold": 0.7
}
```

**Response:**
```json
{
  "status": "success",
  "query": "machine learning algorithms",
  "book_name": "Book Name",
  "chapter": 1,
  "collection_name": "book_book_name_chapter_1",
  "results": [...],
  "total_results": 5
}
```

### GET /collections
List all collections in the vector database.

**Response:**
```json
{
  "status": "success",
  "collections": [...],
  "total_collections": 10
}
```

## Collection Naming

Collections are automatically named based on the book name and chapter:
- Full book: `book_{book_name_lowercase}`
- Chapter: `book_{book_name_lowercase}_chapter_{chapter_number}`

## Chunking Strategy

The semantic chunker uses the following strategy:
- **Max chunk size**: 1000 tokens
- **Overlap size**: 200 tokens
- **Min chunk size**: 100 tokens
- **Section-based**: Chunks are created based on markdown headers and logical sections
- **Metadata**: Each chunk includes book name, chapter, section title, and position information

## Vector Database

- **Database**: Qdrant
- **Embedding Model**: Google Vertex AI textembedding-gecko@001
- **Embedding Dimension**: 768
- **Distance Metric**: Cosine similarity
- **Indexing**: Automatic indexing for fast searches

## Monitoring

The service includes comprehensive logging and can be monitored through:
- Google Cloud Logging
- Cloud Run metrics
- Qdrant dashboard
- Custom application logs

## Testing

Run the test suite:

```bash
python test_service.py
```

## Development

### Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables:
```bash
export PROJECT_ID=your-project
export BUCKET_NAME=llm-books
export MARKER_API_KEY=your-key
export QDRANT_API_KEY=your-key
```

3. Run locally:
```bash
python cli_main.py process --pdf-path path/to/file.pdf --book-name "Test Book"
```

### Docker Development

```bash
# Build image
docker build -t markdown-converter .

# Run container
docker run -e PROJECT_ID=your-project -e MARKER_API_KEY=your-key markdown-converter
```

## Troubleshooting

### Common Issues

1. **PDF Conversion Fails**: Check Marker API key and file accessibility
2. **Embedding Generation Fails**: Verify Vertex AI permissions and quota
3. **Vector Storage Fails**: Check Qdrant API key and cluster connectivity
4. **Chunking Issues**: Verify markdown content structure

### Logs

Check logs in Google Cloud Console:
- Cloud Run logs
- Workflow execution logs
- Application logs

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License.
