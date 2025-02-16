import logging
import asyncio
from datetime import date, datetime, timedelta
import calendar
from .utils import *
import random

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity, SensorDeviceClass
from homeassistant.const import ATTR_ATTRIBUTION
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import Entity,DeviceInfo
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
# Global or module-level variable to track existing sensors
existing_sensors = set()

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required("country", default="BE"): cv.string,
        vol.Required("postalcode"): cv.string,
        vol.Optional("town"): cv.string,
        vol.Optional("filter"): cv.string,
        vol.Optional(FuelType.SUPER95.name_lowercase, default=True): cv.boolean,
        vol.Optional(FuelType.SUPER98.name_lowercase, default=True): cv.boolean,
        vol.Optional(FuelType.DIESEL.name_lowercase, default=True): cv.boolean,
        vol.Optional(FuelType.LPG.name_lowercase, default=True): cv.boolean,
        vol.Optional(FuelType.OILSTD.name_lowercase, default=True): cv.boolean,
        vol.Optional(FuelType.OILEXTRA.name_lowercase, default=True): cv.boolean,
        vol.Optional("quantity", default=1000): cv.positive_int,
    }
)

MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=120 + random.uniform(10, 20))
# MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=10)


async def dry_setup(hass, config_entry, async_add_devices):
    config = config_entry
    country = config.get("country")
    postalcode = config.get("postalcode")
    town = config.get("town")
    filter = config.get("filter")
    individualstation = config.get("individualstation", False)
    station = config.get("station","")
    super95 = config.get(FuelType.SUPER95.name_lowercase)
    super95_e5 = config.get(FuelType.SUPER95_E5.name_lowercase)
    super98 = config.get(FuelType.SUPER98.name_lowercase)
    diesel = config.get(FuelType.DIESEL.name_lowercase)
    lpg = config.get(FuelType.LPG.name_lowercase)
    oilstd = config.get(FuelType.OILSTD.name_lowercase)
    oilextra = config.get(FuelType.OILEXTRA.name_lowercase)
    quantity = config.get("quantity")

    check_settings(config, hass)
    sensors = []


    def appendUniqueSensor(sensor):
        _LOGGER.debug(f"checking unique sensor {sensor.unique_id}")
        sensorName = f"sensor.{sensor.unique_id.replace(" ", "_").replace(".", "_").lower()}"
        _LOGGER.debug(f"checking unique sensor {sensor.unique_id} {sensorName}")
        if sensorName not in existing_sensors:
            _LOGGER.debug(f"Adding unique sensor {sensorName}")
            sensors.append(sensor)
            # Add the sensor to the set of existing sensors
            existing_sensors.add(sensorName)
    
    componentData = ComponentData(
        config,
        hass
    )
    await componentData._forced_update()
    assert componentData._price_info is not None


    # _LOGGER.debug(f"postalcode {postalcode} station: {station} individualstation {individualstation}")

    if super95:
        sensorSuper95 = ComponentPriceSensor(componentData, FuelType.SUPER95, postalcode, False, 0, station)
        # await sensorSuper95.async_update()
        sensors.append(sensorSuper95)
        
        if not individualstation:
                sensorSuper95Neigh = ComponentPriceNeighborhoodSensor(componentData, FuelType.SUPER95, postalcode, 5)
                # await sensorSuper95Neigh.async_update()
                sensors.append(sensorSuper95Neigh)
                
                sensorSuper95Neigh = ComponentPriceNeighborhoodSensor(componentData, FuelType.SUPER95, postalcode, 10)
                # await sensorSuper95Neigh.async_update()
                sensors.append(sensorSuper95Neigh)


        if country.lower() in ['be','fr','lu']:
            sensorSuper95Prediction = ComponentFuelPredictionSensor(componentData, FuelType.SUPER95_PREDICTION)
            appendUniqueSensor(sensorSuper95Prediction)
            sensorSuper95Official = ComponentFuelOfficialSensor(componentData, FuelType.SUPER95_OFFICIAL_E10)
            appendUniqueSensor(sensorSuper95Official)

        if country.lower() in ['nl']:
            sensorSuper95Official = ComponentFuelOfficialSensor(componentData, FuelType.SUPER95_OFFICIAL_E10)
            appendUniqueSensor(sensorSuper95Official)

    if super95_e5:
        sensorSuper95_e5 = ComponentPriceSensor(componentData, FuelType.SUPER95_E5, postalcode, False, 0, station)
        # await sensorSuper95.async_update()
        sensors.append(sensorSuper95_e5)
        
        if not individualstation:
                sensorSuper95Neigh = ComponentPriceNeighborhoodSensor(componentData, FuelType.SUPER95_E5, postalcode, 5)
                # await sensorSuper95Neigh.async_update()
                sensors.append(sensorSuper95Neigh)
                
                sensorSuper95Neigh = ComponentPriceNeighborhoodSensor(componentData, FuelType.SUPER95_E5, postalcode, 10)
                # await sensorSuper95Neigh.async_update()
                sensors.append(sensorSuper95Neigh)

        if country.lower() in ['be','fr','lu'] and not(super95):
            sensorSuper95Prediction = ComponentFuelPredictionSensor(componentData, FuelType.SUPER95_PREDICTION)
            appendUniqueSensor(sensorSuper95Prediction)
            sensorSuper95Official = ComponentFuelOfficialSensor(componentData, FuelType.SUPER95_OFFICIAL_E10)
            appendUniqueSensor(sensorSuper95Official)

        if country.lower() in ['nl'] and not(super95):
            sensorSuper95Official = ComponentFuelOfficialSensor(componentData, FuelType.SUPER95_OFFICIAL_E10)
            appendUniqueSensor(sensorSuper95Official)
    
    
    if super98:
        sensorSuper98 = ComponentPriceSensor(componentData, FuelType.SUPER98, postalcode, False, 0, station)
        # await sensorSuper95.async_update()
        sensors.append(sensorSuper98)
        
        if not individualstation:
            sensorSuper98Neigh = ComponentPriceNeighborhoodSensor(componentData, FuelType.SUPER98, postalcode, 5)
            # await sensorSuper95Neigh.async_update()
            sensors.append(sensorSuper98Neigh)
            
            sensorSuper98Neigh = ComponentPriceNeighborhoodSensor(componentData, FuelType.SUPER98, postalcode, 10)
            # await sensorSuper95Neigh.async_update()
            sensors.append(sensorSuper98Neigh)

        if country.lower() in ['be','fr','lu']:
            sensorSuper98OfficialE10 = ComponentFuelOfficialSensor(componentData, FuelType.SUPER98_OFFICIAL_E10)
            appendUniqueSensor(sensorSuper98OfficialE10)
            
            sensorSuper98OfficialE5 = ComponentFuelOfficialSensor(componentData, FuelType.SUPER98_OFFICIAL_E5)
            appendUniqueSensor(sensorSuper98OfficialE5)

        if country.lower() in ['nl']:
            sensorSuper98OfficialE5 = ComponentFuelOfficialSensor(componentData, FuelType.SUPER98_OFFICIAL_E5)
            appendUniqueSensor(sensorSuper98OfficialE5)

    if diesel:
        sensorDiesel = ComponentPriceSensor(componentData, FuelType.DIESEL, postalcode, False, 0, station)
        # await sensorDiesel.async_update()
        sensors.append(sensorDiesel)
        
        if not individualstation:
            sensorDieselNeigh = ComponentPriceNeighborhoodSensor(componentData, FuelType.DIESEL, postalcode, 5)
            # await sensorDieselNeigh.async_update()
            sensors.append(sensorDieselNeigh)
            
            sensorDieselNeigh = ComponentPriceNeighborhoodSensor(componentData, FuelType.DIESEL, postalcode, 10)
            # await sensorDieselNeigh.async_update()
            sensors.append(sensorDieselNeigh)
        
        if country.lower() in ['be','fr','lu']:
            sensorDieselPrediction = ComponentFuelPredictionSensor(componentData, FuelType.DIESEL_Prediction)
            # await sensorDieselPrediction.async_update()
            appendUniqueSensor(sensorDieselPrediction)

            sensorDieselOfficialB10 = ComponentFuelOfficialSensor(componentData, FuelType.DIESEL_OFFICIAL_B10)            
            appendUniqueSensor(sensorDieselOfficialB10)

            sensorDieselOfficialB7 = ComponentFuelOfficialSensor(componentData, FuelType.DIESEL_OFFICIAL_B7)            
            appendUniqueSensor(sensorDieselOfficialB7)

            sensorDieselOfficialXTL = ComponentFuelOfficialSensor(componentData, FuelType.DIESEL_OFFICIAL_XTL)            
            appendUniqueSensor(sensorDieselOfficialXTL)
        
        if country.lower() in ['nl']:
            sensorDieselOfficialB7 = ComponentFuelOfficialSensor(componentData, FuelType.DIESEL_OFFICIAL_B7)
            appendUniqueSensor(sensorDieselOfficialB7)

    if lpg:
        sensorLpg = ComponentPriceSensor(componentData, FuelType.LPG, postalcode, False, 0, station)
        # await sensorDiesel.async_update()
        sensors.append(sensorLpg)
        
        if not individualstation:
            sensorLpgNeigh = ComponentPriceNeighborhoodSensor(componentData, FuelType.LPG, postalcode, 5)
            # await sensorLpgNeigh.async_update()
            sensors.append(sensorLpgNeigh)
            
            sensorLpgNeigh = ComponentPriceNeighborhoodSensor(componentData, FuelType.LPG, postalcode, 10)
            # await sensorLpgNeigh.async_update()
            sensors.append(sensorLpgNeigh)

        
        if country.lower() in ['be','fr','lu']:
            sensorLpgOfficial = ComponentFuelOfficialSensor(componentData, FuelType.LPG_OFFICIAL)
            appendUniqueSensor(sensorLpgOfficial)

        if country.lower() in ['nl']:
            sensorLpgOfficial = ComponentFuelOfficialSensor(componentData, FuelType.LPG_OFFICIAL)
            appendUniqueSensor(sensorLpgOfficial)
        
    if oilstd and country.lower() in ['be','fr','lu']:
        sensorOilstd = ComponentPriceSensor(componentData, FuelType.OILSTD, postalcode, True, quantity)
        # await sensorOilstd.async_update()
        sensors.append(sensorOilstd)
        
        sensorOilstdPrediction = ComponentOilPredictionSensor(componentData, FuelType.OILSTD_PREDICTION, quantity)
        # await sensorOilstdPrediction.async_update()
        appendUniqueSensor(sensorOilstdPrediction)
    
    if oilextra and country.lower() in ['be','fr','lu']:
        sensorOilextra = ComponentPriceSensor(componentData, FuelType.OILEXTRA, postalcode, True, quantity)
        # await sensorOilextra.async_update()
        sensors.append(sensorOilextra)    
        
        sensorOilextraPrediction = ComponentOilPredictionSensor(componentData, FuelType.OILEXTRA_PREDICTION, quantity)
        # await sensorOilextraPrediction.async_update()
        appendUniqueSensor(sensorOilextraPrediction)
    
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
        self._GEO_API_KEY = config.get("GEO_API_KEY")
        self._session = ComponentSession(self._GEO_API_KEY)
        self._lastupdate = None
        self._country = config.get("country")
        self._postalcode = config.get("postalcode")
        self._town = config.get("town")
        self._filter = config.get("filter","")
        self._logo_with_price = config.get("logo_with_price", True)
        self._price_unit = "€" if self._country.lower() != "us" else "$"
        self._price_unit_per = "€/l" if self._country.lower() != "us" else "$/g"

        
        self._friendly_name_price_template = config.get("friendly_name_price_template","")
        self._friendly_name_neighborhood_template = config.get("friendly_name_neighborhood_template","")
        self._friendly_name_prediction_template = config.get("friendly_name_prediction_template","")
        self._friendly_name_official_template = config.get("friendly_name_official_template","")

        
        self._filter_choice = config.get("filter_choice", True)
        self._friendly_name_price_template_choice = config.get("friendly_name_price_template_choice", False)
        self._friendly_name_neighborhood_template_choice = config.get("friendly_name_neighborhood_template_choice", False)
        self._friendly_name_prediction_template_choice = config.get("friendly_name_prediction_template_choice", False)
        self._friendly_name_official_template_choice = config.get("friendly_name_official_template_choice", False)





        self._price_info = dict()
        
        self._carbuLocationInfo = None
        self._city = None
        self._countryname = None
        self._locationinfo = None
        
        self._quantity = config.get("quantity")
        self._super95 = config.get(FuelType.SUPER95.name_lowercase)
        self._super95_e5 = config.get(FuelType.SUPER95_E5.name_lowercase)
        self._super98 = config.get(FuelType.SUPER98.name_lowercase)
        self._diesel = config.get(FuelType.DIESEL.name_lowercase)
        self._lpg = config.get(FuelType.LPG.name_lowercase)
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
        _LOGGER.debug(f"{NAME} getting fuel price_info {fuel_type.name_lowercase} {self._postalcode}, {self._country}, {self._town}, {self._locationinfo}, {fuel_type}") 
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
        try:
            prediction_info = await self._hass.async_add_executor_job(lambda: self._session.getFuelPrediction(fuel_type.code))
            self._price_info[fuel_type] = prediction_info
            _LOGGER.debug(f"{NAME} prediction_info {fuel_type.name_lowercase} Prediction {prediction_info}")
        except Exception as e:
            _LOGGER.error(f"ERROR: prediction failed for {fuel_type.name_lowercase} : {e}")
    
    async def get_fuel_price_official_info(self, fuel_type: FuelType):
        _LOGGER.debug(f"{NAME} getting official price_info {fuel_type.name_lowercase}") 
        try:
            official_info = await self._hass.async_add_executor_job(lambda: self._session.getFuelOfficial(fuel_type, self._country))
            self._price_info[fuel_type] = official_info
            _LOGGER.debug(f"{NAME} official_info {fuel_type.name_lowercase} Official {official_info}")
        except Exception as e:
            _LOGGER.error(f"ERROR: prediction failed for {fuel_type.name_lowercase} : {e}")
    
    async def get_oil_price_prediction_info(self):
        _LOGGER.debug(f"{NAME} getting price_info oil prediction") 
        try:
            prediction_info = await self._hass.async_add_executor_job(lambda: self._session.getOilPrediction())
            self._price_info[FuelType.OILSTD_PREDICTION] = prediction_info
            self._price_info[FuelType.OILEXTRA_PREDICTION] = prediction_info
            _LOGGER.debug(f"{NAME} prediction_info oilPrediction {prediction_info}")
        except Exception as e:
            _LOGGER.error(f"ERROR: prediction failed for oil : {e}")

    async def getStationInfoFromPriceInfo(self, priceinfo, postalcode, fueltype, max_distance, individual_station=""):
        if self._filter_choice:
            stationInfo =  await self._hass.async_add_executor_job(lambda: self._session.getStationInfoFromPriceInfo(priceinfo, postalcode, fueltype, max_distance, self._filter, individual_station))
        else:
            stationInfo =  await self._hass.async_add_executor_job(lambda: self._session.getStationInfoFromPriceInfo(priceinfo, postalcode, fueltype, max_distance, "", individual_station))
        return stationInfo
    
        
    # same as update, but without throttle to make sure init is always executed
    async def _forced_update(self):
        _LOGGER.info("Fetching init stuff for " + NAME)
        if not(self._session):
            self._session = ComponentSession(self._GEO_API_KEY)

        if self._session:
            _LOGGER.debug("Starting with session for " + NAME)
            if self._locationinfo is None and self._country.lower() in ['be','fr','lu']:
                self._carbuLocationInfo = await self._hass.async_add_executor_job(lambda: self._session.convertPostalCode(self._postalcode, self._country, self._town))
                self._town = self._carbuLocationInfo.get("n")
                self._city = self._carbuLocationInfo.get("pn")
                self._countryname = self._carbuLocationInfo.get("cn")
                self._locationinfo = self._carbuLocationInfo.get("id")
            if self._locationinfo is None and self._country.lower() in ['it','nl','es', 'us']:
                boundingboxLocationInfo = await self._hass.async_add_executor_job(lambda: self._session.convertLocationBoundingBox(self._postalcode, self._country, self._town))
                self._locationinfo = boundingboxLocationInfo
            # postalcode, country, town, locationinfo, fueltypecode)
            if self._super95:
                await self.get_fuel_price_info(FuelType.SUPER95)  
                if self._country.lower() in ['be','fr','lu']:
                    await self.get_fuel_price_prediction_info(FuelType.SUPER95_PREDICTION) 
                    await self.get_fuel_price_official_info(FuelType.SUPER95_OFFICIAL_E10)
                if self._country.lower() in ['nl']:
                    await self.get_fuel_price_official_info(FuelType.SUPER95_OFFICIAL_E10)

            if self._super95_e5:
                await self.get_fuel_price_info(FuelType.SUPER95_E5)  
                if self._country.lower() in ['be','fr','lu'] and not self._super95:
                    await self.get_fuel_price_prediction_info(FuelType.SUPER95_PREDICTION) 
                    await self.get_fuel_price_official_info(FuelType.SUPER95_OFFICIAL_E10)
                if self._country.lower() in ['nl'] and not self._super95:
                    await self.get_fuel_price_official_info(FuelType.SUPER95_OFFICIAL_E10)
                
            if self._super98:
                await self.get_fuel_price_info(FuelType.SUPER98)  
                if self._country.lower() in ['be','fr','lu']:
                    await self.get_fuel_price_official_info(FuelType.SUPER98_OFFICIAL_E10)
                    await self.get_fuel_price_official_info(FuelType.SUPER98_OFFICIAL_E5)
                if self._country.lower() in ['nl']:
                    await self.get_fuel_price_official_info(FuelType.SUPER98_OFFICIAL_E5)
                
            if self._diesel:
                await self.get_fuel_price_info(FuelType.DIESEL)  
                if self._country.lower() in ['be','fr','lu']:
                    await self.get_fuel_price_prediction_info(FuelType.DIESEL_Prediction)
                    await self.get_fuel_price_official_info(FuelType.DIESEL_OFFICIAL_B10)
                    await self.get_fuel_price_official_info(FuelType.DIESEL_OFFICIAL_B7)
                    await self.get_fuel_price_official_info(FuelType.DIESEL_OFFICIAL_XTL)
                if self._country.lower() in ['nl']:
                    await self.get_fuel_price_official_info(FuelType.DIESEL_OFFICIAL_B7)
                
            if self._lpg:
                await self.get_fuel_price_info(FuelType.LPG)
                if self._country.lower() in ['be','fr','lu']:
                    await self.get_fuel_price_official_info(FuelType.LPG_OFFICIAL)
                if self._country.lower() in ['nl']:
                    await self.get_fuel_price_official_info(FuelType.LPG_OFFICIAL)
                
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


    @property
    def unique_id(self):
        return f"{NAME} {self._postalcode}"
    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return self.unique_id.title()


