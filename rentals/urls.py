from django.urls import path
from . import views
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    path('vehicles/', views.VehicleListView.as_view(), name='vehicle-list'),
    path('vehicles/<int:pk>/', views.VehicleDetailView.as_view(), name='vehicle-detail'),
    path('bookings/', views.BookingCreateView.as_view(), name='booking-create'),
    path('bookings/my/', views.BookingListView.as_view(), name='booking-list'),
    path('payments/create-checkout/', views.create_checkout_session, name='create-checkout'),
    path('webhooks/stripe/', views.stripe_webhook, name='stripe-webhook'),
    path('auth/token/', obtain_auth_token, name='api-token-auth'),
]
