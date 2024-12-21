from django.urls import path

from .views import CategoryListView, CategoryDetailView

app_name = 'categories'

urlpatterns = [
    path('', CategoryListView.as_view(), name='category-list'),
    path('<str:slug>/', CategoryDetailView.as_view(), name='category-detail'),
]
