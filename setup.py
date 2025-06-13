#!/usr/bin/env python3
"""
Setup script for the Django RAG application.
This script helps users set up the application step by step.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def run_command(command, description=""):
    """Run a shell command and handle errors."""
    print(f"Running: {description or command}")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        if e.stderr:
            print(f"Error output: {e.stderr}")
        return False


def check_python():
    """Check if Python 3.8+ is available."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("Error: Python 3.8 or higher is required.")
        return False
    print(f"✓ Python {version.major}.{version.minor}.{version.micro} found")
    return True


def setup_environment():
    """Set up the virtual environment."""
    venv_path = Path("CFC_venv")
    
    if venv_path.exists():
        print("✓ Virtual environment already exists")
        return True
    
    print("Creating virtual environment...")
    if not run_command("python3 -m venv CFC_venv", "Creating virtual environment"):
        return False
    
    print("✓ Virtual environment created")
    return True


def install_dependencies():
    """Install Python dependencies."""
    print("Installing dependencies...")
    
    # Activate virtual environment and install dependencies
    if os.name == 'nt':  # Windows
        pip_path = "CFC_venv\\Scripts\\pip"
    else:  # Unix/Linux/macOS
        pip_path = "CFC_venv/bin/pip"
    
    commands = [
        f"{pip_path} install --upgrade pip",
        f"{pip_path} install -r requirements.txt",
        f"{pip_path} install 'numpy<2'",  # Ensure compatible numpy version
    ]
    
    for cmd in commands:
        if not run_command(cmd):
            return False
    
    print("✓ Dependencies installed")
    return True


def setup_env_file():
    """Set up the environment file."""
    env_path = Path(".env")
    env_example_path = Path(".env.example")
    
    if env_path.exists():
        print("✓ .env file already exists")
        return True
    
    if not env_example_path.exists():
        print("Error: .env.example file not found")
        return False
    
    # Copy example file
    shutil.copy(env_example_path, env_path)
    print("✓ .env file created from template")
    
    # Prompt user for Google API key
    print("\n" + "="*60)
    print("IMPORTANT: You need to set up your Google API key!")
    print("1. Go to: https://makersuite.google.com/app/apikey")
    print("2. Create a new API key")
    print("3. Edit the .env file and replace 'your-google-api-key-here' with your actual API key")
    print("="*60 + "\n")
    
    return True


def run_migrations():
    """Run Django migrations."""
    print("Running Django migrations...")
    
    if os.name == 'nt':  # Windows
        python_path = "CFC_venv\\Scripts\\python"
    else:  # Unix/Linux/macOS
        python_path = "CFC_venv/bin/python"
    
    if not run_command(f"{python_path} manage.py migrate", "Running migrations"):
        return False
    
    print("✓ Migrations completed")
    return True


def collect_static():
    """Collect static files."""
    print("Collecting static files...")
    
    if os.name == 'nt':  # Windows
        python_path = "CFC_venv\\Scripts\\python"
    else:  # Unix/Linux/macOS
        python_path = "CFC_venv/bin/python"
    
    if not run_command(f"{python_path} manage.py collectstatic --noinput", "Collecting static files"):
        return False
    
    print("✓ Static files collected")
    return True


def main():
    """Main setup function."""
    print("Django RAG Application Setup")
    print("="*40)
    
    # Check Python version
    if not check_python():
        sys.exit(1)
    
    # Set up virtual environment
    if not setup_environment():
        print("Failed to set up virtual environment")
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("Failed to install dependencies")
        sys.exit(1)
    
    # Set up environment file
    if not setup_env_file():
        print("Failed to set up environment file")
        sys.exit(1)
    
    # Run migrations
    if not run_migrations():
        print("Failed to run migrations")
        sys.exit(1)
    
    # Collect static files
    if not collect_static():
        print("Failed to collect static files")
        sys.exit(1)
    
    print("\n" + "="*60)
    print("✓ Setup completed successfully!")
    print("\nNext steps:")
    print("1. Edit the .env file with your Google API key")
    print("2. Run: ./start.sh (or python CFC_venv/bin/python manage.py runserver)")
    print("3. Open http://localhost:8000 in your browser")
    print("="*60)


if __name__ == "__main__":
    main()
