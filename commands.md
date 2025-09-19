
# Run workflow for PDF splitter:
```
gcloud workflows execute pdf-processing-workflow \
  --location=us-central1 \
  --data='{"pdf_path": "gs://book-qc-cf-pdf-storage/CBSE_Social Science_xii.pdf"}'
```

# Run workflow for Book extractor json:
gcloud workflows execute book-extraction-workflow \
  --location=us-central1 \
  --data='{"folder_path":"CBSE_Social Science_xii","subject":"csbe_social_science","operation_type":"folder"}'


