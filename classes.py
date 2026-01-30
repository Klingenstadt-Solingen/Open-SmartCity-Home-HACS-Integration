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

    def __init__(self, id: str, name: str, sensors: list[Sensor]):
        self.id = id
        self.name = name
        self.sensors = sensors
