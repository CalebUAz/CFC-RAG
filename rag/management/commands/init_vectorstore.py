"""
Management command to initialize the vectorstore.
"""

from django.core.management.base import BaseCommand
from django.conf import settings
from rag.services import SermonRAGService


class Command(BaseCommand):
    help = 'Initialize the vectorstore for the RAG system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force recreation of vectorstore even if it exists',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Starting vectorstore initialization...')
        )
        
        try:
            # Check if vectorstore exists
            vectorstore_path = settings.VECTORSTORE_PATH
            
            if vectorstore_path.exists() and not options['force']:
                self.stdout.write(
                    self.style.WARNING(
                        f'Vectorstore already exists at {vectorstore_path}. '
                        'Use --force to recreate it.'
                    )
                )
                return
            
            # Initialize RAG service (this will create vectorstore if needed)
            self.stdout.write('Initializing RAG service...')
            rag_service = SermonRAGService()
            
            if rag_service.is_ready():
                self.stdout.write(
                    self.style.SUCCESS(
                        'Vectorstore initialized successfully!'
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR(
                        'Failed to initialize vectorstore.'
                    )
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error initializing vectorstore: {e}')
            )
