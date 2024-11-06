from datetime import timedelta

from django.db.models import Prefetch, Count, F
from django.utils import timezone
from rest_framework import viewsets, mixins

from train_station.models import (
    Route,
    Journey,
    Train,
    Order
)
from train_station.serializers import (
    RouteSerializer,
    RouteListSerializer,
    RouteRetrieveSerializer,
    TrainSerializer,
    TrainListSerializer,
    TrainRetrieveSerializer,
    JourneySerializer,
    JourneyListSerializer,
    JourneyRetrieveSerializer,
    OrderSerializer,
    OrderListSerializer,
)


class RouteViewSet(viewsets.ModelViewSet):
    queryset = Route.objects.all()
    serializer_class = RouteSerializer

    def get_retrieve_queryset(self):
        now = timezone.now()
        next_24_hours = now + timedelta(hours=24)
        nearest_journeys = Journey.objects.filter(
            departure_time__range=(now, next_24_hours)
        ).select_related("train")

        queryset = self.queryset.select_related(
            "source", "destination"
        ).prefetch_related(Prefetch(
            "journeys", queryset=nearest_journeys, to_attr="nearest_journeys"
        ))
        return queryset

    def get_queryset(self):
        queryset = self.queryset
        match self.action:
            case "list":
                return queryset.select_related("source", "destination")
            case "retrieve":
                return self.get_retrieve_queryset()
            case _:
                return queryset

    def get_serializer_class(self):
        match self.action:
            case "list":
                return RouteListSerializer
            case "retrieve":
                return RouteRetrieveSerializer
            case _:
                return self.serializer_class


class TrainViewSet(viewsets.ModelViewSet):
    queryset = Train.objects.all()
    serializer_class = TrainSerializer

    def get_queryset(self):
        queryset = self.queryset
        if self.action in ["list", "retrieve"]:
            queryset = queryset.select_related("train_type")
        return queryset

    def get_serializer_class(self):
        match self.action:
            case "list":
                return TrainListSerializer
            case "retrieve":
                return TrainRetrieveSerializer
            case _:
                return self.serializer_class


class JourneyViewSet(viewsets.ModelViewSet):
    queryset = Journey.objects.all()
    serializer_class = JourneySerializer

    def get_queryset(self):
        queryset = self.queryset
        match self.action:
            case "list":
                return queryset.select_related(
                    "route__source", "route__destination", "train"
                ).annotate(seats_available=(
                        F("train__wagons_num")
                        * F("train__places_in_wagon")
                        - Count("tickets")
                ))
            case "retrieve":
                return queryset.select_related(
                    "route__source", "route__destination", "train__train_type"
                ).prefetch_related("crew", "tickets")
            case _:
                return queryset

    def get_serializer_class(self):
        match self.action:
            case "list":
                return JourneyListSerializer
            case "retrieve":
                return JourneyRetrieveSerializer
            case _:
                return self.serializer_class


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    def get_queryset(self):
        queryset = self.queryset
        if self.action == "list":
            return queryset.prefetch_related(
                "tickets__journey__route__source",
                "tickets__journey__route__destination",
                "tickets__journey__train",
            )
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        return self.serializer_class
