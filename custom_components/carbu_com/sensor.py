import logging
import asyncio
from datetime import date, datetime, timedelta
import calendar
from .utils import *

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity, SensorDeviceClass
from homeassistant.const import ATTR_ATTRIBUTION
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle
from homeassistant.const import (
    CONF_NAME,
    CONF_PASSWORD,
    CONF_RESOURCES,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME
)

from . import DOMAIN, NAME

_LOGGER = logging.getLogger(__name__)
_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.0%z"


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required("country", default="BE"): cv.string,
        vol.Required("postalcode"): cv.string,
        vol.Optional("town"): cv.string,
        vol.Optional("filter"): cv.string,
        vol.Optional(FuelType.SUPER95.name_lowercase, default=True): cv.boolean,
        vol.Optional(FuelType.SUPER98.name_lowercase, default=True): cv.boolean,
        vol.Optional(FuelType.DIESEL.name_lowercase, default=True): cv.boolean,
        vol.Optional(FuelType.OILSTD.name_lowercase, default=True): cv.boolean,
        vol.Optional(FuelType.OILEXTRA.name_lowercase, default=True): cv.boolean,
        vol.Optional("quantity", default=1000): cv.positive_int,
    }
)

MIN_TIME_BETWEEN_UPDATES = timedelta(hours=1)


async def dry_setup(hass, config_entry, async_add_devices):
    config = config_entry
    country = config.get("country")
    postalcode = config.get("postalcode")
    town = config.get("town")
    filter = config.get("filter")
    super95 = config.get(FuelType.SUPER95.name_lowercase)
    super98 = config.get(FuelType.SUPER98.name_lowercase)
    diesel = config.get(FuelType.DIESEL.name_lowercase)
    oilstd = config.get(FuelType.OILSTD.name_lowercase)
    oilextra = config.get(FuelType.OILEXTRA.name_lowercase)
    quantity = config.get("quantity")

    check_settings(config, hass)
    sensors = []
    
    componentData = ComponentData(
        config,
        hass
    )
    await componentData._forced_update()
    assert componentData._price_info is not None
    
    if super95:
        sensorSuper95 = ComponentPriceSensor(componentData, FuelType.SUPER95, postalcode, False, 0)
        # await sensorSuper95.async_update()
        sensors.append(sensorSuper95)
        
        sensorSuper95Neigh = ComponentPriceNeighborhoodSensor(componentData, FuelType.SUPER95, postalcode, 5)
        # await sensorSuper95Neigh.async_update()
        sensors.append(sensorSuper95Neigh)
        
        sensorSuper95Neigh = ComponentPriceNeighborhoodSensor(componentData, FuelType.SUPER95, postalcode, 10)
        # await sensorSuper95Neigh.async_update()
        sensors.append(sensorSuper95Neigh)
        
        if country.lower() in ['be','fr','lu']:
            sensorSuper95Prediction = ComponentFuelPredictionSensor(componentData, FuelType.SUPER95_Prediction)
            # await sensorSuper95Prediction.async_update()
            sensors.append(sensorSuper95Prediction)
    
    
    if super98:
        sensorSuper98 = ComponentPriceSensor(componentData, FuelType.SUPER98, postalcode, False, 0)
        # await sensorSuper95.async_update()
        sensors.append(sensorSuper98)
        
        sensorSuper98Neigh = ComponentPriceNeighborhoodSensor(componentData, FuelType.SUPER98, postalcode, 5)
        # await sensorSuper95Neigh.async_update()
        sensors.append(sensorSuper98Neigh)
        
        sensorSuper98Neigh = ComponentPriceNeighborhoodSensor(componentData, FuelType.SUPER98, postalcode, 10)
        # await sensorSuper95Neigh.async_update()
        sensors.append(sensorSuper98Neigh)

    if diesel:
        sensorDiesel = ComponentPriceSensor(componentData, FuelType.DIESEL, postalcode, False, 0)
        # await sensorDiesel.async_update()
        sensors.append(sensorDiesel)
        
        sensorDieselNeigh = ComponentPriceNeighborhoodSensor(componentData, FuelType.DIESEL, postalcode, 5)
        # await sensorDieselNeigh.async_update()
        sensors.append(sensorDieselNeigh)
        
        sensorDieselNeigh = ComponentPriceNeighborhoodSensor(componentData, FuelType.DIESEL, postalcode, 10)
        # await sensorDieselNeigh.async_update()
        sensors.append(sensorDieselNeigh)
    
        if country.lower() in ['be','fr','lu']:
            sensorDieselPrediction = ComponentFuelPredictionSensor(componentData, FuelType.DIESEL_Prediction)
            # await sensorDieselPrediction.async_update()
            sensors.append(sensorDieselPrediction)
    
    if oilstd and country.lower() in ['be','fr','lu']:
        sensorOilstd = ComponentPriceSensor(componentData, FuelType.OILSTD, postalcode, True, quantity)
        # await sensorOilstd.async_update()
        sensors.append(sensorOilstd)
        
        sensorOilstdPrediction = ComponentOilPredictionSensor(componentData, FuelType.OILSTD_Prediction, quantity)
        # await sensorOilstdPrediction.async_update()
        sensors.append(sensorOilstdPrediction)
    
    if oilextra and country.lower() in ['be','fr','lu']:
        sensorOilextra = ComponentPriceSensor(componentData, FuelType.OILEXTRA, postalcode, True, quantity)
        # await sensorOilextra.async_update()
        sensors.append(sensorOilextra)    
        
        sensorOilextraPrediction = ComponentOilPredictionSensor(componentData, FuelType.OILEXTRA_Prediction, quantity)
        # await sensorOilextraPrediction.async_update()
        sensors.append(sensorOilextraPrediction)
    
    async_add_devices(sensors)


