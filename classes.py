from typing import Optional

class Sensor:
    id: str
    name: str
    unit: str
    state: int | float | None

    def __init__(self, id: str, name: str, unit: str , state: int | float | None):
        self.id = id
        self.name = name
        self.unit = unit
        self.state = state
        
class Station:
    id: str
    name: str
    sensors: list[Sensor]

    def __init__(self, id: str, name: str, sensors: list[Sensor]):
        self.id = id
        self.name = name
        self.sensors = sensors
