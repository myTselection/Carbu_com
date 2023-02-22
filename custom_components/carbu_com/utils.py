import json
import logging
import pprint
from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import List
import requests
from pydantic import BaseModel

import voluptuous as vol
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)

_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.0%z"

def check_settings(config, hass):
    if not any(config.get(i) for i in ["country"]):
        _LOGGER.error("country was not set")
    else:
        return True
        
    if not config.get("postalcode"):
        _LOGGER.error("postalcode was not set")
    else:
        return True

    raise vol.Invalid("Missing settings to setup the sensor.")


class ComponentSession(object):
    def __init__(self):
        self.s = requests.Session()
        self.s.headers["User-Agent"] = "Python/3"

    def login(self, username, password):
    # https://my.youfone.be/prov/MyYoufone/MyYOufone.Wcf/v2.0/Service.svc/json/login, POST
    # example payload
    # {
      # "request": {
        # "Login": "sdlkfjsldkfj@gmail.com",
        # "Password": "SDFSDFSDFSDFSDF"
      # }
    # }
    # example response: 
    # {"Message":"Authorization succes","ResultCode":0,"Object":{"Customer":{"CustomerNumber":9223283432,"Email":"eslkdjflksd@gmail.com","FirstName":"slfjs","Gender":null,"Id":3434,"Initials":"I","IsBusinessCustomer":false,"Language":"nl","LastName":"DSFSDF","PhoneNumber":"0412345678","Prefix":null,"RoleId":2},"Customers":[{"CustomerId":12345,"CustomerNumber":1234567890,"IsDefaultCustomer":true,"Msisdn":32412345678,"ProvisioningTypeId":1,"RoleId":2}],"CustomersCount":1}}
        # Get OAuth2 state / nonce
        header = {"Content-Type": "application/json"}
        response = self.s.post("https://my.youfone.be/prov/MyYoufone/MyYOufone.Wcf/v2.0/Service.svc/json/login",data='{"request": {"Login": "'+username+'", "Password": "'+password+'"}}',headers=header,timeout=10)
        _LOGGER.debug("youfone.be login post result status code: " + str(response.status_code) + ", response: " + response.text)
        _LOGGER.debug("youfone.be login header: " + str(response.headers))
        assert response.status_code == 200
        self.userdetails = response.json()
        self.msisdn = self.userdetails.get('Object').get('Customers')[0].get('Msisdn')
        self.s.headers["securitykey"] = response.headers.get('securitykey')
        return self.userdetails

    def usage_details(self):
    # https://my.youfone.be/prov/MyYoufone/MyYOufone.Wcf/v2.0/Service.svc/json/GetOverviewMsisdnInfo
    # request.Msisdn - phonenr 
    # {"Message":null,"ResultCode":0,"Object":[{"Properties":[{"Key":"UsedAmount","Value":"0"},{"Key":"BundleDurationWithUnits","Value":"250 MB"},{"Key":"Percentage","Value":"0.00"},{"Key":"_isUnlimited","Value":"0"},{"Key":"_isExtraMbsAvailable","Value":"1"}],"SectionId":1},{"Properties":[{"Key":"UsedAmount","Value":"24"},{"Key":"BundleDurationWithUnits","Value":"200 Min"},{"Key":"Percentage","Value":"12.00"},{"Key":"_isUnlimited","Value":"0"}],"SectionId":2},{"Properties":[{"Key":"StartDate","Value":"1 februari 2023"},{"Key":"NumberOfRemainingDays","Value":"16"}],"SectionId":3},{"Properties":[{"Key":"UsedAmount","Value":"0.00"}],"SectionId":4}]}
        header = {"Content-Type": "application/json"}
        response = self.s.get("https://my.youfone.be/prov/MyYoufone/MyYOufone.Wcf/v2.0/Service.svc/json/GetOverviewMsisdnInfo",data='{"request": {"Msisdn": '+str(self.msisdn)+'}}',headers=header,timeout=10)
        self.s.headers["securitykey"] = response.headers.get('securitykey')
        _LOGGER.debug("youfone.be  result status code: " + str(response.status_code) + ", msisdn" + str(self.msisdn))
        _LOGGER.debug("youfone.be  result " + response.text)
        assert response.status_code == 200
        return response.json()
        
    def subscription_details(self):
        header = {"Content-Type": "application/json"}
        response = self.s.get("https://my.youfone.be/prov/MyYoufone/MyYOufone.Wcf/v2.0/Service.svc/json/GetAbonnementMsisdnInfo",data='{"request": {"Msisdn": '+str(self.msisdn)+'}}',headers=header,timeout=10)
        self.s.headers["securitykey"] = response.headers.get('securitykey')
        _LOGGER.debug("youfone.be  result status code: " + str(response.status_code) + ", msisdn" + str(self.msisdn))
        _LOGGER.debug("youfone.be  result " + response.text)
        assert response.status_code == 200
        jresponse = response.json()
        assert jresponse["ResultCode"] == 0
        obj = {}
        for section in jresponse["Object"]:
            obj[section["SectionId"]] = {}
            for prop in section["Properties"]:
                obj[section["SectionId"]][prop["Key"]] = prop["Value"]
        return obj