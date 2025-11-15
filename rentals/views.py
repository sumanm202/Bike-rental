from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django.conf import settings
from django.shortcuts import get_object_or_404
import stripe

from .models import Vehicle, Booking, Payment
from .serializers import VehicleSerializer, BookingCreateSerializer, BookingSerializer

stripe.api_key = settings.STRIPE_SECRET_KEY


class VehicleListView(generics.ListAPIView):
    serializer_class = VehicleSerializer
    renderer_classes = [JSONRenderer]

    def get_queryset(self):
        qs = Vehicle.objects.filter(is_active=True)
        vtype = self.request.query_params.get('type')
        seats = self.request.query_params.get('seats')
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        city = self.request.query_params.get('city')
        if vtype:
            qs = qs.filter(type=vtype)
        if seats:
            try:
                qs = qs.filter(seats=int(seats))
            except ValueError:
                pass
        if min_price:
            qs = qs.filter(price_per_day__gte=min_price)
        if max_price:
            qs = qs.filter(price_per_day__lte=max_price)
        if city:
            qs = qs.filter(location_city__icontains=city)
        return qs


class VehicleDetailView(generics.RetrieveAPIView):
    queryset = Vehicle.objects.filter(is_active=True)
    serializer_class = VehicleSerializer
    renderer_classes = [JSONRenderer]


class BookingCreateView(generics.CreateAPIView):
    serializer_class = BookingCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    renderer_classes = [JSONRenderer]


class BookingListView(generics.ListAPIView):
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]
    renderer_classes = [JSONRenderer]

    def get_queryset(self):
        return Booking.objects.filter(user=self.request.user).order_by('-created_at')


class BookingDetailView(generics.RetrieveAPIView):
    """Retrieve a single booking by ID (only owner can view)."""
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]
    renderer_classes = [JSONRenderer]

    def get_queryset(self):
        # Only allow user to view their own bookings
        return Booking.objects.filter(user=self.request.user)


class RegisterView(APIView):
    """Simple registration endpoint that returns an auth token."""
    renderer_classes = [JSONRenderer]
    permission_classes = []

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        email = request.data.get('email')

        if not username or not password:
            return Response({'error': 'username and password required'}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(username=username).exists():
            return Response({'error': 'username taken'}, status=status.HTTP_400_BAD_REQUEST)

        user = User(username=username, email=email or '')
        user.set_password(password)
        user.save()

        token = Token.objects.create(user=user)
        return Response({'token': token.key, 'user_id': user.id, 'username': user.username}, status=status.HTTP_201_CREATED)


class CheckUsernameView(APIView):
    """Check whether a username is available (GET ?username=...)."""
    renderer_classes = [JSONRenderer]
    permission_classes = []

    def get(self, request):
        username = request.query_params.get('username', '')
        if not username:
            return Response({'available': False, 'error': 'username required'}, status=status.HTTP_400_BAD_REQUEST)
        is_taken = User.objects.filter(username=username).exists()
        return Response({'available': not is_taken})


class CurrentUserView(APIView):
    """Get and update the current authenticated user's profile info."""
    renderer_classes = [JSONRenderer]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'date_joined': user.date_joined
        })

    def put(self, request):
        """Update user profile (email, first_name, last_name)."""
        user = request.user
        email = request.data.get('email')
        first_name = request.data.get('first_name', user.first_name)
        last_name = request.data.get('last_name', user.last_name)

        if email and email != user.email:
            # Check if email is already taken
            if User.objects.filter(email=email).exclude(pk=user.pk).exists():
                return Response({'error': 'Email already in use'}, status=status.HTTP_400_BAD_REQUEST)
            user.email = email

        user.first_name = first_name
        user.last_name = last_name
        user.save()

        return Response({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'success': True,
            'message': 'Profile updated successfully'
        })


class CancelBookingView(APIView):
    """Cancel a booking by setting status to 'cancelled' (PATCH /api/bookings/{id}/cancel/)."""
    renderer_classes = [JSONRenderer]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, booking_id):
        try:
            booking = Booking.objects.get(pk=booking_id, user=request.user)
            if booking.status in ['confirmed', 'completed']:
                return Response({'error': 'Cannot cancel a confirmed or completed booking'}, status=status.HTTP_400_BAD_REQUEST)
            booking.status = 'cancelled'
            booking.save()
            serializer = BookingSerializer(booking)
            return Response({'success': True, 'booking': serializer.data})
        except Booking.DoesNotExist:
            return Response({'error': 'Booking not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_checkout_session(request):
    booking_id = request.data.get('booking_id')
    booking = get_object_or_404(Booking, pk=booking_id, user=request.user)
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {'name': f'Booking #{booking.id} - {booking.vehicle.title}'},
                    'unit_amount': int(booking.total_price * 100),
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=request.build_absolute_uri('/payments/success/'),
            cancel_url=request.build_absolute_uri('/payments/cancel/'),
            metadata={'booking_id': str(booking.id)},
        )
        # create Payment record
        Payment.objects.update_or_create(booking=booking, defaults={'amount': booking.total_price})
        return Response({'sessionId': session.id})
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except ValueError:
        return Response(status=400)
    except stripe.error.SignatureVerificationError:
        return Response(status=400)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        booking_id = session.get('metadata', {}).get('booking_id')
        if booking_id:
            try:
                booking = Booking.objects.get(pk=booking_id)
                booking.status = 'confirmed'
                booking.save()
                payment, _ = Payment.objects.get_or_create(booking=booking)
                payment.paid = True
                payment.stripe_payment_intent = session.get('payment_intent', '')
                payment.save()
            except Booking.DoesNotExist:
                pass

    return Response({'status': 'received'})
