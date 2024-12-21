from django.urls import path

from . import views

app_name = 'main'

urlpatterns = [
    path('', views.SpecialProductsListView.as_view(),name='special_products'),
]
