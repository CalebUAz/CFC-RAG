"""
Middleware to ensure RAG system is ready before processing requests.
"""

from django.http import JsonResponse
from django.shortcuts import render
from django.urls import resolve
from rag.services import get_rag_service
import logging

logger = logging.getLogger(__name__)


class RAGReadinessMiddleware:
    """
    Middleware to check if RAG system is ready before processing RAG-related requests.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.rag_service = None
        
    def __call__(self, request):
        # Check if this is a RAG-related request
        if self._is_rag_request(request):
            # Ensure RAG service is ready
            if not self._ensure_rag_ready():
                return self._handle_not_ready(request)
        
        response = self.get_response(request)
        return response
    
    def _is_rag_request(self, request):
        """Check if the request is RAG-related."""
        try:
            resolver_match = resolve(request.path_info)
            # Check if the request is for RAG app
            return resolver_match.app_name == 'rag'
        except:
            return False
    
    def _ensure_rag_ready(self):
        """Ensure RAG service is ready."""
        try:
            if self.rag_service is None:
                self.rag_service = get_rag_service()
            
            return self.rag_service.is_ready()
        except Exception as e:
            logger.error(f"Error checking RAG readiness: {e}")
            return False
    
    def _handle_not_ready(self, request):
        """Handle requests when RAG system is not ready."""
        error_message = "RAG system is initializing. Please try again in a moment."
        
        # Check if it's an API request
        if request.path.startswith('/api/') or request.content_type == 'application/json':
            return JsonResponse({
                'error': error_message,
                'status': 'initializing'
            }, status=503)
        
        # For web requests, render an error page
        return render(request, 'rag/not_ready.html', {
            'error': error_message
        }, status=503)


class RAGWarmupMiddleware:
    """
    Middleware to warm up RAG service on application startup.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.warmed_up = False
        
    def __call__(self, request):
        # Warm up on first request
        if not self.warmed_up:
            self._warmup()
            self.warmed_up = True
            
        response = self.get_response(request)
        return response
    
    def _warmup(self):
        """Warm up the RAG service."""
        try:
            logger.info("Warming up RAG service...")
            rag_service = get_rag_service()
            if rag_service.is_ready():
                logger.info("RAG service warmed up successfully")
            else:
                logger.warning("RAG service warmup completed but system not ready")
        except Exception as e:
            logger.error(f"Error during RAG warmup: {e}")
