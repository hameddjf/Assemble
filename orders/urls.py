from django.urls import path

from . import views

app_name = 'orders'

urlpatterns = [
    path('', views.AddressListView.as_view(), name='address_list'),
    path('add/', views.AddressManagementView.as_view(), name='add_address'),
    path('payment/<int:order_id>/', views.PaymentSelectionView.as_view(), name='payment_page'),
    
    path('go-to-gateway/', views.GoToGateWayView.as_view(), name='goto_gateway'),
    path('order_complete_page/', views.OrderCompleteView.as_view(), name='order_complete_page'),

]
