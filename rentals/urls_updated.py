from django.urls import path
from . import views, frontend_views
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    # Frontend pages
    path('', frontend_views.home, name='frontend-home'),
    path('vehicles/', frontend_views.vehicles_list, name='frontend-vehicles-list'),
    path('vehicle/<int:vehicle_id>/', frontend_views.vehicle_detail, name='frontend-vehicle-detail'),
    path('payment/<int:booking_id>/', frontend_views.payment, name='frontend-payment'),
    path('dashboard/', frontend_views.dashboard, name='frontend-dashboard'),
    path('login/', frontend_views.login, name='frontend-login'),
    path('register/', frontend_views.signup, name='frontend-register'),
    
    # API endpoints
    path('api/vehicles/', views.VehicleListView.as_view(), name='vehicle-list'),
    path('api/vehicles/<int:pk>/', views.VehicleDetailView.as_view(), name='vehicle-detail'),
    path('api/bookings/', views.BookingCreateView.as_view(), name='booking-create'),
    path('api/bookings/<int:pk>/', views.BookingDetailView.as_view(), name='booking-detail'),
    path('api/bookings/my/', views.BookingListView.as_view(), name='booking-list'),
    path('api/payments/create-checkout/', views.create_checkout_session, name='create-checkout'),
    path('api/webhooks/stripe/', views.stripe_webhook, name='stripe-webhook'),
    path('api/auth/token/', obtain_auth_token, name='api-token-auth'),
    path('api/auth/register/', views.RegisterView.as_view(), name='api-register'),
    path('api/auth/check-username/', views.CheckUsernameView.as_view(), name='api-check-username'),
    path('api/auth/user/', views.CurrentUserView.as_view(), name='api-current-user'),
    path('api/bookings/<int:booking_id>/cancel/', views.CancelBookingView.as_view(), name='cancel-booking'),
]
