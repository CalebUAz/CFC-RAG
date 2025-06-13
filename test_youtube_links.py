#!/usr/bin/env python3
"""
Test script for the enhanced RAG system with YouTube links and timestamps.
This script demonstrates the new query_sermons function with YouTube video links.
"""

import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sermon_rag.settings')
django.setup()

# Import the enhanced query function
from rag.services import query_sermons, get_rag_service


def test_timestamp_extraction():
    """Test the timestamp extraction functionality."""
    print("🧪 Testing timestamp extraction...")
    
    rag_service = get_rag_service()
    
    # Test cases for timestamp extraction
    test_cases = [
        ("This happens at 45s in the video", "45"),
        ("At 2:30 he talks about faith", "150"),  # 2*60 + 30 = 150
        ("1h 30m into the sermon", "5400"),  # 1*3600 + 30*60 = 5400
        ("Starting at 10:15 mark", "615"),  # 10*60 + 15 = 615
        ("No timestamp here", "0"),
        ("1:05 - this is important", "65"),  # 1*60 + 5 = 65
    ]
    
    for content, expected in test_cases:
        result = rag_service._extract_timestamp(content)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{content}' -> {result} (expected: {expected})")
    
    print()


def test_youtube_link_creation():
    """Test YouTube link creation."""
    print("🔗 Testing YouTube link creation...")

    rag_service = get_rag_service()

    test_cases = [
        ("dQw4w9WgXcQ", "45", "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=45s"),
        ("abc123", "0", "https://www.youtube.com/watch?v=abc123&t=0s"),
        ("", "30", ""),  # No video ID
        ("test123", "invalid", "https://www.youtube.com/watch?v=test123&t=0s"),  # Invalid timestamp
    ]

    for video_id, timestamp, expected in test_cases:
        result = rag_service._create_youtube_link(video_id, timestamp)
        status = "✅" if result == expected else "❌"
        print(f"{status} video_id='{video_id}', timestamp='{timestamp}' -> {result}")

    print()


def test_content_cleaning():
    """Test content preview cleaning."""
    print("🧹 Testing content cleaning...")

    rag_service = get_rag_service()

    test_cases = [
        ("into your 598s heart but a disciple is much more than 601s that", "into your heart but a disciple is much more than that"),
        ("This is 45s a test 123s with timestamps 789s", "This is a test with timestamps"),
        ("No timestamps here", "No timestamps here"),
        ("Multiple   spaces   should   be   cleaned", "Multiple spaces should be cleaned"),
        ("598s 601s 1234s only timestamps", "only timestamps"),
    ]

    for content, expected in test_cases:
        result = rag_service._clean_content_preview(content, max_length=200)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{content}' -> '{result}'")
        if result != expected:
            print(f"    Expected: '{expected}'")

    print()


def test_timestamp_formatting():
    """Test timestamp display formatting."""
    print("⏰ Testing timestamp formatting...")

    rag_service = get_rag_service()

    test_cases = [
        ("0", "0:00"),
        ("30", "0:30"),
        ("65", "1:05"),
        ("600", "10:00"),
        ("1000", "16:40"),
        ("3661", "1:01:01"),
        ("7200", "2:00:00"),
        ("invalid", "0:00"),
    ]

    for timestamp_seconds, expected in test_cases:
        result = rag_service._format_timestamp_display(timestamp_seconds)
        status = "✅" if result == expected else "❌"
        print(f"{status} {timestamp_seconds}s -> {result} (expected: {expected})")

    print()


def test_enhanced_query():
    """Test the enhanced query function."""
    print("🔍 Testing enhanced query function...")
    
    # Check if RAG service is ready
    rag_service = get_rag_service()
    if not rag_service.is_ready():
        print("❌ RAG service is not ready. Please check your configuration.")
        print("Make sure you have:")
        print("1. Set your GOOGLE_API_KEY in the .env file")
        print("2. The vectorstore exists at vectorstore/sermons_vectorstore")
        return
    
    print("✅ RAG service is ready!")
    
    # Test query
    test_question = "What does the Bible teach about contentment?"
    print(f"\n🧪 Testing with question: '{test_question}'")
    print("=" * 60)
    
    try:
        answer = query_sermons(test_question, show_sources=True)
        print("=" * 60)
        print("✅ Query completed successfully!")
    except Exception as e:
        print(f"❌ Error during query: {e}")


def main():
    """Main test function."""
    print("🚀 Testing Enhanced RAG System with YouTube Links")
    print("=" * 60)

    # Test individual components
    test_timestamp_extraction()
    test_youtube_link_creation()
    test_content_cleaning()
    test_timestamp_formatting()

    # Test the full query system
    test_enhanced_query()

    print("\n🎉 Testing completed!")
    print("\nTo use the enhanced query function in your code:")
    print("```python")
    print("from rag.services import query_sermons")
    print("answer = query_sermons('Your question here', show_sources=True)")
    print("```")


if __name__ == "__main__":
    main()
