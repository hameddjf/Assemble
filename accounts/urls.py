from django.urls import path, include

from . import views

app_name = 'accounts'

urlpatterns = [
    #     path('', include('allauth.urls')),

    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    
    path('verify-email/<str:token>/',views.VerifyEmailView.as_view(), name='verify_email'),
    
    path('password-reset/', views.PasswordResetView.as_view(), name='password_reset'),
    path('reset-password/<str:token>/', views.PasswordResetConfirmView.as_view(), name='reset_password_confirm'),

    path('google/callback/', views.GoogleLoginCallbackView.as_view(),name='google_callback'),
    
    path('contact/', views.ContactView.as_view(), name='contact'),

]
