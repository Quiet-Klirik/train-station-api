from django.urls import path, include
from rest_framework.routers import DefaultRouter

from train_station.views import (
    RouteViewSet,
    TrainViewSet,
    JourneyViewSet,
    OrderViewSet,
)

app_name = "train_station"

router = DefaultRouter()
router.register("routes", RouteViewSet)
router.register("trains", TrainViewSet)
router.register("journeys", JourneyViewSet)
router.register("orders", OrderViewSet)

urlpatterns = [
    path("", include(router.urls))
]