async def async_setup_platform(
    hass, config_entry, async_add_devices, discovery_info=None
):
    """Setup sensor platform for the ui"""
    _LOGGER.info("async_setup_platform " + NAME)
    await dry_setup(hass, config_entry, async_add_devices)
    return True


async def async_setup_entry(hass, config_entry, async_add_devices):
    """Setup sensor platform for the ui"""
    _LOGGER.info("async_setup_entry " + NAME)
    config = config_entry.data
    await dry_setup(hass, config, async_add_devices)
    return True


async def async_remove_entry(hass, config_entry):
    _LOGGER.info("async_remove_entry " + NAME)
    try:
        await hass.config_entries.async_forward_entry_unload(config_entry, "sensor")
        _LOGGER.info("Successfully removed sensor from the integration")
    except ValueError:
        pass
        

class ComponentData:
    def __init__(self, config, hass):
        self._config = config
        self._hass = hass
        self._session = ComponentSession()
        self._lastupdate = None
        self._country = config.get("country")
        self._postalcode = config.get("postalcode")
        self._town = config.get("town")
        self._filter = config.get("filter")
        self._price_info = dict()
        
        self._carbuLocationInfo = None
        self._city = None
        self._countryname = None
        self._locationinfo = None
        
        self._quantity = config.get("quantity")
        self._super95 = config.get(FuelType.SUPER95.name_lowercase)
        self._super98 = config.get(FuelType.SUPER98.name_lowercase)
        self._diesel = config.get(FuelType.DIESEL.name_lowercase)
        self._oilstd = config.get(FuelType.OILSTD.name_lowercase)
        self._oilextra = config.get(FuelType.OILEXTRA.name_lowercase)
            
        # <optgroup label="Brandstof">
            # <option value="E10">Super 95 (E10)</option>
            # <option value="SP98">Super 98 (E5)</option>
            # <option value="E10_98">Super 98 (E10)</option>
            # <option value="GO">Diesel (B7)</option>
            # <option value="DB10">Diesel (B10)</option>
            # <option value="DXTL">Diesel (XTL)</option>
            # <option value="GPL">LPG</option>
            # <option value="CNG">CNG</option>
            # <option value="HYDROG">Hydrogeen</option>
            # <option value="LNG">LNG</option>
            # <option value="GO_plus">Diesel+</option>
            # <option value="AdBlue">AdBlue</option>
            # <option value="Elec">Elektriciteit</option>
        # </optgroup>
        
    async def get_fuel_price_info(self, fuel_type: FuelType):
        _LOGGER.debug(f"{NAME} getting fuel price_info {fuel_type.name_lowercase}") 
        price_info = await self._hass.async_add_executor_job(lambda: self._session.getFuelPrices(self._postalcode, self._country, self._town, self._locationinfo, fuel_type, False))
        self._price_info[fuel_type] = price_info
        _LOGGER.debug(f"{NAME} price_info {fuel_type.name_lowercase} {price_info}")  

    async def get_oil_price_info(self, fuel_type: FuelType):
        _LOGGER.debug(f"{NAME} getting oil price_info {fuel_type.name_lowercase}") 
        price_info = await self._hass.async_add_executor_job(lambda: self._session.getOilPrice(self._locationinfo, self._quantity, fuel_type.code))
        self._price_info[fuel_type] = price_info
        _LOGGER.debug(f"{NAME} price_info {fuel_type.name_lowercase} {price_info}")   
    
    async def get_fuel_price_prediction_info(self, fuel_type: FuelType):
        _LOGGER.debug(f"{NAME} getting prediction price_info {fuel_type.name_lowercase}") 
        prediction_info = await self._hass.async_add_executor_job(lambda: self._session.getFuelPrediction(fuel_type.code))
        self._price_info[fuel_type] = prediction_info
        _LOGGER.debug(f"{NAME} prediction_info {fuel_type.name_lowercase}Prediction {prediction_info}")
    
    async def get_oil_price_prediction_info(self):
        _LOGGER.debug(f"{NAME} getting price_info oil prediction") 
        prediction_info = await self._hass.async_add_executor_job(lambda: self._session.getOilPrediction())
        self._price_info[FuelType.OILSTD_Prediction] = prediction_info
        self._price_info[FuelType.OILEXTRA_Prediction] = prediction_info
        _LOGGER.debug(f"{NAME} prediction_info oilPrediction {prediction_info}")

    async def getStationInfoFromPriceInfo(self, priceinfo, postalcode, fueltype, max_distance, filter):
        stationInfo =  await self._hass.async_add_executor_job(lambda: self._session.getStationInfoFromPriceInfo(priceinfo, postalcode, fueltype, max_distance, filter))
        return stationInfo
    
        
    # same as update, but without throttle to make sure init is always executed
    async def _forced_update(self):
        _LOGGER.info("Fetching init stuff for " + NAME)
        if not(self._session):
            self._session = ComponentSession()

        if self._session:
            _LOGGER.debug("Starting with session for " + NAME)
            if self._locationinfo is None and self._country.lower() in ['be','fr','lu']:
                self._carbuLocationInfo = await self._hass.async_add_executor_job(lambda: self._session.convertPostalCode(self._postalcode, self._country, self._town))
                self._town = self._carbuLocationInfo.get("n")
                self._city = self._carbuLocationInfo.get("pn")
                self._countryname = self._carbuLocationInfo.get("cn")
                self._locationinfo = self._carbuLocationInfo.get("id")
            if self._locationinfo is None and self._country.lower() in ['it','nl']:
                boundingboxLocationInfo = await self._hass.async_add_executor_job(lambda: self._session.convertLocationBoundingBox(self._postalcode, self._country, self._town))
                self._locationinfo = boundingboxLocationInfo
            # postalcode, country, town, locationinfo, fueltypecode)
            if self._super95:
                await self.get_fuel_price_info(FuelType.SUPER95)  
                if self._country.lower() in ['be','fr','lu']:
                    await self.get_fuel_price_prediction_info(FuelType.SUPER95_Prediction) 
            else:
                _LOGGER.debug(f"{NAME} not getting fuel price_info {self._super95} FueltType.SUPER95.name_lowercase {FuelType.SUPER95.name_lowercase}")  
                
            if self._super98:
                await self.get_fuel_price_info(FuelType.SUPER98)  
                
            if self._diesel:
                await self.get_fuel_price_info(FuelType.DIESEL)  
                if self._country.lower() in ['be','fr','lu']:
                    await self.get_fuel_price_prediction_info(FuelType.DIESEL_Prediction)
                
            if self._oilstd and self._country.lower() in ['be','fr','lu']:
                await self.get_oil_price_info(FuelType.OILSTD)  
                
            if self._oilextra and self._country.lower() in ['be','fr','lu']:
                await self.get_oil_price_info(FuelType.OILEXTRA)
                
            if self._oilstd or self._oilextra and self._country.lower() in ['be','fr','lu']:
                await self.get_oil_price_prediction_info()
                
            self._lastupdate = datetime.now()
        else:
            _LOGGER.debug(f"{NAME} no session available")

                
    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def _update(self):
        await self._forced_update()

    async def update(self):
        # force update if (some) values are still unknown
        # if ((self._super95 and self._price_info.get(FuelType.SUPER95) is None) 
        #     or (self._super95 and self._price_info.get(FuelType.SUPER95_Prediction) is None)
        #     or (self._super98 and self._price_info.get(FuelType.SUPER98) is None) 
        #     or (self._diesel and self._price_info.get(FuelType.DIESEL) is None) 
        #     or (self._diesel and self._price_info.get(FuelType.DIESEL_Prediction) is None)
        #     or (self._oilstd and self._price_info.get(FuelType.OILSTD) is None) 
        #     or (self._oilextra and self._price_info.get(FuelType.OILEXTRA) is None) 
        #     or (self._oilstd and self._price_info.get(FuelType.OILSTD_Prediction) is None)
        #     or (self._oilextra and self._price_info.get(FuelType.OILEXTRA_Prediction) is None)):
        #     await self._forced_update()
        # else:
            await self._update()
    
    def clear_session(self):
        self._session : None



