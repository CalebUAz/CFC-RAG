"""
RAG Service for Sermon Question Answering

This service handles the RAG (Retrieval-Augmented Generation) functionality
for querying sermon content using FAISS vectorstore and Google Gemini.
"""

import os
import re
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional
import time
import hashlib
from collections import OrderedDict

from django.conf import settings
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores.faiss import FAISS
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough


class MemoryEfficientCache:
    """Memory-efficient LRU cache with automatic cleanup."""
    
    def __init__(self, max_size=100, max_age=3600):
        self.max_size = max_size
        self.max_age = max_age
        self.cache = OrderedDict()
    
    def get(self, key: str) -> Optional[Dict]:
        """Get item from cache if not expired."""
        if key in self.cache:
            item = self.cache[key]
            if time.time() - item['timestamp'] < self.max_age:
                # Move to end (most recently used)
                self.cache.move_to_end(key)
                return item['data']
            else:
                # Remove expired item
                del self.cache[key]
        return None
    
    def set(self, key: str, data: Dict):
        """Set item in cache with automatic cleanup."""
        # Remove oldest items if cache is full
        while len(self.cache) >= self.max_size:
            self.cache.popitem(last=False)
        
        self.cache[key] = {
            'data': data,
            'timestamp': time.time()
        }
    
    def cleanup(self):
        """Remove expired items."""
        current_time = time.time()
        expired_keys = [
            key for key, item in self.cache.items()
            if current_time - item['timestamp'] > self.max_age
        ]
        for key in expired_keys:
            del self.cache[key]


