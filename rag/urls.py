"""
URL configuration for the RAG app.
"""

from django.urls import path
from . import views

app_name = 'rag'

urlpatterns = [
    path('', views.index, name='index'),
    path('query/', views.QueryView.as_view(), name='query'),
    path('api/query/', views.query_sermons, name='api_query'),
    path('health/', views.health_check, name='health'),
    path('status/', views.status, name='status'),
]
