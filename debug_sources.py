#!/usr/bin/env python3
"""
Debug script to test RAG service source retrieval.
"""

import os
import sys
import django

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sermon_rag.settings')
django.setup()

from rag.services import get_rag_service

def debug_sources():
    """Debug the source retrieval process."""
    print("🔍 Debugging RAG source retrieval...")
    
    # Get RAG service
    rag_service = get_rag_service()
    
    if not rag_service.is_ready():
        print("❌ RAG service is not ready!")
        return
    
    print("✅ RAG service is ready!")
    
    # Test question
    test_question = "What does the Bible teach about love?"
    print(f"\n❓ Testing with question: '{test_question}'")
    
    try:
        # Get relevant documents directly
        relevant_docs = rag_service.retriever.get_relevant_documents(test_question)
        print(f"\n📚 Retrieved {len(relevant_docs)} documents from vectorstore")
        
        # Analyze each document
        for i, doc in enumerate(relevant_docs, 1):
            print(f"\n📄 Document {i}:")
            print(f"  Title: {doc.metadata.get('title', 'Unknown')}")
            print(f"  Video ID: {doc.metadata.get('video_id', 'Unknown')}")
            print(f"  Author: {doc.metadata.get('author', 'Unknown')}")
            
            # Extract timestamp
            timestamp = rag_service._extract_timestamp(doc.page_content)
            print(f"  Timestamp: {timestamp}")
            
            # Show first 200 characters of content
            content_preview = doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
            print(f"  Content preview: {content_preview}")
            
            # Create source key
            video_id = doc.metadata.get('video_id', '')
            title = doc.metadata.get('title', 'Unknown Title')
            source_key = f"{video_id}_{title}_{timestamp}"
            print(f"  Source key: {source_key}")
        
        # Test the full query
        print(f"\n🤖 Testing full query...")
        result = rag_service.query(test_question)
        
        print(f"\n📊 Query Results:")
        print(f"  Answer length: {len(result['answer'])} characters")
        print(f"  Number of sources: {result['num_sources']}")
        print(f"  Sources:")
        
        for i, source in enumerate(result['sources'], 1):
            print(f"    {i}. {source['title']} - {source['timestamp_display']}")
            print(f"       Video: {source['youtube_link']}")
        
    except Exception as e:
        print(f"❌ Error during debugging: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_sources() 