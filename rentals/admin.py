from django.contrib import admin
from .models import Vehicle, VehicleImage, Booking, Payment, Review
import csv
from django.http import HttpResponse


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('title', 'type', 'price_per_day', 'is_active')


@admin.register(VehicleImage)
class VehicleImageAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'alt_text')


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'vehicle', 'user', 'start_date', 'end_date', 'status')
    actions = ['confirm_bookings', 'export_csv']

    def confirm_bookings(self, request, queryset):
        queryset.update(status='confirmed')

    def export_csv(self, request, queryset):
        fields = ['id', 'vehicle', 'user', 'start_date', 'end_date', 'total_price', 'status']
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="bookings.csv"'
        writer = csv.writer(response)
        writer.writerow(fields)
        for b in queryset:
            writer.writerow([getattr(b, f) for f in fields])
        return response


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('booking', 'amount', 'paid')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('booking', 'rating')
