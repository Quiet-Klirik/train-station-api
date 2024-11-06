from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class Station(models.Model):
    name = models.CharField(max_length=255, unique=True)
    latitude = models.FloatField(
        validators=[MinValueValidator(-90), MaxValueValidator(90)]
    )
    longitude = models.FloatField(
        validators=[MinValueValidator(-180), MaxValueValidator(180)]
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["latitude", "longitude"],
                name="station_latitude_longitude_unique"
            )
        ]
        ordering = ["name"]

    def __str__(self):
        return self.name


class Route(models.Model):
    source = models.ForeignKey(
        Station,
        on_delete=models.CASCADE,
        related_name="source_routes"
    )
    destination = models.ForeignKey(
        Station,
        on_delete=models.CASCADE,
        related_name="destination_routes"
    )
    distance = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["source", "destination"],
                name="route_source_destination_unique"
            )
        ]
        ordering = ["source__name", "destination__name"]

    @staticmethod
    def validate_destination(
            destination,
            source,
            exception_error=ValidationError
    ):
        if destination == source:
            raise exception_error({
                "destination": "Source and destination stations "
                               "must be different"
            })

    def clean(self):
        self.validate_destination(self.destination, self.source)

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.source} -> {self.destination}"


class TrainType(models.Model):
    name = models.CharField(max_length=255)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Train(models.Model):
    name = models.CharField(max_length=255)
    wagons_num = models.PositiveIntegerField()
    places_in_wagon = models.PositiveIntegerField()
    train_type = models.ForeignKey(
        TrainType,
        on_delete=models.CASCADE,
        related_name="trains"
    )

    class Meta:
        ordering = ["name"]

    @property
    def capacity(self):
        return self.wagons_num * self.places_in_wagon

    def __str__(self):
        return self.name


class Crew(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)

    class Meta:
        ordering = ["first_name", "last_name"]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Journey(models.Model):
    route = models.ForeignKey(
        Route,
        on_delete=models.CASCADE,
        related_name="journeys"
    )
    train = models.ForeignKey(
        Train,
        on_delete=models.CASCADE,
        related_name="journeys"
    )
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()
    crew = models.ManyToManyField(Crew, related_name="journeys")

    class Meta:
        ordering = ["-departure_time"]

    def __str__(self):
        return (
            f"Train {self.train} ({self.route}) {self.departure_time.time()}"
        )


class Order(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name="orders"
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"#{self.pk}"


class Ticket(models.Model):
    wagon = models.PositiveIntegerField()
    seat = models.PositiveIntegerField()
    journey = models.ForeignKey(
        Journey,
        on_delete=models.CASCADE,
        related_name="tickets"
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="tickets"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["journey", "wagon", "seat"],
                name="ticket_journey_wagon_seat_unique"
            )
        ]
        ordering = ["-journey__departure_time", "wagon", "seat"]

    @staticmethod
    def validate_seat(wagon, seat, journey, exception_error=ValidationError):
        if wagon > journey.train.wagons_num:
            raise exception_error({
                "wagon": f"The wagon number must be less than "
                         f"or equal to {journey.train.wagons_num}."
            })
        if seat > journey.train.places_in_wagon:
            raise exception_error({
                "seat": f"The seat number must be less than "
                        f"or equal to {journey.train.places_in_wagon}"
            })

    def clean(self):
        self.validate_seat(self.wagon, self.seat, self.journey)

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.journey} [wagon: {self.wagon}, seat: {self.seat}]"