class SermonRAGService:
    """Service class for handling sermon RAG operations."""
    
    def __init__(self):
        self.embeddings = None
        self.vectorstore = None
        self.llm = None
        self.retriever = None
        self.rag_chain = None
        self._initialized = False
        self._lazy_loaded = False  # Track if vectorstore is lazily loaded
        self._last_used = None  # Track last usage for cleanup
        self._query_cache = MemoryEfficientCache(max_size=50, max_age=1800)  # 30 min cache
    
    def _initialize_components(self):
        """Initialize all RAG components."""
        if self._initialized:
            return
            
        try:
            print("🚀 Initializing RAG components...")
            
            # Initialize embeddings
            self.embeddings = GoogleGenerativeAIEmbeddings(
                model="models/embedding-001",
                google_api_key=settings.GOOGLE_API_KEY
            )
            
            # Initialize LLM
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                temperature=0.0,
                google_api_key=settings.GOOGLE_API_KEY
            )
            
            # Don't load vectorstore immediately - use lazy loading
            self._initialized = True
            print("✅ RAG components initialized successfully!")
                
        except Exception as e:
            print(f"Error initializing RAG components: {e}")
            raise
    
    def _load_or_create_vectorstore(self):
        """Load existing vectorstore or create new one if not found."""
        vectorstore_path = settings.VECTORSTORE_PATH
        
        if vectorstore_path.exists():
            try:
                print("Loading existing vectorstore...")
                self.vectorstore = FAISS.load_local(
                    str(vectorstore_path), 
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
                print("✅ Vectorstore loaded successfully!")
            except Exception as e:
                print(f"Error loading vectorstore: {e}")
                print("Creating new vectorstore...")
                self._create_vectorstore()
        else:
            print("Vectorstore not found. Creating new one...")
            self._create_vectorstore()
    
    def _create_vectorstore(self):
        """Create new vectorstore from sermon dataset."""
        try:
            dataset_path = settings.DATASET_PATH
            if not dataset_path.exists():
                raise FileNotFoundError(f"Dataset not found at {dataset_path}")
            
            print("Loading sermon dataset...")
            df = pd.read_csv(dataset_path)
            
            # Clean the data
            df = df.dropna(subset=['sermon'])
            df['sermon'] = df['sermon'].apply(
                lambda x: x[6:] if x.lower().startswith('music ') else x
            )
            df['sermon'] = df['sermon'].apply(
                lambda x: re.sub(r'\d+s\s+music\s+', '', x, 
                                 flags=re.IGNORECASE))
            if 'Unnamed: 0' in df.columns:
                df.drop(columns=['Unnamed: 0'], inplace=True)
            df.reset_index(drop=True, inplace=True)
            
            print(f"📊 Dataset loaded: {len(df)} sermons")
            
            # Convert to documents
            documents = []
            for index, row in df.iterrows():
                doc = Document(
                    page_content=row['sermon'],
                    metadata={
                        "title": row['title'],
                        "author": row['author'],
                        "video_id": row['video_id'],
                        "doc_id": index
                    }
                )
                documents.append(doc)
            
            # Split documents
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=500,
                chunk_overlap=200,
                length_function=len,
                separators=["\n\n", "\n", " ", ""]
            )
            split_docs = text_splitter.split_documents(documents)
            print(f"🔪 Split into {len(split_docs)} chunks")
            
            # Create vectorstore with smaller initial batch
            print("⏳ Creating vector store... (this may take a few minutes)")
            self.vectorstore = FAISS.from_documents(
                documents=split_docs[0:100],  # Reduced from 500 to save memory
                embedding=self.embeddings
            )
            
            # Add remaining documents in smaller batches
            batch_size = 50  # Reduced from 100 to save memory
            for i in range(100, len(split_docs), batch_size):
                end_idx = min(i + batch_size, len(split_docs))
                self.vectorstore.add_documents(split_docs[i:end_idx])
                
                # Force garbage collection every few batches
                if i % (batch_size * 10) == 0:
                    import gc
                    gc.collect()
                    print(f"Processed {i}/{len(split_docs)} documents")
            
            # Save vectorstore
            vectorstore_path = settings.VECTORSTORE_PATH
            vectorstore_path.parent.mkdir(parents=True, exist_ok=True)
            self.vectorstore.save_local(str(vectorstore_path))
            print("💾 Vector store saved to disk")
            
        except Exception as e:
            print(f"Error creating vectorstore: {e}")
            raise
    
    def _create_rag_chain(self):
        """Create the RAG chain for question answering."""
        # Define the RAG prompt template
        rag_prompt = ChatPromptTemplate.from_template("""
You are a helpful assistant that answers questions based on sermon content from Zac Poonen.

Use the following context from the sermons to answer the question. If the context doesn't contain 
enough information to answer the question, say so honestly.

Context from sermons:
{context}

Question: {question}

Answer: Provide a thoughtful response based on the sermon content. Include relevant Bible verses 
or spiritual insights when mentioned in the context. Be helpful and encouraging in your tone.
""")
        
        # Create the RAG chain
        self.rag_chain = (
            {"context": self.retriever | self._format_docs, "question": RunnablePassthrough()}
            | rag_prompt
            | self.llm
            | StrOutputParser()
        )
    
    def _format_docs(self, docs: List[Document]) -> str:
        """Format retrieved documents for context."""
        formatted_context = []
        for i, doc in enumerate(docs, 1):
            title = doc.metadata.get('title', 'Unknown Title')
            # Clean the content and limit to 500 characters for context
            content = self._clean_content_preview(doc.page_content, max_length=500)
            formatted_context.append(f"Sermon {i}: {title}\n{content}\n")
        return "\n".join(formatted_context)

    def _extract_timestamp(self, content: str) -> str:
        """
        Extract timestamp from content.

        Looks for patterns like:
        - "10s" or "1s" (seconds)
        - "1:30" or "10:45" (minutes:seconds)
        - "1h 30m" or "2h 15m 30s" (hours, minutes, seconds)

        Args:
            content (str): The content to search for timestamps

        Returns:
            str: Timestamp in seconds for YouTube URL
        """
        # Look for various timestamp patterns in the entire content
        search_text = content.lower()

        # Pattern 1: Simple seconds like "10s", "45s"
        seconds_match = re.search(r'(\d+)s(?!\w)', search_text)
        if seconds_match:
            return seconds_match.group(1)

        # Pattern 2: Minutes:seconds like "1:30", "10:45"
        time_match = re.search(r'(\d+):(\d+)', search_text)
        if time_match:
            minutes = int(time_match.group(1))
            seconds = int(time_match.group(2))
            total_seconds = minutes * 60 + seconds
            return str(total_seconds)

        # Pattern 3: Hours, minutes, seconds like "1h 30m 45s"
        hms_match = re.search(r'(?:(\d+)h\s*)?(?:(\d+)m\s*)?(?:(\d+)s)?', search_text)
        if hms_match and any(hms_match.groups()):
            hours = int(hms_match.group(1) or 0)
            minutes = int(hms_match.group(2) or 0)
            seconds = int(hms_match.group(3) or 0)
            total_seconds = hours * 3600 + minutes * 60 + seconds
            if total_seconds > 0:
                return str(total_seconds)

        # Pattern 4: Look for time-like numbers at the beginning
        start_time_match = re.search(r'^(\d{1,2}):(\d{2})', search_text)
        if start_time_match:
            minutes = int(start_time_match.group(1))
            seconds = int(start_time_match.group(2))
            total_seconds = minutes * 60 + seconds
            return str(total_seconds)

        # Default to 0 if no timestamp found
        return "0"

    def _create_youtube_link(self, video_id: str, timestamp: str = "0") -> str:
        """
        Create a YouTube link with timestamp.

        Args:
            video_id (str): YouTube video ID
            timestamp (str): Timestamp in seconds

        Returns:
            str: Complete YouTube URL with timestamp
        """
        if not video_id:
            return ""

        # Ensure timestamp is valid
        try:
            int(timestamp)
        except (ValueError, TypeError):
            timestamp = "0"

        return f"https://www.youtube.com/watch?v={video_id}&t={timestamp}s"

    def _clean_content_preview(self, content: str, max_length: int = 200) -> str:
        """
        Clean content preview by removing timestamp markers and formatting.

        Args:
            content (str): Raw content from the document
            max_length (int): Maximum length of the preview

        Returns:
            str: Cleaned content preview
        """
        # Remove timestamp markers like "598s", "601s", etc.
        cleaned = re.sub(r'\b\d+s\b', '', content)

        # Remove extra whitespace that might be left after removing timestamps
        cleaned = re.sub(r'\s+', ' ', cleaned)

        # Remove leading/trailing whitespace
        cleaned = cleaned.strip()

        # Truncate to max length and add ellipsis if needed
        if len(cleaned) > max_length:
            cleaned = cleaned[:max_length].rsplit(' ', 1)[0] + "..."

        return cleaned

    def _format_timestamp_display(self, timestamp_seconds: str) -> str:
        """
        Format timestamp in seconds to human-readable format.

        Args:
            timestamp_seconds (str): Timestamp in seconds

        Returns:
            str: Formatted timestamp (e.g., "16:40", "1:23:45")
        """
        try:
            total_seconds = int(timestamp_seconds)
        except (ValueError, TypeError):
            return "0:00"

        if total_seconds == 0:
            return "0:00"

        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes}:{seconds:02d}"

    def _format_llm_response(self, response: str) -> str:
        """
        Format LLM response by converting markdown formatting to HTML.

        Args:
            response (str): Raw LLM response with markdown formatting

        Returns:
            str: Formatted response with HTML tags
        """
        # Convert **text** to <b>text</b> for bold formatting
        formatted = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', response)

        # Convert *text* to <i>text</i> for italic formatting
        formatted = re.sub(r'\*(.*?)\*', r'<i>\1</i>', formatted)

        # Convert line breaks to HTML line breaks for better web display
        formatted = formatted.replace('\n', '<br>')

        return formatted
    
    def query(self, question: str) -> Dict[str, Any]:
        """
        Query the RAG system with a question.
        
        Args:
            question (str): The question to ask
            
        Returns:
            Dict containing the answer and source information
        """
        # Initialize components if not already done
        if not self._initialized:
            self._initialize_components()
        
        # Ensure vectorstore is loaded if not already
        self._ensure_vectorstore_loaded()

        if not self.rag_chain:
            raise RuntimeError("RAG system not properly initialized")
        
        # Check cache first
        cache_key = hashlib.md5(question.encode()).hexdigest()
        cached_result = self._query_cache.get(cache_key)
        if cached_result:
            print("💾 Returning cached result")
            return cached_result
        
        try:
            # Update last used timestamp
            self._last_used = time.time()
            
            # Get relevant documents
            relevant_docs = self.retriever.get_relevant_documents(question)
            print(f"🔍 Retrieved {len(relevant_docs)} documents from vectorstore")
            
            # Generate answer
            raw_answer = self.rag_chain.invoke(question)

            # Format the answer for better display
            answer = self._format_llm_response(raw_answer)

            # Format sources with YouTube links and deduplicate
            sources = []
            seen_sources = set()  # Track unique source combinations
            print(f"🔍 Processing {len(relevant_docs)} documents for sources...")
            
            for doc in relevant_docs:
                video_id = doc.metadata.get('video_id', '')
                title = doc.metadata.get('title', 'Unknown Title')
                timestamp = self._extract_timestamp(doc.page_content)
                
                # Create unique identifier for deduplication including timestamp
                # This allows multiple sources from same sermon if they have different timestamps
                source_key = f"{video_id}_{title}_{timestamp}"
                
                print(f"  📄 Document: {title} | Video: {video_id} | Timestamp: {timestamp} | Key: {source_key}")
                
                # Skip if we've already seen this exact source with same timestamp
                if source_key in seen_sources:
                    print(f"    ⏭️ Skipping duplicate source")
                    continue
                
                seen_sources.add(source_key)
                print(f"    ✅ Adding new source")
                
                youtube_link = self._create_youtube_link(video_id, timestamp)

                source_info = {
                    'title': title,
                    'author': doc.metadata.get('author', 'Unknown Author'),
                    'video_id': video_id,
                    'timestamp': timestamp,
                    'timestamp_display': self._format_timestamp_display(timestamp),
                    'youtube_link': youtube_link,
                    'content_preview': self._clean_content_preview(doc.page_content)
                }
                sources.append(source_info)
            
            result = {
                'question': question,
                'answer': answer,
                'sources': sources,
                'num_sources': len(sources)
            }
            
            # Cache the result
            self._query_cache.set(cache_key, result)
            
            return result
            
        except Exception as e:
            print(f"Error processing query: {e}")
            return {
                'question': question,
                'answer': f"Sorry, I encountered an error while processing your question: {str(e)}",
                'sources': [],
                'num_sources': 0
            }
    
    def is_ready(self) -> bool:
        """Check if the RAG system is ready to handle queries."""
        if not self._initialized:
            try:
                self._initialize_components()
            except Exception as e:
                print(f"Error during initialization: {e}")
                return False
        
        # Check if vectorstore is loaded and initialized
        return all([
            self.embeddings is not None,
            self.vectorstore is not None,
            self.llm is not None,
            self.retriever is not None,
            self.rag_chain is not None
        ])

    def get_vectorstore_status(self) -> Dict[str, Any]:
        """Get detailed status of the vectorstore."""
        vectorstore_path = settings.VECTORSTORE_PATH

        status = {
            'exists': vectorstore_path.exists(),
            'path': str(vectorstore_path),
            'loaded': self.vectorstore is not None,
            'ready': self.is_ready()
        }

        if self.vectorstore:
            try:
                # Get approximate document count
                status['document_count'] = self.vectorstore.index.ntotal
            except:
                status['document_count'] = 'unknown'

        return status

    def cleanup_memory(self, max_idle_time=300):
        """Clean up memory by unloading vectorstore if idle."""
        if (self._lazy_loaded and self._last_used and 
            time.time() - self._last_used > max_idle_time):
            print("🧹 Cleaning up memory - unloading vectorstore...")
            self.vectorstore = None
            self.retriever = None
            self.rag_chain = None
            self._lazy_loaded = False
            import gc
            gc.collect()  # Force garbage collection


