# Vectorstore Management Guide

This guide explains how the vectorstore is managed in the CFC-RAG application and ensures it's always ready before queries are processed.

## Overview

The RAG system uses FAISS (Facebook AI Similarity Search) to store and retrieve sermon embeddings. The vectorstore must be generated or loaded before any queries can be processed.

## Automatic Vectorstore Management

### 1. Initialization on Startup

The `SermonRAGService` class automatically handles vectorstore initialization:

```python
# In rag/services.py
def _load_or_create_vectorstore(self):
    """Load existing vectorstore or create new one if not found."""
    vectorstore_path = settings.VECTORSTORE_PATH
    
    if vectorstore_path.exists():
        # Load existing vectorstore
        self.vectorstore = FAISS.load_local(
            str(vectorstore_path), 
            self.embeddings,
            allow_dangerous_deserialization=True
        )
    else:
        # Create new vectorstore from dataset
        self._create_vectorstore()
```

### 2. Readiness Checks

Before processing any query, the system checks if all components are ready:

```python
def is_ready(self) -> bool:
    """Check if the RAG system is ready to handle queries."""
    return all([
        self.embeddings is not None,
        self.vectorstore is not None,
        self.llm is not None,
        self.retriever is not None,
        self.rag_chain is not None
    ])
```

## Management Commands

### Check Vectorstore Status

```bash
python manage.py check_vectorstore
```

Output example:
```
Vectorstore Status:
Path: /path/to/vectorstore/sermons_vectorstore
Exists: True
Loaded: True
Ready: True
Document count: 1234
✅ RAG system is ready for queries!
```

### Initialize/Recreate Vectorstore

```bash
# Create vectorstore if it doesn't exist
python manage.py init_vectorstore

# Force recreate existing vectorstore
python manage.py init_vectorstore --force
```

## API Endpoints

### Health Check
```
GET /rag/health/
```

Response:
```json
{
    "status": "healthy",
    "rag_ready": true
}
```

### Detailed Status
```
GET /rag/status/
```

Response:
```json
{
    "exists": true,
    "path": "/path/to/vectorstore/sermons_vectorstore",
    "loaded": true,
    "ready": true,
    "document_count": 1234,
    "components": {
        "embeddings": true,
        "llm": true,
        "vectorstore": true,
        "retriever": true,
        "rag_chain": true
    },
    "overall_status": "ready"
}
```

## Deployment Considerations

### 1. Pre-deployment Check

Run the vectorstore check script before starting the application:

```bash
python scripts/ensure_vectorstore.py
```

### 2. Docker Deployment

In your Dockerfile or docker-compose.yml, ensure the vectorstore is ready:

```dockerfile
# In Dockerfile
RUN python scripts/ensure_vectorstore.py
```

### 3. Environment Variables

Required environment variables:
- `GOOGLE_API_KEY`: For Google Gemini embeddings and LLM
- `VECTORSTORE_PATH`: Path to vectorstore (default: `vectorstore/sermons_vectorstore`)
- `DATASET_PATH`: Path to sermon dataset (default: `dataset/RLCF-Pitts.csv`)

## Middleware Protection

The application includes middleware to ensure RAG readiness:

### RAGReadinessMiddleware
- Checks if RAG system is ready before processing RAG-related requests
- Returns appropriate error responses if not ready
- Handles both API and web requests

### RAGWarmupMiddleware
- Warms up the RAG service on application startup
- Ensures faster response times for first requests

## Error Handling

### Common Issues and Solutions

1. **Vectorstore not found**
   - Solution: Run `python manage.py init_vectorstore`

2. **Google API key missing**
   - Solution: Set `GOOGLE_API_KEY` environment variable

3. **Dataset file missing**
   - Solution: Ensure dataset file exists at `DATASET_PATH`

4. **Memory issues during vectorstore creation**
   - Solution: Increase available memory or process dataset in smaller batches

### Error Responses

When RAG system is not ready:

**API Requests:**
```json
{
    "error": "RAG system is initializing. Please try again in a moment.",
    "status": "initializing"
}
```

**Web Requests:**
- Redirected to `/rag/not_ready.html` with auto-refresh

## File Structure

```
vectorstore/
├── sermons_vectorstore/
│   ├── .gitkeep              # Preserves directory in git
│   ├── index.faiss           # FAISS index (ignored by git)
│   └── index.pkl             # Metadata (ignored by git)
```

## Best Practices

1. **Always check readiness** before processing queries
2. **Use management commands** for vectorstore operations
3. **Monitor health endpoints** in production
4. **Implement proper error handling** for initialization failures
5. **Use middleware** to protect against unready state
6. **Warm up on startup** for better performance

## Troubleshooting

### Debug Mode

Enable debug logging to see detailed initialization steps:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Manual Initialization

```python
from rag.services import SermonRAGService

# Create service instance (will auto-initialize)
service = SermonRAGService()

# Check status
print(f"Ready: {service.is_ready()}")
print(f"Status: {service.get_vectorstore_status()}")
```

This comprehensive approach ensures that the vectorstore is always properly initialized and ready before any queries are processed, providing a robust and reliable RAG system.
