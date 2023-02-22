import json
import logging
import pprint
from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import List
import requests
import re
from bs4 import BeautifulSoup

import voluptuous as vol

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
        
    # Country = country code: BE/FR/LU
    def convertPostalCode(self, postalcode, country):
        header = {"Content-Type": "application/x-www-form-urlencoded"}
        # https://carbu.com//commonFunctions/getlocation/controller.getlocation_JSON.php?location=1831&SHRT=1
        # {"id":"FR_24_18_183_1813_18085","area_code":"FR_24_18_183_1813_18085","name":"Dampierre-en-GraÃ§ay","parent_name":"Centre","area_level":"","area_levelName":"","country":"FR","country_name":"France","lat":"47.18111","lng":"1.9425","postcode":"18310","region_name":""},{"id":"FR_24_18_183_1813_18100","area_code":"FR_24_18_183_1813_18100","name":"Genouilly","parent_name":"Centre","area_level":"","area_levelName":"","country":"FR","country_name":"France","lat":"47.19194","lng":"1.88417","postcode":"18310","region_name":""},{"id":"FR_24_18_183_1813_18103","area_code":"FR_24_18_183_1813_18103","name":"GraÃ§ay","parent_name":"Centre","area_level":"","area_levelName":"","country":"FR","country_name":"France","lat":"47.14389","lng":"1.84694","postcode":"18310","region_name":""},{"id":"FR_24_18_183_1813_18167","area_code":"FR_24_18_183_1813_18167","name":"Nohant-en-GraÃ§ay","parent_name":"Centre","area_level":"","area_levelName":"","country":"FR","country_name":"France","lat":"47.13667","lng":"1.89361","postcode":"18310","region_name":""},{"id":"FR_24_18_183_1813_18228","area_code":"FR_24_18_183_1813_18228","name":"Saint-Outrille","parent_name":"Centre","area_level":"","area_levelName":"","country":"FR","country_name":"France","lat":"47.14361","lng":"1.84","postcode":"18310","region_name":""},{"id":"BE_bf_279","area_code":"BE_bf_279","name":"Diegem","parent_name":"Machelen","area_level":"","area_levelName":"","country":"BE","country_name":"Belgique","lat":"50.892365","lng":"4.446127","postcode":"1831","region_name":""},{"id":"LU_lx_3287","area_code":"LU_lx_3287","name":"Luxembourg","parent_name":"Luxembourg","area_level":"","area_levelName":"","country":"LU","country_name":"Luxembourg","lat":"49.610004","lng":"6.129596","postcode":"1831","region_name":""}
        data ={"location":postalcode,"SHRT":1}
        response = self.s.get(f"https://carbu.com//commonFunctions/getlocation/controller.getlocation_JSON.php?location={postalcode}&SHRT=1",headers=header,timeout=10)
        assert response.status_code == 200
        locationinfo = json.loads(response.text)
        _LOGGER.debug(f"location info : {locationinfo}")
        for info_dict in locationinfo:
            _LOGGER.debug(f"loop location info found: {info_dict}")
            if info_dict["c"] == country and info_dict["pc"] == postalcode:
                _LOGGER.info(f"location info found: {info_dict}")
                return info_dict
        return False        
        
    def getFuelPrice(self, postalcode, country, town, locationid, fueltypecode):
        header = {"Content-Type": "application/x-www-form-urlencoded"}
        # https://carbu.com/belgie//liste-stations-service/GO/Diegem/1831/BE_bf_279

        response = self.s.get(f"https://carbu.com/belgie//liste-stations-service/{fueltypecode}/{town}/{postalcode}/{locationid}",headers=header,timeout=10)
        assert response.status_code == 200
        
        
        stationdetails = []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        	# <div class="container list-stations main-title" style="padding-top:15px;">
                # <div class="stations-grid row">
                    # <div class="station-content col-xs-12">
                    # <div class="station-content col-xs-12">
                # <div class="stations-grid row">
                    # <div class="station-content col-xs-12">
        stationgrids = soup.find_all('div', class_='stations-grid')
        # _LOGGER.debug(f"stationgrids: {stationgrids}")
        for div in stationgrids:
            stationcontents = div.find_all('div', class_='station-content')
            for stationcontent in stationcontents:
            
                # <div id="item_21313"
                 # data-lat="50.768739608759"
                 # data-lng="4.2587584325408"
                 # data-id="21313"
                 # data-logo="texaco.gif"
                 # data-name="Texaco Lot"
                 # data-fuelname="Diesel (B7)"
                 # data-price="1.609"
                 # data-distance="5.5299623109514"
                 # data-link="https://carbu.com/belgie/index.php/station/texaco/lot/1651/21313"
                 # data-address="Bergensesteenweg 155<br/>1651 Lot"
                 # class="stationItem panel panel-default">
                
                station_elem = stationcontent.find('div', {'id': lambda x: x and x.startswith('item_')})
                
                stationid = station_elem.get('data-id')
                lat = station_elem.get('data-lat')
                lng = station_elem.get('data-lng')
                logo_url = f"https://carbucomstatic-5141.kxcdn.com//brandLogo/{station_elem.get('data-logo')}"
                url = station_elem.get('data-link')
                name = station_elem.get('data-name')
                fuelname = station_elem.get('data-fuelname')
                address = station_elem.get('data-address').replace('<br/>',', ')
                price = station_elem.get('data-price')
                distance = round(float(station_elem.get('data-distance')),2)
                    
                detail_div = stationcontent.find('a', {'class': 'discreteLink'}).find('span', {'itemprop': 'locality'})
                try:
                    locality = detail_div.text.strip()
                except AttributeError:
                    locality = ""
                    
                try:
                    date = re.search(r'Update-datum:\s+(\d{2}/\d{2}/\d{2})', stationcontent.text).group(1)
                except AttributeError:
                    date = ""
                
                stationdetails.append({"id":stationid,"name":name,"url":url,"logo_url":logo_url,"address":address,"locality":locality,"price":price,"lat":lat,"lon":lng,"fuelname":fuelname,"distance":distance,"date":date})
                
                # _LOGGER.debug(f"stationdetails: {stationdetails}")
        return stationdetails
        
    def getOilPrice(self, locationid, volume, oiltypecode):
        header = {"Content-Type": "application/x-www-form-urlencoded"}
        header = {"Accept-Language": "nl-BE"}
        # https://mazout.com/belgie/offers?areaCode=BE_bf_279&by=quantity&for=2000&productId=7
        # https://mazout.com/config.378173423.json
        # https://api.carbu.com/mazout/v1/offers?api_key=elPb39PWhWJj9K2t73tlxyRL0cxEcTCr0cgceQ8q&areaCode=BE_bf_223&productId=7&quantity=1000&sk=T211ck5hWEtySXFMRTlXRys5KzVydz09

        response = self.s.get(f"https://mazout.com/config.378173423.json",headers=header,timeout=10)
        assert response.status_code == 200
        api_details = response.json()
        api_key = api_details.get("api").get("accessToken").get("val")
        sk = api_details.get("api").get("appId").get("val") #x.api.appId.val
        url = api_details.get("api").get("url")
        namespace = api_details.get("api").get("namespace")
        offers = api_details.get("api").get("routes").get("offers") #x.api.routes.offers
        oildetails_url = f"{url}{namespace}{offers}?api_key={api_key}&sk={sk}&areaCode={locationid}&productId={oiltypecode}&quantity={volume}&locale=nl-BE"
        
        response = self.s.get(oildetails_url,headers=header,timeout=10, verify=False)
        assert response.status_code == 200
        oildetails = response.json()
        
        return oildetails


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