class ComponentPriceSensor(Entity):
    def __init__(self, data, fueltype: FuelType, postalcode, isOil, quantity, individual_station = ""):
        self._data = data
        self._fueltype = fueltype
        self._postalcode = postalcode
        self._isOil = isOil
        self._quantity = quantity
        self._individual_station = individual_station
        self._logo_with_price = data._logo_with_price
        self._friendly_name_price_template = self._data._friendly_name_price_template
        self._friendly_name_price_template_choice = self._data._friendly_name_price_template_choice
        
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
        self._price_unit = data._price_unit
        self._price_unit_per = data._price_unit_per
        self._id = None

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._price

    async def async_update(self):
        await self._data.update()
        self._last_update =  self._data._lastupdate;
        
        self._priceinfo = self._data._price_info.get(self._fueltype)
        if self._isOil:
            if len(self._priceinfo.get("data"))>0:
                self._price = float(self._priceinfo.get("data")[0].get("unitPrice"))
                self._supplier  = self._priceinfo.get("data")[0].get("supplier").get("name") #x.data[0].supplier.name
                oilproductid = self._fueltype.code
                try:
                    self._url   = f"https://mazout.com/belgie/offers?areaCode={self._data._locationinfo}&by=quantity&for={self._quantity}&productId={oilproductid}"
                except:
                    self._url   = None
                try:
                    self._logourl = self._priceinfo.get("data")[0].get("supplier").get("media").get("logo").get("src") #x.data[0].supplier.media.logo.src
                except:
                    self._logourl = None
                try:
                    self._score = self._priceinfo.get("data")[0].get("supplier").get("rating").get("score") #x.data[0].supplier.rating.score
                except:
                    self._score = None
                # self._address = 
                # self._city = 
                # self._lat = 
                # self._lon = 
                self._fuelname = self._priceinfo.get("data")[0].get("product").get("name") #x.data[0].product.name
                # self._distance = 
                self._date = self._priceinfo.get("data")[0].get("available").get("visible")# x.data[0].available.visible
                # self._quantity = self._priceinfo.get("data")[0].get("quantity")
            else:
                _LOGGER.debug(f'No data available in priceinfo')
        else:
            # _LOGGER.debug(f'indiv. station: {self._individual_station}')
            stationInfo = await self._data.getStationInfoFromPriceInfo(self._priceinfo, self._postalcode, self._fueltype, 0, self._individual_station)
            # stationInfo = await self._data._hass.async_add_executor_job(lambda: self._data._session.getStationInfoFromPriceInfo(self._priceinfo, self._postalcode, self._fueltype, 0, self._data._filter))
            self._price = stationInfo.get("price") 
            self._supplier  = stationInfo.get("supplier")
            # self._supplier_brand  = stationInfo.get("supplier_brand")
            self._supplier_brand  = stationInfo.get("supplier_brand") if stationInfo.get("supplier_brand") != None and len(stationInfo.get("supplier_brand")) > 1 else f'{stationInfo.get("supplier_brand")}  '
            self._url   = stationInfo.get("url")
            if self._logo_with_price or self._logo_with_price is None:
                self._logourl = f"https://www.prezzibenzina.it/www2/marker.php?brand={self._supplier_brand[:2].upper()}&status=AP&price={stationInfo.get('price')}&certified=0&marker_type=1"
            else:
                self._logourl = stationInfo.get("entity_picture")
            self._address = stationInfo.get("address")
            self._postalcode = stationInfo.get("postalcode")
            self._city = stationInfo.get("city")
            self._lat = stationInfo.get("latitude")
            self._lon = stationInfo.get("longitude")
            self._fuelname = stationInfo.get("fuelname")
            self._distance = stationInfo.get("distance")
            self._date = stationInfo.get("date")
            self._country = stationInfo.get("country")
            self._id = stationInfo.get("id")
            self._score = stationInfo.get("score")
            
        
    async def async_will_remove_from_hass(self):
        """Clean up after entity before removal."""
        _LOGGER.info("async_will_remove_from_hass " + NAME)
        self._data.clear_session()


    @property
    def icon(self) -> str:
        """Shows the correct icon for container."""
        if self._isOil:
            return "mdi:barrel"
        return "mdi:gas-station"
        
    @property
    def unique_id(self) -> str:
        """Return the name of the sensor."""
        name = f"{NAME} {self._fueltype.name_lowercase} {self._postalcode}"
        if self._quantity != 0:
            name += f" {self._quantity}l"
        if self._individual_station != "":
            name += f" {self._individual_station.split(',')[0]}"
        name += " price"
        return (name)

    @property
    def name(self) -> str:
        # return self.unique_id.title()
        if self._friendly_name_price_template_choice:
            return friendly_name_template(self._friendly_name_price_template, self.extra_state_attributes)
        else:
            return self.unique_id.title()

    @property
    def extra_state_attributes(self) -> dict:
        """Return the state attributes."""
        return {
            ATTR_ATTRIBUTION: NAME,
            "last update": self._last_update,
            "fueltype": self._fueltype.name_lowercase.title(),
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
            "country": self._country,
            "id": self._id
            # "suppliers": self._priceinfo
        }


    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        # _LOGGER.debug(f"official device_info: {self._data.name}")
        return DeviceInfo(
            identifiers={
                # Serial numbers are unique identifiers within a specific domain
                (NAME, self._data.unique_id)
            },
            name=f"{NAME} {self._data._postalcode} {self._data._country}",
            model=f"{self._data._postalcode} {self._data._country}",
            manufacturer= NAME
        )
    @property
    def unit(self) -> int:
        """Unit"""
        return int

    @property
    def unit_of_measurement(self) -> str:
        """Return the unit of measurement this sensor expresses itself in."""
        return self._price_unit_per
        
    @property
    def device_class(self):
        return SensorDeviceClass.MONETARY

