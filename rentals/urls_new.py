from django.urls import path
from . import views
from . import frontend_views
from rest_framework.authtoken.views import obtain_auth_token

# Frontend routes
frontend_patterns = [
    path('', frontend_views.home, name='home'),
    path('vehicles/', frontend_views.vehicles_list, name='vehicles-list'),
    path('vehicle/<int:vehicle_id>/', frontend_views.vehicle_detail, name='vehicle-detail'),
    path('payment/<int:booking_id>/', frontend_views.payment, name='payment'),
    path('dashboard/', frontend_views.dashboard, name='dashboard'),
    path('login/', frontend_views.login, name='login'),
]

# API routes
api_patterns = [
    path('api/vehicles/', views.VehicleListView.as_view(), name='vehicle-list'),
    path('api/vehicles/<int:pk>/', views.VehicleDetailView.as_view(), name='vehicle-detail'),
    path('api/bookings/', views.BookingCreateView.as_view(), name='booking-create'),
    path('api/bookings/my/', views.BookingListView.as_view(), name='booking-list'),
    path('api/payments/create-checkout/', views.create_checkout_session, name='create-checkout'),
    path('api/webhooks/stripe/', views.stripe_webhook, name='stripe-webhook'),
    path('api/auth/token/', obtain_auth_token, name='api-token-auth'),
]

urlpatterns = frontend_patterns + api_patterns
