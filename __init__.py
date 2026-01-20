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

   
    if hasattr(mqtt, "CallbackAPIVersion"):
        mqtt_client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION1
        )
    else:
        # paho-mqtt 1.6.x
        mqtt_client = mqtt.Client()
    mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    mqtt_client.reconnect_delay_set(min_delay=1, max_delay=60)
    loop = asyncio.get_event_loop()
    mqtt_client.connect(MQTT_HOST, MQTT_PORT)

    def _handle_mqtt_update(hass, entity, state):
        entity_name = entity._name
        entity_id = entity._attr_unique_id
        _LOGGER.info(f"[{entity_id}] {entity_name}: {state}")
        entity._state = state
        entity.async_schedule_update_ha_state()

    def on_connect(client, userdata, flags, rc, properties=None):
        if rc == 0:
            _LOGGER.info("MQTT connected, subscribing to %s", MQTT_TOPIC)
            client.subscribe(MQTT_TOPIC)
        else:
            _LOGGER.warning("MQTT connect failed rc=%s", rc)

    def on_disconnect(client, userdata, rc, properties=None):
        _LOGGER.warning("MQTT disconnected rc=%s (will auto-reconnect)", rc)

    def on_message(client, userdata, msg):
        topic = msg.topic
        topic_parts = topic.split("/")
        if len(topic_parts) == 4:
            sensor_id = topic_parts[2]
            entity = hass.data[DOMAIN][entry.entry_id]["entity_map"].get(sensor_id, None)
            if entity is not None:
                payload = msg.payload.decode()
                if payload is not None:
                    hass.loop.call_soon_threadsafe(
                        _handle_mqtt_update, hass, entity, payload
                    )

    mqtt_client.on_connect = on_connect
    mqtt_client.on_disconnect = on_disconnect
    mqtt_client.on_message = on_message

    loop.run_in_executor(None, mqtt_client.loop_forever)

    entry.async_on_unload(lambda: mqtt_client.disconnect())

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)

    return unload_ok