class ComponentPriceNeighborhoodSensor(Entity):
    def __init__(self, data, fueltype: FuelType, postalcode, max_distance):
        self._data = data
        self._fueltype = fueltype
        self._postalcode = postalcode
        self._max_distance = max_distance
        self._logo_with_price = data._logo_with_price
        self._friendly_name_neighborhood_template = self._data._friendly_name_neighborhood_template
        self._friendly_name_neighborhood_template_choice = self._data._friendly_name_neighborhood_template_choice
        
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
        self._id = None
        self._price_unit = data._price_unit
        self._price_unit_per = data._price_unit_per

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._price

    async def async_update(self):
        await self._data.update()
        self._last_update =  self._data._lastupdate;
        
        self._price = None
        self._priceinfo = self._data._price_info.get(self._fueltype)
        stationInfo = await self._data.getStationInfoFromPriceInfo(self._priceinfo, self._postalcode, self._fueltype, self._max_distance)
        # stationInfo = await self._data._hass.async_add_executor_job(lambda: self._data._session.getStationInfoFromPriceInfo(self._priceinfo, self._postalcode, self._fueltype, 0, self._data._filter))
        # stationInfo = await self._data._hass.async_add_executor_job(lambda: self._data._session.getStationInfoFromPriceInfo(self._priceinfo, self._postalcode, self._fueltype, 0, self._data._filter))
        self._price = stationInfo.get("price") 
        self._diff = stationInfo.get("diff") 
        self._diff30 = stationInfo.get("diff30") 
        self._diffPct = stationInfo.get("diffPct") 
        self._supplier  = stationInfo.get("supplier")
        # self._supplier_brand  = stationInfo.get("supplier_brand")
        self._supplier_brand  = stationInfo.get("supplier_brand") if stationInfo.get("supplier_brand") != None and len(stationInfo.get("supplier_brand")) > 1 else f'{stationInfo.get("supplier_brand")}  '
        self._url   = stationInfo.get("url")
        if self._logo_with_price or self._logo_with_price is None:
            self._logourl = f"https://www.prezzibenzina.it/www2/marker.php?brand={self._supplier_brand[:2].upper()}&status=AP&price={stationInfo.get('price')}&certified=0&marker_type={2 if self._max_distance == 5 else 3}"
        else:
            self._logourl = stationInfo.get("entity_picture")
        self._address = stationInfo.get("address")
        self._postalcode = stationInfo.get("postalcode")
        self._city = stationInfo.get("city")
        self._lat = stationInfo.get("latitude")
        self._lon = stationInfo.get("longitude")
        self._fuelname = stationInfo.get("fuelname")
        self._distance = stationInfo.get("distance")
        self._date = stationInfo.get("date")
        self._country = stationInfo.get("country")
        self._id = stationInfo.get("id")
        self._score = stationInfo.get("score")
        
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
        # return self.unique_id.title()
        if self._friendly_name_neighborhood_template_choice:
            return friendly_name_template(self._friendly_name_neighborhood_template, self.extra_state_attributes)
        else:
            return self.unique_id.title()

    @property
    def extra_state_attributes(self) -> dict:
        """Return the state attributes."""
        return {
            ATTR_ATTRIBUTION: self._supplier_brand,
            "last update": self._last_update,
            "fueltype": self._fueltype.name_lowercase.title(),
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
            "price diff": f"{self._diff}{self._price_unit}",
            "price diff %": f"{self._diffPct}%",
            "price diff 30l": f"{self._diff30}{self._price_unit}",
            "date": self._date,
            "score": self._score,
            "filter": self._data._filter,
            "country": self._country,
            "id": self._id
        }

   
    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        # _LOGGER.debug(f"official device_info: {self._data.name}")
        return DeviceInfo(
            identifiers={
                # Serial numbers are unique identifiers within a specific domain
                (NAME, self._data.unique_id)
            },
            name=f"{NAME} {self._data._postalcode} {self._data._country}",
            model=f"{self._data._postalcode} {self._data._country}",
            manufacturer= NAME
        )

    @property
    def unit(self) -> int:
        """Unit"""
        return int

    @property
    def unit_of_measurement(self) -> str:
        """Return the unit of measurement this sensor expresses itself in."""
        return self._price_unit_per
        
    @property
    def device_class(self):
        return SensorDeviceClass.MONETARY


