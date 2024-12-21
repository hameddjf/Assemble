from django.urls import path,re_path

from . import views


app_name = 'blog'

urlpatterns = [
    path('', views.ArticleListView.as_view(), name='article_list'),
    re_path(r'(?P<slug>[\w-]+)/$', views.ArticleDetailView.as_view(), name='article_detail'),
]