"""
Management command to check vectorstore status.
"""

from django.core.management.base import BaseCommand
from django.conf import settings
from rag.services import get_rag_service
import json


class Command(BaseCommand):
    help = 'Check the status of the vectorstore'

    def add_arguments(self, parser):
        parser.add_argument(
            '--json',
            action='store_true',
            help='Output status as JSON',
        )

    def handle(self, *args, **options):
        try:
            # Get RAG service
            rag_service = get_rag_service()
            
            # Get status
            status = rag_service.get_vectorstore_status()
            
            if options['json']:
                self.stdout.write(json.dumps(status, indent=2))
            else:
                self.stdout.write(
                    self.style.SUCCESS('Vectorstore Status:')
                )
                self.stdout.write(f"Path: {status['path']}")
                self.stdout.write(f"Exists: {status['exists']}")
                self.stdout.write(f"Loaded: {status['loaded']}")
                self.stdout.write(f"Ready: {status['ready']}")
                
                if 'document_count' in status:
                    self.stdout.write(f"Document count: {status['document_count']}")
                
                if status['ready']:
                    self.stdout.write(
                        self.style.SUCCESS('✅ RAG system is ready for queries!')
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR('❌ RAG system is not ready.')
                    )
                    
        except Exception as e:
            if options['json']:
                self.stdout.write(json.dumps({'error': str(e)}))
            else:
                self.stdout.write(
                    self.style.ERROR(f'Error checking vectorstore: {e}')
                )