class ComponentPriceSensor(Entity):
    def __init__(self, data, fueltype: FuelType, postalcode, isOil, quantity):
        self._data = data
        self._fueltype = fueltype
        self._postalcode = postalcode
        self._isOil = isOil
        self._quantity = quantity
        
        self._last_update = None
        self._price = None
        self._supplier = None
        self._supplier_brand = None
        self._url = None
        self._logourl = None
        self._address = None
        self._city = None
        self._lat = None
        self._lon = None
        self._fuelname = None
        self._distance = None
        self._date = None
        self._score = None
        self._country = data._country

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._price

    async def async_update(self):
        await self._data.update()
        self._last_update =  self._data._lastupdate;
        
        self._priceinfo = self._data._price_info.get(self._fueltype)
        if self._isOil:
            self._price = float(self._priceinfo.get("data")[0].get("unitPrice"))
            self._supplier  = self._priceinfo.get("data")[0].get("supplier").get("name") #x.data[0].supplier.name
            oilproductid = self._fueltype.code
            self._url   = f"https://mazout.com/belgie/offers?areaCode={self._data._locationinfo}&by=quantity&for={self._quantity}&productId={oilproductid}"
            self._logourl = self._priceinfo.get("data")[0].get("supplier").get("media").get("logo").get("src") #x.data[0].supplier.media.logo.src
            self._score = self._priceinfo.get("data")[0].get("supplier").get("rating").get("score") #x.data[0].supplier.rating.score
            # self._address = 
            # self._city = 
            # self._lat = 
            # self._lon = 
            self._fuelname = self._priceinfo.get("data")[0].get("product").get("name") #x.data[0].product.name
            # self._distance = 
            self._date = self._priceinfo.get("data")[0].get("available").get("visible")# x.data[0].available.visible
            # self._quantity = self._priceinfo.get("data")[0].get("quantity")
        else:
            stationInfo = await self._data.getStationInfoFromPriceInfo(self._priceinfo, self._postalcode, self._fueltype, 0, self._data._filter)
            # stationInfo = await self._data._hass.async_add_executor_job(lambda: self._data._session.getStationInfoFromPriceInfo(self._priceinfo, self._postalcode, self._fueltype, 0, self._data._filter))
            self._price = stationInfo.get("price") 
            self._supplier  = stationInfo.get("supplier")
            # self._supplier_brand  = stationInfo.get("supplier_brand")
            self._supplier_brand  = stationInfo.get("supplier_brand") if stationInfo.get("supplier_brand") != None and len(stationInfo.get("supplier_brand")) > 1 else f'{stationInfo.get("supplier_brand")}  '
            self._url   = stationInfo.get("url")
            # self._logourl = stationInfo.get("entity_picture")
            self._logourl = f"https://www.prezzibenzina.it/www2/marker.php?brand={self._supplier_brand[:2].upper()}&status=AP&price={stationInfo.get('price')}&certified=0&marker_type=1"
            self._address = stationInfo.get("address")
            self._postalcode = stationInfo.get("postalcode")
            self._city = stationInfo.get("city")
            self._lat = stationInfo.get("latitude")
            self._lon = stationInfo.get("longitude")
            self._fuelname = stationInfo.get("fuelname")
            self._distance = stationInfo.get("distance")
            self._date = stationInfo.get("date")
            self._country = stationInfo.get("country")
            
        
    async def async_will_remove_from_hass(self):
        """Clean up after entity before removal."""
        _LOGGER.info("async_will_remove_from_hass " + NAME)
        self._data.clear_session()


    @property
    def icon(self) -> str:
        """Shows the correct icon for container."""
        return "mdi:gas-station"
        
    @property
    def unique_id(self) -> str:
        """Return the name of the sensor."""
        name = f"{NAME} {self._fueltype.name_lowercase} {self._postalcode}"
        if self._quantity != 0:
            name += f" {self._quantity}l"
        name += " price"
        return (name)

    @property
    def name(self) -> str:
        return self.unique_id

    @property
    def extra_state_attributes(self) -> dict:
        """Return the state attributes."""
        return {
            ATTR_ATTRIBUTION: NAME,
            "last update": self._last_update,
            "fueltype": self._fueltype.name_lowercase,
            "fuelname": self._fuelname,
            "postalcode": self._postalcode,
            "supplier": self._supplier,
            "supplier_brand": self._supplier_brand,
            "url": self._url,
            "entity_picture": self._logourl,
            "address": self._address,
            "city": self._city,
            "latitude": self._lat,
            "longitude": self._lon,
            "distance": f"{self._distance}km",
            "date": self._date,
            "quantity": self._quantity,
            "score": self._score,
            "filter": self._data._filter,
            "country": self._country
            # "suppliers": self._priceinfo
        }

    @property
    def device_info(self) -> dict:
        """I can't remember why this was needed :D"""
        return {
            "identifiers": {(DOMAIN, self.unique_id)},
            "name": self.name,
            "manufacturer": DOMAIN,
        }

    @property
    def unit(self) -> int:
        """Unit"""
        return int

    @property
    def unit_of_measurement(self) -> str:
        """Return the unit of measurement this sensor expresses itself in."""
        return "€/l"
        
    @property
    def device_class(self):
        return SensorDeviceClass.MONETARY

    @property
    def friendly_name(self) -> str:
        return self.unique_id

