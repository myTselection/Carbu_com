"""Adds config flow for component."""
import logging
from collections import OrderedDict

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.selector import selector
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
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


def create_schema(entry, option=False):
    """Create a default schema based on if a option or if settings
    is already filled out.
    """

    if option:
        # We use .get here incase some of the texts gets changed.
        default_country = entry.data.get("country", "BE")
        default_postalcode = entry.data.get("postalcode", "")
        default_filter = entry.data.get("filter","")
        default_friendly_name_template = entry.data.get("friendly_name_template","")
        default_super95 = entry.data.get("super95", True)
        default_super98 = entry.data.get("super98", True)
        default_diesel = entry.data.get("diesel", True)
        default_lpg = entry.data.get("lpg", False)
        default_logo_with_price = entry.data.get("default_logo_with_price", True)
    else:
        default_country = "BE"
        default_postalcode = ""
        default_filter = ""
        default_friendly_name_template = ""
        default_super95 = True
        default_super98 = True
        default_diesel = True
        default_lpg = False
        default_logo_with_price = True

    data_schema = OrderedDict()
    data_schema[
        vol.Required("country", default=default_country, description="Country")
    ] = selector({
                "select": {
                    "options": ['BE', 'DE', 'FR', 'IT', 'LU', 'NL','ES'],
                    "mode": "dropdown"
                }
            })
    data_schema[
        vol.Required("postalcode", default=default_postalcode, description="Postal Code")
    ] = str
    data_schema[
        vol.Optional("filter", default=default_filter, description="Fuel supplier brand filter (optional)")
    ] = str
    data_schema[
        vol.Optional(FuelType.SUPER95.name_lowercase, default=default_super95, description="Super 95 sensors")
    ] = bool
    data_schema[
        vol.Optional(FuelType.SUPER98.name_lowercase, default=default_super98, description="Super 98 sensors")
    ] = bool
    data_schema[
        vol.Optional(FuelType.DIESEL.name_lowercase, default=default_diesel, description="Diesel sensors")
    ] = bool
    data_schema[
        vol.Optional(FuelType.LPG.name_lowercase, default=default_lpg, description="LPG sensors")
    ] = bool
    data_schema[
        vol.Optional("logo_with_price", default=default_logo_with_price, description="Logo with price")
    ] = bool

    return data_schema

def create_update_schema(entry, option=False):
    """Create an update schema based on if a option or if settings
    is already filled out.
    """

    if option:
        # We use .get here incase some of the texts gets changed.
        default_filter_choice = entry.data.get("filter_choice", False)
        default_filter = entry.data.get("filter","")
        default_friendly_name_price_template_choice = entry.data.get("friendly_name_price_template_choice", False)
        default_friendly_name_price_template = entry.data.get("friendly_name_price_template","")
        default_friendly_name_neighborhood_template_choice = entry.data.get("friendly_name_neighborhood_template_choice", False)
        default_friendly_name_neighborhood_template = entry.data.get("friendly_name_neighborhood_template","")
        default_friendly_name_prediction_template_choice = entry.data.get("friendly_name_prediction_template_choice", False)
        default_friendly_name_prediction_template = entry.data.get("friendly_name_prediction_template","")
        default_friendly_name_official_template_choice = entry.data.get("friendly_name_official_template_choice", False)
        default_friendly_name_official_template = entry.data.get("friendly_name_official_template","")
        default_logo_with_price = entry.data.get("logo_with_price", True)
    else:
        default_filter = ""
        default_friendly_name_price_template_choice = False
        default_friendly_name_price_template = ""
        default_friendly_name_neighborhood_template_choice = False
        default_friendly_name_neighborhood_template = ""
        default_friendly_name_prediction_template_choice = False
        default_friendly_name_prediction_template = ""
        default_friendly_name_official_template_choice = False
        default_friendly_name_official_template = ""
        default_logo_with_price = True

    data_schema = OrderedDict()
    data_schema[
        vol.Optional("filter_choice", default=default_filter_choice, description="Use filter?")
    ] = bool
    data_schema[
        vol.Optional("filter", default=default_filter, description="Fuel supplier brand filter (optional)")
    ] = str
    data_schema[
        vol.Optional("friendly_name_price_template_choice", default=default_friendly_name_price_template_choice, description="Use price template?")
    ] = bool
    data_schema[
        vol.Optional("friendly_name_price_template", default=default_friendly_name_price_template, description="Friendly name Price template (optional)")
    ] = str
    data_schema[
        vol.Optional("friendly_name_neighborhood_template_choice", default=default_friendly_name_neighborhood_template_choice, description="Use neighborhood template?")
    ] = bool
    data_schema[
        vol.Optional("friendly_name_neighborhood_template", default=default_friendly_name_neighborhood_template, description="Friendly name Neighborhood template (optional)")
    ] = str
    data_schema[
        vol.Optional("friendly_name_prediction_template_choice", default=default_friendly_name_prediction_template_choice, description="Use prediction template?")
    ] = bool
    data_schema[
        vol.Optional("friendly_name_prediction_template", default=default_friendly_name_prediction_template, description="Friendly name Prediction template (optional)")
    ] = str
    data_schema[
        vol.Optional("friendly_name_official_template_choice", default=default_friendly_name_official_template_choice, description="Use official template?")
    ] = bool
    data_schema[
        vol.Optional("friendly_name_official_template", default=default_friendly_name_official_template, description="Friendly name Official template (optional)")
    ] = str
    data_schema[
        vol.Optional("logo_with_price", default=default_logo_with_price, description="Logo with price")
    ] = bool
    
    _LOGGER.debug(f"create_update_schema data_schema: {data_schema}")

    return data_schema

