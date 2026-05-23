"""
Management command: python manage.py index_docs

Usage:
  python manage.py index_docs                  # Index all unindexed documents
  python manage.py index_docs --all            # Re-index all documents
  python manage.py index_docs --file path.txt  # Ingest a single file and index it
  python manage.py index_docs --dir ./corpus   # Ingest all files in a directory
"""
import os
import logging
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

logger = logging.getLogger('search_app')


class Command(BaseCommand):
    help = 'Index documents into the WolloNet search engine'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all', action='store_true',
            help='Re-index all documents (not just unindexed ones)'
        )
        parser.add_argument(
            '--file', type=str,
            help='Path to a single document file (.txt, .pdf, .html) to ingest and index'
        )
        parser.add_argument(
            '--dir', type=str,
            help='Path to a directory of documents to ingest and index'
        )

    def handle(self, *args, **options):
        from search_app.models import Document
        from search_app.indexer import build_index

        # --- Ingest files if specified ---
        if options['file']:
            self._ingest_file(options['file'])

        if options['dir']:
            self._ingest_directory(options['dir'])

        # --- Build index ---
        self.stdout.write(self.style.NOTICE('Starting indexing...'))

        if options['all']:
            # Reset is_indexed flag for all documents
            Document.objects.all().update(is_indexed=False)
            self.stdout.write('Marked all documents for re-indexing.')

        stats = build_index(incremental=True)

        self.stdout.write(self.style.SUCCESS(
            f'\nIndexing complete:\n'
            f'  Documents indexed : {stats["indexed_count"]}\n'
            f'  Unique terms      : {stats["unique_terms"]}\n'
            f'  Elapsed time      : {stats["elapsed_seconds"]}s\n'
            f'  Skipped (errors)  : {stats["skipped_count"]}'
        ))

    def _ingest_file(self, filepath):
        """Ingest a single file into the Document model."""
        from search_app.models import Document

        path = Path(filepath)
        if not path.exists():
            raise CommandError(f'File not found: {filepath}')

        self.stdout.write(f'Ingesting file: {path.name}')
        text, title = self._extract_text(path)

        if not text:
            self.stdout.write(self.style.WARNING(f'  Skipped (no text extracted): {path.name}'))
            return

        doc, created = Document.objects.update_or_create(
            file_path=str(path.resolve()),
            defaults={
                'title': title,
                'raw_text': text,
                'pub_date': timezone.now(),
                'is_indexed': False,
            }
        )
        action = 'Created' if created else 'Updated'
        self.stdout.write(self.style.SUCCESS(f'  {action}: "{title}"'))

    def _ingest_directory(self, dirpath):
        """Ingest all supported files in a directory."""
        path = Path(dirpath)
        if not path.is_dir():
            raise CommandError(f'Directory not found: {dirpath}')

        supported = ('.txt', '.pdf', '.html', '.htm')
        files = [f for f in path.iterdir() if f.suffix.lower() in supported]

        if not files:
            self.stdout.write(self.style.WARNING(f'No supported files found in {dirpath}'))
            return

        self.stdout.write(f'Found {len(files)} file(s) in {dirpath}')
        for f in files:
            self._ingest_file(str(f))

    def _extract_text(self, path):
        """Extract plain text and title from a file."""
        suffix = path.suffix.lower()
        title = path.stem.replace('_', ' ').replace('-', ' ').title()

        if suffix == '.txt':
            return self._read_txt(path), title
        elif suffix == '.pdf':
            return self._read_pdf(path), title
        elif suffix in ('.html', '.htm'):
            return self._read_html(path), title
        else:
            logger.warning(f'Unsupported file type: {path}')
            return '', title

    def _read_txt(self, path):
        try:
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                return f.read()
        except Exception as e:
            logger.warning(f'Failed to read TXT file {path}: {e}')
            return ''

    def _read_pdf(self, path):
        try:
            import PyPDF2
            text_parts = []
            with open(path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text_parts.append(page.extract_text() or '')
            return '\n'.join(text_parts)
        except ImportError:
            logger.warning('PyPDF2 not installed; cannot read PDF files.')
            return ''
        except Exception as e:
            logger.warning(f'Failed to parse PDF {path}: {e}')
            return ''

    def _read_html(self, path):
        try:
            from bs4 import BeautifulSoup
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                soup = BeautifulSoup(f.read(), 'lxml')
            # Remove script, style, head content
            for tag in soup(['script', 'style', 'head', 'meta', 'link']):
                tag.decompose()
            return soup.get_text(separator=' ', strip=True)
        except ImportError:
            logger.warning('BeautifulSoup/lxml not installed; cannot read HTML files.')
            return ''
        except Exception as e:
            logger.warning(f'Failed to parse HTML {path}: {e}')
            return ''
