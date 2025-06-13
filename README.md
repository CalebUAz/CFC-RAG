# Sermon RAG - Django-based Question Answering System

A Django web application that uses Retrieval-Augmented Generation (RAG) to answer questions about Zac Poonen's sermons. The system uses Google Gemini for embeddings and text generation, with FAISS for vector search.

## Features

- 🔍 **Semantic Search**: Search through 417 sermons using vector embeddings
- 🤖 **AI-Powered Answers**: Get contextual answers using Google Gemini
- 🌐 **Web Interface**: Clean, responsive web interface for easy querying
- 📚 **Source Attribution**: See which sermons the answers come from
- 🎥 **YouTube Integration**: Direct links to YouTube videos with timestamps
- 🐳 **Docker Support**: Fully containerized for easy deployment
- ⚡ **Fast Retrieval**: FAISS vector database for efficient similarity search

## Quick Start

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd CFC-RAG
   ```

2. **Set up environment**
   ```bash
   # Copy environment template
   cp .env.example .env

   # Edit .env file with your Google API key
   # Get your API key from: https://makersuite.google.com/app/apikey
   nano .env
   ```

3. **Run the startup script**
   ```bash
   chmod +x start.sh
   ./start.sh
   ```

   This script will:
   - Create a virtual environment
   - Install dependencies
   - Run migrations
   - Initialize the vectorstore (if needed)
   - Start the development server

4. **Access the application**
   - Open your browser to `http://localhost:8000`
   - Start asking questions about the sermons!

### Docker Deployment

1. **Build and run with Docker Compose**
   ```bash
   # Copy environment file
   cp .env.example .env
   # Edit .env with your settings

   # Build and start
   docker-compose up --build
   ```

2. **Access the application**
   - Open your browser to `http://localhost:8000`

## Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# Django Configuration
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# Google API Configuration
GOOGLE_API_KEY=your-google-api-key-here
```

### Google API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Add it to your `.env` file

## API Endpoints

- `GET /` - Main web interface
- `GET /query/` - Query form page
- `POST /api/query/` - JSON API for queries
- `GET /health/` - Health check endpoint

### API Usage Example

```bash
curl -X POST http://localhost:8000/api/query/ \
  -H "Content-Type: application/json" \
  -d '{"question": "What does the Bible teach about contentment?"}'
```

### Enhanced Query Function

The system now includes an enhanced query function with YouTube video links and timestamps:

```python
from rag.services import query_sermons

# Query with YouTube links and timestamps
answer = query_sermons("What does the Bible teach about contentment?", show_sources=True)
```

This will output:
- The answer to your question
- Source sermons with clickable YouTube links
- Automatic timestamp extraction and linking

## Project Structure

```
CFC-RAG/
├── sermon_rag/          # Django project settings
├── rag/                 # Main RAG application
│   ├── services.py      # RAG service logic
│   ├── views.py         # Web views
│   ├── templates/       # HTML templates
│   └── management/      # Django management commands
├── dataset/             # Sermon dataset
├── vectorstore/         # FAISS vector database
├── requirements.txt     # Python dependencies
├── Dockerfile          # Docker configuration
├── docker-compose.yml  # Docker Compose setup
└── start.sh            # Local development startup script
```

## Technical Details

### RAG Pipeline

1. **Document Processing**: Sermons are split into chunks using RecursiveCharacterTextSplitter
2. **Embeddings**: Google Gemini embeddings (models/embedding-001)
3. **Vector Storage**: FAISS for efficient similarity search
4. **Retrieval**: Top-5 most relevant chunks for each query
5. **Generation**: Google Gemini Flash for answer generation

### Performance

- **Dataset**: 417 sermons, ~3.8M words
- **Chunks**: 63,420 document chunks (500 chars each, 200 overlap)
- **Retrieval**: Sub-second search times
- **Generation**: 2-5 seconds for answer generation

## Deployment

### Cloud Deployment

The application is fully dockerized and can be deployed to any cloud platform:

- **AWS**: ECS, EKS, or Elastic Beanstalk
- **Google Cloud**: Cloud Run, GKE, or App Engine
- **Azure**: Container Instances or AKS
- **DigitalOcean**: App Platform or Droplets

### Production Considerations

1. **Environment Variables**: Set `DEBUG=False` and proper `ALLOWED_HOSTS`
2. **Static Files**: Configure proper static file serving
3. **Database**: Consider PostgreSQL for production
4. **Caching**: Add Redis for caching vectorstore queries
5. **Monitoring**: Add logging and monitoring

## Development

### Adding New Features

1. **New Endpoints**: Add to `rag/views.py` and `rag/urls.py`
2. **UI Changes**: Modify templates in `rag/templates/`
3. **RAG Logic**: Update `rag/services.py`

### Management Commands

```bash
# Initialize vectorstore
python manage.py init_vectorstore

# Force recreate vectorstore
python manage.py init_vectorstore --force
```

## Troubleshooting

### Common Issues

1. **Google API Key Error**
   - Ensure your API key is valid and has Gemini API access
   - Check the `.env` file is properly loaded

2. **Vectorstore Not Found**
   - Run `python manage.py init_vectorstore`
   - Ensure the dataset file exists at `dataset/sermons_zac.csv`

3. **Memory Issues**
   - The vectorstore creation requires significant memory
   - Consider using a machine with at least 8GB RAM

4. **Docker Issues**
   - Ensure Docker and Docker Compose are installed
   - Check that ports 8000 is available

## License

This project is licensed under the MIT License - see the LICENSE file for details.