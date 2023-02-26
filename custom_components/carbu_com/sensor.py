import logging
import asyncio
from datetime import date, datetime, timedelta
import calendar

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
from .utils import *

_LOGGER = logging.getLogger(__name__)
_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.0%z"


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required("country", default="BE"): cv.string,
        vol.Required("postalcode"): cv.string,
        vol.Optional("super95", default=True): cv.boolean,
        vol.Optional("diesel", default=True): cv.boolean,
        vol.Optional("oilstd", default=True): cv.boolean,
        vol.Optional("oilextra", default=True): cv.boolean,
        vol.Optional("quantity", default=1000): cv.positive_int,
    }
)

MIN_TIME_BETWEEN_UPDATES = timedelta(hours=1)


async def dry_setup(hass, config_entry, async_add_devices):
    config = config_entry
    country = config.get("country")
    postalcode = config.get("postalcode")
    super95 = config.get("super95")
    diesel = config.get("diesel")
    oilstd = config.get("oilstd")
    oilextra = config.get("oilextra")
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
        sensorSuper95 = ComponentPriceSensor(componentData, "super95", postalcode, False, 0)
        # await sensorSuper95.async_update()
        sensors.append(sensorSuper95)
        
        sensorSuper95Neigh = ComponentPriceNeighbourhoodSensor(componentData, "super95", postalcode, 5)
        # await sensorSuper95Neigh.async_update()
        sensors.append(sensorSuper95Neigh)
        
        sensorSuper95Neigh = ComponentPriceNeighbourhoodSensor(componentData, "super95", postalcode, 10)
        # await sensorSuper95Neigh.async_update()
        sensors.append(sensorSuper95Neigh)
        
        sensorSuper95Prediction = ComponentFuelPredictionSensor(componentData, "super95")
        # await sensorSuper95Prediction.async_update()
        sensors.append(sensorSuper95Prediction)
    
    if diesel:
        sensorDiesel = ComponentPriceSensor(componentData, "diesel", postalcode, False, 0)
        # await sensorDiesel.async_update()
        sensors.append(sensorDiesel)
        
        sensorDieselNeigh = ComponentPriceNeighbourhoodSensor(componentData, "diesel", postalcode, 5)
        # await sensorDieselNeigh.async_update()
        sensors.append(sensorDieselNeigh)
        
        sensorDieselNeigh = ComponentPriceNeighbourhoodSensor(componentData, "diesel", postalcode, 10)
        # await sensorDieselNeigh.async_update()
        sensors.append(sensorDieselNeigh)
        
        sensorDieselPrediction = ComponentFuelPredictionSensor(componentData, "diesel")
        # await sensorDieselPrediction.async_update()
        sensors.append(sensorDieselPrediction)
    
    if oilstd:
        sensorOilstd = ComponentPriceSensor(componentData, "oilstd", postalcode, True, quantity)
        # await sensorOilstd.async_update()
        sensors.append(sensorOilstd)
        
        sensorOilstdPrediction = ComponentOilPredictionSensor(componentData, "oilstd", quantity)
        # await sensorOilstdPrediction.async_update()
        sensors.append(sensorOilstdPrediction)
    
    if oilextra:
        sensorOilextra = ComponentPriceSensor(componentData, "oilextra", postalcode, True, quantity)
        # await sensorOilextra.async_update()
        sensors.append(sensorOilextra)    
        
        sensorOilextraPrediction = ComponentOilPredictionSensor(componentData, "oilextra", quantity)
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
        self._price_info = dict()
        
        self._carbuLocationInfo = None
        self._town = None
        self._city = None
        self._countryname = None
        self._locationid = None
        
        self._super95 = config.get("super95")
        self._super95_fueltypecode = "E10"
        self._super95_fueltype_prediction_code = "E95"
        self._super98 = config.get("super98")
        self._super98_fueltypecode = "SP98"
        self._diesel = config.get("diesel")
        self._diesel_fueltypecode = "GO"
        self._diesel_fueltype_prediction_code = "D"
        self._oilstd = config.get("oilstd")
        self._oilstd_oiltypecode = "7"
        self._oilextra = config.get("oilextra")
        self._oilextra_oiltypecode = "2"
        self._quantity = config.get("quantity")
            
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
        
        
    # same as update, but without throttle to make sure init is always executed
    async def _forced_update(self):
        _LOGGER.info("Fetching init stuff for " + NAME)
        if not(self._session):
            self._session = ComponentSession()

        if self._session:
            self._carbuLocationInfo = await self._hass.async_add_executor_job(lambda: self._session.convertPostalCode(self._postalcode, self._country))
            self._town = self._carbuLocationInfo.get("n")
            self._city = self._carbuLocationInfo.get("pn")
            self._countryname = self._carbuLocationInfo.get("cn")
            self._locationid = self._carbuLocationInfo.get("id")
        # postalcode, country, town, locationid, fueltypecode)
            if self._super95:
                price_info = await self._hass.async_add_executor_job(lambda: self._session.getFuelPrice(self._postalcode, self._country, self._town, self._locationid, self._super95_fueltypecode, False))
                self._price_info["super95"] = price_info
                _LOGGER.debug(f"{NAME} price_info super95 {price_info}")   
                
                prediction_info = await self._hass.async_add_executor_job(lambda: self._session.getFuelPrediction(self._super95_fueltype_prediction_code))
                self._price_info["super95Prediction"] = prediction_info
                _LOGGER.debug(f"{NAME} prediction_info dieselPrediction {prediction_info}")
                
            # if self._super98:
                # price_info = await self._hass.async_add_executor_job(lambda: self._session.getFuelPrice(self._postalcode, self._country, self._town, self._locationid, self._super98_fueltypecode, False))
                # self._price_info["super98"] = price_info
                # _LOGGER.debug(f"{NAME} price_info super98 {price_info}")
                
            if self._diesel:
                price_info = await self._hass.async_add_executor_job(lambda: self._session.getFuelPrice(self._postalcode, self._country, self._town, self._locationid, self._diesel_fueltypecode, False))
                self._price_info["diesel"] = price_info
                _LOGGER.debug(f"{NAME} price_info diesel {price_info}")
                
                prediction_info = await self._hass.async_add_executor_job(lambda: self._session.getFuelPrediction(self._diesel_fueltype_prediction_code))
                self._price_info["dieselPrediction"] = prediction_info
                _LOGGER.debug(f"{NAME} prediction_info dieselPrediction {prediction_info}")
                
            if self._oilstd:
                price_info = await self._hass.async_add_executor_job(lambda: self._session.getOilPrice(self._locationid, self._quantity, self._oilstd_oiltypecode))
                self._price_info["oilstd"] = price_info
                _LOGGER.debug(f"{NAME} price_info oilstd {price_info}")
                
            if self._oilextra:
                price_info = await self._hass.async_add_executor_job(lambda: self._session.getOilPrice(self._locationid, self._quantity, self._oilextra_oiltypecode))
                self._price_info["oilextra"] = price_info
                _LOGGER.debug(f"{NAME} price_info oilextra {price_info}")
                
            if self._oilstd or self._oilextra:
                prediction_info = await self._hass.async_add_executor_job(lambda: self._session.getOilPrediction())
                self._price_info["oilPrediction"] = prediction_info
                _LOGGER.debug(f"{NAME} prediction_info oilPrediction {prediction_info}")
            self._lastupdate = datetime.now()
                
    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def _update(self):
        await self._forced_update()

    async def update(self):
        await self._update()
    
    def clear_session(self):
        self._session : None



