import logging
import json
from pathlib import Path

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

    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_IMPORT}, data={}
        )
    )
    return True

async def async_update_options(hass: HomeAssistant, config_entry: ConfigEntry):
    await hass.config_entries.async_reload(config_entry.entry_id)

async def update_listener(hass: HomeAssistant, config_entry: ConfigEntry):
    """Reload integration when options changed"""
    await hass.config_entries.async_reload(config_entry.entry_id)

async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    unload_ok = await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS)
    # if unload_ok:
        # hass.data[DOMAIN].pop(config_entry.entry_id)

    return unload_ok


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up component as config entry."""
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(config_entry, Platform.SENSOR)
    )
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
        max_distance = call.data.get('max_distance')
        filter = call.data.get('filter','')
        
        session = ComponentSession()
        carbuLocationInfo = await hass.async_add_executor_job(lambda: session.convertPostalCode(postalcode, country, town))
        if not carbuLocationInfo:
            raise Exception(f"Location not found country: {country}, postalcode: {postalcode}, town: {town}")
        town = carbuLocationInfo.get("n")
        city = carbuLocationInfo.get("pn")
        countryname = carbuLocationInfo.get("cn")
        locationid = carbuLocationInfo.get("id")
        _LOGGER.debug(f"{NAME} serivce get_lowest_fuel_price convertPostalCode postalcode: {postalcode}, town: {town}, city: {city}, countryname: {countryname}, locationid: {locationid}")
        price_info = await hass.async_add_executor_job(lambda: session.getFuelPrice(postalcode, country, town, locationid, fuel_type.code, False))
        _LOGGER.debug(f"{NAME} price_info {fuel_type.name} {price_info}")
        
        data = {
            "price" : None,
            "distance" : 0,
            "region" : max_distance,
            "localPrice" : 0,
            "diff" : 0,
            "diff30" : 0,
            "diffPct" : 0,
            "supplier" : None,
            "supplier_brand" : None,
            "url" : None,
            "entity_picture" : None,
            "address" : None,
            "city" : None,
            "latitude" : None,
            "longitude" : None,
            "fuelname" : None,
            "fueltype" : fuel_type,
            "date" : None
        }

        filterSet = False
        if filter is not None and filter.strip() != "":
            filterSet = filter.strip().lower()

        for station in price_info:
            if filterSet:
                match = re.search(filterSet, station.get("brand").lower())
                if not match:
                    continue
            try:
                currDistance = float(station.get("distance"))
                currPrice = float(station.get("price"))
            except ValueError:
                continue
            if currDistance <= max_distance and (data.get("price") == None or currPrice < data.get("price")):
                data["distance"] = float(station.get("distance"))
                data["price"] = float(station.get("price"))
                data["localPrice"] = 0 if price_info[0].get("price") == '' else float(price_info[0].get("price"))
                data["diff"] = round(data["price"] - data["localPrice"],3)
                data["diff30"] = round(data["diff"] * 30,3)
                data["diffPct"] = round(100*((data["price"] - data["localPrice"])/data["price"]),3)
                data["supplier"]  = station.get("name")
                data["supplier_brand"]  = station.get("brand")
                data["url"]   = station.get("url")
                data["entity_picture"] = station.get("logo_url")
                data["address"] = station.get("address")
                data["city"] = station.get("locality")
                data["latitude"] = station.get("lat")
                data["longitude"] = station.get("lon")
                data["fuelname"] = station.get("fuelname")
                data["date"] = station.get("date")
        if data["supplier"] is None and filterSet:
            _LOGGER.warning(f"{NAME} {postalcode} the station filter '{filter}' may result in no results found, if needed, please review filter")
        
        _LOGGER.debug(f"{NAME} get_lowest_fuel_price info found: {data}")
        hass.bus.async_fire(f"{DOMAIN}_lowest_fuel_price", data)
        
    async def handle_get_lowest_fuel_price_on_route(call):
        """Handle the service call."""
        country = call.data.get('country')
        fuel_type = getattr(FuelType, call.data.get('fuel_type').upper(), None)
        filter = call.data.get('filter','')
        from_postalcode = call.data.get('from_postalcode')
        from_town = call.data.get('from_town','')
        to_postalcode = call.data.get('to_postalcode')
        to_town = call.data.get('to_town','')
        
        session = ComponentSession()
        carbuLocationInfo = await hass.async_add_executor_job(lambda: session.convertPostalCode(from_postalcode, country, town))
        if not carbuLocationInfo:
            raise Exception(f"Location not found country: {country}, from_postalcode: {from_postalcode}, town: {town}")
        town = carbuLocationInfo.get("n")
        city = carbuLocationInfo.get("pn")
        countryname = carbuLocationInfo.get("cn")
        locationid = carbuLocationInfo.get("id")
        _LOGGER.debug(f"{NAME} serivce get_lowest_fuel_price convertPostalCode from_postalcode: {from_postalcode}, town: {town}, city: {city}, countryname: {countryname}, locationid: {locationid}")
        price_info = await hass.async_add_executor_job(lambda: session.getFuelPrice(from_postalcode, country, town, locationid, fuel_type.code, False))
        _LOGGER.debug(f"{NAME} price_info {fuel_type} {price_info}")
        
        data = {
            "price" : None,
            "distance" : 0,
            "localPrice" : 0,
            "diff" : 0,
            "diff30" : 0,
            "diffPct" : 0,
            "supplier" : None,
            "supplier_brand" : None,
            "url" : None,
            "entity_picture" : None,
            "address" : None,
            "city" : None,
            "latitude" : None,
            "longitude" : None,
            "fuelname" : None,
            "fueltype" : fuel_type,
            "date" : None
        }

        filterSet = False
        if filter is not None and filter.strip() != "":
            filterSet = filter.strip().lower()

        for station in price_info:
            if filterSet:
                match = re.search(filterSet, station.get("brand").lower())
                if not match:
                    continue
            try:
                currDistance = float(station.get("distance"))
                currPrice = float(station.get("price"))
            except ValueError:
                continue
            if (data.get("price") == None or currPrice < data.get("price")):
                data["distance"] = float(station.get("distance"))
                data["price"] = float(station.get("price"))
                data["localPrice"] = 0 if price_info[0].get("price") == '' else float(price_info[0].get("price"))
                data["diff"] = round(data["price"] - data["localPrice"],3)
                data["diff30"] = round(data["diff"] * 30,3)
                data["diffPct"] = round(100*((data["price"] - data["localPrice"])/data["price"]),3)
                data["supplier"]  = station.get("name")
                data["supplier_brand"]  = station.get("brand")
                data["url"]   = station.get("url")
                data["entity_picture"] = station.get("logo_url")
                data["address"] = station.get("address")
                data["city"] = station.get("locality")
                data["latitude"] = station.get("lat")
                data["longitude"] = station.get("lon")
                data["fuelname"] = station.get("fuelname")
                data["date"] = station.get("date")
        if data["supplier"] is None and filterSet:
            _LOGGER.warning(f"{NAME} {from_postalcode} the station filter '{filter}' may result in no results found, if needed, please review filter")
        
        _LOGGER.debug(f"{NAME} get_lowest_fuel_price info found: {data}")
        hass.bus.async_fire(f"{DOMAIN}_lowest_fuel_price", data)
        
           


    hass.services.async_register(DOMAIN, 'get_lowest_fuel_price', handle_get_lowest_fuel_price)
    hass.services.async_register(DOMAIN, 'get_lowest_fuel_price_on_route', handle_get_lowest_fuel_price_on_route)
    _LOGGER.info(f"async_register done")