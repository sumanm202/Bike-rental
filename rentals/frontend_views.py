from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django.conf import settings

@require_http_methods(["GET"])
def home(request):
    return render(request, 'home.html')

@require_http_methods(["GET"])
def vehicles_list(request):
    return render(request, 'vehicles.html')

@require_http_methods(["GET"])
def vehicle_detail(request, vehicle_id):
    return render(request, 'vehicle_detail.html', {'vehicle_id': vehicle_id})

@require_http_methods(["GET"])
def payment(request, booking_id):
    # Extract publishable key from secret key (remove 'sk_' prefix and add 'pk_')
    stripe_secret = settings.STRIPE_SECRET_KEY
    # For now, hardcode the test publishable key or derive it
    stripe_publishable = 'pk_test_51Q5Z8wDp44a7OqORfDLqL47c0016U36vHDmR8C9QXLGZJhR0Sq5j0CwD0q8tYJOzAKV7MJqNLGI8kPWPaGMArfUq00pj8XvDFo'
    return render(request, 'payment.html', {
        'booking_id': booking_id,
        'stripe_publishable_key': stripe_publishable
    })

@require_http_methods(["GET"])
def dashboard(request):
    return render(request, 'dashboard.html')

@require_http_methods(["GET"])
def login(request):
    return render(request, 'login.html')


@require_http_methods(["GET"])
def signup(request):
    return render(request, 'register.html')
