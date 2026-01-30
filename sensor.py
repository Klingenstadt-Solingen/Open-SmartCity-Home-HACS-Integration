from __future__ import annotations
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers import device_registry as dr
from homeassistant.const import STATE_UNKNOWN

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
    _attr_should_poll = False

    def __init__(self, sensor: Sensor, station: Station):
        # Basic entity info
        self._attr_name = sensor.name
        self._attr_native_unit_of_measurement = sensor.unit
        self._attr_native_value = sensor.state

        if sensor.status is not None:
            status = sensor.status.lower()
            self._attr_available = status == "online"
            self._attr_extra_state_attributes = {"status": status}
        else:
            self._attr_available = False
            self._attr_extra_state_attributes = {"status": "unknown"}

        # Device info (groups sensors into one device)
        self._attr_device_info = {
            "identifiers": {(DOMAIN, station.id)},
            "name": f"Sensorstation {station.name}",
            "manufacturer": "Open SmartCity Home",
            "model": "Sensorstation",
        }

        # Stable unique ID
        self._attr_unique_id = sensor.id

    async def async_added_to_hass(self) -> None:
        self.async_write_ha_state()

    # ---- Public update helpers (called from MQTT) ----

    def set_state(self, value) -> None:
        """Update sensor value from MQTT."""
        self._attr_native_value = value
        self.async_write_ha_state()

    def set_status(self, status: str | None) -> None:
        """Mark entity online/offline."""
        if status is not None:
            status = status.lower()
            self._attr_available = status == "online"
            self._attr_extra_state_attributes = {"status": status}
        else:
            self._attr_available = False
            self._attr_extra_state_attributes = {"status": "unknown"}
        self.async_write_ha_state()

