# Sermon RAG - AI-Powered Sermon Question Answering

A Retrieval-Augmented Generation (RAG) system that answers questions about sermons using AI. Built with Django, LangChain, FAISS, and Google Gemini.

## 🚀 Quick Deploy to Production

### Prerequisites
- [Fly.io CLI](https://fly.io/docs/hands-on/install-flyctl/)
- [Docker](https://docs.docker.com/get-docker/)
- Google API Key from [Google AI Studio](https://makersuite.google.com/app/apikey)

### One-Command Deployment

```bash
# Clone the repository
git clone <your-repo-url>
cd CFC-RAG

# Run the deployment script
./deploy.sh
```

The deployment script will:
- ✅ Check prerequisites
- ✅ Set up environment variables
- ✅ Create Fly.io app and volume
- ✅ Deploy the application
- ✅ Initialize the vectorstore
- ✅ Verify deployment

## 🏗️ Local Development

### Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd CFC-RAG

# Create virtual environment
python3 -m venv CFC_venv
source CFC_venv/bin/activate  # On Windows: CFC_venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp env.example .env
# Edit .env with your Google API key

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic

# Initialize vectorstore (first time only)
python manage.py init_vectorstore

# Start development server
python manage.py runserver
```

### Environment Variables

Create a `.env` file with:

```bash
# Django Configuration
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Google API Configuration
GOOGLE_API_KEY=your-google-api-key-here
```

## 🎯 Features

- **AI-Powered Q&A**: Ask questions about sermon content using Google Gemini
- **Semantic Search**: Find relevant sermon passages using FAISS vector search
- **YouTube Integration**: Direct links to sermon timestamps
- **Production Ready**: Optimized for deployment on Fly.io
- **Health Monitoring**: Built-in health checks and status endpoints
- **Auto-scaling**: Configured for optimal performance

## 📊 API Endpoints

### Query Sermons
```http
POST /api/query/
Content-Type: application/json

{
    "question": "What does the Bible teach about love?"
}
```

### Health Check
```http
GET /health/
```

### System Status
```http
GET /status/
```

## 🔧 Production Configuration

### Fly.io Configuration

The application is configured for production deployment on Fly.io with:

- **Auto-scaling**: 1-2 instances based on demand
- **Persistent Storage**: 10GB volume for data persistence
- **Health Checks**: Automatic monitoring and restart
- **SSL/TLS**: Automatic HTTPS with HSTS
- **Security Headers**: Production-grade security configuration

### Performance Optimizations

- **MMR Retrieval**: Diverse document retrieval for better results
- **Caching**: In-memory caching for improved response times
- **Connection Pooling**: Optimized database connections
- **Static File Optimization**: Compressed and cached static assets

## 📈 Monitoring

### Health Checks
- Application health: `/health/`
- System status: `/status/`
- Vectorstore status: `python manage.py check_vectorstore`

### Logs
```bash
# View application logs
fly logs

# SSH into running container
fly ssh console
```

### Scaling
```bash
# Scale horizontally
fly scale count 2

# Scale vertically
fly scale memory 8192
fly scale cpu 4
```

## 🛠️ Management Commands

### Initialize Vectorstore
```bash
python manage.py init_vectorstore
```

### Check Vectorstore Status
```bash
python manage.py check_vectorstore
```

### Force Recreate Vectorstore
```bash
python manage.py init_vectorstore --force
```

## 🔒 Security

- **HTTPS Only**: All production traffic is encrypted
- **Security Headers**: HSTS, CSP, XSS protection
- **CORS Configuration**: Restricted to production domains
- **Environment Variables**: Sensitive data stored as secrets
- **Non-root Container**: Application runs as non-privileged user

## 📁 Project Structure

```
CFC-RAG/
├── rag/                    # RAG application
│   ├── services.py        # RAG service implementation
│   ├── views.py           # API endpoints
│   └── management/        # Django management commands
├── sermon_rag/            # Django project settings
├── dataset/               # Sermon dataset
├── vectorstore/           # FAISS vectorstore
├── Dockerfile            # Production container
├── fly.toml              # Fly.io configuration
├── deploy.sh             # Deployment script
└── requirements.txt      # Python dependencies
```

## 🚨 Troubleshooting

### Common Issues

1. **Vectorstore not found**
   ```bash
   python manage.py init_vectorstore
   ```

2. **Google API Key issues**
   - Verify API key is set in environment
   - Check API key permissions

3. **Memory issues**
   ```bash
   fly scale memory 8192
   ```

4. **Deployment failures**
   ```bash
   fly logs
   fly status
   ```

### Debug Mode

For debugging, temporarily enable debug mode:
```bash
fly secrets set DEBUG="True"
fly deploy
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

For issues and questions:
- Check the [troubleshooting section](#-troubleshooting)
- Review the [production deployment guide](PRODUCTION_DEPLOYMENT.md)
- Open an issue on GitHub