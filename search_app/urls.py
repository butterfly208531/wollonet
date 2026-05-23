from django.urls import path
from . import views

app_name = 'search_app'

urlpatterns = [
    path('', views.home, name='home'),
    path('search/', views.search_results, name='search'),
    path('document/<int:doc_id>/', views.document_detail, name='document'),
]
