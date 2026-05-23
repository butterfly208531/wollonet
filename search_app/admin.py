from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.utils.html import format_html
from .models import Document, IndexEntry, CorpusStats, DocumentLength, EvaluationMetric

# Rebrand the admin site
admin.site.site_header = 'WolloNet Administration'
admin.site.site_title = 'WolloNet Admin'
admin.site.index_title = 'WolloNet Search Engine'

# Remove Authentication and Authorization section
admin.site.unregister(User)
admin.site.unregister(Group)

class WolloNetAdminSite(admin.AdminSite):
    pass


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_indexed', 'pub_date', 'created_at', 'short_url')
    list_filter = ('is_indexed', 'pub_date')
    search_fields = ('title', 'raw_text')
    readonly_fields = ('created_at', 'updated_at', 'is_indexed')
    ordering = ('-created_at',)
    list_per_page = 25

    fieldsets = (
        ('Document Info', {
            'fields': ('title', 'url', 'pub_date', 'file_path')
        }),
        ('Content', {
            'fields': ('raw_text',),
            'classes': ('wide',),
        }),
        ('Status', {
            'fields': ('is_indexed', 'created_at', 'updated_at'),
        }),
    )

    def short_url(self, obj):
        if obj.url:
            return format_html('<a href="{}" target="_blank">{}</a>', obj.url, obj.url[:50])
        return '-'
    short_url.short_description = 'URL'

    actions = ['mark_for_reindex']

    def mark_for_reindex(self, request, queryset):
        queryset.update(is_indexed=False)
        self.message_user(request, f'{queryset.count()} document(s) marked for re-indexing.')
    mark_for_reindex.short_description = 'Mark selected documents for re-indexing'


@admin.register(IndexEntry)
class IndexEntryAdmin(admin.ModelAdmin):
    list_display = ('term', 'doc_frequency')
    search_fields = ('term',)
    ordering = ('-doc_frequency',)
    list_per_page = 50
    readonly_fields = ('term', 'doc_frequency', 'postings_json')


@admin.register(CorpusStats)
class CorpusStatsAdmin(admin.ModelAdmin):
    list_display = ('total_documents', 'avg_doc_length', 'last_indexed')
    readonly_fields = ('total_documents', 'avg_doc_length', 'last_indexed')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(DocumentLength)
class DocumentLengthAdmin(admin.ModelAdmin):
    list_display = ('document', 'token_count')
    search_fields = ('document__title',)


@admin.register(EvaluationMetric)
class EvaluationMetricAdmin(admin.ModelAdmin):
    list_display = ('query_text', 'model', 'precision_at_5', 'recall_at_5', 'evaluated_at')
    list_filter = ('model',)
    ordering = ('-evaluated_at',)