class ComponentPriceNeighborhoodSensor(Entity):
    def __init__(self, data, fueltype: FuelType, postalcode, max_distance):
        self._data = data
        self._fueltype = fueltype
        self._postalcode = postalcode
        self._max_distance = max_distance
        
        self._last_update = None
        self._price = None
        self._priceinfo = None
        self._supplier = None
        self._supplier_brand = None
        self._url = None
        self._logourl = None
        self._address = None
        self._city = None
        self._lat = None
        self._lon = None
        self._fuelname = None
        self._distance = None
        self._date = None
        self._score = None
        self._diff = None
        self._diff30 = None
        self._diffPct = None
        self._country = data._country

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._price

    async def async_update(self):
        await self._data.update()
        self._last_update =  self._data._lastupdate;
        
        self._price = None
        self._priceinfo = self._data._price_info.get(self._fueltype)
        stationInfo = await self._data.getStationInfoFromPriceInfo(self._priceinfo, self._postalcode, self._fueltype, self._max_distance, self._data._filter)
        # stationInfo = await self._data._hass.async_add_executor_job(lambda: self._data._session.getStationInfoFromPriceInfo(self._priceinfo, self._postalcode, self._fueltype, 0, self._data._filter))
        # stationInfo = await self._data._hass.async_add_executor_job(lambda: self._data._session.getStationInfoFromPriceInfo(self._priceinfo, self._postalcode, self._fueltype, 0, self._data._filter))
        self._price = stationInfo.get("price") 
        self._diff = stationInfo.get("diff") 
        self._diff30 = stationInfo.get("diff30") 
        self._diffPct = stationInfo.get("diffPct") 
        self._supplier  = stationInfo.get("supplier")
        # self._supplier_brand  = stationInfo.get("supplier_brand")
        self._supplier_brand  = stationInfo.get("supplier_brand") if stationInfo.get("supplier_brand") != None and len(stationInfo.get("supplier_brand")) > 1 else f'{stationInfo.get("supplier_brand")}  '
        # self._logourl = stationInfo.get("entity_picture")
        self._logourl = f"https://www.prezzibenzina.it/www2/marker.php?brand={self._supplier_brand[:2].upper()}&status=AP&price={stationInfo.get('price')}&certified=0&marker_type=1"
        self._address = stationInfo.get("address")
        self._postalcode = stationInfo.get("postalcode")
        self._city = stationInfo.get("city")
        self._lat = stationInfo.get("latitude")
        self._lon = stationInfo.get("longitude")
        self._fuelname = stationInfo.get("fuelname")
        self._distance = stationInfo.get("distance")
        self._date = stationInfo.get("date")
        self._country = stationInfo.get("country")
        
    async def async_will_remove_from_hass(self):
        """Clean up after entity before removal."""
        _LOGGER.info("async_will_remove_from_hass " + NAME)
        self._data.clear_session()


    @property
    def icon(self) -> str:
        """Shows the correct icon for container."""
        return "mdi:gas-station"
        
    @property
    def unique_id(self) -> str:
        """Return the name of the sensor."""
        name = f"{NAME} {self._fueltype.name_lowercase} {self._postalcode} {self._max_distance}km"
        return (name)

    @property
    def name(self) -> str:
        return self.unique_id

    @property
    def extra_state_attributes(self) -> dict:
        """Return the state attributes."""
        return {
            ATTR_ATTRIBUTION: self._supplier_brand,
            "last update": self._last_update,
            "fueltype": self._fueltype.name_lowercase,
            "fuelname": self._fuelname,
            "postalcode": self._postalcode,
            "supplier": self._supplier,
            "supplier_brand": self._supplier_brand,
            "url": self._url,
            "entity_picture": self._logourl,
            "address": self._address,
            "city": self._city,
            "latitude": self._lat,
            "longitude": self._lon,
            "region": f"{self._max_distance}km",
            "distance": f"{self._distance}km",
            "price diff": f"{self._diff}€",
            "price diff %": f"{self._diffPct}%",
            "price diff 30l": f"{self._diff30}€",
            "date": self._date,
            "score": self._score,
            "filter": self._data._filter,
            "country": self._country
        }

    @property
    def device_info(self) -> dict:
        """I can't remember why this was needed :D"""
        return {
            "identifiers": {(DOMAIN, self.unique_id)},
            "name": self.name,
            "manufacturer": DOMAIN,
        }

    @property
    def unit(self) -> int:
        """Unit"""
        return int

    @property
    def unit_of_measurement(self) -> str:
        """Return the unit of measurement this sensor expresses itself in."""
        return "€/l"
        
    @property
    def device_class(self):
        return SensorDeviceClass.MONETARY

    @property
    def friendly_name(self) -> str:
        return self.unique_id
      

