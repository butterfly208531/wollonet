"""
Ranking engine for WolloNet Search Engine.
Implements VSM (Cosine Similarity) and BM25 ranking models.
"""
import math
import logging
from collections import defaultdict

from .preprocessor import preprocess, get_default_stemmer

logger = logging.getLogger('search_app')

# BM25 parameters
BM25_K1 = 1.5
BM25_B = 0.75


def search(query_text, model='vsm', top_k=10):
    """
    Main search function.

    Args:
        query_text: raw query string from the user
        model: 'vsm' or 'bm25'
        top_k: number of results to return

    Returns:
        list of dicts: [{doc, score, snippet, query_terms}, ...]
    """
    from .models import Document, IndexEntry, CorpusStats

    stemmer = get_default_stemmer()
    query_terms = preprocess(query_text, stemmer=stemmer)

    if not query_terms:
        return []

    # Find candidate documents (those containing at least one query term)
    candidate_doc_ids = set()
    term_entries = {}

    for term in set(query_terms):
        try:
            entry = IndexEntry.objects.get(term=term)
            term_entries[term] = entry
            postings = entry.get_postings()
            candidate_doc_ids.update(int(k) for k in postings.keys())
        except IndexEntry.DoesNotExist:
            pass  # term not in index, skip silently

    if not candidate_doc_ids:
        return []

    # Score candidates
    if model == 'bm25':
        scores = _score_bm25(query_terms, term_entries, candidate_doc_ids)
    else:
        scores = _score_vsm(query_terms, term_entries, candidate_doc_ids)

    # Filter zero scores and sort descending; tie-break by doc_id ascending
    ranked = sorted(
        [(doc_id, score) for doc_id, score in scores.items() if score > 0],
        key=lambda x: (-x[1], x[0])
    )[:top_k]

    if not ranked:
        return []

    # Fetch documents
    doc_ids = [doc_id for doc_id, _ in ranked]
    docs_map = {d.id: d for d in Document.objects.filter(id__in=doc_ids)}

    results = []
    for doc_id, score in ranked:
        doc = docs_map.get(doc_id)
        if doc:
            results.append({
                'doc': doc,
                'score': round(score, 4),
                'query_terms': query_terms,
            })

    return results


def _score_vsm(query_terms, term_entries, candidate_doc_ids):
    """
    Vector Space Model scoring using cosine similarity.
    Document vectors are pre-computed TF-IDF weights.
    Query vector uses raw term frequency normalized by query length.
    """
    from .models import IndexEntry
    import math

    num_docs = _get_total_docs()

    # Build query TF-IDF vector
    query_tf = defaultdict(int)
    for term in query_terms:
        query_tf[term] += 1

    query_vec = {}
    for term, count in query_tf.items():
        if term in term_entries:
            entry = term_entries[term]
            tf = count / len(query_terms)
            idf = math.log10(num_docs / entry.doc_frequency) if entry.doc_frequency > 0 else 0
            query_vec[term] = tf * idf

    if not query_vec:
        return {}

    # Compute dot product for each candidate document
    doc_scores = defaultdict(float)
    query_norm = math.sqrt(sum(v ** 2 for v in query_vec.values()))

    for term, q_weight in query_vec.items():
        if term not in term_entries:
            continue
        postings = term_entries[term].get_postings()
        for doc_id_str, doc_tfidf in postings.items():
            doc_id = int(doc_id_str)
            if doc_id in candidate_doc_ids:
                doc_scores[doc_id] += q_weight * doc_tfidf

    # Normalize by query norm (document norms are implicitly 1 for ranking purposes)
    if query_norm > 0:
        for doc_id in doc_scores:
            doc_scores[doc_id] /= query_norm

    return dict(doc_scores)


def _score_bm25(query_terms, term_entries, candidate_doc_ids):
    """
    Okapi BM25 scoring.
    BM25(d, q) = sum_t [ IDF(t) * (tf(t,d) * (k1+1)) / (tf(t,d) + k1*(1 - b + b*|d|/avgdl)) ]
    """
    from .models import DocumentLength, CorpusStats
    import math

    num_docs = _get_total_docs()

    # Get corpus stats
    try:
        stats = CorpusStats.objects.get(id=1)
        avg_dl = stats.avg_doc_length if stats.avg_doc_length > 0 else 1.0
    except CorpusStats.DoesNotExist:
        avg_dl = 1.0

    # Get document lengths
    doc_lengths = {
        dl.document_id: dl.token_count
        for dl in DocumentLength.objects.filter(document_id__in=candidate_doc_ids)
    }

    doc_scores = defaultdict(float)

    for term in set(query_terms):
        if term not in term_entries:
            continue
        entry = term_entries[term]
        df = entry.doc_frequency
        if df == 0:
            continue

        idf = math.log((num_docs - df + 0.5) / (df + 0.5) + 1)

        # Get raw TF from postings (we stored TF-IDF, so we need to back-calculate)
        # Instead, we recompute from the stored TF-IDF by dividing by IDF
        postings = entry.get_postings()
        stored_idf = math.log10(num_docs / df) if df > 0 else 0

        for doc_id_str, tfidf_weight in postings.items():
            doc_id = int(doc_id_str)
            if doc_id not in candidate_doc_ids:
                continue

            # Recover TF from stored TF-IDF weight
            tf = (tfidf_weight / stored_idf) if stored_idf > 0 else tfidf_weight
            dl = doc_lengths.get(doc_id, avg_dl)

            numerator = tf * (BM25_K1 + 1)
            denominator = tf + BM25_K1 * (1 - BM25_B + BM25_B * dl / avg_dl)
            bm25_score = idf * (numerator / denominator) if denominator > 0 else 0

            doc_scores[doc_id] += bm25_score

    return dict(doc_scores)


def _get_total_docs():
    """Return total number of indexed documents."""
    from .models import Document
    count = Document.objects.filter(is_indexed=True).count()
    return max(count, 1)  # avoid division by zero
