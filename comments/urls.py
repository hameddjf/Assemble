from django.urls import path

from . import views

app_name = 'comments'

urlpatterns = [
    path('comments/<str:content_type>/<int:object_id>/comment/create/', views.CommentCreateView.as_view(), name='comment_create'),
    
    path('comment/<int:pk>/update/', views.CommentUpdateView.as_view(), name='comment_update'),
    path('comment/<int:pk>/delete/', views.CommentDeleteView.as_view(), name='comment_delete'),
    path('comments/<int:comment_id>/react/<str:reaction_type>/', 
     views.CommentReactionView.as_view(), 
     name='comment_reaction')
    
    ]