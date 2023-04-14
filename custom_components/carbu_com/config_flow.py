"""Adds config flow for component."""
import logging
from collections import OrderedDict

import voluptuous as vol
from homeassistant import config_entries
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
from .utils import (check_settings)

_LOGGER = logging.getLogger(__name__)


def create_schema(entry, option=False):
    """Create a default schema based on if a option or if settings
    is already filled out.
    """

    if option:
        # We use .get here incase some of the texts gets changed.
        default_country = entry.data.get("country", "BE")
        default_postalcode = entry.data.get("postalcode", "")
        default_town = entry.data.get("town","")
        default_super95 = entry.data.get("super95", True)
        default_super98 = entry.data.get("super98", True)
        default_diesel = entry.data.get("diesel", True)
        default_oilstd = entry.data.get("oilstd", True)
        default_oilextra = entry.data.get("oilextra", True)
        default_quantity = entry.data.get("quantity", 1000)
    else:
        default_country = "BE"
        default_postalcode = ""
        default_town = ""
        default_super95 = True
        default_super98 = True
        default_diesel = True
        default_oilstd = True
        default_oilextra = True
        default_quantity = 1000

    data_schema = OrderedDict()
    data_schema[
        vol.Required("country", default=default_country, description="Country")
    ] = str
    data_schema[
        vol.Required("postalcode", default=default_postalcode, description="Postal Code")
    ] = str
    data_schema[
        vol.Optional("town", default=default_town, description="Town (leave empty if postal code is unique)")
    ] = str
    data_schema[
        vol.Optional("super95", default=default_super95, description="Super 95 sensors")
    ] = bool
    data_schema[
        vol.Optional("super98", default=default_super98, description="Super 98 sensors")
    ] = bool
    data_schema[
        vol.Optional("diesel", default=default_diesel, description="Diesel sensors")
    ] = bool
    data_schema[
        vol.Optional("oilstd", default=default_oilstd, description="Standard oil sensors")
    ] = bool
    data_schema[
        vol.Optional("oilextra", default=default_oilextra, description="Extra oil sensors")
    ] = bool
    data_schema[
        vol.Optional("quantity", default=default_quantity, description="Oil quantity in liters (eg 1000)")
    ] = int

    return data_schema


class Validator:
    async def test_setup(self, user_input):
        client = async_get_clientsession(self.hass)

        try:
            check_settings(user_input, self.hass)
        except ValueError:
            self._errors["base"] = "no_valid_settings"
            return False

        # This is what we really need.
        country = None

        if user_input.get("country"):
            country = user_input.get("country")
        else:
            self._errors["base"] = "missing country"
            
            
        postalcode = None

        if user_input.get("postalcode"):
            postalcode = user_input.get("postalcode")
        else:
            self._errors["base"] = "missing postalcode"
            


class ComponentFlowHandler(Validator, config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for component."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self):
        """Initialize."""
        self._errors = {}

    async def async_step_user(self, user_input=None):  # pylint: disable=dangerous-default-value
        """Handle a flow initialized by the user."""

        if user_input is not None:
            await self.test_setup(user_input)
            return self.async_create_entry(title=NAME, data=user_input)

        return await self._show_config_form(user_input)

    async def _show_config_form(self, user_input):
        """Show the configuration form to edit location data."""
        data_schema = create_schema(user_input)
        return self.async_show_form(
            step_id="user", data_schema=vol.Schema(data_schema), errors=self._errors
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


class ComponentOptionsHandler(Validator, config_entries.ConfigFlow):
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
        # edit does not work.
        if user_input is not None:
            ok = await self.test_setup(user_input)
            if ok:
                self.hass.config_entries.async_update_entry(
                    self.config_entry, data=user_input
                )
                return self.async_create_entry(title="", data={})
            else:
                self._errors["base"] = "missing data options handler"
                # not suere this should be config_entry or user_input.
                return self.async_show_form(
                    step_id="edit",
                    data_schema=vol.Schema(
                        create_schema(self.config_entry, option=True)
                    ),
                    errors=self._errors,
                )