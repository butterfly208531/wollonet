import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'wollo_search.settings'
import django
django.setup()

import sys
import json
from pathlib import Path

PASS = "PASS"
FAIL = "FAIL"
WARN = "WARN"

results = []

def check(name, status, detail=""):
    results.append((name, status, detail))
    icon = "OK" if status == PASS else ("!!" if status == FAIL else "??")
    print(f"  [{icon}] {name:<45} {detail}")

print()
print("=" * 65)
print("  WOLLONET FULL SYSTEM CHECK")
print("=" * 65)

# ── 1. DATABASE ──────────────────────────────────────────────
print("\n[1] DATABASE")
from search_app.models import Document, IndexEntry, CorpusStats, DocumentLength, EvaluationMetric

doc_count = Document.objects.count()
indexed_count = Document.objects.filter(is_indexed=True).count()
term_count = IndexEntry.objects.count()
dl_count = DocumentLength.objects.count()
eval_count = EvaluationMetric.objects.count()
stats = CorpusStats.objects.first()

check("Total documents", PASS if doc_count > 0 else FAIL, f"{doc_count} documents")
check("All documents indexed", PASS if doc_count == indexed_count else WARN,
      f"{indexed_count}/{doc_count} indexed")
check("Inverted index built", PASS if term_count > 0 else FAIL, f"{term_count} terms")
check("Document lengths stored", PASS if dl_count == indexed_count else WARN,
      f"{dl_count} records")
check("Corpus stats exist", PASS if stats else FAIL,
      f"avg_len={stats.avg_doc_length:.1f}" if stats else "MISSING")
check("Evaluation metrics exist", PASS if eval_count > 0 else WARN,
      f"{eval_count} records")

# ── 2. INDEX DATA FILE ───────────────────────────────────────
print("\n[2] INDEX FILE")
index_file = Path("index_data/inverted_index.json")
if index_file.exists():
    size_kb = index_file.stat().st_size // 1024
    with open(index_file, encoding='utf-8') as f:
        data = json.load(f)
    check("inverted_index.json exists", PASS, f"{size_kb} KB, {len(data)} terms")
else:
    check("inverted_index.json exists", FAIL, "File not found")

# ── 3. PREPROCESSOR ──────────────────────────────────────────
print("\n[3] PREPROCESSOR")
from search_app.preprocessor import preprocess, tokenize, remove_stopwords

tokens = tokenize("Wollo University is located in Dessie Ethiopia")
check("Tokenizer works", PASS if len(tokens) > 0 else FAIL, f"tokens={tokens}")

filtered = remove_stopwords(tokens)
check("Stopword removal works", PASS if len(filtered) < len(tokens) else WARN,
      f"{len(tokens)} -> {len(filtered)} tokens")

amharic = tokenize("ወሎ ዩኒቨርሲቲ በደሴ ከተማ")
check("Amharic tokenizer works", PASS if len(amharic) > 0 else FAIL,
      f"tokens={amharic}")

processed = preprocess("Agriculture coffee Ethiopia teff wheat")
check("Full pipeline works", PASS if len(processed) > 0 else FAIL,
      f"output={processed}")

# ── 4. SEARCH — VSM ──────────────────────────────────────────
print("\n[4] SEARCH — VSM")
from search_app.ranker import search

test_vsm = [
    ("Wollo University", 1),
    ("agriculture Ethiopia", 1),
    ("machine learning", 1),
    ("Django framework", 1),
    ("information retrieval", 1),
]
for query, min_results in test_vsm:
    results_list = search(query, model='vsm', top_k=5)
    status = PASS if len(results_list) >= min_results else FAIL
    top = results_list[0]['doc'].title if results_list else "no results"
    check(f'VSM: "{query}"', status, f"{len(results_list)} results | top: {top}")

# ── 5. SEARCH — BM25 ─────────────────────────────────────────
print("\n[5] SEARCH — BM25")
test_bm25 = [
    ("Wollo University Dessie", 1),
    ("coffee export Ethiopia", 1),
    ("neural network algorithm", 1),
    ("admission student", 1),
    ("engineering college", 1),
]
for query, min_results in test_bm25:
    results_list = search(query, model='bm25', top_k=5)
    status = PASS if len(results_list) >= min_results else FAIL
    top = results_list[0]['doc'].title if results_list else "no results"
    check(f'BM25: "{query}"', status, f"{len(results_list)} results | top: {top}")

# ── 6. EDGE CASES ────────────────────────────────────────────
print("\n[6] EDGE CASES")
r1 = search("the and or is a", model='vsm', top_k=5)
check("All-stopwords -> 0 results", PASS if len(r1) == 0 else FAIL,
      f"{len(r1)} results (expected 0)")

r2 = search("xyznonexistent999", model='vsm', top_k=5)
check("Unknown word -> 0 results", PASS if len(r2) == 0 else FAIL,
      f"{len(r2)} results (expected 0)")

r3 = search("ወሎ ዩኒቨርሲቲ", model='vsm', top_k=3)
check("Amharic query returns results", PASS if len(r3) > 0 else WARN,
      f"{len(r3)} results")

r4 = search("a" * 501, model='vsm', top_k=5)
check("Very long query handled", PASS, f"{len(r4)} results (no crash)")

# ── 7. WEB PAGES ─────────────────────────────────────────────
print("\n[7] WEB PAGES")
import urllib.request
import urllib.error

pages = [
    ("Homepage", "http://127.0.0.1:8000/"),
    ("Search results", "http://127.0.0.1:8000/search/?q=Wollo+University"),
    ("Empty query", "http://127.0.0.1:8000/search/?q="),
    ("Admin panel", "http://127.0.0.1:8000/admin/"),
    ("Document detail", f"http://127.0.0.1:8000/document/{Document.objects.first().id}/"),
]
for name, url in pages:
    try:
        r = urllib.request.urlopen(url, timeout=5)
        check(name, PASS, f"HTTP {r.status}")
    except urllib.error.HTTPError as e:
        check(name, WARN if e.code in (302, 301) else FAIL, f"HTTP {e.code}")
    except Exception as e:
        check(name, FAIL, str(e)[:40])

# ── 8. MANAGEMENT COMMANDS ───────────────────────────────────
print("\n[8] MANAGEMENT COMMANDS")
from django.core.management import get_commands
cmds = get_commands()
check("index_docs command exists", PASS if 'index_docs' in cmds else FAIL, "")
check("evaluate command exists",   PASS if 'evaluate'   in cmds else FAIL, "")

# ── SUMMARY ──────────────────────────────────────────────────
print()
print("=" * 65)
total  = len(results)
passed = sum(1 for _, s, _ in results if s == PASS)
warned = sum(1 for _, s, _ in results if s == WARN)
failed = sum(1 for _, s, _ in results if s == FAIL)
print(f"  TOTAL: {total}  |  PASS: {passed}  |  WARN: {warned}  |  FAIL: {failed}")
print("=" * 65)
if failed == 0:
    print("  ALL SYSTEMS OPERATIONAL")
else:
    print("  SOME CHECKS FAILED — see [!!] items above")
print()
