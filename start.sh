#!/bin/bash

# Startup script for the Django RAG application

echo "Starting Django RAG Application..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "Please edit .env file with your Google API key and other settings."
    echo "You can get a Google API key from: https://makersuite.google.com/app/apikey"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "CFC_venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv CFC_venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source CFC_venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Install compatible numpy version
echo "Installing compatible numpy version..."
pip install "numpy<2"

# Run migrations
echo "Running migrations..."
python manage.py migrate

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Check if vectorstore exists, if not create it
if [ ! -d "vectorstore/sermons_vectorstore" ]; then
    echo "Vectorstore not found. Initializing..."
    echo "This may take several minutes..."
    echo "Make sure you have set your GOOGLE_API_KEY in the .env file!"
    python manage.py init_vectorstore
else
    echo "Vectorstore found. Skipping initialization."
fi

# Start the development server
echo "Starting Django development server..."
echo "Access the application at: http://localhost:8000"
python manage.py runserver 0.0.0.0:8000

# Start the development server
echo "Starting Django development server..."
python manage.py runserver 0.0.0.0:8000
