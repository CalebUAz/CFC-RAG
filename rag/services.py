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

from django.conf import settings
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores.faiss import FAISS
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough


class SermonRAGService:
    """Service class for handling sermon RAG operations."""
    
    def __init__(self):
        self.embeddings = None
        self.vectorstore = None
        self.llm = None
        self.retriever = None
        self.rag_chain = None
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize all RAG components."""
        try:
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
            
            # Load or create vectorstore
            self._load_or_create_vectorstore()
            
            # Create retriever
            if self.vectorstore:
                self.retriever = self.vectorstore.as_retriever(
                    search_type="similarity",
                    search_kwargs={"k": 5}
                )
                
                # Create RAG chain
                self._create_rag_chain()
                
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
            
            # Create vectorstore
            print("⏳ Creating vector store... (this may take a few minutes)")
            self.vectorstore = FAISS.from_documents(
                documents=split_docs[0:100],
                embedding=self.embeddings
            )
            
            # Add remaining documents in batches
            for i in range(100, len(split_docs), 100):
                self.vectorstore.add_documents(split_docs[i:i+100])
                if i % 1000 == 0:
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
            content = doc.page_content[:500] + "..." if len(doc.page_content) > 500 else doc.page_content
            formatted_context.append(f"Sermon {i}: {title}\n{content}\n")
        return "\n".join(formatted_context)
    
    def query(self, question: str) -> Dict[str, Any]:
        """
        Query the RAG system with a question.
        
        Args:
            question (str): The question to ask
            
        Returns:
            Dict containing the answer and source information
        """
        if not self.rag_chain:
            raise RuntimeError("RAG system not properly initialized")
        
        try:
            # Get relevant documents
            relevant_docs = self.retriever.get_relevant_documents(question)
            
            # Generate answer
            answer = self.rag_chain.invoke(question)
            
            # Format sources
            sources = []
            for doc in relevant_docs:
                sources.append({
                    'title': doc.metadata.get('title', 'Unknown Title'),
                    'author': doc.metadata.get('author', 'Unknown Author'),
                    'video_id': doc.metadata.get('video_id', ''),
                    'content_preview': doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
                })
            
            return {
                'question': question,
                'answer': answer,
                'sources': sources,
                'num_sources': len(sources)
            }
            
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
        return all([
            self.embeddings is not None,
            self.vectorstore is not None,
            self.llm is not None,
            self.retriever is not None,
            self.rag_chain is not None
        ])


# Global instance
_rag_service = None

def get_rag_service() -> SermonRAGService:
    """Get or create the global RAG service instance."""
    global _rag_service
    if _rag_service is None:
        _rag_service = SermonRAGService()
    return _rag_service
