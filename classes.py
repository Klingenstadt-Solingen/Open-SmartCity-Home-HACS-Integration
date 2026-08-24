from typing import Optional

# 5 decimals hold a coordinate within about 0.7 m in Solingen, measured over the 69 stations the
# API delivers the worst case is 0.56 m off. 4 would already be 5.65 m, which is wider than a
# station cabinet, so this is the first step that is honest about the position
COORDINATE_DECIMALS = 5

def format_coordinate(value: float | None) -> str | None:
    """One coordinate as pasteable text, point separator and a fixed number of decimals.

    Home Assistant renders numeric attributes with the user locale and two decimals, so 51.1431
    reaches a German frontend as "51,14" and cannot be pasted into a map service.
    """
    if value is None:
        return None
    return f"{value:.{COORDINATE_DECIMALS}f}"

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

    @property
    def latitude_text(self) -> str | None:
        return format_coordinate(self.latitude)

    @property
    def longitude_text(self) -> str | None:
        return format_coordinate(self.longitude)

    @property
    def coordinates_text(self) -> str | None:
        """Both values in one string, ready to paste into a map service.

        The numeric latitude and longitude stay next to this, the frontend drops an entity off
        the map unless they are really of type number.
        """
        if not self.has_location:
            return None
        return f"{self.latitude_text}, {self.longitude_text}"
