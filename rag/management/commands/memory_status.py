"""
Management command to check memory usage and perform cleanup.
"""

import psutil
import gc
from django.core.management.base import BaseCommand
from rag.services import get_rag_service


class Command(BaseCommand):
    help = 'Check memory usage and perform cleanup if needed'

    def add_arguments(self, parser):
        parser.add_argument(
            '--cleanup',
            action='store_true',
            help='Perform memory cleanup',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force aggressive cleanup',
        )

    def handle(self, *args, **options):
        try:
            # Get system memory info
            system_memory = psutil.virtual_memory()
            process = psutil.Process()
            
            self.stdout.write(
                self.style.SUCCESS('📊 Memory Status Report:')
            )
            self.stdout.write(f"System Total: {system_memory.total / (1024**3):.1f} GB")
            self.stdout.write(f"System Available: {system_memory.available / (1024**3):.1f} GB")
            self.stdout.write(f"System Usage: {system_memory.percent:.1f}%")
            self.stdout.write(f"Process Memory: {process.memory_info().rss / (1024**2):.1f} MB")
            self.stdout.write(f"Process Usage: {process.memory_percent():.1f}%")
            
            # Get RAG service status
            rag_service = get_rag_service()
            self.stdout.write(f"RAG Service Ready: {rag_service.is_ready()}")
            self.stdout.write(f"Vectorstore Loaded: {rag_service.vectorstore is not None}")
            self.stdout.write(f"Cache Size: {len(rag_service._query_cache.cache)}")
            
            # Perform cleanup if requested
            if options['cleanup']:
                self.stdout.write("🧹 Performing memory cleanup...")
                
                # Force garbage collection
                collected = gc.collect()
                self.stdout.write(f"Garbage collected: {collected} objects")
                
                # Clean up RAG service cache
                rag_service._query_cache.cleanup()
                self.stdout.write("Cache cleaned up")
                
                # Force cleanup if requested
                if options['force']:
                    rag_service.cleanup_memory(max_idle_time=0)
                    self.stdout.write("Forced vectorstore cleanup")
                
                # Report memory after cleanup
                process = psutil.Process()
                self.stdout.write(f"Memory after cleanup: {process.memory_info().rss / (1024**2):.1f} MB")
                self.stdout.write(f"Usage after cleanup: {process.memory_percent():.1f}%")
                
                self.stdout.write(
                    self.style.SUCCESS('✅ Memory cleanup completed!')
                )
            
            # Warning if memory usage is high
            if system_memory.percent > 80:
                self.stdout.write(
                    self.style.WARNING('⚠️ High system memory usage detected!')
                )
            
            if process.memory_percent() > 50:
                self.stdout.write(
                    self.style.WARNING('⚠️ High process memory usage detected!')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error checking memory: {e}')
            ) 