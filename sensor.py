from __future__ import annotations
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.const import STATE_UNKNOWN
from datetime import timedelta

from .const import DOMAIN, CONFIG_STATIONS
from .api import async_get_all_stations, async_get_sensors_for_station_id
from .logger import _LOGGER
from .classes import Sensor, Station

# the service refreshes the station positions from Frost every 6 hours, polling faster only
# produces API calls without new data
POSITION_REFRESH_INTERVAL = timedelta(hours=6)

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

    async def _refresh_positions(_now) -> None:
        """Pick up a moved station without a restart.

        Only the position is taken from the API. The status keeps coming from MQTT, which is
        live, while the API answer can be older than the last status message.
        """
        stations_by_id = {station.id: station for station in await async_get_all_stations()}
        for sensor_entity in entity_map.values():
            station = stations_by_id.get(sensor_entity.station_id)
            if station is not None:
                sensor_entity.set_position(station)

    entry.async_on_unload(
        async_track_time_interval(hass, _refresh_positions, POSITION_REFRESH_INTERVAL)
    )

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
        # kept so the position can be re-applied on every status update
        self._station = station

        # Basic entity info
        self._attr_name = sensor.name
        # only used to translate the attribute names, the entity name stays _attr_name
        self._attr_translation_key = "station_sensor"
        self._attr_native_unit_of_measurement = sensor.unit
        self._attr_native_value = sensor.state

        self._apply_status(sensor.status)

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

    @property
    def station_id(self) -> str:
        return self._station.id

    def set_position(self, station: Station) -> None:
        """Replace the station behind this sensor, keeping the status from MQTT."""
        if (station.latitude, station.longitude) == (
            self._station.latitude,
            self._station.longitude,
        ):
            return
        self._station = station
        self._apply_status(self._status)
        self.async_write_ha_state()

    def set_status(self, status: str | None) -> None:
        """Mark entity online/offline."""
        self._apply_status(status)
        self.async_write_ha_state()

    def _apply_status(self, status: str | None) -> None:
        """Rebuild the attributes in one place.

        The coordinates must be re-added on every update, otherwise a status message replaces the
        whole dict and the sensor drops off the map. They come from the station, the API has no
        per sensor position.
        """
        status = status.lower() if status is not None else None
        # kept so a position refresh can rebuild the attributes without a status message
        self._status = status
        self._attr_available = status == "online"

        attributes: dict = {"status": status or "unknown"}
        # latitude and longitude are the names Home Assistant looks for to place an entity on a map
        if self._station.has_location:
            attributes["latitude"] = self._station.latitude
            attributes["longitude"] = self._station.longitude
            attributes["latitude_text"] = self._station.latitude_text
            attributes["longitude_text"] = self._station.longitude_text
            attributes["coordinates"] = self._station.coordinates_text
        self._attr_extra_state_attributes = attributes


