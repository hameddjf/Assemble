from django.urls import path

from . import views

app_name = 'dashboard'

urlpatterns = [
    path('processing/', views.ProcessingOrdersView.as_view(), name='processing_orders'),
    path('delivered/', views.DeliveredOrdersView.as_view(), name='delivered_orders'),
    path('cancelled/', views.CancelledOrdersView.as_view(), name='cancelled_orders'),
    path('addresses/', views.DashboardAddressView.as_view(), name='address_list'),
    
    # path('addresses/edit/<int:pk>/', views.EditAddressView.as_view(), name='edit_address'),
]