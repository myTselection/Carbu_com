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
        default_super95 = entry.data.get("super95", True)
        default_super98 = entry.data.get("super98", True)
        default_diesel = entry.data.get("diesel", True)
        default_oilstd = entry.data.get("oilstd", True)
        default_oilextra = entry.data.get("oilextra", True)
        default_quantity = entry.data.get("quantity", 1000)
    else:
        default_country = "BE"
        default_postalcode = ""
        default_filter = ""
        default_super95 = True
        default_super98 = True
        default_diesel = True
        default_oilstd = True
        default_oilextra = True
        default_quantity = 1000

    data_schema = OrderedDict()
    data_schema[
        vol.Required("country", default=default_country, description="Country")
    ] = selector({
                "select": {
                    "options": ['BE','FR','LU','DE'],
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
        vol.Optional(FuelType.OILSTD.name_lowercase, default=default_oilstd, description="Standard oil sensors")
    ] = bool
    data_schema[
        vol.Optional(FuelType.OILEXTRA.name_lowercase, default=default_oilextra, description="Extra oil sensors")
    ] = bool
    data_schema[
        vol.Optional("quantity", default=default_quantity, description="Oil quantity in liters (eg 1000)")
    ] = int

    return data_schema


def create_town_schema(towns):
    """Create a default schema based on if a option or if settings
    is already filled out.
    """
    data_schema = OrderedDict()

    data_schema["town"] = selector({
                "select": {
                    "options": towns,
                    "mode": "dropdown"
                }
            })

    return data_schema


class ComponentFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for component."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL
    _init_info = {}
    _carbuLocationInfo = {}
    _towns = []
    _session = None

    def __init__(self):
        """Initialize."""
        self._errors = {}

    async def async_step_user(self, user_input=None):  # pylint: disable=dangerous-default-value
        """Handle a flow initialized by the user."""

        if user_input is not None:
            self._init_info = user_input
            if not(self._session):
                self._session = ComponentSession()
            if user_input.get('country') == 'DE':
                return self.async_create_entry(title=NAME, data=self._init_info)
            carbuLocationInfo = await self.hass.async_add_executor_job(lambda: self._session.convertPostalCodeMultiMatch(user_input.get('postalcode'), user_input.get('country')))
            if len(carbuLocationInfo) > 1:
                for location in carbuLocationInfo:
                    self._towns.append(location.get('n'))
                _LOGGER.debug(f"carbuLocationInfo: {carbuLocationInfo} towns {self._towns}")
                return await self.async_step_town()
            elif len(carbuLocationInfo) == 1:
                self._init_info['town'] = carbuLocationInfo[0].get('n')
                return self.async_create_entry(title=NAME, data=self._init_info)
        
        return await self._show_config_form(user_input)

    async def async_step_town(self, user_input=None):  # pylint: disable=dangerous-default-value
        """Handle a flow initialized by the user."""
        if user_input is not None:
            self._init_info.update(user_input)
            return self.async_create_entry(title=NAME, data=self._init_info)

        return await self._show_town_config_form(self._towns)

    async def _show_config_form(self, user_input):
        """Show the configuration form to edit location data."""
        data_schema = create_schema(user_input)
        return self.async_show_form(
            step_id="user", data_schema=vol.Schema(data_schema), errors=self._errors
        )

    async def _show_town_config_form(self, towns):
        """Show the configuration form to edit location data."""
        data_schema = create_town_schema(towns)
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
    # @callback
    # @staticmethod
    # def async_get_options_flow(config_entry): 
    #     """Get the options flow for this handler."""
    #     return ComponentOptionsHandler(config_entry)


class ComponentOptionsHandler(config_entries.ConfigFlow):
    """Now this class isnt like any normal option handlers.. as ha devs option seems think options is
    #  supposed to be EXTRA options, i disagree, a user should be able to edit anything.."""

    def __init__(self, config_entry):
        self.config_entry = config_entry
        self.options = dict(config_entry.options)
        self._errors = {}

    async def async_step_init(self, user_input=None):
        return self.async_show_form(
            step_id="edit",
            data_schema=vol.Schema(create_schema(self.config_entry, option=True)),
            errors=self._errors,
        )

    async def async_step_edit(self, user_input):
        _LOGGER.debug(f"{NAME} async_step_edit user_input: {user_input}")
        if user_input is not None:
            self.hass.config_entries.async_update_entry(
                self.config_entry, data=user_input
            )
            return self.async_create_entry(title="", data={})