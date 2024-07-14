import logging
import json
from pathlib import Path
import re

from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Config, HomeAssistant
from homeassistant.const import Platform
from .utils import check_settings, FuelType, ComponentSession

manifestfile = Path(__file__).parent / 'manifest.json'
with open(manifestfile, 'r') as json_file:
    manifest_data = json.load(json_file)
    
DOMAIN = manifest_data.get("domain")
NAME = manifest_data.get("name")
VERSION = manifest_data.get("version")
ISSUEURL = manifest_data.get("issue_tracker")
PLATFORMS = [Platform.SENSOR]

STARTUP = """
-------------------------------------------------------------------
{name}
Version: {version}
This is a custom component
If you have any issues with this you need to open an issue here:
{issueurl}
-------------------------------------------------------------------
""".format(
    name=NAME, version=VERSION, issueurl=ISSUEURL
)


_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up this component using YAML."""
    _LOGGER.info(STARTUP)
    if config.get(DOMAIN) is None:
        # We get her if the integration is set up using config flow
        return True

    try:
        await hass.config_entries.async_forward_entry(config, Platform.SENSOR)
        _LOGGER.info("Successfully added sensor from the integration")
    except ValueError:
        pass

    await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_IMPORT}, data={}
    )
    return True

async def async_update_options(hass: HomeAssistant, config_entry: ConfigEntry):
    """Reload integration when options changed"""
    await hass.config_entries.async_reload(config_entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    unload_ok = await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS)
    # if unload_ok:
        # hass.data[DOMAIN].pop(config_entry.entry_id)

    return unload_ok


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up component as config entry."""
    await hass.config_entries.async_forward_entry_setup(config_entry, Platform.SENSOR)
    config_entry.async_on_unload(config_entry.add_update_listener(async_update_options))
    _LOGGER.info(f"{DOMAIN} register_services")
    register_services(hass, config_entry)
    return True


async def async_remove_entry(hass, config_entry):
    try:
        await hass.config_entries.async_forward_entry_unload(config_entry, Platform.SENSOR)
        _LOGGER.info("Successfully removed sensor from the integration")
    except ValueError:
        pass


def register_services(hass, config_entry):
        
    async def handle_get_lowest_fuel_price(call):
        """Handle the service call."""
        fuel_type = getattr(FuelType, call.data.get('fuel_type').upper(), None)
        country = call.data.get('country')
        postalcode = call.data.get('postalcode')
        town = call.data.get('town','')
        if town is None:
            town = ""
        max_distance = call.data.get('max_distance')
        if max_distance is None:
            max_distance = 0
        filter = call.data.get('filter','')
        if filter is None:
            filter = ""
        
        session = ComponentSession()
        station_info = await hass.async_add_executor_job(lambda: session.getStationInfo(postalcode, country, fuel_type, town, max_distance, filter))
        
        _LOGGER.debug(f"{NAME} get_lowest_fuel_price info found: {station_info}")
        hass.bus.async_fire(f"{DOMAIN}_lowest_fuel_price", station_info)
        
    async def handle_get_lowest_fuel_price_coor(call):
        """Handle the service call."""
        fuel_type = getattr(FuelType, call.data.get('fuel_type').upper(), None)
        latitude = call.data.get('latitude')
        longitude = call.data.get('longitude')
        max_distance = call.data.get('max_distance')
        if max_distance is None:
            max_distance = 0
        filter = call.data.get('filter','')
        if filter is None:
            filter = ""
        
        session = ComponentSession()
        station_info = await hass.async_add_executor_job(lambda: session.getStationInfoLatLon(latitude, longitude, fuel_type, max_distance, filter))
        
        _LOGGER.debug(f"{NAME} get_lowest_fuel_price_coor info found: {station_info}")
        hass.bus.async_fire(f"{DOMAIN}_lowest_fuel_price_coor", station_info)

        
    async def handle_get_lowest_fuel_price_on_route(call):
        """Handle the service call."""
        country = call.data.get('country')
        to_country = call.data.get('to_country', country)
        fuel_type = getattr(FuelType, call.data.get('fuel_type').upper(), None)
        filter = call.data.get('filter','')
        from_postalcode = call.data.get('from_postalcode')
        to_postalcode = call.data.get('to_postalcode')
        # here_api_key = call.data.get('here_api_key','')
        # ors_api_key = call.data.get('ors_api_key','')

        _LOGGER.debug(f"handle_get_lowest_fuel_price_on_route: country: {country}, to_country: {to_country}, fuel_type: {fuel_type}, filter: {filter}, from_postalcode: {from_postalcode}, to_postalcode: {to_postalcode}")

        session = ComponentSession()
        station_info = await hass.async_add_executor_job(lambda: session.getPriceOnRoute(country, fuel_type, from_postalcode, to_postalcode, to_country, filter))
        
        _LOGGER.debug(f"{NAME} get_lowest_fuel_price_on_route info found: {station_info}")
        hass.bus.async_fire(f"{DOMAIN}_lowest_fuel_price_on_route", station_info)
        
        
    async def handle_get_lowest_fuel_price_on_route_coor(call):
        """Handle the service call."""
        fuel_type = getattr(FuelType, call.data.get('fuel_type').upper(), None)
        filter = call.data.get('filter','')
        from_latitude = call.data.get('from_latitude')
        from_longitude = call.data.get('from_longitude')
        to_latitude = call.data.get('to_latitude')
        to_longitude = call.data.get('to_longitude')
        # here_api_key = call.data.get('here_api_key','')
        # ors_api_key = call.data.get('ors_api_key','')

        _LOGGER.debug(f"handle_get_lowest_fuel_price_on_route_coor: fuel_type: {fuel_type}, filter: {filter}, from_latitude: {from_latitude}, from_longitude: {from_longitude}, to_latitude: {to_latitude}, to_longitude: {to_longitude}")

        session = ComponentSession()
        station_info = await hass.async_add_executor_job(lambda: session.getPriceOnRouteLatLon(fuel_type, from_latitude, from_longitude, to_latitude, to_longitude, filter))
        
        _LOGGER.debug(f"{NAME} get_lowest_fuel_price_on_route_coor info found: {station_info}")
        hass.bus.async_fire(f"{DOMAIN}_lowest_fuel_price_on_route_coor", station_info)
    
        
           


    hass.services.async_register(DOMAIN, 'get_lowest_fuel_price', handle_get_lowest_fuel_price)
    hass.services.async_register(DOMAIN, 'get_lowest_fuel_price_on_route', handle_get_lowest_fuel_price_on_route)
    hass.services.async_register(DOMAIN, 'get_lowest_fuel_price_coor', handle_get_lowest_fuel_price_coor)
    hass.services.async_register(DOMAIN, 'get_lowest_fuel_price_on_route_coor', handle_get_lowest_fuel_price_on_route_coor)
    _LOGGER.info(f"async_register done")