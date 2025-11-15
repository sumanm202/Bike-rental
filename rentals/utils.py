from django.db.models import Q


def is_vehicle_available(vehicle, start_date, end_date):
    # Overlap rule: existing.start_date <= new.end_date AND existing.end_date >= new.start_date
    conflicts = vehicle.bookings.filter(
        status__in=['pending', 'confirmed']
    ).filter(
        start_date__lte=end_date,
        end_date__gte=start_date
    )
    return not conflicts.exists()