class ComponentPriceSensor(Entity):
    def __init__(self, data, fueltype, postalcode, isOil, quantity):
        self._data = data
        self._fueltype = fueltype
        self._postalcode = postalcode
        self._isOil = isOil
        self._quantity = quantity
        
        self._last_update = None
        self._price = None
        self._supplier = None
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
            if self._fueltype == "oilstd":
                oilproductid = self._data._oilstd_oiltypecode
            else:
                oilproductid = self._data._oilextra_oiltypecode
            self._url   = f"https://mazout.com/belgie/offers?areaCode={self._data._locationid}&by=quantity&for={self._quantity}&productId={oilproductid}"
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
            self._price = float(self._priceinfo[0].get("price"))
            self._supplier  = self._priceinfo[0].get("name")
            self._url   = self._priceinfo[0].get("url")
            self._logourl = self._priceinfo[0].get("logo_url")
            self._address = self._priceinfo[0].get("address")
            self._city = self._priceinfo[0].get("locality")
            self._lat = self._priceinfo[0].get("lat")
            self._lon = self._priceinfo[0].get("lon")
            self._fuelname = self._priceinfo[0].get("fuelname")
            self._distance = float(self._priceinfo[0].get("distance"))
            self._date = self._priceinfo[0].get("date")
                       
            
        
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
        name = f"{NAME} {self._fueltype} {self._postalcode}"
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
            "fueltype": self._fueltype,
            "fuelname": self._fuelname,
            "postalcode": self._postalcode,
            "supplier": self._supplier,
            "url": self._url,
            "logourl": self._logourl,
            "address": self._address,
            "city": self._city,
            "lat": self._lat,
            "lon": self._lon,
            "distance": f"{self._distance}km",
            "date": self._date,
            "quantity": self._quantity,
            "score": self._score
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

