from .classes import Station, Sensor
from .const import API_URL, API_USER, API_PASSWORD
import aiohttp
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from datetime import datetime, timedelta

open_smartcity_home_stations: list[Station] = []
open_smartcity_home_stations_cache_time: datetime | None = None
CACHE_TTL = timedelta(hours=1)

async def async_fetch_stations() -> list[Station]:
    global open_smartcity_home_stations
    global open_smartcity_home_stations_cache_time

    if (open_smartcity_home_stations_cache_time and datetime.now() - open_smartcity_home_stations_cache_time < CACHE_TTL):
        if (len(open_smartcity_home_stations) != 0):
            return open_smartcity_home_stations
        
    async with aiohttp.ClientSession(auth=aiohttp.BasicAuth(API_USER, API_PASSWORD)) as session:
        async with session.get(API_URL) as response:
            stations: list[Station] = []
            if response.status == 200:
                stations_data = await response.json()
                for station_data in stations_data:
                    station_id = station_data.get("id", None)
                    station_name = station_data.get("name", None)
                    if station_id and station_name:
                        sensors_data = station_data.get("sensors", [])
                        sensors: list[Sensor] = []
                        for sensor_data in sensors_data:
                            sensor_id = sensor_data.get("id", None)
                            sensor_name = sensor_data.get("name", None)
                            sensor_unit = sensor_data.get("unit", None)
                            sensor_state = sensor_data.get("state", None)
                            if sensor_id and sensor_name and sensor_unit:
                                sensors.append(Sensor(sensor_id, sensor_name, sensor_unit, sensor_state))
                        stations.append(Station(station_id, station_name, sensors))
            open_smartcity_home_stations = stations
            open_smartcity_home_stations_cache_time = datetime.now()
            return stations
        
    return []

async def async_get_all_stations() -> list[Station]:
    return await async_fetch_stations()

async def async_get_sensors_for_station_id(station_id: str) -> list[Sensor]:
    stations = await async_fetch_stations()
    station: Station | None = None
    for _station in stations:
        if _station.id == station_id:
            station = _station
    if station:
        return station.sensors
    else:
        return []