class ComponentFuelPredictionSensor(Entity):
    def __init__(self, data, fueltype):
        self._data = data
        self._fueltype = fueltype
        self._friendly_name_prediction_template = self._data._friendly_name_prediction_template
        self._friendly_name_prediction_template_choice = self._data._friendly_name_prediction_template_choice
        
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
        
        try:
            priceinfo = self._data._price_info.get(self._fueltype)
        
            
            self._trend = round( priceinfo[0],3)
            
            self._date = priceinfo[1]
        except Exception as e:
            _LOGGER.error(f"ERROR: prediction failed for {self._fueltype.name_lowercase} : {e}")
        
            
        
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
        # return self.unique_id.title()
        if self._friendly_name_prediction_template_choice:
            return friendly_name_template(self._friendly_name_prediction_template, self.extra_state_attributes)
        else:
            return self.unique_id.title()

    @property
    def extra_state_attributes(self) -> dict:
        """Return the state attributes."""
        return {
            ATTR_ATTRIBUTION: NAME,
            "last update": self._last_update,
            "fueltype": self._fueltype.name_lowercase.split('_')[0].title(),
            "trend": f"{self._trend}%",
            "date": self._date
        }

   
    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        # _LOGGER.debug(f"official device_info: {self._data.name}")
        return DeviceInfo(
            identifiers={
                # Serial numbers are unique identifiers within a specific domain
                (NAME, self._data.unique_id)
            },
            name=f"{NAME} {self._data._postalcode} {self._data._country}",
            model=f"{self._data._postalcode} {self._data._country}",
            manufacturer= NAME
        )

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
        

