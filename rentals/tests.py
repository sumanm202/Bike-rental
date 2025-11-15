from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Vehicle, Booking
from .utils import is_vehicle_available
from datetime import date, timedelta
from rest_framework.test import APIClient
from django.urls import reverse
import stripe
from unittest import mock


class AvailabilityTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user('u1', 'u1@example.com', 'pass')
        self.vehicle = Vehicle.objects.create(type='car', title='T1', price_per_day=10, deposit=0, seats=4)

    def test_available_when_no_bookings(self):
        start = date.today()
        end = start + timedelta(days=2)
        self.assertTrue(is_vehicle_available(self.vehicle, start, end))

    def test_overlap_blocks_booking(self):
        b = Booking.objects.create(user=self.user, vehicle=self.vehicle, start_date=date(2025,1,10), end_date=date(2025,1,15), total_price=100)
        self.assertFalse(is_vehicle_available(self.vehicle, date(2025,1,12), date(2025,1,13)))

    def test_adjacent_days(self):
        # end_date inclusive: booking end 15 blocks new booking start 15
        Booking.objects.create(user=self.user, vehicle=self.vehicle, start_date=date(2025,1,10), end_date=date(2025,1,15), total_price=100)
        self.assertFalse(is_vehicle_available(self.vehicle, date(2025,1,15), date(2025,1,17)))

    def test_non_overlapping_after(self):
        Booking.objects.create(user=self.user, vehicle=self.vehicle, start_date=date(2025,1,10), end_date=date(2025,1,15), total_price=100)
        self.assertTrue(is_vehicle_available(self.vehicle, date(2025,1,16), date(2025,1,18)))


class BookingCreateTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user('u2', 'u2@example.com', 'pass')
        self.vehicle = Vehicle.objects.create(type='bike', title='B1', price_per_day=20, deposit=10, seats=1)

    def test_create_booking_total_price(self):
        start = date(2025,2,1)
        end = date(2025,2,3)
        days = (end - start).days + 1
        b = Booking.objects.create(user=self.user, vehicle=self.vehicle, start_date=start, end_date=end, total_price=self.vehicle.price_per_day * days + self.vehicle.deposit)
        self.assertEqual(b.total_price, 20 * 3 + 10)

    def test_create_overlapping_booking_fails(self):
        Booking.objects.create(user=self.user, vehicle=self.vehicle, start_date=date(2025,3,5), end_date=date(2025,3,7), total_price=60)
        self.assertFalse(is_vehicle_available(self.vehicle, date(2025,3,7), date(2025,3,9)))


class APITests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user('apiuser', 'api@example.com', 'pass')
        self.vehicle = Vehicle.objects.create(type='car', title='API Car', price_per_day=30, deposit=0, seats=4)
        self.client = APIClient()

    def test_vehicle_list(self):
        url = reverse('vehicle-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_create_booking_endpoint_requires_auth(self):
        url = reverse('booking-create')
        data = {'vehicle': self.vehicle.id, 'start_date': '2025-12-01', 'end_date': '2025-12-03'}
        resp = self.client.post(url, data)
        self.assertIn(resp.status_code, (401, 403))

    def test_create_booking_and_checkout(self):
        # login and create booking via API then create checkout session (mock Stripe)
        self.client.force_authenticate(self.user)
        url = reverse('booking-create')
        data = {'vehicle': self.vehicle.id, 'start_date': '2025-12-10', 'end_date': '2025-12-12'}
        resp = self.client.post(url, data)
        self.assertEqual(resp.status_code, 201)
        booking_id = resp.data['id']

        # mock stripe.checkout.Session.create
        with mock.patch('rentals.views.stripe.checkout.Session.create') as mock_create:
            mock_create.return_value = mock.MagicMock(id='sess_123')
            url2 = reverse('create-checkout')
            resp2 = self.client.post(url2, {'booking_id': booking_id}, format='json')
            self.assertEqual(resp2.status_code, 200)

    def test_stripe_webhook_marks_booking_confirmed(self):
        # create a pending booking
        b = Booking.objects.create(user=self.user, vehicle=self.vehicle, start_date=date(2025,11,20), end_date=date(2025,11,22), total_price=90)
        payload = {'type': 'checkout.session.completed', 'data': {'object': {'metadata': {'booking_id': str(b.id)}, 'payment_intent': 'pi_123'}}}
        # mock stripe.Webhook.construct_event to return payload
        with mock.patch('rentals.views.stripe.Webhook.construct_event', return_value=payload):
            url = reverse('stripe-webhook')
            resp = self.client.post(url, data=b'{}', content_type='application/json', HTTP_STRIPE_SIGNATURE='sig')
            self.assertEqual(resp.status_code, 200)
            b.refresh_from_db()
            self.assertEqual(b.status, 'confirmed')
