from django.db import transaction
from rest_framework import serializers

from train_station.models import (
    Station,
    Route,
    TrainType,
    Train,
    Crew,
    Journey,
    Order,
    Ticket
)


class StationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Station
        fields = ["id", "name", "latitude", "longitude"]


class RouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = ["id", "source", "destination", "distance"]

    def validate(self, attrs):
        data = super().validate(attrs=attrs)
        Route.validate_destination(
            data["destination"], data["source"], serializers.ValidationError
        )
        return data


class RouteListSerializer(RouteSerializer):
    source = serializers.CharField(
        source="source.name", read_only=True
    )
    destination = serializers.CharField(
        source="destination.name", read_only=True
    )


class RouteRetrieveSerializer(RouteSerializer):
    source = StationSerializer(read_only=True)
    destination = StationSerializer(read_only=True)
    nearest_journeys = serializers.SerializerMethodField()

    class Meta:
        model = Route
        fields = [
            "id",
            "source",
            "destination",
            "distance",
            "nearest_journeys"
        ]

    @staticmethod
    def get_nearest_journeys(obj):
        return [str(journey) for journey in obj.nearest_journeys]


class TrainTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainType
        fields = ["id", "name"]


class TrainSerializer(serializers.ModelSerializer):
    class Meta:
        model = Train
        fields = ["id", "name", "wagons_num", "places_in_wagon", "train_type"]


class TrainListSerializer(serializers.ModelSerializer):
    train_type = serializers.CharField(
        source="train_type.name", read_only=True
    )

    class Meta:
        model = Train
        fields = ["id", "name", "capacity", "train_type"]


class TrainRetrieveSerializer(TrainSerializer):
    total_capacity = serializers.IntegerField(
        source="capacity", read_only=True
    )
    train_type = TrainTypeSerializer(read_only=True)

    class Meta:
        model = Train
        fields = [
            "id",
            "name",
            "wagons_num",
            "places_in_wagon",
            "total_capacity",
            "train_type"
        ]


class CrewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Crew
        fields = ["id", "first_name", "last_name"]


class JourneySerializer(serializers.ModelSerializer):
    class Meta:
        model = Journey
        fields = [
            "id",
            "route",
            "train",
            "departure_time",
            "arrival_time",
            "crew",
        ]


class JourneyListSerializer(serializers.ModelSerializer):
    route = serializers.SerializerMethodField()
    train = serializers.CharField(source="train.name", read_only=True)
    seats_available = serializers.IntegerField(read_only=True)

    class Meta:
        model = Journey
        fields = [
            "id",
            "route",
            "train",
            "departure_time",
            "arrival_time",
            "seats_available",
        ]

    @staticmethod
    def get_route(obj):
        return str(obj.route)


class JourneyTicketListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = [
            "wagon",
            "seat",
        ]


class JourneyRetrieveSerializer(serializers.ModelSerializer):
    route = RouteListSerializer(many=False, read_only=True)
    train = TrainListSerializer(many=False)
    crew = CrewSerializer(many=True, read_only=True)
    seats_taken = JourneyTicketListSerializer(
        source="tickets",
        many=True,
        read_only=True
    )

    class Meta:
        model = Journey
        fields = [
            "id",
            "route",
            "train",
            "departure_time",
            "arrival_time",
            "crew",
            "seats_taken",
        ]


class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ["id", "wagon", "seat", "journey"]

    def validate(self, attrs):
        data = super().validate(attrs=attrs)
        Ticket.validate_seat(
            data["wagon"],
            data["seat"],
            data["journey"],
            serializers.ValidationError
        )
        return data


class TicketListSerializer(TicketSerializer):
    journey = serializers.SerializerMethodField()

    @staticmethod
    def get_journey(obj):
        return str(obj.journey)


class OrderSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(many=True, read_only=False, allow_empty=False)

    class Meta:
        model = Order
        fields = ["id", "tickets"]

    def create(self, validated_data):
        with transaction.atomic():
            tickets_data = validated_data.pop("tickets")
            order = Order.objects.create(**validated_data)
            for ticket_data in tickets_data:
                Ticket.objects.create(order=order, **ticket_data)
            return order


class OrderListSerializer(serializers.ModelSerializer):
    tickets = TicketListSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ["id", "created_at", "tickets"]
