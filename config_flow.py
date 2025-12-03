import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from .const import DOMAIN, CONFIG_STATIONS
from homeassistant.helpers.selector import selector
from .logger import _LOGGER
from .classes import Station
from .api import async_get_all_stations

def create_station_selection_schema(stations: list[Station], selected_station_ids: list[str] = []):
    options = []
    for station in stations:
        options.append({
            "label": station.name,
            "value": station.id
        })
    return vol.Schema({
            vol.Required(CONFIG_STATIONS, default=selected_station_ids): selector({
                "select": {
                    "options": options,
                    "multiple": True
                }
            })
        })

class StationConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        errors = {}
        if user_input is not None:
            return self.async_create_entry(
                title="Sensorstationsmanager", 
                data={ CONFIG_STATIONS: user_input.get(CONFIG_STATIONS, []) }
            )
        try:
            stations = await async_get_all_stations()
        except Exception as exc:
            errors["base"] = "cannot_connect"
            stations = {}
        return self.async_show_form(
            step_id="user",
            data_schema=create_station_selection_schema(stations),
            errors=errors,
            description_placeholders=None
        )
    
    @staticmethod
    def async_get_options_flow(config_entry):
        return StationOptionsFlowHandler()

class StationOptionsFlowHandler(config_entries.OptionsFlow):
    def get_selected_stations(self) -> list[str]:
        config_entry_options = self.config_entry.options.get(CONFIG_STATIONS, [])
        if len(config_entry_options) != 0:
            return config_entry_options
        else:
            return self.config_entry.data.get(CONFIG_STATIONS, [])

    async def async_step_init(self, user_input=None):
        errors = {}
        stations = await async_get_all_stations()

        if user_input is not None:
            return self.async_create_entry(
                title="Sensorstationsmanager",
                data=user_input
            )
        selected_station_ids = self.get_selected_stations()

        return self.async_show_form(
            step_id="init",
            data_schema=create_station_selection_schema(stations, selected_station_ids),
            errors=errors
        )