def create_town_carbu_schema(towns):
    """Create a default schema based on if a option or if settings
    is already filled out.
    """
    default_oilstd = True
    default_oilextra = True
    default_quantity = 1000
    data_schema = OrderedDict()
    data_schema[
        vol.Required("town", description="Town")
    ] = selector({
                "select": {
                    "options": [item['n'] for item in towns],
                    "mode": "dropdown"
                }
            })
    data_schema[
        vol.Optional("individualstation", default=False, description="Select an individual gas station")
    ] = bool
    data_schema[
        vol.Optional(FuelType.OILSTD.name_lowercase, default=default_oilstd, description="Standard oil sensors")
    ] = bool
    data_schema[
        vol.Optional(FuelType.OILEXTRA.name_lowercase, default=default_oilextra, description="Extra oil sensors")
    ] = bool
    data_schema[
        vol.Optional("quantity", default=default_quantity, description="Oil quantity in liters (eg 1000)")
    ] = int

    return data_schema


def create_station_carbu_schema(stations):
    """Create a default schema based on if a option or if settings
    is already filled out.
    """
    data_schema = OrderedDict()
    data_schema[
        vol.Required("station", description="Gas station")
    ] = selector({
                "select": {
                    "options": [f"{item['name']}, {item['address']}" for item in stations],
                    "mode": "dropdown"
                }
            })

    return data_schema

def create_town_schema():
    """Create a default schema based on if a option or if settings
    is already filled out.
    """
    data_schema = OrderedDict()

    data_schema[
        vol.Required("town", default="", description="Town")
    ] = str
    data_schema[
        vol.Optional("individualstation", default=False, description="Select an individual gas station")
    ] = bool

    return data_schema


class ComponentFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for component."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL
    _init_info = {}
    _carbuLocationInfo = {}
    _towns = []
    _stations = []
    _session = None

    def __init__(self):
        """Initialize."""
        self._errors = {}

    async def async_step_user(self, user_input=None):  # pylint: disable=dangerous-default-value
        """Handle a flow initialized by the user."""

        if user_input is not None:
            user_input["filter_choice"] = True # init filter choice to True, as a filter can be set but the flag is not visible on the setup form (only on edit)
            self._init_info = user_input
            if not(self._session):
                self._session = ComponentSession()
            if user_input.get('country') in ['BE','FR','LU']:
                self._towns = []
                carbuLocationInfo = await self.hass.async_add_executor_job(lambda: self._session.convertPostalCodeMultiMatch(user_input.get('postalcode'), user_input.get('country')))
                for location in carbuLocationInfo:
                    self._towns.append(location)
                _LOGGER.debug(f"carbuLocationInfo: {carbuLocationInfo} towns {self._towns}")
                return await self.async_step_town_carbu()
            # Other countries: get town
            return await self.async_step_town()
        
        return await self._show_config_form(user_input)

    async def _show_config_form(self, user_input):
        """Show the configuration form to edit location data."""
        data_schema = create_schema(user_input)
        return self.async_show_form(
            step_id="user", data_schema=vol.Schema(data_schema), errors=self._errors
        )
    
    def find_town_by_name(self, target_name):
        for item in self._towns:
            if item.get('n') == target_name:
                return item
        return None  # If the name is not found in the list

    async def async_step_town_carbu(self, user_input=None):  # pylint: disable=dangerous-default-value
        """Handle a flow initialized by the user."""
        if user_input is not None:
            self._init_info.update(user_input)
            # _LOGGER.debug(f"individualstation: {user_input.get('individualstation')}")
            if user_input.get('individualstation') == True:
                town = self.find_town_by_name(user_input.get('town'))
                # self._stations = []
                self._stations = await self.hass.async_add_executor_job(lambda: self._session.getFuelPrices(self._init_info.get('postalcode'), self._init_info.get('country'), self._init_info.get('town'), town.get('id'), FuelType.DIESEL, False))
                # for station in carbuStationInfo:
                    # self._stations.append(station)
                # _LOGGER.debug(f"stations: {self._stations}")
                return await self.async_step_station()
            return self.async_create_entry(title=NAME, data=self._init_info)

        return await self._show_town_carbu_config_form(self._towns)

    async def _show_town_carbu_config_form(self, towns):
        """Show the configuration form to edit location data."""
        data_schema = create_town_carbu_schema(towns)
        return self.async_show_form(
            step_id="town_carbu", data_schema=vol.Schema(data_schema), errors=self._errors
        )

    async def async_step_station(self, user_input=None):  # pylint: disable=dangerous-default-value
        """Handle a flow initialized by the user."""
        if user_input is not None:
            self._init_info.update(user_input)
            return self.async_create_entry(title=NAME, data=self._init_info)

        return await self._show_station_config_form(self._stations)

    async def _show_station_config_form(self, stations):
        """Show the configuration form to edit location data."""
        data_schema = create_station_carbu_schema(stations)
        return self.async_show_form(
            step_id="station", data_schema=vol.Schema(data_schema), errors=self._errors
        )

    async def async_step_town(self, user_input=None):  # pylint: disable=dangerous-default-value
        """Handle a flow initialized by the user."""
        if user_input is not None:
            self._init_info.update(user_input)
            if user_input.get('individualstation') == True:
                boundingboxLocationInfo = None
                if self._init_info.get('country').lower() in ['it','nl','es']:
                    boundingboxLocationInfo = await self.hass.async_add_executor_job(lambda: self._session.convertLocationBoundingBox(self._init_info.get('postalcode'), self._init_info.get('country'), self._init_info.get('town')))
                # self._stations = []
                self._stations  = await self.hass.async_add_executor_job(lambda: self._session.getFuelPrices(self._init_info.get('postalcode'), self._init_info.get('country'), self._init_info.get('town'), boundingboxLocationInfo, FuelType.DIESEL, False))
                # for station in stationInfo:
                    # self._stations.append(station)
                _LOGGER.debug(f"stations: {self._stations}")
                return await self.async_step_station()
            return self.async_create_entry(title=NAME, data=self._init_info)
        return await self._show_town_config_form(self._towns)

    async def _show_town_config_form(self, towns):
        """Show the configuration form to edit location data."""
        data_schema = create_town_schema()
        return self.async_show_form(
            step_id="town", data_schema=vol.Schema(data_schema), errors=self._errors
        )

    async def async_step_import(self, user_input):  # pylint: disable=unused-argument
        """Import a config entry.
        Special type of import, we're not actually going to store any data.
        Instead, we're going to rely on the values that are in config file.
        """
        return self.async_create_entry(title="configuration.yaml", data={})

    # Disabled 'CONFIGURE' edit option, as it would require sensor full re-init
    @callback
    @staticmethod
    def async_get_options_flow(config_entry): 
        """Get the options flow for this handler."""
        return ComponentOptionsHandler(config_entry)


class ComponentOptionsHandler(config_entries.ConfigFlow):
    """Now this class isnt like any normal option handlers.. as ha devs option seems think options is
    #  supposed to be EXTRA options, i disagree, a user should be able to edit anything.."""

    def __init__(self, config_entry):
        self.config_entry = config_entry
        self.options = dict(config_entry.options)
        self._errors = {}

    async def async_step_init(self, user_input=None):
        # _LOGGER.debug(f"{NAME} async_step_init user_input: {user_input}, options: {self.options}, errors: {self._errors},  config_entry: {self.config_entry}")
        return self.async_show_form(
            step_id="edit",
            data_schema=vol.Schema(create_update_schema(self.config_entry, option=True)),
            errors=self._errors,
        )

    async def async_step_edit(self, user_input):

        _LOGGER.debug(f"{NAME} async_step_edit user_input: {user_input}, options: {self.options}, errors: {self._errors},  config_entry: {self.config_entry}")

        if user_input is not None:
            user_input["country"] = self.config_entry.data.get("country", "BE")
            user_input["postalcode"] = self.config_entry.data.get("postalcode", "")
            user_input["super95"] = self.config_entry.data.get("super95", True)
            user_input["super98"] = self.config_entry.data.get("super98", True)
            user_input["diesel"] = self.config_entry.data.get("diesel", True)
            user_input["lpg"] = self.config_entry.data.get("lpg", False)
            user_input["individualstation"] = self.config_entry.data.get("individualstation", False)
            user_input["station"] = self.config_entry.data.get("station", "")
            user_input["town"] = self.config_entry.data.get("town", False)
            user_input[FuelType.OILSTD.name_lowercase] = self.config_entry.data.get(FuelType.OILSTD.name_lowercase, True)
            user_input[FuelType.OILEXTRA.name_lowercase] = self.config_entry.data.get(FuelType.OILEXTRA.name_lowercase, True)
            user_input["quantity"] = self.config_entry.data.get("quantity", 1000)
            
            self.hass.config_entries.async_update_entry(
                self.config_entry, data=user_input
            )
            return self.async_create_entry(title=None, data=None)