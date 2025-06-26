"""
Views for the RAG application.
"""

import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View

from .services import get_rag_service


def index(request):
    """Main page with query interface."""
    return render(request, 'rag/index.html')


@csrf_exempt
@require_http_methods(["POST"])
def query_sermons(request):
    """API endpoint for querying sermons."""
    try:
        # Parse request data
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            question = data.get('question', '').strip()
        else:
            question = request.POST.get('question', '').strip()

        if not question:
            return JsonResponse({
                'error': 'Question is required'
            }, status=400)

        # Get RAG service
        rag_service = get_rag_service()

        if not rag_service.is_ready():
            return JsonResponse({
                'error': 'RAG system is not ready. Please try again later.'
            }, status=503)

        # Process query
        result = rag_service.query(question)

        return JsonResponse(result)

    except Exception as e:
        return JsonResponse({
            'error': f'An error occurred: {str(e)}'
        }, status=500)


def health_check(request):
    """Health check endpoint."""
    try:
        rag_service = get_rag_service()
        is_ready = rag_service.is_ready()

        return JsonResponse({
            'status': 'healthy' if is_ready else 'initializing',
            'rag_ready': is_ready
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'error': str(e)
        }, status=500)


def status(request):
    """Detailed status endpoint for RAG system."""
    try:
        rag_service = get_rag_service()
        status_info = rag_service.get_vectorstore_status()

        # Add component status
        status_info.update({
            'components': {
                'embeddings': rag_service.embeddings is not None,
                'llm': rag_service.llm is not None,
                'vectorstore': rag_service.vectorstore is not None,
                'retriever': rag_service.retriever is not None,
                'rag_chain': rag_service.rag_chain is not None,
            },
            'overall_status': 'ready' if rag_service.is_ready() else 'not_ready'
        })

        return JsonResponse(status_info)

    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'overall_status': 'error'
        }, status=500)


class QueryView(View):
    """Class-based view for handling queries."""

    def get(self, request):
        """Show query form."""
        return render(request, 'rag/query.html')

    def post(self, request):
        """Process query and show results."""
        question = request.POST.get('question', '').strip()

        if not question:
            return render(request, 'rag/query.html', {
                'error': 'Please enter a question.'
            })

        try:
            rag_service = get_rag_service()

            if not rag_service.is_ready():
                return render(request, 'rag/query.html', {
                    'error': 'RAG system is not ready. Please try again later.'
                })

            result = rag_service.query(question)

            return render(request, 'rag/results.html', {
                'result': result
            })

        except Exception as e:
            return render(request, 'rag/query.html', {
                'error': f'An error occurred: {str(e)}'
            })
