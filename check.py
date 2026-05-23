import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'wollo_search.settings'
import django
django.setup()

from search_app.models import Document, IndexEntry, CorpusStats, DocumentLength
from search_app.ranker import search
from search_app.preprocessor import preprocess

print("=" * 50)
print("DATABASE CHECK")
print("=" * 50)
print(f"Documents      : {Document.objects.count()}")
print(f"Indexed docs   : {Document.objects.filter(is_indexed=True).count()}")
print(f"Index entries  : {IndexEntry.objects.count()}")
print(f"Doc lengths    : {DocumentLength.objects.count()}")
stats = CorpusStats.objects.first()
if stats:
    print(f"Corpus stats   : {stats.total_documents} docs, avg_len={stats.avg_doc_length:.1f}")
else:
    print("Corpus stats   : MISSING !")

print()
print("=" * 50)
print("PREPROCESSOR CHECK")
print("=" * 50)
tokens = preprocess("Agriculture in Ethiopia coffee teff wheat")
print(f"Tokens: {tokens}")

print()
print("=" * 50)
print("SEARCH CHECK — VSM")
print("=" * 50)
queries_vsm = ["agriculture", "machine learning", "Django framework", "information retrieval"]
for q in queries_vsm:
    results = search(q, model='vsm', top_k=3)
    print(f'  "{q}" -> {len(results)} results')
    for r in results:
        print(f"      [{r['score']}] {r['doc'].title}")

print()
print("=" * 50)
print("SEARCH CHECK — BM25")
print("=" * 50)
queries_bm25 = ["Wollo university Dessie", "coffee export Ethiopia", "neural network algorithm"]
for q in queries_bm25:
    results = search(q, model='bm25', top_k=3)
    print(f'  "{q}" -> {len(results)} results')
    for r in results:
        print(f"      [{r['score']}] {r['doc'].title}")

print()
print("=" * 50)
print("EDGE CASES")
print("=" * 50)
# Empty query after stopword removal
r1 = search("the and or is", model='vsm', top_k=5)
print(f"  All-stopwords query -> {len(r1)} results (expected 0)")

# Unknown term
r2 = search("xyznonexistentterm123", model='vsm', top_k=5)
print(f"  Unknown term query  -> {len(r2)} results (expected 0)")

# Amharic query
r3 = search("ወሎ ዩኒቨርሲቲ", model='vsm', top_k=3)
print(f"  Amharic query       -> {len(r3)} results")
for r in r3:
    print(f"      [{r['score']}] {r['doc'].title}")

print()
print("=" * 50)
print("ALL CHECKS COMPLETE")
print("=" * 50)
