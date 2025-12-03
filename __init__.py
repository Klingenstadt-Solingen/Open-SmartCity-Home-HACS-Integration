from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN, PLATFORMS, CONFIG_STATIONS, MQTT_HOST, MQTT_USERNAME, MQTT_PASSWORD, MQTT_PORT, MQTT_TOPIC
from .logger import _LOGGER
from .helper import get_selected_station_ids
import asyncio
import paho.mqtt.client as mqtt

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    selected_station_ids = get_selected_station_ids(entry)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        CONFIG_STATIONS: selected_station_ids
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    mqtt_client = mqtt.Client()
    mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    loop = asyncio.get_event_loop()
    mqtt_client.connect(MQTT_HOST, MQTT_PORT)

    def _handle_mqtt_update(hass, entity, state):
        _LOGGER.info(f"HANDLE MQTT: {entity._attr_unique_id} {state}")
        entity._state = state
        entity.async_schedule_update_ha_state()

    def on_message(client, userdata, msg):
        topic = msg.topic
        topic_parts = topic.split("/")
        if len(topic_parts) == 4:
            sensor_id = topic_parts[2]
            entity = hass.data[DOMAIN][entry.entry_id]["entity_map"].get(sensor_id, None)
            if entity is not None:
                payload = msg.payload.decode()
                hass.loop.call_soon_threadsafe(
                    _handle_mqtt_update, hass, entity, payload
                )
                _LOGGER.info(f"MSG: topic: {topic}, payload: {payload}")

    mqtt_client.on_message = on_message
    mqtt_client.subscribe(MQTT_TOPIC)

    loop.run_in_executor(None, mqtt_client.loop_forever)

    entry.async_on_unload(lambda: mqtt_client.disconnect())

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)

    return unload_ok
