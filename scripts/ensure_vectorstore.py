#!/usr/bin/env python
"""
Script to ensure vectorstore is ready before starting the application.
This can be run as part of deployment or startup process.
"""

import os
import sys
import django
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sermon_rag.settings')
django.setup()

from django.conf import settings
from rag.services import get_rag_service


def main():
    """Main function to ensure vectorstore is ready."""
    print("🔍 Checking vectorstore status...")
    
    try:
        # Get RAG service (this will initialize everything)
        rag_service = get_rag_service()
        
        # Check if ready
        if rag_service.is_ready():
            print("✅ Vectorstore is ready!")
            
            # Get status details
            status = rag_service.get_vectorstore_status()
            print(f"📊 Vectorstore path: {status['path']}")
            print(f"📊 Document count: {status.get('document_count', 'unknown')}")
            
            return 0
        else:
            print("❌ Vectorstore is not ready!")
            return 1
            
    except Exception as e:
        print(f"❌ Error checking vectorstore: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
