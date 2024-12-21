from django.urls import path
from . import views

app_name = 'ratings'

urlpatterns = [
    path('create/<slug:slug>/', views.RatingCreateView.as_view(), name='rating_create'),
]