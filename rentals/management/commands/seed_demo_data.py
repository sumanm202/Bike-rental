from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from rentals.models import Vehicle


class Command(BaseCommand):
    help = 'Seed demo data: users and vehicles'

    def handle(self, *args, **options):
        User = get_user_model()
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@example.com', 'password')
            self.stdout.write('Created admin user (admin/password)')

        if Vehicle.objects.count() == 0:
            Vehicle.objects.create(type='car', title='Demo Car', price_per_day=50, deposit=100, seats=5)
            Vehicle.objects.create(type='bike', title='Demo Bike', price_per_day=15, deposit=20, seats=1)
            self.stdout.write('Created 2 demo vehicles')
