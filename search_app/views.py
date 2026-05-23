import time
import logging
import re

from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.conf import settings
from django.utils.html import escape
from django.utils.safestring import mark_safe

from .models import Document, IndexEntry, CorpusStats
from .ranker import search

logger = logging.getLogger('search_app')

RESULTS_PER_PAGE = getattr(settings, 'SEARCH_RESULTS_PER_PAGE', 10)
MAX_QUERY_LENGTH = 500


def home(request):
    """Google-style homepage with centered search bar."""
    return render(request, 'search_app/home.html')


def search_results(request):
    """Search results page."""
    query = request.GET.get('q', '').strip()
    model = request.GET.get('model', 'vsm').lower()
    page_number = request.GET.get('page', 1)

    if model not in ('vsm', 'bm25'):
        model = 'vsm'

    context = {
        'query': query,
        'model': model,
        'results': [],
        'total_results': 0,
        'search_time_ms': 0,
        'error': None,
        'page_obj': None,
    }

    if not query:
        context['error'] = 'empty'
        return render(request, 'search_app/results.html', context)

    if len(query) > MAX_QUERY_LENGTH:
        context['error'] = 'too_long'
        context['max_length'] = MAX_QUERY_LENGTH
        return render(request, 'search_app/results.html', context)

    # Check if index is empty
    if not IndexEntry.objects.exists():
        context['error'] = 'no_index'
        return render(request, 'search_app/results.html', context)

    try:
        start = time.time()
        raw_results = search(query, model=model, top_k=1000)
        elapsed_ms = round((time.time() - start) * 1000)

        # Build enriched results with highlighted snippets
        enriched = []
        for r in raw_results:
            doc = r['doc']
            query_terms = r['query_terms']
            snippet = doc.get_snippet(query_terms, length=200)
            highlighted_snippet = highlight_terms(snippet, query_terms)
            highlighted_title = highlight_terms(doc.title, query_terms)
            enriched.append({
                'doc': doc,
                'score': r['score'],
                'snippet': highlighted_snippet,
                'title': highlighted_title,
                'query_terms': query_terms,
            })

        total = len(enriched)

        # Paginate
        paginator = Paginator(enriched, RESULTS_PER_PAGE)
        page_obj = paginator.get_page(page_number)

        context.update({
            'results': page_obj,
            'page_obj': page_obj,
            'total_results': total,
            'search_time_ms': elapsed_ms,
        })

    except Exception as e:
        logger.error(f'Error during search for query="{query}": {e}', exc_info=True)
        context['error'] = 'server_error'

    return render(request, 'search_app/results.html', context)


def document_detail(request, doc_id):
    """Full document view."""
    doc = get_object_or_404(Document, id=doc_id)
    query = request.GET.get('q', '')
    return render(request, 'search_app/document.html', {'doc': doc, 'query': query})


def highlight_terms(text, terms):
    """Wrap matched query terms in <strong> tags."""
    if not terms or not text:
        return escape(text)

    escaped = escape(text)
    for term in sorted(set(terms), key=len, reverse=True):
        if len(term) < 2:
            continue
        pattern = re.compile(re.escape(term), re.IGNORECASE)
        escaped = pattern.sub(
            lambda m: f'<strong class="highlight">{m.group(0)}</strong>',
            escaped
        )
    return mark_safe(escaped)