class ComponentPriceNeighbourhoodSensor(Entity):
    def __init__(self, data, fueltype, postalcode, region):
        self._data = data
        self._fueltype = fueltype
        self._postalcode = postalcode
        self._region = region
        
        self._last_update = None
        self._price = None
        self._priceinfo = None
        self._supplier = None
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

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._price

    async def async_update(self):
        await self._data.update()
        self._last_update =  self._data._lastupdate;
        
        self._price = None
        self._priceinfo = self._data._price_info.get(self._fueltype)
        
        for station in self._priceinfo:
            try:
                currDistance = float(station.get("distance"))
                currPrice = float(station.get("price"))
            except ValueError:
                continue
            if currDistance <= self._region and (self._price == None or currPrice < self._price):
                self._distance = float(station.get("distance"))
                self._price = float(station.get("price"))
                localPrice = float(self._priceinfo[0].get("price"))
                self._diff = round(self._price - localPrice,3)
                self._diff30 = round(self._diff * 30,3)
                self._diffPct = round(100*((self._price - localPrice)/self._price),3)
                self._supplier  = station.get("name")
                self._url   = station.get("url")
                self._logourl = station.get("logo_url")
                self._address = station.get("address")
                self._city = station.get("locality")
                self._lat = station.get("lat")
                self._lon = station.get("lon")
                self._fuelname = station.get("fuelname")
                self._date = station.get("date")
                       
            
        
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
        name = f"{NAME} {self._fueltype} {self._postalcode} {self._region}km"
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
            "fueltype": self._fueltype,
            "fuelname": self._fuelname,
            "postalcode": self._postalcode,
            "supplier": self._supplier,
            "url": self._url,
            "logourl": self._logourl,
            "address": self._address,
            "city": self._city,
            "lat": self._lat,
            "lon": self._lon,
            "region": f"{self._region}km",
            "distance": f"{self._distance}km",
            "price diff": f"{self._diff}€",
            "price diff %": f"{self._diffPct}%",
            "price diff 30l": f"{self._diff30}€",
            "date": self._date,
            "score": self._score
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
        
        
        if self._fueltype == "super95":
            priceinfo = self._data._price_info.get("super95Prediction")
        elif self._fueltype == "diesel":
            priceinfo = self._data._price_info.get("dieselPrediction")
        
        
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
        name = f"{NAME} {self._fueltype} prediction"
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
            "fueltype": self._fueltype,
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
    def __init__(self, data, fueltype, quantity):
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
        
        priceinfo = self._data._price_info.get("oilPrediction")
        
        if self._fueltype == "oilstd":
            code = "mazout50s"
        elif self._fueltype == "oilextra":
            code = "extra"
        
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
        name = f"{NAME} {self._fueltype}"
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
            "fueltype": self._fueltype,
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
        