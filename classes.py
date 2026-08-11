from typing import Optional

class Sensor:
    id: str
    name: str
    unit: str
    state: int | float | None
    status: str | None

    def __init__(self, id: str, name: str, unit: str , state: int | float | None, status: str | None):
        self.id = id
        self.name = name
        self.unit = unit
        self.state = state
        self.status = status

class Station:
    id: str
    name: str
    sensors: list[Sensor]
    # Position of the station. The API only knows it per station, not per sensor, and it stays None
    # when Frost has no location for it.
    latitude: float | None
    longitude: float | None
    status: str | None

    def __init__(
        self,
        id: str,
        name: str,
        sensors: list[Sensor],
        latitude: float | None = None,
        longitude: float | None = None,
        status: str | None = None,
    ):
        self.id = id
        self.name = name
        self.sensors = sensors
        self.latitude = latitude
        self.longitude = longitude
        self.status = status

    @property
    def has_location(self) -> bool:
        return self.latitude is not None and self.longitude is not None
