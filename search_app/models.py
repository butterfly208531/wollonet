from django.db import models
import json


class Document(models.Model):
    """Represents a document in the corpus."""
    title = models.CharField(max_length=500)
    raw_text = models.TextField()
    url = models.URLField(max_length=1000, blank=True, unique=True, null=True)
    pub_date = models.DateTimeField(null=True, blank=True)
    file_path = models.CharField(max_length=1000, blank=True)
    is_indexed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-pub_date', '-created_at']

    def __str__(self):
        return self.title

    def get_snippet(self, query_terms=None, length=200):
        """Return a snippet of text, optionally centered around query terms."""
        text = self.raw_text
        if not query_terms:
            return text[:length] + ('...' if len(text) > length else '')

        text_lower = text.lower()
        best_pos = 0
        for term in query_terms:
            pos = text_lower.find(term.lower())
            if pos != -1:
                best_pos = max(0, pos - 60)
                break

        snippet = text[best_pos:best_pos + length]
        if best_pos > 0:
            snippet = '...' + snippet
        if best_pos + length < len(text):
            snippet = snippet + '...'
        return snippet


class IndexEntry(models.Model):
    """Stores an inverted index entry for a term."""
    term = models.CharField(max_length=200, unique=True, db_index=True)
    doc_frequency = models.IntegerField(default=0)
    postings_json = models.TextField(default='{}')  # JSON: {doc_id: tfidf_weight}

    class Meta:
        verbose_name_plural = 'Index Entries'

    def __str__(self):
        return f'{self.term} (df={self.doc_frequency})'

    def get_postings(self):
        return json.loads(self.postings_json)

    def set_postings(self, postings_dict):
        self.postings_json = json.dumps(postings_dict)


class CorpusStats(models.Model):
    """Stores corpus-level statistics for BM25."""
    total_documents = models.IntegerField(default=0)
    avg_doc_length = models.FloatField(default=1.0)
    last_indexed = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Corpus Stats'

    def __str__(self):
        return f'Corpus: {self.total_documents} docs, avg_len={self.avg_doc_length:.1f}'


class DocumentLength(models.Model):
    """Stores the token count for each document (needed for BM25)."""
    document = models.OneToOneField(Document, on_delete=models.CASCADE, related_name='length_record')
    token_count = models.IntegerField(default=0)

    def __str__(self):
        return f'{self.document.title}: {self.token_count} tokens'


class EvaluationMetric(models.Model):
    """Stores evaluation results for test queries."""
    MODEL_CHOICES = [('vsm', 'VSM'), ('bm25', 'BM25')]

    query_text = models.CharField(max_length=500)
    model = models.CharField(max_length=10, choices=MODEL_CHOICES)
    precision_at_5 = models.FloatField(null=True, blank=True)
    recall_at_5 = models.FloatField(null=True, blank=True)
    evaluated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-evaluated_at']

    def __str__(self):
        return f'{self.query_text} [{self.model}] P@5={self.precision_at_5}'