class ComponentFuelPredictionSensor(Entity):
    def __init__(self, data, fueltype):
        self._data = data
        self._fueltype = fueltype
        
        
        self._fuelname = None
        self._last_update = None
        self._trend = None
        self._date = None
        

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._trend

    async def async_update(self):
        await self._data.update()
        self._last_update =  self._data._lastupdate
        
        priceinfo = self._data._price_info.get(self._fueltype)
        
        
        self._trend = round(priceinfo,3)
        
        self._date = self._data._lastupdate
        
            
        
    async def async_will_remove_from_hass(self):
        """Clean up after entity before removal."""
        _LOGGER.info("async_will_remove_from_hass " + NAME)
        self._data.clear_session()


    @property
    def icon(self) -> str:
        """Shows the correct icon for container."""
        return "mdi:gas-station"
        
    @property
    def unique_id(self) -> str:
        """Return the name of the sensor."""
        name = f"{NAME} {self._fueltype.name_lowercase.replace('_',' ')}"
        return (name)

    @property
    def name(self) -> str:
        return self.unique_id

    @property
    def extra_state_attributes(self) -> dict:
        """Return the state attributes."""
        return {
            ATTR_ATTRIBUTION: NAME,
            "last update": self._last_update,
            "fueltype": self._fueltype.name_lowercase.split('_')[0],
            "trend": f"{self._trend}%",
            "date": self._date
        }

    @property
    def device_info(self) -> dict:
        """I can't remember why this was needed :D"""
        return {
            "identifiers": {(DOMAIN, self.unique_id)},
            "name": self.name,
            "manufacturer": DOMAIN,
        }

    @property
    def unit(self) -> int:
        """Unit"""
        return int

    @property
    def unit_of_measurement(self) -> str:
        """Return the unit of measurement this sensor expresses itself in."""
        return "%"

    @property
    def device_class(self):
        return SensorDeviceClass.MONETARY
        
    @property
    def friendly_name(self) -> str:
        return self.unique_id
           

