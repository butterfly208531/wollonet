"""
Indexer for WolloNet Search Engine.
Builds the inverted index with TF-IDF weights and BM25 corpus stats.
"""
import json
import math
import logging
import time
from collections import defaultdict
from pathlib import Path

from django.conf import settings

from .preprocessor import preprocess, get_default_stemmer

logger = logging.getLogger('search_app')


def compute_tf(term_count, total_tokens):
    """TF = raw count / total token count in document."""
    if total_tokens == 0:
        return 0.0
    return term_count / total_tokens


def compute_idf(num_docs, doc_freq):
    """IDF = log10(N / df). Returns 0 if df is 0."""
    if doc_freq == 0:
        return 0.0
    return math.log10(num_docs / doc_freq)


def build_index(documents=None, incremental=False):
    """
    Build or update the inverted index.

    Args:
        documents: queryset of Document objects to index. If None, indexes all unindexed docs.
        incremental: if True, only process documents with is_indexed=False.

    Returns:
        dict with stats: {indexed_count, unique_terms, elapsed_seconds, skipped_count}
    """
    from .models import Document, IndexEntry, CorpusStats, DocumentLength

    start_time = time.time()
    stemmer = get_default_stemmer()
    skipped = 0

    if documents is None:
        if incremental:
            documents = Document.objects.filter(is_indexed=False)
        else:
            documents = Document.objects.all()

    docs_to_index = list(documents)
    if not docs_to_index:
        logger.info('No documents to index.')
        return {'indexed_count': 0, 'unique_terms': IndexEntry.objects.count(),
                'elapsed_seconds': 0.0, 'skipped_count': 0}

    # --- Step 1: Tokenize all documents ---
    doc_tokens = {}       # doc_id -> list of tokens
    doc_term_counts = {}  # doc_id -> {term: count}
    doc_lengths = {}      # doc_id -> total token count

    for doc in docs_to_index:
        try:
            tokens = preprocess(doc.raw_text, stemmer=stemmer)
            doc_tokens[doc.id] = tokens
            counts = defaultdict(int)
            for token in tokens:
                counts[token] += 1
            doc_term_counts[doc.id] = dict(counts)
            doc_lengths[doc.id] = len(tokens)
        except Exception as e:
            logger.error(f'Error preprocessing doc id={doc.id}: {e}', exc_info=True)
            skipped += 1

    successfully_processed = [d for d in docs_to_index if d.id in doc_tokens]
    if not successfully_processed:
        return {'indexed_count': 0, 'unique_terms': IndexEntry.objects.count(),
                'elapsed_seconds': round(time.time() - start_time, 2), 'skipped_count': skipped}

    all_doc_count = Document.objects.count()

    # --- Step 2: Build in-memory index structure ---
    # term -> {doc_id: tf}
    term_doc_tf = defaultdict(dict)
    for doc_id, term_counts in doc_term_counts.items():
        total = doc_lengths[doc_id]
        for term, count in term_counts.items():
            term_doc_tf[term][doc_id] = compute_tf(count, total)

    # --- Step 3: Bulk update IndexEntry records ---
    # Load existing entries
    existing_entries = {e.term: e for e in IndexEntry.objects.filter(term__in=term_doc_tf.keys())}

    to_create = []
    to_update = []

    for term, doc_tf_map in term_doc_tf.items():
        if term in existing_entries:
            entry = existing_entries[term]
            existing_postings = entry.get_postings()
            # Merge new postings (TF only; IDF applied below)
            existing_postings.update({str(k): v for k, v in doc_tf_map.items()})
            entry.doc_frequency = len(existing_postings)
            entry.set_postings(existing_postings)
            to_update.append(entry)
        else:
            entry = IndexEntry(term=term, doc_frequency=len(doc_tf_map))
            entry.set_postings({str(k): v for k, v in doc_tf_map.items()})
            to_create.append(entry)

    if to_create:
        IndexEntry.objects.bulk_create(to_create, ignore_conflicts=True)
    if to_update:
        IndexEntry.objects.bulk_update(to_update, ['doc_frequency', 'postings_json'])

    # --- Step 4: Apply IDF to convert TF -> TF-IDF ---
    all_entries = list(IndexEntry.objects.filter(term__in=term_doc_tf.keys()))
    for entry in all_entries:
        idf = compute_idf(all_doc_count, entry.doc_frequency)
        postings = entry.get_postings()
        updated = {doc_id_str: tf * idf for doc_id_str, tf in postings.items()}
        entry.set_postings(updated)

    IndexEntry.objects.bulk_update(all_entries, ['postings_json'])

    # --- Step 5: Save document lengths ---
    dl_objects = []
    for doc in successfully_processed:
        dl_objects.append(DocumentLength(
            document=doc,
            token_count=doc_lengths.get(doc.id, 0)
        ))
    DocumentLength.objects.bulk_create(dl_objects, update_conflicts=True,
                                        update_fields=['token_count'],
                                        unique_fields=['document'])

    # --- Step 6: Mark documents as indexed ---
    doc_ids = [d.id for d in successfully_processed]
    Document.objects.filter(id__in=doc_ids).update(is_indexed=True)

    # --- Step 7: Update corpus stats ---
    all_lengths = list(DocumentLength.objects.values_list('token_count', flat=True))
    avg_len = sum(all_lengths) / len(all_lengths) if all_lengths else 1.0
    CorpusStats.objects.update_or_create(
        id=1,
        defaults={'total_documents': all_doc_count, 'avg_doc_length': avg_len}
    )

    # --- Step 8: Save JSON backup ---
    _save_index_json()

    elapsed = round(time.time() - start_time, 2)
    unique_terms = IndexEntry.objects.count()
    indexed_count = len(successfully_processed)

    logger.info(
        f'Indexing complete: {indexed_count} docs, {unique_terms} terms, '
        f'{elapsed}s, {skipped} skipped.'
    )

    return {
        'indexed_count': indexed_count,
        'unique_terms': unique_terms,
        'elapsed_seconds': elapsed,
        'skipped_count': skipped,
    }


def _save_index_json():
    """Save the inverted index to index_data/inverted_index.json."""
    from .models import IndexEntry

    index_dir = Path(settings.INDEX_DATA_DIR)
    index_dir.mkdir(parents=True, exist_ok=True)
    output_path = index_dir / 'inverted_index.json'

    index_data = {}
    for entry in IndexEntry.objects.all():
        index_data[entry.term] = {
            'df': entry.doc_frequency,
            'postings': entry.get_postings(),
        }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2)

    logger.info(f'Index saved to {output_path}')
