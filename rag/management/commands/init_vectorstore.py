"""
Management command to initialize the vectorstore.
"""

import os
import sys
from django.core.management.base import BaseCommand
from django.conf import settings
from rag.services import SermonRAGService


class Command(BaseCommand):
    help = 'Initialize the vectorstore from the sermon dataset'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force recreation of vectorstore even if it exists',
        )
        parser.add_argument(
            '--check-only',
            action='store_true',
            help='Only check if vectorstore exists and is valid',
        )

    def handle(self, *args, **options):
        try:
            # Check if Google API key is available
            if not settings.GOOGLE_API_KEY:
                self.stdout.write(
                    self.style.ERROR('❌ GOOGLE_API_KEY not found in environment variables')
                )
                self.stdout.write('Please set GOOGLE_API_KEY in your environment or .env file')
                sys.exit(1)

            # Check if dataset exists
            if not settings.DATASET_PATH.exists():
                self.stdout.write(
                    self.style.ERROR(f'❌ Dataset not found at {settings.DATASET_PATH}')
                )
                self.stdout.write('Please ensure the dataset file exists')
                sys.exit(1)

            # Check if vectorstore already exists
            vectorstore_exists = settings.VECTORSTORE_PATH.exists()
            
            if options['check_only']:
                if vectorstore_exists:
                    self.stdout.write(
                        self.style.SUCCESS('✅ Vectorstore exists and is ready')
                    )
                    return
                else:
                    self.stdout.write(
                        self.style.WARNING('⚠️ Vectorstore does not exist')
                    )
                    return

            if vectorstore_exists and not options['force']:
                self.stdout.write(
                    self.style.WARNING('⚠️ Vectorstore already exists. Use --force to recreate.')
                )
                return

            if vectorstore_exists and options['force']:
                self.stdout.write('🔄 Recreating vectorstore...')
                # Remove existing vectorstore
                import shutil
                shutil.rmtree(settings.VECTORSTORE_PATH)
            else:
                self.stdout.write('🚀 Initializing vectorstore...')

            # Create vectorstore directory
            settings.VECTORSTORE_PATH.parent.mkdir(parents=True, exist_ok=True)

            # Initialize RAG service (this will create the vectorstore)
            self.stdout.write('📚 Loading sermon dataset...')
            rag_service = SermonRAGService()

            if rag_service.is_ready():
                self.stdout.write(
                    self.style.SUCCESS('✅ Vectorstore initialized successfully!')
                )
                
                # Get status information
                status = rag_service.get_vectorstore_status()
                if 'document_count' in status and status['document_count'] != 'unknown':
                    self.stdout.write(f'📊 Vectorstore contains {status["document_count"]} documents')
                
                self.stdout.write('🎉 RAG system is ready for queries!')
            else:
                self.stdout.write(
                    self.style.ERROR('❌ Failed to initialize vectorstore')
                )
                sys.exit(1)

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error initializing vectorstore: {e}')
            )
            sys.exit(1)