# Global instance - Initialize lazily
_rag_service = None

def get_rag_service() -> SermonRAGService:
    """Get the global RAG service instance."""
    global _rag_service
    if _rag_service is None:
        print("🔄 Creating RAG service instance...")
        _rag_service = SermonRAGService()
    return _rag_service


def query_sermons(question: str, show_sources: bool = True):
    """
    Query the RAG system with a question about the sermons.
    Enhanced version with YouTube links and timestamps.

    Args:
        question (str): The question to ask
        show_sources (bool): Whether to show the source documents

    Returns:
        str: The generated answer
    """
    print(f"❓ Question: {question}")
    print("🔍 Searching for relevant content...")

    # Get RAG service
    rag_service = get_rag_service()

    if not rag_service.is_ready():
        print("❌ RAG system is not ready. Please check your configuration.")
        return "RAG system is not ready. Please check your configuration."

    try:
        # Get relevant documents
        relevant_docs = rag_service.retriever.get_relevant_documents(question)

        if show_sources:
            print("\n📚 Sources found:")
            seen_sources = set()  # Track unique source combinations
            source_count = 0
            
            for doc in relevant_docs:
                title = doc.metadata.get('title', 'Unknown Title')
                video_id = doc.metadata.get('video_id', '')
                
                # Extract timestamp using the service method
                timestamp = rag_service._extract_timestamp(doc.page_content)
                
                # Create unique identifier for deduplication including timestamp
                # This allows multiple sources from same sermon if they have different timestamps
                source_key = f"{video_id}_{title}_{timestamp}"
                
                # Skip if we've already seen this exact source with same timestamp
                if source_key in seen_sources:
                    continue
                
                seen_sources.add(source_key)
                source_count += 1

                # Create YouTube link with timestamp
                youtube_link = rag_service._create_youtube_link(video_id, timestamp)

                if youtube_link:
                    print(f"{source_count}. {title} - [Watch Video]({youtube_link})")
                else:
                    print(f"{source_count}. {title} - (No video link available)")

        # Generate answer using the service
        result = rag_service.query(question)
        answer = result['answer']

        print("\n🤖 Generating answer...")
        print("\n💬 Answer:")
        print(answer)

        return answer

    except Exception as e:
        error_msg = f"Error processing query: {str(e)}"
        print(f"❌ {error_msg}")
        return error_msg


def initialize_rag_service():
    """Explicitly initialize the RAG service. Useful for startup scripts."""
    global _rag_service
    if _rag_service is None or not _rag_service.is_ready():
        print("🔄 Initializing RAG service...")
        _rag_service = SermonRAGService()
        if _rag_service.is_ready():
            print("✅ RAG service ready!")
            return True
        else:
            print("❌ RAG service failed to initialize properly")
            return False
    else:
        print("✅ RAG service already initialized and ready")
        return True


# Final startup message
print("🎉 RAG services module loaded successfully!")
