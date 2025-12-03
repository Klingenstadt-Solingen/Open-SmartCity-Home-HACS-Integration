from homeassistant.config_entries import ConfigEntry
from .const import DOMAIN, PLATFORMS, CONFIG_STATIONS

def get_selected_station_ids(config_entry: ConfigEntry):
    return config_entry.options.get(
        CONFIG_STATIONS,
        config_entry.data.get(CONFIG_STATIONS, [])
    )
