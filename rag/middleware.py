"""
Middleware for the RAG application.
"""

import time
import psutil
import gc
from django.http import JsonResponse
from django.conf import settings
from .services import get_rag_service


class RAGMiddleware:
    """Middleware to ensure RAG system is ready before processing requests."""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.last_cleanup = time.time()
        self.cleanup_interval = 300  # 5 minutes
    
    def __call__(self, request):
        # Check if we need to perform memory cleanup
        current_time = time.time()
        if current_time - self.last_cleanup > self.cleanup_interval:
            self._perform_memory_cleanup()
            self.last_cleanup = current_time
        
        # Check if this is a RAG-related request
        if request.path.startswith('/api/query') or request.path.startswith('/rag/'):
            try:
                rag_service = get_rag_service()
                
                # Check memory usage
                memory_usage = self._get_memory_usage()
                if memory_usage > 80:  # If memory usage > 80%
                    print(f"⚠️ High memory usage detected: {memory_usage:.1f}%")
                    rag_service.cleanup_memory(max_idle_time=60)  # More aggressive cleanup
                
                # Check if RAG system is ready
                if not rag_service.is_ready():
                    return JsonResponse({
                        'error': 'RAG system is initializing. Please try again in a moment.',
                        'status': 'initializing'
                    }, status=503)
                    
            except Exception as e:
                return JsonResponse({
                    'error': f'RAG system error: {str(e)}',
                    'status': 'error'
                }, status=500)
        
        response = self.get_response(request)
        return response
    
    def _get_memory_usage(self):
        """Get current memory usage percentage."""
        try:
            process = psutil.Process()
            memory_percent = process.memory_percent()
            return memory_percent
        except:
            return 0
    
    def _perform_memory_cleanup(self):
        """Perform periodic memory cleanup."""
        try:
            # Force garbage collection
            gc.collect()
            
            # Clean up RAG service cache
            rag_service = get_rag_service()
            rag_service._query_cache.cleanup()
            
            # Log memory usage
            memory_usage = self._get_memory_usage()
            print(f"🧹 Memory cleanup completed. Current usage: {memory_usage:.1f}%")
            
        except Exception as e:
            print(f"Error during memory cleanup: {e}")


class MemoryMonitoringMiddleware:
    """Middleware to monitor and log memory usage."""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Log memory usage before request
        start_memory = self._get_memory_usage()
        
        response = self.get_response(request)
        
        # Log memory usage after request
        end_memory = self._get_memory_usage()
        memory_diff = end_memory - start_memory
        
        # Log significant memory changes
        if abs(memory_diff) > 5:  # More than 5% change
            print(f"📊 Memory change: {start_memory:.1f}% → {end_memory:.1f}% (Δ{memory_diff:+.1f}%)")
        
        return response
    
    def _get_memory_usage(self):
        """Get current memory usage percentage."""
        try:
            process = psutil.Process()
            memory_percent = process.memory_percent()
            return memory_percent
        except:
            return 0
