from rest_framework import serializers
from .models import Vehicle, Booking, VehicleImage
from .utils import is_vehicle_available
from datetime import timedelta


class VehicleImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleImage
        fields = ('id', 'image', 'alt_text')


class VehicleSerializer(serializers.ModelSerializer):
    images = VehicleImageSerializer(many=True, read_only=True)
    
    class Meta:
        model = Vehicle
        fields = '__all__'


class VehicleDetailSerializer(serializers.ModelSerializer):
    images = VehicleImageSerializer(many=True, read_only=True)

    class Meta:
        model = Vehicle
        fields = '__all__'


class BookingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ['id', 'vehicle', 'start_date', 'end_date']

    def validate(self, attrs):
        vehicle = attrs.get('vehicle')
        start = attrs.get('start_date')
        end = attrs.get('end_date')
        if start > end:
            raise serializers.ValidationError('start_date must be <= end_date')
        if not is_vehicle_available(vehicle, start, end):
            raise serializers.ValidationError('Vehicle not available for these dates')
        return attrs

    def create(self, validated_data):
        vehicle = validated_data['vehicle']
        start = validated_data['start_date']
        end = validated_data['end_date']
        days = (end - start).days + 1  # inclusive of end_date
        total = vehicle.price_per_day * days + vehicle.deposit
        booking = Booking.objects.create(
            user=self.context['request'].user,
            vehicle=vehicle,
            start_date=start,
            end_date=end,
            total_price=total,
            status='pending'
        )
        return booking


class BookingSerializer(serializers.ModelSerializer):
    vehicle = VehicleSerializer(read_only=True)

    class Meta:
        model = Booking
        fields = '__all__'