class ComponentOilPredictionSensor(Entity):
    def __init__(self, data, fueltype: FuelType, quantity):
        self._data = data
        self._fueltype = fueltype
        self._quantity = quantity
        self._friendly_name_prediction_template = self._data._friendly_name_prediction_template
        self._friendly_name_prediction_template_choice = self._data._friendly_name_prediction_template_choice
        
        
        self._fuelname = None
        self._last_update = None
        self._price = None
        self._trend = None
        self._date = None
        self._officialPriceToday = None
        self._officialPriceTodayDate = None
        self._price_unit = data._price_unit
        self._price_unit_per = data._price_unit_per
        

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._trend

    async def async_update(self):
        await self._data.update()
        self._last_update =  self._data._lastupdate
        
        try:
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
                if element.get("code").lower() == code.lower():
                    self._fuelname = element.get("name")
                    if element.get("data")[1]:
                        todayPrice = element.get("data")[1].get("price")
                    if element.get("data")[2]:
                        tomorrowPrice = element.get("data")[2].get("price")
                    elif element.get("data")[1]:
                        tomorrowPrice = element.get("data")[1].get("price")
                    break
            
            self._price = tomorrowPrice
            
            if todayPrice != 0:
                self._trend = round(100 * ((tomorrowPrice - todayPrice) / todayPrice),3)
                self._officialPriceToday = todayPrice
            
            if len(priceinfo.get("data").get("heads")) > 1:
                self._date = priceinfo.get("data").get("heads")[2].get("name")
                self._officialPriceTodayDate = priceinfo.get("data").get("heads")[1].get("name")
        except Exception as e:
            _LOGGER.error(f"ERROR: prediction failed for {self._fueltype.name_lowercase} : {e}")
        
            
        
    async def async_will_remove_from_hass(self):
        """Clean up after entity before removal."""
        _LOGGER.info("async_will_remove_from_hass " + NAME)
        self._data.clear_session()


    @property
    def icon(self) -> str:
        """Shows the correct icon for container."""
        return "mdi:barrel"
        
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
        # return self.unique_id.title()
        if self._friendly_name_prediction_template_choice:
            return friendly_name_template(self._friendly_name_prediction_template, self.extra_state_attributes)
        else:
            return self.unique_id.title()

    @property
    def extra_state_attributes(self) -> dict:
        """Return the state attributes."""
        return {
            ATTR_ATTRIBUTION: NAME,
            "last update": self._last_update,
            "fueltype": self._fueltype.name_lowercase.split('_')[0].title(),
            "fuelname": self._fuelname,
            "trend": self._trend,
            "price": f"{self._price}{self._price_unit}",
            "date": self._date,
            "current official max price": f"{self._officialPriceToday} {self._price_unit_per}",
            "current official max price date": {self._officialPriceTodayDate},
            "quantity": self._quantity
        }

   
    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        # _LOGGER.debug(f"official device_info: {self._data.name}")
        return DeviceInfo(
            identifiers={
                # Serial numbers are unique identifiers within a specific domain
                (NAME, self._data.unique_id)
            },
            name=f"{NAME} {self._data._postalcode} {self._data._country}",
            model=f"{self._data._postalcode} {self._data._country}",
            manufacturer= NAME
        )

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
        
        
class ComponentFuelOfficialSensor(Entity):
    def __init__(self, data, fueltype):
        self._data = data
        self._fueltype = fueltype
        self._country = data._country
        
        
        self._fuelname = None
        self._last_update = None
        self._price = None
        self._date = None
        self._priceNext = None
        self._dateNext = None
        self._price_unit = data._price_unit
        self._price_unit_per = data._price_unit_per
        
        self._friendly_name_official_template = self._data._friendly_name_official_template
        self._friendly_name_official_template_choice = self._data._friendly_name_official_template_choice

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._price

    async def async_update(self):
        await self._data.update()
        self._last_update =  self._data._lastupdate
        
        try:
            priceinfo = self._data._price_info.get(self._fueltype)
            # _LOGGER.debug(f"official priceinfo: {priceinfo}")
            
            if self._country.lower() in ['be','fr','lu']:
                self._price= priceinfo.get(self._fueltype.sp_code)
                self._date = priceinfo.get('Brandstof')
                
                self._priceNext= priceinfo.get(self._fueltype.sp_code+"Next")
                self._dateNext = priceinfo.get('BrandstofNext')
            elif self._country.lower() == 'nl':
                self._price= priceinfo.get(self._fueltype.nl_name).get("GLA")
                self._date = priceinfo.get(self._fueltype.nl_name).get("date")
                
                self._priceNext= None
                self._dateNext = None
        except Exception as e:
            _LOGGER.error(f"ERROR: official failed for {self._fueltype.name_lowercase} : {e}")
            
        
            
        
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
        if self._country.lower() in ['nl']:
            name = f"{name} {self._country}"
        # _LOGGER.debug(f"official name: {name}")
        return (name)

    @property
    def name(self) -> str:
        # return self.unique_id.title()
        if self._friendly_name_official_template_choice:
            return friendly_name_template(self._friendly_name_official_template, self.extra_state_attributes)
        else:
            return self.unique_id.title()

    @property
    def extra_state_attributes(self) -> dict:
        """Return the state attributes."""
        return {
            ATTR_ATTRIBUTION: NAME,
            "last update": self._last_update,
            "fueltype": self._fueltype.name_lowercase.replace('_',' ').replace('Official ','').title(),
            "price": f"{self._price}",
            "date": self._date,
            "country": self._country,
            "price next": f"{self._priceNext}",
            "date next": f"{self._dateNext}"
        }

   
    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        # _LOGGER.debug(f"official device_info: {self._data.name}")
        return DeviceInfo(
            identifiers={
                # Serial numbers are unique identifiers within a specific domain
                (NAME, self._data.unique_id)
            },
            name=f"{NAME} {self._data._postalcode} {self._data._country}",
            model=f"{self._data._postalcode} {self._data._country}",
            manufacturer= NAME
        )

    @property
    def unit(self) -> int:
        """Unit"""
        return int

    @property
    def unit_of_measurement(self) -> str:
        """Return the unit of measurement this sensor expresses itself in."""
        return self._price_unit_per

    @property
    def device_class(self):
        return SensorDeviceClass.MONETARY
        
           
def friendly_name_template(template, attributes):
    return template.format(**attributes)