class ComponentOilPredictionSensor(Entity):
    def __init__(self, data, fueltype: FuelType, quantity):
        self._data = data
        self._fueltype = fueltype
        self._quantity = quantity
        
        
        self._fuelname = None
        self._last_update = None
        self._price = None
        self._trend = None
        self._date = None
        

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._trend

    async def async_update(self):
        await self._data.update()
        self._last_update =  self._data._lastupdate
        
        priceinfo = self._data._price_info.get(self._fueltype)
        
        code = self._fueltype.code
        
        if int(self._quantity) < 2000:
            code += "Inf2000"
        else:
            code += "Sup2000"
        
        table = priceinfo.get("data").get("table")
        # _LOGGER.debug(f"{NAME} code {code} table: {table}")
        
        todayPrice = 0
        tomorrowPrice = 0
        
        for element in table:
            if element.get("code") == code:
                self._fuelname = element.get("name")
                if element.get("data")[1]:
                    todayPrice = element.get("data")[1].get("price")
                if element.get("data")[2]:
                    tomorrowPrice = element.get("data")[2].get("price")
                elif element.get("data")[1]:
                    tomorrowPrice = element.get("data")[1].get("price")
                break
        
        self._price = tomorrowPrice
        
        self._trend = round(100 * ((tomorrowPrice - todayPrice) / todayPrice),3)
        
        self._date = priceinfo.get("data").get("heads")[2].get("name")
        
            
        
    async def async_will_remove_from_hass(self):
        """Clean up after entity before removal."""
        _LOGGER.info("async_will_remove_from_hass " + NAME)
        self._data.clear_session()


    @property
    def icon(self) -> str:
        """Shows the correct icon for container."""
        return "mdi:gas-station"
        
    @property
    def unique_id(self) -> str:
        """Return the name of the sensor."""
        name = f"{NAME} {self._fueltype.name_lowercase.split('_')[0]}"
        if self._quantity != 0:
            name += f" {self._quantity}l"
        name += " prediction"
        return (name)

    @property
    def name(self) -> str:
        return self.unique_id

    @property
    def extra_state_attributes(self) -> dict:
        """Return the state attributes."""
        return {
            ATTR_ATTRIBUTION: NAME,
            "last update": self._last_update,
            "fueltype": self._fueltype.name_lowercase.split('_')[0],
            "fuelname": self._fuelname,
            "price": f"{self._price}€",
            "date": self._date,
            "quantity": self._quantity
        }

    @property
    def device_info(self) -> dict:
        """I can't remember why this was needed :D"""
        return {
            "identifiers": {(DOMAIN, self.unique_id)},
            "name": self.name,
            "manufacturer": DOMAIN,
        }

    @property
    def unit(self) -> int:
        """Unit"""
        return int

    @property
    def unit_of_measurement(self) -> str:
        """Return the unit of measurement this sensor expresses itself in."""
        return "%"

    @property
    def device_class(self):
        return SensorDeviceClass.MONETARY
        
    @property
    def friendly_name(self) -> str:
        return self.unique_id
        