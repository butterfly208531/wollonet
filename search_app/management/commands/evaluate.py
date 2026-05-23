"""
Management command: python manage.py evaluate

Runs Precision@5 and Recall@5 evaluation for 10 test queries
on both VSM and BM25 models and saves results to EvaluationMetric.
"""
from django.core.management.base import BaseCommand
from search_app.models import EvaluationMetric
from search_app.ranker import search

# ---------------------------------------------------------------
# 10 Test queries with ground-truth relevant document IDs
# Edit the doc IDs to match your actual database IDs
# ---------------------------------------------------------------
TEST_QUERIES = [
    {
        'query': 'Wollo University',
        'relevant_ids': [15, 16, 12, 13, 14, 6],   # overview, research, admission, colleges, ict, region
    },
    {
        'query': 'Dessie city campus',
        'relevant_ids': [8, 15, 6],                  # dessie city, overview, wollo region
    },
    {
        'query': 'computer science information technology',
        'relevant_ids': [14, 17, 13, 10],            # ict, IT dept, colleges, IR
    },
    {
        'query': 'agriculture coffee Ethiopia',
        'relevant_ids': [2, 7, 6],                   # ethiopia agriculture, coffee history, wollo region
    },
    {
        'query': 'machine learning algorithm',
        'relevant_ids': [11],                        # machine learning
    },
    {
        'query': 'research community service',
        'relevant_ids': [16, 15],                    # research, overview
    },
    {
        'query': 'admission student dormitory',
        'relevant_ids': [12, 15],                    # admission, overview
    },
    {
        'query': 'Django web framework Python',
        'relevant_ids': [9, 17],                     # django framework, IT dept
    },
    {
        'query': 'information retrieval indexing TF-IDF',
        'relevant_ids': [10, 14],                    # information retrieval, ict
    },
    {
        'query': 'engineering college medicine health',
        'relevant_ids': [13, 15],                    # colleges, overview
    },
]


def precision_at_k(retrieved_ids, relevant_ids, k=5):
    """Fraction of top-k retrieved that are relevant."""
    top_k = retrieved_ids[:k]
    if not top_k:
        return 0.0
    hits = sum(1 for doc_id in top_k if doc_id in relevant_ids)
    return hits / k


def recall_at_k(retrieved_ids, relevant_ids, k=5):
    """Fraction of all relevant docs found in top-k."""
    if not relevant_ids:
        return 0.0
    top_k = retrieved_ids[:k]
    hits = sum(1 for doc_id in top_k if doc_id in relevant_ids)
    return hits / len(relevant_ids)


class Command(BaseCommand):
    help = 'Evaluate VSM and BM25 models using Precision@5 and Recall@5'

    def handle(self, *args, **options):
        # Clear old evaluation results
        EvaluationMetric.objects.all().delete()

        self.stdout.write(self.style.NOTICE('\nRunning evaluation on 10 test queries...\n'))

        vsm_p_scores = []
        vsm_r_scores = []
        bm25_p_scores = []
        bm25_r_scores = []

        header = f"{'Query':<40} {'VSM P@5':>8} {'VSM R@5':>8} {'BM25 P@5':>9} {'BM25 R@5':>9}"
        self.stdout.write(header)
        self.stdout.write('-' * len(header))

        for item in TEST_QUERIES:
            query = item['query']
            relevant = set(item['relevant_ids'])

            # VSM
            vsm_results = search(query, model='vsm', top_k=5)
            vsm_ids = [r['doc'].id for r in vsm_results]
            vsm_p = precision_at_k(vsm_ids, relevant, k=5)
            vsm_r = recall_at_k(vsm_ids, relevant, k=5)

            # BM25
            bm25_results = search(query, model='bm25', top_k=5)
            bm25_ids = [r['doc'].id for r in bm25_results]
            bm25_p = precision_at_k(bm25_ids, relevant, k=5)
            bm25_r = recall_at_k(bm25_ids, relevant, k=5)

            # Save to database
            EvaluationMetric.objects.create(
                query_text=query, model='vsm',
                precision_at_5=round(vsm_p, 4),
                recall_at_5=round(vsm_r, 4)
            )
            EvaluationMetric.objects.create(
                query_text=query, model='bm25',
                precision_at_5=round(bm25_p, 4),
                recall_at_5=round(bm25_r, 4)
            )

            vsm_p_scores.append(vsm_p)
            vsm_r_scores.append(vsm_r)
            bm25_p_scores.append(bm25_p)
            bm25_r_scores.append(bm25_r)

            self.stdout.write(
                f"{query:<40} {vsm_p:>8.2f} {vsm_r:>8.2f} {bm25_p:>9.2f} {bm25_r:>9.2f}"
            )

        # Summary
        self.stdout.write('-' * len(header))
        mean_vsm_p  = sum(vsm_p_scores)  / len(vsm_p_scores)
        mean_vsm_r  = sum(vsm_r_scores)  / len(vsm_r_scores)
        mean_bm25_p = sum(bm25_p_scores) / len(bm25_p_scores)
        mean_bm25_r = sum(bm25_r_scores) / len(bm25_r_scores)

        self.stdout.write(
            f"{'MEAN':<40} {mean_vsm_p:>8.2f} {mean_vsm_r:>8.2f} {mean_bm25_p:>9.2f} {mean_bm25_r:>9.2f}"
        )

        self.stdout.write(self.style.SUCCESS(
            f'\nDone! Saved {EvaluationMetric.objects.count()} evaluation records.\n'
            f'View results at: http://127.0.0.1:8000/admin/search_app/evaluationmetric/'
        ))
