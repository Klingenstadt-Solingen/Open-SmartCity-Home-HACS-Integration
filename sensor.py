from __future__ import annotations
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers import device_registry as dr

from .const import DOMAIN, CONFIG_STATIONS
from .api import async_get_all_stations, async_get_sensors_for_station_id
from .logger import _LOGGER
from .classes import Sensor, Station

def get_station_ids(hass: HomeAssistant, entry: ConfigEntry):
    config = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if config is None:
        return None
    return config.get(CONFIG_STATIONS, None)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    selected_station_ids = get_station_ids(hass, entry)
    if selected_station_ids is None:
        return

    stations = await async_get_all_stations()
    entities: list[SensorEntity] = []
    entity_map = {}
    for station_id in selected_station_ids:
        station = next((station for station in stations if station.id == station_id), None)
        if station is None:
            continue
        sensors = await async_get_sensors_for_station_id(station_id)
        if len(sensors) == 0:
            continue
        for sensor in sensors:
            sensor_entity = SmartHomeSensorEntity(sensor, station)
            entities.append(
                sensor_entity
            )
            entity_map[sensor.id] = sensor_entity

    async_add_entities(entities)

    hass.data[DOMAIN][entry.entry_id]["entity_map"] = entity_map

    entry.async_on_unload(
        entry.add_update_listener(_config_entry_updated)
    )

    cleanup_remove_stations(hass, entry, selected_station_ids)

def cleanup_remove_stations(hass, entry, selected_station_ids: list[str]):
    device_registry = dr.async_get(hass)
    devices = dr.async_entries_for_config_entry(device_registry, entry.entry_id)
    for device in devices:
        for identifier in device.identifiers:
            if identifier[0] == DOMAIN:
                station_id = identifier[1]
                if station_id not in selected_station_ids:
                    device_registry.async_remove_device(device.id)
                    break

async def _config_entry_updated(hass: HomeAssistant, entry: ConfigEntry) -> None:
    selected_station_ids = get_station_ids(hass, entry)
    if selected_station_ids is None:
        return None
    cleanup_remove_stations(hass, entry, selected_station_ids)
    await hass.config_entries.async_reload(entry.entry_id)

class SmartHomeSensorEntity(SensorEntity):
    def __init__(self, sensor: Sensor, station: Station):
        self._name = sensor.name
        self._unit = sensor.unit
        self._state = sensor.state

        self._attr_device_info = {
            "identifiers": {(DOMAIN, station.id)},
            "name": f"Sensorstation {station.name}",
            "manufacturer": "Open SmartCity Home",
            "model": "Sensorstation",
        }

        # Set unique_id for this entity so HA tracks it persistently
        self._attr_unique_id = sensor.id

    async def async_added_to_hass(self):
        self.async_write_ha_state()


    @property
    def name(self) -> str:
        return self._name

    @property
    def native_unit_of_measurement(self) -> str | None:
        return self._unit

    # Since you'll use MQTT (push) for updates, disable polling
    @property
    def should_poll(self) -> bool:
        return False

    # You may omit async_update() — instead, on MQTT message:
    # call self.async_schedule_update_ha_state()

    @property
    def native_value(self):
        return self._state

