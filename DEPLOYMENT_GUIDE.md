# Django RAG Deployment Guide

## 📁 Project Structure

```
CFC-RAG/
├── sermon_rag/              # Django project
│   ├── settings.py          # Configured with CORS, WhiteNoise, etc.
│   ├── urls.py              # Main URL routing
│   └── wsgi.py              # WSGI configuration
├── rag/                     # Main RAG application
│   ├── services.py          # RAG service with FAISS vectorstore
│   ├── views.py             # Web views and API endpoints
│   ├── urls.py              # App URL patterns
│   ├── templates/           # Beautiful HTML templates
│   └── management/commands/ # Django management commands
├── dataset/                 # Your sermon dataset
├── vectorstore/             # FAISS vector database
├── requirements.txt         # Python dependencies
├── Dockerfile              # Docker configuration
├── docker-compose.yml      # Docker Compose setup
├── start.sh                # Local development script
├── setup.py                # Automated setup script
└── .env                    # Environment configuration
```

## 🚀 Quick Start Options

### Option 1: Local Development (Recommended for testing)

1. **Set up your Google API key:**
   ```bash
   # Edit the .env file
   nano .env
   # Replace 'your-google-api-key-here' with your actual API key
   # Get it from: https://makersuite.google.com/app/apikey
   ```

2. **Run the setup script:**
   ```bash
   python3 setup.py
   ```

3. **Start the application:**
   ```bash
   ./start.sh
   ```

4. **Access the application:**
   - Open http://localhost:8000 in your browser
   - The vectorstore will be loaded automatically from your existing `vectorstore/sermons_vectorstore`

### Option 2: Docker Deployment (For production/cloud)

1. **Set up environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your Google API key
   ```

2. **Build and run:**
   ```bash
   docker-compose up --build
   ```

3. **Access the application:**
   - Open http://localhost:8000

## 🌟 Features Implemented

### ✅ Core RAG Functionality
- **Vectorstore Loading**: Uses your existing FAISS vectorstore with `FAISS.load_local("vectorstore/sermons_vectorstore", embeddings, allow_dangerous_deserialization=True)`
- **Google Gemini Integration**: Same embeddings and LLM as your notebook
- **Document Retrieval**: Top-5 similar chunks for each query
- **Answer Generation**: Contextual answers with source attribution

### ✅ Web Interface
- **Beautiful UI**: Modern, responsive design with Bootstrap
- **Query Interface**: Easy-to-use form for asking questions
- **Results Display**: Formatted answers with source information
- **Example Questions**: Pre-built questions to get users started
- **Real-time API**: AJAX-powered for smooth user experience

### ✅ API Endpoints
- `GET /` - Main web interface
- `POST /api/query/` - JSON API for queries
- `GET /health/` - Health check endpoint
- `GET /query/` - Alternative query form

### ✅ Production Ready
- **Docker Support**: Complete containerization
- **Static Files**: WhiteNoise for serving static files
- **CORS**: Configured for API access
- **Environment Variables**: Secure configuration
- **Health Checks**: Built-in monitoring

## 🔧 Configuration

### Environment Variables (.env)
```env
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
GOOGLE_API_KEY=your-google-api-key-here
```

### Google API Key Setup
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Add it to your `.env` file

## 🌐 Cloud Deployment

The application is ready for deployment to any cloud platform:

### AWS (ECS/EKS/Elastic Beanstalk)
```bash
# Build and push to ECR
docker build -t sermon-rag .
docker tag sermon-rag:latest your-account.dkr.ecr.region.amazonaws.com/sermon-rag:latest
docker push your-account.dkr.ecr.region.amazonaws.com/sermon-rag:latest
```

### Google Cloud (Cloud Run)
```bash
# Build and deploy
gcloud builds submit --tag gcr.io/your-project/sermon-rag
gcloud run deploy --image gcr.io/your-project/sermon-rag --platform managed
```

### DigitalOcean App Platform
- Connect your GitHub repository
- Set environment variables in the dashboard
- Deploy automatically

## 🧪 Testing

### API Testing
```bash
# Health check
curl http://localhost:8000/health/

# Query API
curl -X POST http://localhost:8000/api/query/ \
  -H "Content-Type: application/json" \
  -d '{"question": "What does the Bible teach about contentment?"}'
```

### Web Interface Testing
1. Open http://localhost:8000
2. Try the example questions
3. Ask your own questions about the sermons

## 🔍 Troubleshooting

### Common Issues

1. **Google API Key Error**
   - Ensure your API key is valid
   - Check it has Gemini API access
   - Verify the `.env` file is loaded

2. **Vectorstore Not Found**
   - Ensure `vectorstore/sermons_vectorstore` exists
   - Run `python manage.py init_vectorstore` if needed

3. **Dependencies Issues**
   - Use Python 3.8+
   - Install with `pip install "numpy<2"`
   - Use virtual environment

4. **Docker Issues**
   - Ensure Docker is running
   - Check port 8000 is available
   - Verify environment variables

## 📊 Performance

- **Dataset**: 417 sermons, ~3.8M words
- **Chunks**: 63,420 document chunks
- **Search**: Sub-second retrieval
- **Generation**: 2-5 seconds per answer

## 🎯 Next Steps

1. **Set your Google API key** in the `.env` file
2. **Test the application** locally
3. **Deploy to your preferred cloud platform**
4. **Customize the UI** if needed
5. **Add monitoring and logging** for production

## 🆘 Support

If you encounter any issues:
1. Check the logs: `docker-compose logs` or terminal output
2. Verify your Google API key is working
3. Ensure all dependencies are installed
4. Check the health endpoint: `/health/`

Your Django RAG application is now ready to serve questions about Zac Poonen's sermons! 🎉
