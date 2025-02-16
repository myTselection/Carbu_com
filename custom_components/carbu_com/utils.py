import json
import logging
import requests
import uuid
import re
import math
from bs4 import BeautifulSoup
from datetime import date, datetime, timedelta
import urllib.parse
from enum import Enum
from .spain_gas_stations_api import GasStationApi
# from spain_gas_stations_api import GasStationApi
import urllib3
from ratelimit import limits, sleep_and_retry

import voluptuous as vol

# Disable SSL warnings globally
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# logging.basicConfig(level=logging.DEBUG)
_LOGGER = logging.getLogger(__name__)

_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.0%z"
_DATE_FORMAT = "%d/%m/%Y"


def check_settings(config, hass):
    errors_found = False
    if not any(config.get(i) for i in ["country"]):
        _LOGGER.error("country was not set")
        errors_found = True
    
    if not any(config.get(i) for i in ["postalcode"]):
        _LOGGER.error("postalcode was not set")
        errors_found = True

    if errors_found:
        raise vol.Invalid("Missing settings to setup the sensor.")
    else:
        return True
        

class FuelType(Enum):
            # 0: carbu code, 1: de code, 2: it name, 3: nl name, 4: sp code, 5: us code
    SUPER95_E5 = "E10", 7, "benzina", "specbenzine","20", "regular_gas"
    SUPER95 = "E10", 5, "benzina", "euro95","23", "regular_gas"
    SUPER95_PREDICTION = "E95",0
    SUPER95_OFFICIAL_E10 = "super95",0,"","Euro95","Super 95 E10"
    SUPER98 = "SP98", 6, "benzinasp","superplus", "3", "premium_gas"
    SUPER98_OFFICIAL_E5 = "super95/98_E5",0,"","Super","Super 98 E5"
    SUPER98_OFFICIAL_E10 = "super95/98_E10",0,"","","Super 98 E10"
    DIESEL = "GO",3,"diesel","diesel","4", "diesel"
    DIESEL_Prediction = "D",0
    DIESEL_OFFICIAL_B7 = "diesel/b7",0,"","Diesel","Diesel B7"
    DIESEL_OFFICIAL_B10 = "diesel/b10",0,"","","Diesel B10"
    DIESEL_OFFICIAL_XTL = "diesel/xtl",0,"","","Diesel XTL"
    OILSTD = "10",0
    OILSTD_PREDICTION = "mazoutH0H7",0
    OILEXTRA = "2",0
    OILEXTRA_PREDICTION = "extra",0
    LPG = "GPL", 1, "gpl","lpg","17"
    LPG_OFFICIAL = "lpg", 1, "gpl","LPG","LPG"
    
    # https://www.anwb.nl/auto/brandstof/tanken-in-het-buitenland


    @property
    def code(self):
        return self.value[0]
    
    @property
    def de_code(self):
        return self.value[1]
    @property
    def it_name(self):
        return self.value[2]
    @property
    def nl_name(self):
        return self.value[3]
    @property
    def sp_code(self):
        return self.value[4]
    @property
    def us_code(self):
        return self.value[5]

    @property
    def name_lowercase(self):
        return self.name.lower()

class ComponentSession(object):
    def __init__(self, GEO_API_KEY):
        self.s = requests.Session()
        self.s.headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
        self.s.headers["Referer"] = "https://homeassistant.io"
        # self.API_KEY_GEOCODIFY = GEO_API_KEY
        # self.GEOCODIFY_BASE_URL = "https://api.geocodify.com/v2/"
        self.API_KEY_GEOAPIFY = GEO_API_KEY
        self.GEOAPIFY_BASE_URL = "https://api.geoapify.com/v1/geocode"
        
    # Country = country code: BE/FR/LU/DE/IT
    
    @sleep_and_retry
    @limits(calls=1, period=5)
    def convertPostalCode(self, postalcode, country, town = ''):
        # _LOGGER.debug(f"convertPostalCode: postalcode: {postalcode}, country: {country}, town: {town}")
        header = {"Content-Type": "application/x-www-form-urlencoded"}
        # https://carbu.com//commonFunctions/getlocation/controller.getlocation_JSON.php?location=1831&SHRT=1
        # {"id":"FR_24_18_183_1813_18085","area_code":"FR_24_18_183_1813_18085","name":"Dampierre-en-GraÃ§ay","parent_name":"Centre","area_level":"","area_levelName":"","country":"FR","country_name":"France","lat":"47.18111","lng":"1.9425","postcode":"18310","region_name":""},{"id":"FR_24_18_183_1813_18100","area_code":"FR_24_18_183_1813_18100","name":"Genouilly","parent_name":"Centre","area_level":"","area_levelName":"","country":"FR","country_name":"France","lat":"47.19194","lng":"1.88417","postcode":"18310","region_name":""},{"id":"FR_24_18_183_1813_18103","area_code":"FR_24_18_183_1813_18103","name":"GraÃ§ay","parent_name":"Centre","area_level":"","area_levelName":"","country":"FR","country_name":"France","lat":"47.14389","lng":"1.84694","postcode":"18310","region_name":""},{"id":"FR_24_18_183_1813_18167","area_code":"FR_24_18_183_1813_18167","name":"Nohant-en-GraÃ§ay","parent_name":"Centre","area_level":"","area_levelName":"","country":"FR","country_name":"France","lat":"47.13667","lng":"1.89361","postcode":"18310","region_name":""},{"id":"FR_24_18_183_1813_18228","area_code":"FR_24_18_183_1813_18228","name":"Saint-Outrille","parent_name":"Centre","area_level":"","area_levelName":"","country":"FR","country_name":"France","lat":"47.14361","lng":"1.84","postcode":"18310","region_name":""},{"id":"BE_bf_279","area_code":"BE_bf_279","name":"Diegem","parent_name":"Machelen","area_level":"","area_levelName":"","country":"BE","country_name":"Belgique","lat":"50.892365","lng":"4.446127","postcode":"1831","region_name":""},{"id":"LU_lx_3287","area_code":"LU_lx_3287","name":"Luxembourg","parent_name":"Luxembourg","area_level":"","area_levelName":"","country":"LU","country_name":"Luxembourg","lat":"49.610004","lng":"6.129596","postcode":"1831","region_name":""}
        data ={"location":str(postalcode),"SHRT":1}
        response = self.s.get(f"https://carbu.com//commonFunctions/getlocation/controller.getlocation_JSON.php?location={postalcode}&SHRT=1",headers=header,timeout=30)
        if response.status_code != 200:
            _LOGGER.error(f"ERROR: {response.text}")
        assert response.status_code == 200
        locationinfo = json.loads(response.text)
        _LOGGER.debug(f"location info : {locationinfo}")
        for info_dict in locationinfo:
            # _LOGGER.debug(f"loop location info found: {info_dict}")
            if info_dict.get('c') is not None and info_dict.get('pc') is not None:
                if town is not None and town.strip() != '' and info_dict.get("n") is not None:
                    if (info_dict.get("pn",'').lower() == town.lower() or info_dict.get("n",'').lower() == town.lower()) and info_dict.get("c",'').lower() == country.lower() and info_dict.get("pc",'') == str(postalcode):
                        # _LOGGER.debug(f"location info found: {info_dict}, matching town {town}, postal {postalcode} and country {country}")
                        return info_dict
                else:
                    if info_dict.get("c",'').lower() == country.lower() and info_dict.get("pc",'') == str(postalcode):
                        # _LOGGER.debug(f"location info found: {info_dict}, matching postal {postalcode} and country {country}")
                        return info_dict
            else:
                _LOGGER.warning(f"locationinfo missing info to process: {info_dict}")
        _LOGGER.warning(f"locationinfo no match found: {info_dict}")
        return False        
        
    @sleep_and_retry
    @limits(calls=1, period=1)
    def convertPostalCodeMultiMatch(self, postalcode, country, town = ''):
        _LOGGER.debug(f"convertPostalCode: postalcode: {postalcode}, country: {country}, town: {town}")
        header = {"Content-Type": "application/x-www-form-urlencoded"}
        # https://carbu.com//commonFunctions/getlocation/controller.getlocation_JSON.php?location=1831&SHRT=1
        # {"id":"FR_24_18_183_1813_18085","area_code":"FR_24_18_183_1813_18085","name":"Dampierre-en-GraÃ§ay","parent_name":"Centre","area_level":"","area_levelName":"","country":"FR","country_name":"France","lat":"47.18111","lng":"1.9425","postcode":"18310","region_name":""},{"id":"FR_24_18_183_1813_18100","area_code":"FR_24_18_183_1813_18100","name":"Genouilly","parent_name":"Centre","area_level":"","area_levelName":"","country":"FR","country_name":"France","lat":"47.19194","lng":"1.88417","postcode":"18310","region_name":""},{"id":"FR_24_18_183_1813_18103","area_code":"FR_24_18_183_1813_18103","name":"GraÃ§ay","parent_name":"Centre","area_level":"","area_levelName":"","country":"FR","country_name":"France","lat":"47.14389","lng":"1.84694","postcode":"18310","region_name":""},{"id":"FR_24_18_183_1813_18167","area_code":"FR_24_18_183_1813_18167","name":"Nohant-en-GraÃ§ay","parent_name":"Centre","area_level":"","area_levelName":"","country":"FR","country_name":"France","lat":"47.13667","lng":"1.89361","postcode":"18310","region_name":""},{"id":"FR_24_18_183_1813_18228","area_code":"FR_24_18_183_1813_18228","name":"Saint-Outrille","parent_name":"Centre","area_level":"","area_levelName":"","country":"FR","country_name":"France","lat":"47.14361","lng":"1.84","postcode":"18310","region_name":""},{"id":"BE_bf_279","area_code":"BE_bf_279","name":"Diegem","parent_name":"Machelen","area_level":"","area_levelName":"","country":"BE","country_name":"Belgique","lat":"50.892365","lng":"4.446127","postcode":"1831","region_name":""},{"id":"LU_lx_3287","area_code":"LU_lx_3287","name":"Luxembourg","parent_name":"Luxembourg","area_level":"","area_levelName":"","country":"LU","country_name":"Luxembourg","lat":"49.610004","lng":"6.129596","postcode":"1831","region_name":""}
        data ={"location":str(postalcode),"SHRT":1}
        response = self.s.get(f"https://carbu.com//commonFunctions/getlocation/controller.getlocation_JSON.php?location={postalcode}&SHRT=1",headers=header,timeout=30)
        if response.status_code != 200:
            _LOGGER.error(f"ERROR: {response.text}")
        assert response.status_code == 200
        locationinfo = json.loads(response.text)
        _LOGGER.debug(f"location info : {locationinfo}")
        results = []
        for info_dict in locationinfo:
            _LOGGER.debug(f"loop location info found: {info_dict}")
            if info_dict.get('c') is not None and info_dict.get('pc') is not None:
                if town is not None and town.strip() != '' and info_dict.get("n") is not None:
                    if (info_dict.get("pn",'').lower() == town.lower() or info_dict.get("n",'').lower() == town.lower()) and info_dict.get("c",'').lower() == country.lower() and info_dict.get("pc",'') == str(postalcode):
                        _LOGGER.debug(f"location info found: {info_dict}, matching town {town}, postal {postalcode} and country {country}")
                        results.append(info_dict)
                else:
                    if info_dict.get("c",'').lower() == country.lower() and info_dict.get("pc",'') == str(postalcode):
                        _LOGGER.debug(f"location info found: {info_dict}, matching postal {postalcode} and country {country}")
                        results.append(info_dict)
            else:
                _LOGGER.warning(f"locationinfo missing info to process: {info_dict}")
        return results        
        
        
    @sleep_and_retry
    @limits(calls=1, period=1)
    def convertLocationBoundingBox(self, postalcode, country, town):
        country_name = "Italy"
        if country.lower() == 'it':
            country_name = "Italy"
        if country.lower() == 'nl':
            country_name = "Netherlands"
        if country.lower() == 'es':
            country_name = "Spain"
        if country.lower() == 'us':
            country_name = "United States of America"
        orig_location = self.searchGeocode(postalcode, town, country_name)
        _LOGGER.debug(f"searchGeocodeOSM({postalcode}, {town}, {country_name}): {orig_location}")
        if orig_location is None:
            return []
        orig_boundingbox = orig_location.get('boundingbox')
        boundingboxes = {"lat": orig_location.get('lat'), "lon": orig_location.get('lon'), "boundingbox": [orig_boundingbox, [float(orig_boundingbox[0])-0.045, float(orig_boundingbox[1])+0.045, float(orig_boundingbox[2])-0.045, float(orig_boundingbox[3])+0.045], [float(orig_boundingbox[0])-0.09, float(orig_boundingbox[1])+0.09, float(orig_boundingbox[2])-0.09, float(orig_boundingbox[3])+0.09]]}
        return boundingboxes
    
    
    def convertLatLonBoundingBox(self, lat, lon):
        f_lat = float(lat)
        f_lon = float(lon)
        boundingboxes = [[f_lat-0.020, f_lat+0.020,f_lon-0.020, f_lon+0.02], [f_lat-0.045, f_lat+0.045, f_lon-0.045, f_lon+0.045], [f_lat-0.09, f_lat+0.09, f_lon-0.09, f_lon+0.09]]
        return boundingboxes
    

    @sleep_and_retry
    @limits(calls=1, period=1)
    def getFuelPrices(self, postalcode, country, town, locationinfo, fueltype: FuelType, single):
        # _LOGGER.debug(f"getFuelPrices(self, {postalcode}, {country}, {town}, {locationinfo}, {fueltype}: FuelType, {single})")
        self.s = requests.Session()
        self.s.headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        if country.lower() == 'de':
            return self.getFuelPricesDE(postalcode,country,town,locationinfo, fueltype, single)
        if country.lower() == 'it':
            return self.getFuelPricesIT(postalcode,country,town,locationinfo, fueltype, single)
        if country.lower() == 'nl':
            return self.getFuelPricesNL(postalcode,country,town,locationinfo, fueltype, single)
        if country.lower() == 'at':
            return self.getFuelPricesAT(postalcode,country,town,locationinfo, fueltype, single)
        if country.lower() == 'es':
            return self.getFuelPricesSP(postalcode,country,town,locationinfo, fueltype, single)
        if country.lower() == 'us':
            return self.getFuelPricesUS(postalcode,country,town,locationinfo, fueltype, single)
        if country.lower() not in ['be','fr','lu']:
            _LOGGER.info(f"Not supported country: {country}")
            return []
        
        #CARU.COM BE / FR / LU:
        header = {"Content-Type": "application/x-www-form-urlencoded"}
        # https://carbu.com/belgie//liste-stations-service/GO/Diegem/1831/BE_bf_279

        response = self.s.get(f"https://carbu.com/belgie//liste-stations-service/{fueltype.code}/{town}/{postalcode}/{locationinfo}",headers=header,timeout=10)
        if response.status_code != 200:
            _LOGGER.error(f"ERROR: {response.text}")
        assert response.status_code == 200

        _LOGGER.info(f"New carbu prices retrieved")
        
        
        stationdetails = []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        	# <div class="container list-stations main-title" style="padding-top:15px;">
                # <div class="stations-grid row">
                    # <div class="station-content col-xs-12">
                    # <div class="station-content col-xs-12">
                # <div class="stations-grid row">
                    # <div class="station-content col-xs-12">
        stationgrids = soup.find_all('div', class_='stations-grid')
        _LOGGER.debug(f"stationgrids: {len(stationgrids)}, postalcode: {postalcode}, stationgrids")
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
                # logo_url = "https://carbucomstatic-5141.kxcdn.com//brandLogo/326_Capture%20d%E2%80%99%C3%A9cran%202021-09-27%20%C3%A0%2011.11.24.png"
                # logo_url = "https://carbucomstatic-5141.kxcdn.com/brandLogo/"+ station_elem.get('data-logo').replace('’','%E2%80%99')
                # logo_url = r"https://carbucomstatic-5141.kxcdn.com/brandLogo/"+ station_elem.get('data-logo').replace("’", "\\’")
                # logo_url = r"https://carbucomstatic-5141.kxcdn.com/brandLogo/"+ urllib.parse.quote(station_elem.get('data-logo'))
                logo_url = "https://carbucomstatic-5141.kxcdn.com/brandLogo/"+ station_elem.get('data-logo')
                url = station_elem.get('data-link')
                brand = url.split("https://carbu.com/belgie/index.php/station/")[1]
                brand = brand.split("/")[0].title()
                if brand.lower() == "tinq":
                    # no url encoding worked correctl for this specific case, so hard coded for now
                    logo_url = "https://carbucomstatic-5141.kxcdn.com//brandLogo/326_Capture%20d%E2%80%99%C3%A9cran%202021-09-27%20%C3%A0%2011.11.24.png"
                # else:
                #     _LOGGER.debug(f"Tinq brand not found: {brand}")
                name = station_elem.get('data-name')
                fuelname = station_elem.get('data-fuelname')
                # address = station_elem.get('data-address').replace('<br/>',', ')
                address = station_elem.get('data-address')
                address = address.split('<br/>')
                address_postalcode = address[1].split(" ")[0]
                # _LOGGER.debug(f"address {address}, postalcode: {postalcode}")
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
                
                stationdetail = {"id":stationid,"name":name,"url":url,"logo_url":logo_url,"brand":brand,"address":', '.join(el for el in address),"postalcode": address_postalcode, "locality":locality,"price":price,"lat":lat,"lon":lng,"fuelname":fuelname,"distance":distance,"date":date, "country": country}
                if price != None and price != "":
                    stationdetails.append(stationdetail)
                
                # _LOGGER.debug(f"stationdetails: {stationdetails}")
                if single:
                    break
            if single:
                break
        return stationdetails
    
    
    @sleep_and_retry
    @limits(calls=1, period=1)
    def getFuelPricesDE(self, postalcode, country, town, locationinfo, fueltype: FuelType, single):
        if country.lower() != 'de':
            return self.getFuelPrices(postalcode,country,town,locationinfo, fueltype, single)
        header = {"Content-Type": "application/x-www-form-urlencoded"}
        # https://www.clever-tanken.de/tankstelle_liste?lat=&lon=&ort=Kr%C3%BCn&spritsorte=3&r=5
        # _LOGGER.debug(f"https://www.clever-tanken.de/tankstelle_liste?lat=&lon=&ort={postalcode}&spritsorte={fueltype.de_code}&r=25&sort=km")

        response = self.s.get(f"https://www.clever-tanken.de/tankstelle_liste?lat=&lon=&ort={postalcode}&spritsorte={fueltype.de_code}&r=25&sort=km",headers=header,timeout=50)
        if response.status_code != 200:
            _LOGGER.error(f"ERROR: {response.text}")
        assert response.status_code == 200

        stationdetails = []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        blocks = soup.find_all('a', href=lambda href: href and href.startswith('/tankstelle_details/'))
        # _LOGGER.debug(f"blocks: {len(blocks)}")

        stationdetails = []
        for block in blocks:
            url = block['href']
            station_id = url.split('/')[-1]
            try:
                station_name = block.find('span', class_='fuel-station-location-name').text.strip()
            except:
                station_name = "Unknown"
            try:
                station_street = block.find('div', class_='fuel-station-location-street').text.strip()
            except:
                station_street = "Unknown"
            try:
                station_city = block.find('div', class_='fuel-station-location-city').text.strip()
            except:
                station_city = "Unknown"
            try:
                station_postalcode, station_locality = station_city.split(maxsplit=1)
            except:
                station_postalcode = "Unknown"
            
            price_text = block.find('div', class_='price-text')
            if price_text != None:
                price_text = price_text.text.strip()

            try:
                price_changed = [span.text.strip() for span in block.find_all('span', class_='price-changed')]
            except:
                price_changed = None

            try:
                logo_url = block.find('img', class_='mtsk-logo')['src']
            except:
                logo_url = ""

            try:
                distance = float(block.find('div', class_='fuel-station-location-distance').text.strip().replace(' km',''))
            except:
                distance = 10
            today = date.today()
            current_date = today.strftime("%Y-%m-%d")
            # _LOGGER.debug(f"blocks id : {station_id}, postalcode: {station_postalcode}")


            block_data = {
                'id': station_id,
                'name': station_name,
                'url': f"https://www.clever-tanken.de{url}",
                'logo_url': f"https://www.clever-tanken.de/{logo_url}",
                'brand': station_name,
                'address': f"{station_street}, {station_city}",
                'postalcode': station_postalcode,
                'locality': station_locality,
                'price': price_text,
                'price_changed': price_changed,
                'lat': 0,
                'lon': 0,
                'fuelname': fueltype.name,
                'distance': distance,
                'date': price_changed[0] if price_changed else current_date, 
                'country': country
            }
            if price_text:
                if single:
                    if postalcode == station_postalcode:
                        stationdetails.append(block_data)
                        return stationdetails
                else:
                    stationdetails.append(block_data)
        return stationdetails
    
    
    @sleep_and_retry
    @limits(calls=1, period=1)
    def getFuelPricesAT(self, postalcode, country, town, locationinfo, fueltype: FuelType, single):
        if country.lower() != 'at':
            return self.getFuelPrices(postalcode,country,town,locationinfo, fueltype, single)
        header = {"Content-Type": "application/x-www-form-urlencoded"}
        # https://www.spritpreisrechner.at/#/fossil
        return

    
    
    @sleep_and_retry
    @limits(calls=1, period=1)
    def getFuelPricesNL(self, postalcode, country, town, locationinfo, fueltype: FuelType, single):
        if country.lower() != 'nl':
            return self.getFuelPrices(postalcode,country,town,locationinfo, fueltype, single)
        header = {"Content-Type": "application/x-www-form-urlencoded"}
        # https://www.brandstof-zoeker.nl/
        # https://www.brandstof-zoeker.nl/ajax/stations/?pageType=geo%2FpostalCode&type=diesel&latitude=51.9487915&longitude=5.8837565&radius=0.008
        
        all_stations = []
        radius = 0.008
        for boundingbox in locationinfo.get('boundingbox'):
            #TODO check if needs to be retrieved 3 times 0, 5 & 10km or radius can be set to 0.09 to get all at once
            # _LOGGER.debug(f"Retrieving brandstof-zoeker data: https://www.brandstof-zoeker.nl/ajax/stations/?pageType=geo%2FpostalCode&type={fueltype.nl_name}&latitude={locationinfo.get('lat')}&longitude={locationinfo.get('lon')}&radius={radius}")
            nl_url = f"https://www.brandstof-zoeker.nl/ajax/stations/?pageType=geo%2FpostalCode&type={fueltype.nl_name}&latitude={locationinfo.get('lat')}&longitude={locationinfo.get('lon')}&radius={radius}"
            # _LOGGER.debug(f"NL URL: {nl_url}")
            response = self.s.get(nl_url,headers=header,timeout=50)
            if response.status_code != 200:
                _LOGGER.error(f"ERROR: NL URL: {nl_url}, {response.text}")
            assert response.status_code == 200
            radius = radius + 0.045

            nl_prices = response.json()
            all_stations.extend(nl_prices)

        # _LOGGER.debug(f"NL All station data retrieved: {all_stations}")

        stationdetails = []
        for block in all_stations:
            if block.get('fuelPrice') is None:
                continue
            block_data = {
                'id': block.get('id'),
                'name': block.get('station').get('naam'),
                'url': f"https://www.brandstof-zoeker.nl/station/{block.get('station').get('url')}",
                'brand':block.get('station').get('chain'),
                'address': block.get('station').get('adres'),
                'postalcode': f"{block.get('station').get('postcode')}".replace(" ",""),
                'locality': block.get('station').get('plaats'),
                'price': block.get('fuelPrice').get('prijs'),
                'price_changed': block.get('fuelPrice').get('datum'),
                'lat': block.get('station').get('latitude'),
                'lon': block.get('station').get('longitude'),
                'fuelname': fueltype.name,
                'distance': block.get('distance'),
                'date': block.get('fuelPrice').get('datum'), 
                'country': country
            }
            if single:
                if postalcode.lower() == block.get('station').get('postcode').lower().replace(" ",""):
                    stationdetails.append(block_data)
                    return stationdetails
            else:
                stationdetails.append(block_data)
        return stationdetails
    
    
    @sleep_and_retry
    @limits(calls=1, period=1)
    def getFuelPricesIT(self, postalcode, country, town, locationinfo, fueltype: FuelType, single):
        if country.lower() != 'it':
            return self.getFuelPrices(postalcode,country,town,locationinfo, fueltype, single)
        header = {"Content-Type": "application/x-www-form-urlencoded"}

        # https://www.prezzibenzina.it/downloads/dos_log.txt
        #get stations on lat lon: https://api3.prezzibenzina.it/?do=pb_get_prices&output=json&os=android&appname=AndroidFuel&sdk=33&platform=SM-S906B&udid=dlwHryfCRXy-zJWX6mMN22&appversion=3.22.08.14&loc_perm=foreground&network=mobile&limit=5000&offset=1&min_lat=45.56&max_lat=46&min_long=8.82&max_long=9.26
        #get station details prices https://api3.prezzibenzina.it/?do=pb_get_stations&output=json&appname=PrezziBenzinaWidget&ids=21249,20078,5922,28629,5914&prices=on&minprice=1&fuels=d&apiversion=3.1

        if len(locationinfo) < 3:
            return []
        
        all_stations = dict()
        curr_dist = 0
        for boundingbox in locationinfo.get('boundingbox'):
            response = self.s.get(f"https://api3.prezzibenzina.it/?do=pb_get_prices&output=json&os=android&appname=AndroidFuel&sdk=33&platform=SM-S906B&udid=dlwHryfCRXy-zJWX6mMN22&appversion=3.22.08.14&loc_perm=foreground&network=mobile&limit=5000&offset=1&min_lat={boundingbox[0]}&max_lat={boundingbox[2]}&min_long={boundingbox[1]}&max_long={boundingbox[3]}",headers=header,timeout=50)
            if response.status_code != 200:
                _LOGGER.error(f"ERROR: {response.text}")
            assert response.status_code == 200

            pb_get_prices = response.json()
            pb_get_prices = pb_get_prices.get('pb_get_prices')
            pb_get_prices_price = pb_get_prices.get('prices').get('price')

            # Filter the list to keep only items containing "diesel" in the "fuel" value
            fuel_type_items = [item for item in pb_get_prices_price if fueltype.it_name in item["fuel"].lower() and item["service"] == "SS"]

            # Sort the filtered list by the "price" key in ascending order
            sorted_fuel_type_items = sorted(fuel_type_items, key=lambda x: float(x["price"]))

            # Extract all the station IDs into a list
            sorted_fuel_type_items_dict = {item.get('station'): item for item in sorted_fuel_type_items}
            if len(sorted_fuel_type_items_dict) == 0:
                continue

            # station_ids = [item["station"] for item in sorted_diesel_items]
            comma_separated_station_ids = ",".join(sorted_fuel_type_items_dict.keys())
            url = f"https://api3.prezzibenzina.it/?do=pb_get_stations&output=json&appname=PrezziBenzinaWidget&ids={comma_separated_station_ids}&prices=on&minprice=1&fuels=d&apiversion=3.1"
            _LOGGER.debug(f"url: {url}")
            response = self.s.get(url,headers=header,timeout=50)
            if response.status_code != 200:
                _LOGGER.error(f"ERROR: {response.text}")
            assert response.status_code == 200

            stationdetails_prezzibenzina = response.json()
            stationdetails_prezzibenzina = stationdetails_prezzibenzina.get('pb_get_stations')
            stationdetails_prezzibenzina_stations = stationdetails_prezzibenzina.get("stations").get("station")
            for station_details in stationdetails_prezzibenzina_stations:
                station_details['price'] = (sorted_fuel_type_items_dict.get(station_details.get('id'))).get('price')
                station_details['date'] = (sorted_fuel_type_items_dict.get(station_details.get('id'))).get('date')
            all_stations[str(curr_dist)] = stationdetails_prezzibenzina_stations
            curr_dist = curr_dist + 5


        stationdetails = []
        for curr_dist, d_stations in all_stations.items():
            for block in d_stations:
                # Filter the list to keep only items containing "diesel" in the "fuel" value
                if len(block.get('reports').get('report')) == 0:
                    continue
                fuel_price_items = [item for item in block.get('reports').get('report') if fueltype.it_name in item["fuel"].lower()]
                if len(fuel_price_items) == 0:
                    fuel_price = block.get('price')
                    fuel_price_date = block.get('date')
                    if fuel_price is None:
                        continue
                else:
                    fuel_price = fuel_price_items[0].get('price')
                    fuel_price_date = fuel_price_items[0].get('date')
                block_data = {
                    'id': block.get('id'),
                    'name': block.get('name'),
                    'url': block.get('url'),
                    'logo_url': f"https://www.prezzibenzina.it/www2/marker.php?brand={block.get('co')}&status=AP&price={fuel_price}&certified=0&marker_type=1",
                    'brand': block.get('co_name'),
                    'address': block.get('address'),
                    'postalcode': block.get('zip'),
                    'locality': block.get('city_name'),
                    'price': fuel_price,
                    'price_changed': fuel_price_date,
                    'lat': block.get('lat'),
                    'lon': block.get('lng'),
                    'fuelname': fueltype.name,
                    'distance': curr_dist,
                    'date': block.get('last_updated'), 
                    'country': country
                }
                if single:
                    if postalcode == block.get('zip'):
                        stationdetails.append(block_data)
                        return stationdetails
                else:
                    stationdetails.append(block_data)
        return stationdetails
    
    
    
    @sleep_and_retry
    @limits(calls=1, period=1)
    def getFuelPricesSP(self, postalcode, country, town, locationinfo, fueltype: FuelType, single):
        if country.lower() != 'es':
            return self.getFuelPrices(postalcode,country,town,locationinfo, fueltype, single)


        if len(locationinfo) < 3:
            return []
        
        all_stations = dict()
        curr_dist = 0


        # boundingboxes = {"lat": "lat", 
        #                  "lon": "lon", 
        #                  "boundingbox": [["lat","lon"], ["lat", "lon", "lat", "lon"], ["lat", "lon", "lat", "lon"]]}
        
        knownProvinces = GasStationApi.get_provinces()
        boundingBoxReversed = self.reverseGeocode(locationinfo.get('lon'), locationinfo.get('lat'))

        # requiredProv = boundingBoxReversed[3].get('state', None).lower()
        requiredProv = boundingBoxReversed.get('region').lower()

        #_LOGGER.debug(f"requiredProv: {requiredProv}")

        
        prov_id = next(filter(lambda p: p.name.lower() in requiredProv, knownProvinces), None).id
        #_LOGGER.debug(f"prov_id: {prov_id}")


        sp_stations = GasStationApi.get_gas_stations_provincia(prov_id, fueltype.sp_code)
        # Sort the list first by "price" and then by "distance"
        self.add_station_distance(sp_stations.get('ListaEESSPrecio'), 'Latitud', 'Longitud (WGS84)', float(str(locationinfo.get('lat')).replace(',','.')), float(str(locationinfo.get('lon')).replace(',','.')))
        #_LOGGER.debug(f"sp_stations: {sp_stations}")
        sorted_stations = sorted(sp_stations.get('ListaEESSPrecio'), key=lambda x: (x['distance'], x['PrecioProducto']))
        # sorted_stations =  sp_stations.get('ListaEESSPrecio').sort(key=lambda item: (
        #     item['Localidad'] != town,  # Sort by postal code (current postal code first)
        #     item['distance'],  # Sort by distance
        #     item['PrecioProducto']  # Sort by price
        # ))


        stationdetails = []
        for block in sorted_stations:
            # url = block['href']
            station_id = block.get('C.P.')
            station_name = block.get('Rótulo')
            station_street = block.get('Dirección')
            station_city = block.get('Provincia')
            station_postalcode = block.get('IDMunicipio')
            station_locality = block.get('Localidad')
            price_text = float(block.get('PrecioProducto').replace(',','.'))
            distance = block.get('distance')
            date = sp_stations.get('Fecha')
            lat = block.get('Latitud')
            lon = block.get('Longitud (WGS84)')


            block_data = {
                'id': station_id,
                'name': station_name,
                # 'url': f"https://www.clever-tanken.de{url}",
                # 'logo_url': f"https://www.clever-tanken.de/{logo_url}",
                'brand': station_name,
                'address': f"{station_street}, {station_city}",
                'postalcode': station_postalcode,
                'locality': station_locality,
                'price': price_text,
                # 'price_changed': price_changed,
                'lat': lat,
                'lon': lon,
                'fuelname': fueltype.name,
                'distance': distance,
                'date': date, 
                'country': country
            }
            stationdetails.append(block_data)
            if single:
                if postalcode == station_postalcode:
                    return stationdetails
        return stationdetails

    @sleep_and_retry
    @limits(calls=1, period=1)
    def getFuelPricesUS(self, postalcode, country, town, locationinfo, fueltype: FuelType, single):
        if country.lower() != 'us':
            return self.getFuelPrices(postalcode,country,town,locationinfo, fueltype, single)


        if len(locationinfo) < 3:
            return []
        
        all_stations = dict()
        curr_dist = 0


        # boundingboxes = {"lat": "<lat>", 
        #                  "lon": "<lon>", 
        #                  "boundingbox": [["<lat>","<lon>"], ["<lat>", "<lon>", "<lat>", "<lon>"], ["<lat>", "<lon>", "<lat>", "<lon>"]]}
        
        boundingBoxReversed = self.reverseGeocode(locationinfo.get('lon'), locationinfo.get('lat'))

        # requiredState = boundingBoxReversed[3].get('state', None).lower()
        requiredState = boundingBoxReversed.get("region").lower()


        _LOGGER.debug(f"requiredProv: {requiredState}")

        
        AUTHID = str(uuid.uuid4())
        COUNTRY = "US"
        DISTANCEFMT = "km"
        LIMIT = "500"
        LAT = locationinfo.get('lat')
        LONG = locationinfo.get('lon')
        STATE = requiredState
        CONST_GASBUDDY_STATIONS_FMT = f"https://services.gasbuddy.com/mobile-orchestration/stations?authid={AUTHID}&country={COUNTRY}&distance_format={DISTANCEFMT}&limit={LIMIT}&region={STATE}&lat={LAT}&lng={LONG}"
        CONST_GASBUDDY_GET_STATION_FMT = "https://services.gasbuddy.com/mobile-orchestration/stations/{STATIONID}?authid={AUTHID}"

        
        ANDROID_USER_AGENT = "Dalvik/2.1.0 (Linux; U; Android 13; Pixel 4 XL Build/TQ3A.230705.001.B4)"
        
        GASBUDDY_HEADERS = {
            "apikey": "56c57e8f1132465d817d6a753c59387e",
            "User-Agent": ANDROID_USER_AGENT
        }

        response = self.s.get(url=CONST_GASBUDDY_STATIONS_FMT, headers=GASBUDDY_HEADERS)
        stations = response.json().get('stations')
        self.add_station_distance(stations, "info.latitude", "info.longitude", float(str(locationinfo.get('lat')).replace(',','.')), float(str(locationinfo.get('lon')).replace(',','.')))
        
        _LOGGER.debug(f"stations: {stations}")

        
        # sorted_stations = sorted(stations, key=lambda x: (x['distance'], x['price']))
        # sorted_stations =  stations.sort(key=lambda item: (
        #     item.get('info').get('address').get('postal_code') != postalcode,  # Sort by postal code (current postal code first)
        #     item['distance'],  # Sort by distance
        #     item.get('fuel_products').get('credit').get('price')  # Sort by price
        # ))



        # Sort stations based on postal code, price for the predefined fuel type, and distance
        # sorted_stations = sorted(stations, key=lambda x: (x['info']['address']['postal_code']!= postalcode, 
        #                                                 next((product['credit']['price'] for product in x['fuel_products'] if product['fuel_product'] == fueltype.us_code), float('inf')), 
        #                                                 x['distance']))
        sorted_stations = sorted(stations, key=lambda x: (next((product['credit']['price'] for product in x['fuel_products'] if product['fuel_product'] == fueltype.us_code), float('inf')), 
                                                        x['distance']))

        stationdetails = []
        for block in sorted_stations:
            # Find the fuel product matching the predefined fuel type
            matching_fuel_product = next((product for product in block["fuel_products"] if product["fuel_product"] == fueltype.us_code), None)
            _LOGGER.debug(f"matching_fuel_product: {matching_fuel_product}")
            # Check if matching fuel product is found
            if matching_fuel_product:
                # Get the price for the predefined fuel type
                try:
                    price_text = float(str(matching_fuel_product.get("credit", {}).get("price",0)).replace(',','.'))
                
                    # url = block['href']
                    station_id = block.get('id')
                    station_name = block.get('info').get('name')
                    alias_name = block.get('info').get('alias')
                    brand_name = block.get('info').get('brand_name')
                    station_street = block.get('info').get('address').get('line_1')
                    station_city = block.get('info').get('address').get('locality')
                    station_postalcode = block.get('info').get('address').get('postal_code')
                    station_locality = block.get('info').get('address').get('WA')
                    distance = block.get('distance')
                    date = matching_fuel_product.get("credit", {}).get("posted_time")
                    lat = block.get('info').get('latitude')
                    lon = block.get('info').get('longitude')
                    score = block.get('info').get('star_rating')
                except Exception as e:
                    _LOGGER.error(f"ERROR: geocode : {e}")



                block_data = {
                    'id': station_id,
                    'name': f"{alias_name} {station_name}" if alias_name else station_name,
                    # 'url': f"https://www.clever-tanken.de{url}",
                    # 'logo_url': f"https://www.clever-tanken.de/{logo_url}",
                    'brand': brand_name,
                    'city': station_city,
                    'address': f"{station_street}, {station_city}",
                    'postalcode': station_postalcode,
                    'locality': station_locality,
                    'price': price_text,
                    # 'price_changed': price_changed,
                    'lat': lat,
                    'score': score,
                    'lon': lon,
                    'fuelname': fueltype.name,
                    'distance': distance,
                    'date': date, 
                    'country': country
                }
                if price_text and price_text > 0:
                    stationdetails.append(block_data)
                    if single:
                        if postalcode == station_postalcode:
                            return stationdetails
        return stationdetails
     

    @sleep_and_retry
    @limits(calls=1, period=1)
    def getFuelPrediction(self, fueltype_prediction_code):
        header = {"Content-Type": "application/x-www-form-urlencoded"}
        # Super 95: https://carbu.com/belgie//index.php/voorspellingen?p=M&C=E95
        # Diesel: https://carbu.com/belgie//index.php/voorspellingen?p=M&C=D
        _LOGGER.debug(f"https://carbu.com/belgie//index.php/voorspellingen?p=M&C={fueltype_prediction_code}")

        response = self.s.get(f"https://carbu.com/belgie//index.php/voorspellingen?p=M&C={fueltype_prediction_code}",headers=header,timeout=30)
        if response.status_code != 200:
            _LOGGER.error(f"ERROR: {response.text}")
        assert response.status_code == 200
        
        last_category = None
        last_data = None
        soup = BeautifulSoup(response.text, 'html.parser')
        # Find the Highchart series data
        highchart_series = soup.find_all('script')
        value = 0
        try:
            for series in highchart_series:
                # _LOGGER.debug(f"chart loop: {series.text}")
                if "chart'" in series.text:
                    # Extract the categories and data points
                    categories = series.text.split('categories: [')[1].split(']')[0].strip()
                    categories = categories.replace("'", '"').rstrip(',')
                    # _LOGGER.debug(f"categories found: {categories}")
                    categories = f"[{categories}]"
                    categories = json.loads(categories, strict=False)
                    # _LOGGER.debug(f"categories found: {categories.index('+1')}")
                    
                    categoriesIndex = categories.index('+1')
                    
                    dataseries = "[" + series.text.split('series: [')[1].split('});')[0].strip().rstrip(',')
                    dataseries = dataseries.replace("'", '"').rstrip(',')
                    dataseries = dataseries.replace("series:", '"series":').replace("name:", '"name":').replace("type :", '"type":').replace("color:", '"color":').replace("data:", '"data":').replace("dashStyle:", '"dashStyle":').replace("step:", '"step":').replace(", ]","]").replace('null','"null"').replace("]],","]]")
                    # dataseries = re.sub(r'([a-zA-Z0-9_]+):', r'"\1":', dataseries)
                    dataseries = dataseries[:-1] + ',{"test":"test"}]'
                    # _LOGGER.debug(f"series found: {dataseries}")
                    dataseries = json.loads(dataseries, strict=False)
                    # _LOGGER.debug(f"series found: {dataseries}")

                    value = 0
                    for elem in dataseries:
                        if elem.get("name") == "Maximum prijs  (Voorspellingen)":
                            # _LOGGER.debug(f"+4 found: {elem.get('data')[categoriesIndex +4]}")
                            # _LOGGER.debug(f"-1 found: {elem.get('data')[categoriesIndex -1]}")
                            value = 100 * (elem.get('data')[categoriesIndex +4] - elem.get('data')[categoriesIndex -1]) / elem.get('data')[categoriesIndex -1]
                    
                    # _LOGGER.debug(f"value: {value}")  
        except:
            _LOGGER.error(f"Carbu_com Prediction code {fueltype_prediction_code} could not be retrieved")
            return [value, datetime.now()]
        
        predictiondate = categories[categoriesIndex-1]
        # Convert the string to a datetime object
        # _LOGGER.debug(f"Carbu_com predictiondate {predictiondate}")
        predictiondate = datetime.strptime(predictiondate, _DATE_FORMAT)
        # Add 5 days
        predictiondate = predictiondate + timedelta(days=5)
        return [value,predictiondate.strftime(_DATE_FORMAT)]
        
    @sleep_and_retry
    @limits(calls=1, period=1)
    def getFuelOfficial(self, fueltype: FuelType, country):
        if country.lower() == 'nl':
            return self.getFuelOfficialNl(fueltype, country)
        fueltype_prediction_code = fueltype.code
        header = {"Content-Type": "application/x-www-form-urlencoded"}

        # Super 95: https://carbu.com/belgie/super95
        # Diesel: https://carbu.com/belgie/diesel
        # Diesel: https://carbu.com/belgie/lpg
        _LOGGER.debug(f"https://carbu.com/belgie/{fueltype_prediction_code}")

        response = self.s.get(f"https://carbu.com/belgie/{fueltype_prediction_code}",headers=header,timeout=30)
        if response.status_code != 200:
            _LOGGER.error(f"ERROR: {response.text}")
        assert response.status_code == 200
        
        soup = BeautifulSoup(response.text, 'html.parser')
        official_price_information = soup.find('section', {'id': 'news', 'class': 'bg-news'})

        # Define a function to convert HTML table to JSON
        def table_to_json(table):
            data = {}
            rows = table.find_all('tr')
            for row in rows:
                cols = row.find_all(['th', 'td'])
                cols = [col.text.strip().replace('(','').replace(')','').replace(' â‚¬/l','').replace(' €/l','').replace('= ','').replace('Vandaag','').replace(',','.') for col in cols]
                if len(cols) > 0:
                    name = cols[0]
                    data[name] = cols[1]
                    if len(cols) > 2:
                        data[name+"Next"] = cols[2]
            return data

        # Extract data from the HTML structure
        # section_data = {
        #     # 'id': soup.select_one('#news')['id'],
        #     # 'class': soup.select_one('#news')['class'],
        #     # 'heading': soup.select_one('#news h1').text.strip(),
        #     'table': table_to_json(soup.select_one('.prix-officiel')),
        #     # 'source': soup.select_one('.text-muted').text.strip(),
        # }
        html_table = official_price_information.select_one('.prix-officiel')
        result = {}
        if html_table is not None:
            result = table_to_json(html_table)

        return result
    
    
    @sleep_and_retry
    @limits(calls=1, period=1)
    def getFuelOfficialNl(self, fueltype: FuelType, country):
        if country.lower() != 'nl':
            return self.getFuelOfficial(fueltype, country)
        fueltype_prediction_code = fueltype.nl_name
        header = {"Content-Type": "application/x-www-form-urlencoded"}
        # https://www.unitedconsumers.com/tanken/brandstofprijzen
        

        response = self.s.get(f"https://www.unitedconsumers.com/tanken/brandstofprijzen",headers=header,timeout=30)
        if response.status_code != 200:
            _LOGGER.error(f"ERROR: {response.text}")
        assert response.status_code == 200
        
        soup = BeautifulSoup(response.text, 'html.parser')

        date_text = None
        for paragraph in soup.find_all('div', class_='_tableFooter_14l7y_20'):
            if paragraph.text.strip().startswith("Datum overzicht"):
                date_text = paragraph.text.replace("Datum overzicht ", "").strip()
                date_text = date_text.split("*")[0]
                break


        # Mapping of Dutch month names to English month names
        month_translation = {
            "januari": "January",
            "februari": "February",
            "maart": "March",
            "april": "April",
            "mei": "May",
            "juni": "June",
            "juli": "July",
            "augustus": "August",
            "september": "September",
            "oktober": "October",
            "november": "November",
            "december": "December"
        }

        def translate_month(dutch_date_str):
            spaceSplit = dutch_date_str.lower().split(" ")
            return f"{spaceSplit[0]} {month_translation.get(spaceSplit[1], spaceSplit[1])} {spaceSplit[2]}"
        
        # Convert the date text to a datetime.date object if found
        date_object = date.today()
        if date_text:
            try:
                # Translate Dutch month to English
                translated_date_text = translate_month(date_text)
                # Define the expected date format
                date_object = datetime.strptime(translated_date_text, "%d %B %Y").date()
            except ValueError:
                # Handle cases where the date format is unexpected or incorrect
                date_object = date.today()

        # Assuming 'soup' is the BeautifulSoup object containing your HTML
        data = {}

        # Find all rows
        rows = soup.find_all('div', class_='_row_14l7y_25')

        # Loop through each row to extract data
        for row in rows:
            # fuel_type = row.find('a').text.strip()
            # gla_value = row.find_all('span', class_='_root_1d6z8_1')[0].text.strip()
            # # Remove the Euro sign and convert the GLA value to a float
            # gla_value = float(gla_value.replace('€', '').replace(',', '.').strip())
            # verschil_value = row.find_all('span', class_='_root_vw1r2_1')[0].next_sibling.strip()

            try:
                fuel_type = row.find('a').text.strip()
            except AttributeError:
                fuel_type = None

            try:
                gla_value_str = row.find_all('span', class_='_root_1d6z8_1')[0].text.strip()
                gla_value = float(gla_value_str.replace('€', '').replace(',', '.').strip())
            except (IndexError, AttributeError, ValueError):
                gla_value = None

            try:
                verschil_value = row.find_all('span', class_='_root_vw1r2_1')[0].next_sibling.strip()
            except (IndexError, AttributeError):
                verschil_value = None

            # Append the extracted data to the list
            data[fuel_type] = {
                'fuel_type': fuel_type,
                'GLA': gla_value,
                'Verschil': verschil_value,
                'date': date_object
            }
        return data
    

    @sleep_and_retry
    @limits(calls=1, period=1)
    def getOilPrice(self, locationinfo, volume, oiltypecode):
        header = {"Content-Type": "application/x-www-form-urlencoded"}
        header = {"Accept-Language": "nl-BE"}
        # https://mazout.com/belgie/offers?areaCode=BE_bf_279&by=quantity&for=2000&productId=7
        # https://mazout.com/config.378173423.json
        # https://api.carbu.com/mazout/v1/offers?api_key=elPb39PWhWJj9K2t73tlxyRL0cxEcTCr0cgceQ8q&areaCode=BE_bf_223&productId=7&quantity=1000&sk=T211ck5hWEtySXFMRTlXRys5KzVydz09

        response = self.s.get(f"https://mazout.com/config.204135307.json",headers=header,timeout=30)
        if response.status_code != 200:
            _LOGGER.error(f"ERROR: {response.text}")
        assert response.status_code == 200
        api_details = response.json()
        api_key = api_details.get("api").get("accessToken").get("val")
        sk = api_details.get("api").get("appId").get("val") #x.api.appId.val
        url = api_details.get("api").get("url")
        namespace = api_details.get("api").get("namespace")
        offers = api_details.get("api").get("routes").get("offers") #x.api.routes.offers
        oildetails_url = f"{url}{namespace}{offers}?api_key={api_key}&sk={sk}&areaCode={locationinfo}&productId={oiltypecode}&quantity={volume}&locale=nl-BE"
        _LOGGER.debug(f"oildetails_url: {oildetails_url}")
        
        response = self.s.get(oildetails_url,headers=header,timeout=30, verify=False)
        if response.status_code != 200:
            _LOGGER.error(f"ERROR: {response.text}")
        assert response.status_code == 200
        oildetails = response.json()
        
        return oildetails
        
    @sleep_and_retry
    @limits(calls=1, period=1)
    def getOilPrediction(self):
        header = {"Content-Type": "application/x-www-form-urlencoded"}
        header = {"Accept-Language": "nl-BE"}
        # https://mazout.com/belgie/offers?areaCode=BE_bf_279&by=quantity&for=2000&productId=7
        # https://mazout.com/config.378173423.json
        # https://api.carbu.com/mazout/v1/price-summary?api_key=elPb39PWhWJj9K2t73tlxyRL0cxEcTCr0cgceQ8q&sk=T211ck5hWEtySXFMRTlXRys5KzVydz09

        response = self.s.get(f"https://mazout.com/config.204135307.json",headers=header,timeout=30)
        if response.status_code != 200:
            _LOGGER.error(f"ERROR: {response.text}")
        assert response.status_code == 200
        api_details = response.json()
        api_key = api_details.get("api").get("accessToken").get("val")
        sk = api_details.get("api").get("appId").get("val") #x.api.appId.val
        url = api_details.get("api").get("url")
        namespace = api_details.get("api").get("namespace")
        oildetails_url = f"{url}{namespace}/price-summary?api_key={api_key}&sk={sk}"
        
        response = self.s.get(oildetails_url,headers=header,timeout=30, verify=False)
        if response.status_code != 200:
            _LOGGER.error(f"ERROR: {response.text}")
        assert response.status_code == 200
        oildetails = response.json()
        
        return oildetails


    @sleep_and_retry
    @limits(calls=10, period=5)
    def getStationInfo(self, postalcode, country, fuel_type: FuelType, town="", max_distance=0, filter="", townConfirmed = False):
        locationinfo = None
        single = True if max_distance == 0 else False
        if country.lower() in ["be","fr","lu"]:
            if townConfirmed:
                carbuLocationInfo = self.convertPostalCodeMultiMatch(postalcode, country, town)[0]
            else:
                carbuLocationInfo = self.convertPostalCode(postalcode, country)
            if not carbuLocationInfo:
                raise Exception(f"Location not found country: {country}, postalcode: {postalcode}, town: {town}")
            _LOGGER.debug(f"getStationInfo carbuLocationInfo: {carbuLocationInfo}")
            town = carbuLocationInfo.get("n")
            city = carbuLocationInfo.get("pn")
            countryname = carbuLocationInfo.get("cn")
            locationinfo = carbuLocationInfo.get("id")
            _LOGGER.debug(f"convertPostalCode postalcode: {postalcode}, town: {town}, city: {city}, countryname: {countryname}, locationinfo: {locationinfo}")
        if country.lower() in ["it","nl","es"]:
            boundingBoxLocationInfo = self.convertLocationBoundingBox(postalcode, country, town)
            locationinfo = boundingBoxLocationInfo

        price_info = self.getFuelPrices(postalcode, country, town, locationinfo, fuel_type, single)
        # _LOGGER.debug(f"price_info {fuel_type.name} {price_info}")
        return self.getStationInfoFromPriceInfo(price_info, postalcode, fuel_type, max_distance, filter)
    
    

    @sleep_and_retry
    @limits(calls=1, period=1)
    def getStationInfoLatLon(self,latitude, longitude, fuel_type: FuelType, max_distance=0, filter=""):
        postal_code_country = self.reverseGeocode(longitude, latitude)
        town = None
        locationinfo = None
        if postal_code_country.get('country_code').lower() in ["be","fr","lu"]:        
            carbuLocationInfo = self.convertPostalCode(postal_code_country.get('postal_code'), postal_code_country.get('country_code'))
            if not carbuLocationInfo:
                raise Exception(f"Location not found country: {postal_code_country.get('country_code')}, postalcode: {postal_code_country.get('postal_code')}")
            town = carbuLocationInfo.get("n")
            city = carbuLocationInfo.get("pn")
            countryname = carbuLocationInfo.get("cn")
            locationinfo = carbuLocationInfo.get("id")
            _LOGGER.debug(f"convertPostalCode postalcode: {postal_code_country.get('postal_code')}, town: {town}, city: {city}, countryname: {countryname}, locationinfo: {locationinfo}")
        if postal_code_country.get('country_code').lower() in ["it","nl","es"]: 
            #TODO calc boudingboxes for known lat lon
            town = postal_code_country.get('town')
            itLocationInfo = self.convertLocationBoundingBox(postal_code_country.get('postal_code'), postal_code_country.get('country_code'), town)
            locationinfo = itLocationInfo
        price_info = self.getFuelPrices(postal_code_country.get('postal_code'), postal_code_country.get('country_code'), town, locationinfo, fuel_type, False)
        # _LOGGER.debug(f"price_info {fuel_type.name} {price_info}")
        return self.getStationInfoFromPriceInfo(price_info, postal_code_country.get('postal_code'), fuel_type, max_distance, filter)
        

    def getStationInfoFromPriceInfo(self,price_info, postalcode, fuel_type: FuelType, max_distance=0, filter="", individual_station=""):
        # _LOGGER.debug(f"getStationInfoFromPriceInfo(self,{price_info}, {postalcode}, {fuel_type}: FuelType, {max_distance}=0, {filter}='', {individual_station}='')")
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
            "postalcode" : None,
            "postalcodes" : [postalcode],
            "city" : None,
            "latitude" : None,
            "longitude" : None,
            "fuelname" : None,
            "fueltype" : fuel_type,
            "date" : None,
            "country": None,
            "id": None
        }
        # _LOGGER.debug(f"getStationInfoFromPriceInfo {fuel_type.name}, postalcode: {postalcode}, max_distance : {max_distance}, filter: {filter}, price_info: {price_info}")

        if price_info is None or len(price_info) == 0:
            return data
        
        filterSet = False
        if filter is not None and filter.strip() != "":
            filterSet = filter.strip().lower()



        for station in price_info:
            # _LOGGER.debug(f"getStationInfoFromPriceInfo station: {station} , {filterSet}, {individual_station}")
            if filterSet:
                match = re.search(filterSet, station.get("brand").lower())
                if not match:
                    continue
            if individual_station != "":
                # _LOGGER.debug(f"utils individual_station {individual_station}: {station.get('name')}, {station.get('address')}")
                if f"{station.get('name')}, {station.get('address')}" != individual_station:
                    # _LOGGER.debug(f"No match found for individual station, checking next")
                    continue
                
            # if max_distance == 0 and str(postalcode) not in station.get("address"):
            #     break
            try:
                currDistance = float(station.get("distance"))
                currPrice = float(station.get("price"))
            except ValueError:
                continue
            _LOGGER.debug(f"getStationInfoFromPriceInfo maxDistance: {max_distance}, currDistance: {currDistance}, postalcode: {station.get("postalcode")}, currPrice: {currPrice} new price: {data.get("price")}")
            
            data_recently_updated = True
            if station.get("date") is not None:
                try:
                    station_date = datetime.strptime(station.get("date"), "%d/%m/%y") #assuming the date is in the format dd/mm/yy
                    six_months_ago = datetime.now() - timedelta(days=180)  # 180 days = 6 months
                    if station_date >= six_months_ago:
                        data_recently_updated = True
                    else:
                        # The date is older than 6 months
                        data_recently_updated = False
                except:
                    _LOGGER.debug(f"date validation not possible since non matching date notation: {station.get("date")}")
            if station.get('country').lower() == 'it' and max_distance == 0:
                # IT results are not sorted by price, so don't expect the first to be the best match for local price
                max_distance = 0.1
            # _LOGGER.debug(f'if (({max_distance} == 0 and ({currDistance} <= 5 or {postalcode} == {station.get("postalcode")})) or {currDistance} <= {max_distance}) and ({data.get("price")} is None or {currPrice} < {float(data.get("price"))})')
            if ((max_distance == 0  and (currDistance <= 5 or postalcode == station.get("postalcode"))) or currDistance <= max_distance) and data_recently_updated and (data.get("price") is None or currPrice < float(data.get("price"))):
                data["distance"] = float(station.get("distance"))
                data["price"] = 0 if station.get("price") == '' else float(station.get("price"))
                data["localPrice"] = 0 if price_info[0].get("price") == '' else float(price_info[0].get("price"))
                data["diff"] = round(data["price"] - data["localPrice"],3)
                data["diff30"] = round(data["diff"] * 30,3)
                data["diffPct"] = 0 if data["price"] == 0 else round(100*((data["price"] - data["localPrice"])/data["price"]),3)
                data["supplier"]  = station.get("name")
                data["supplier_brand"]  = station.get("brand")
                data["url"]   = station.get("url")
                data["entity_picture"] = station.get("logo_url")
                data["address"] = station.get("address")
                data["postalcode"] = station.get("postalcode")
                data["city"] = station.get("locality")
                data["latitude"] = station.get("lat")
                data["longitude"] = station.get("lon")
                data["fuelname"] = station.get("fuelname")
                data["date"] = station.get("date")
                if data["postalcode"] not in data["postalcodes"]:
                    data["postalcodes"].append(data["postalcode"])
                data['country'] = station.get('country')
                data['id'] = station.get('id')
                # _LOGGER.debug(f"before break {max_distance}, country: {station.get('country') }, postalcode: {station.get('postalcode')} required postalcode {postalcode}")
                if max_distance == 0:
                        #if max distance is 0, we expect the first result to be the cheapest and no need to loop over the rest
                        # _LOGGER.debug(f"break {max_distance}, country: {station.get('country') }, postalcode: {station.get('postalcode')} required postalcode {postalcode}")
                        break
            # else:
                # _LOGGER.debug(f'no match found: if (({max_distance} == 0 and ({currDistance} <= 5 or {postalcode} == {station.get("postalcode")})) or {currDistance} <= {max_distance}) and ({data.get("price")} is None or {currPrice} < {float(data.get("price"))})')
        if data["supplier"] is None and filterSet:
            _LOGGER.warning(f"{postalcode} the station filter '{filter}' may result in no results found, if needed, please review filter")
        
        _LOGGER.debug(f"get_lowest_fuel_price info found: {data}")
        return data
        
    # NOT USED
    def geocodeHere(self, country, postalcode, here_api_key):
        header = {"Content-Type": "application/x-www-form-urlencoded"}
        # header = {"Accept-Language": "nl-BE"}
        country_fullname = ""
        if country == "BE":
            country_fullname = "Belgium"
        elif country == "FR":
            country_fullname = "France"
        elif country == "LU":
            country_fullname = "Luxembourg"
        else:
            raise Exception(f"Country {country} not supported, only BE/FR/LU is currently supported")
        
        response = self.s.get(f"https://geocode.search.hereapi.com/v1/geocode?q={postalcode}+{country_fullname}&apiKey={here_api_key}",headers=header,timeout=30)
        if response.status_code != 200:
            _LOGGER.error(f"ERROR: {response.text}")
        assert response.status_code == 200
        location = response.json()["items"][0]["position"]
        return location
    
    # NOT USED
    def getPriceOnRouteORS(self, country, fuel_type: FuelType, from_postalcode, to_postalcode, ors_api_key, filter = ""):
        from_location = self.geocodeORS(country, from_postalcode, ors_api_key)
        assert from_location is not None
        to_location = self.geocodeORS(country, to_postalcode, ors_api_key)
        assert to_location is not None
        route = self.getOrsRoute(from_location, to_location, ors_api_key)
        assert route is not None
        _LOGGER.debug(f"route: {route}, lenght: {len(route)}")

        processedPostalCodes = []
        
        bestPriceOnRoute = None
        bestStationOnRoute = None

        for i in range(1, len(route), 20):
            _LOGGER.debug(f"point: {route[i]}")
            postal_code = self.reverseGeocodeORS({"latitude":route[i][1], "longitude": route[i][0]}, ors_api_key)
            if postal_code is not None and postal_code not in processedPostalCodes:
                bestAroundPostalCode = self.getStationInfo(postal_code, country, fuel_type, '', 3, filter)
                processedPostalCodes.append(bestAroundPostalCode.get('postalcodes'))                    
                if bestPriceOnRoute is None or bestAroundPostalCode.get('price') < bestPriceOnRoute:
                    bestStationOnRoute = bestAroundPostalCode

        _LOGGER.debug(f"handle_get_lowest_fuel_price_on_route info found: {processedPostalCodes}")
        return bestStationOnRoute


    #USED BY Service: handle_get_lowest_fuel_price_on_route
    @sleep_and_retry
    @limits(calls=1, period=1)
    def getPriceOnRoute(self, country, fuel_type: FuelType, from_postalcode, to_postalcode, to_country = "", filter = ""):
        from_location = self.geocode(country, from_postalcode)
        assert from_location is not None
        if to_country == "":
            to_country = country
        to_location = self.geocode(to_country, to_postalcode)
        assert to_location is not None
        return self.getPriceOnRouteLatLon(fuel_type, from_location[1], from_location[0], to_location[1], to_location[0], filter)

    
    #USED BY Service: handle_get_lowest_fuel_price_on_route_coor
    @sleep_and_retry
    @limits(calls=1, period=1)
    def getPriceOnRouteLatLon(self, fuel_type: FuelType, from_latitude, from_longitude, to_latitude, to_longitude, filter = ""):
        from_location = (from_latitude, from_longitude)
        assert from_location is not None
        to_location = (to_latitude, to_longitude)
        assert to_location is not None
        route = self.getOSMRoute(from_location, to_location)
        assert route is not None
        _LOGGER.debug(f"route lenght: {len(route)}, from_location {from_location}, to_location {to_location}, route: {route}")

        # Calculate the number of elements to process (30% of the total)
        elements_to_process = round((30 / 100) * len(route))
        # Calculate the step size to evenly spread the elements
        step_size = len(route) // elements_to_process

        if len(route) < 8:
            step_size = 1

        processedPostalCodes = []
        
        bestPriceOnRoute = None
        bestStationOnRoute = None

        for i in range(0, len(route), step_size):
            _LOGGER.debug(f"point: {route[i]}, step_size {step_size} of len(route): {len(route)}")
            postal_code_country = self.reverseGeocode(route[i]['maneuver']['location'][0], route[i]['maneuver']['location'][1])
            if postal_code_country.get('postal_code') is not None and postal_code_country.get('postal_code') not in processedPostalCodes:
                _LOGGER.debug(f"Get route postalcode {postal_code_country.get('postal_code')}, processedPostalCodes {processedPostalCodes}")
                bestAroundPostalCode = None
                try:
                    bestAroundPostalCode = self.getStationInfo(postal_code_country.get('postal_code'), postal_code_country.get('country_code'), fuel_type, postal_code_country.get('town'), 3, filter, False)
                except Exception as e:
                    _LOGGER.error(f"ERROR: getStationInfo failed : {e}")
                if bestAroundPostalCode is None:
                    continue
                processedPostalCodes.extend(bestAroundPostalCode.get('postalcodes'))                    
                if (bestPriceOnRoute is None) or (bestAroundPostalCode.get('price') is not None and bestAroundPostalCode.get('price',999) < bestPriceOnRoute):
                    bestStationOnRoute = bestAroundPostalCode
                    bestPriceOnRoute = bestAroundPostalCode.get('price',999)
            else:
                _LOGGER.debug(f"skipped route postalcode {postal_code_country.get('postal_code')}, processedPostalCodes {processedPostalCodes}")

        _LOGGER.debug(f"handle_get_lowest_fuel_price_on_route info found: {processedPostalCodes}")
        return bestStationOnRoute
    
    # set the maximum number of requests per minute
    @sleep_and_retry
    @limits(calls=1, period=1)
    def make_api_request(self, url,headers="",timeout=30):
        response = self.s.get(url, headers=headers, timeout=timeout)
        if response.status_code != 200:
            _LOGGER.error(f"ERROR: {response.text}")
            return response
        else:
            return response
    
    # NOT USED
    @sleep_and_retry
    @limits(calls=100, period=60)
    def geocodeORS(self, country_code, postalcode, ors_api_key):
        _LOGGER.debug(f"geocodeORS request: country_code: {country_code}, postalcode: {postalcode}, ors_api_key: {ors_api_key}")
        header = {"Content-Type": "application/x-www-form-urlencoded"}
        # header = {"Accept-Language": "nl-BE"}
        
        response = self.make_api_request(f"https://api.openrouteservice.org/geocode/search?api_key={ors_api_key}&text={postalcode}&boundary.country={country_code}",headers=header,timeout=30)
        if response.status_code != 200:
            _LOGGER.error(f"ERROR: {response.text}")
        else:
            _LOGGER.debug(f"geocodeORS response: {response.text}")
        assert response.status_code == 200
        # parse the response as JSON
        response_json = json.loads(response.text)
        # extract the latitude and longitude coordinates from the response
        if response_json.get('features') and len(response_json.get('features')) > 0:
            coordinates = response_json['features'][0]['geometry']['coordinates']
            location = { 
                "latitude" : coordinates[1],
                "longitude" : coordinates[0]
                }
            return location
        else:
            _LOGGER.debug(f"geocodeORS response no features found: {response_json}")
            return
    
    # USED by services on route
    @sleep_and_retry
    @limits(calls=1, period=1)
    def geocode(self, country_code, postal_code):
        _LOGGER.debug(f"geocode request: country_code: {country_code}, postalcode: {postal_code}")
        try:
            # header = {"Content-Type": "application/x-www-form-urlencoded"}
            # header = {"Accept-Language": "nl-BE"}
            address = f"{postal_code}, {country_code}"

            if self.API_KEY_GEOAPIFY in ["","GEO_API_KEY"]:
                raise Exception("Geocode failed: GEO_API_KEY not set!")
            # GEOCODIFY
        #     response = self.s.get(f"{self.GEOCODIFY_BASE_URL}geocode?api_key={self.API_KEY_GEOCODIFY}&q={address}")
        #     response = response.json()
        #     status = response.get('meta').get('code')
        #     if response and status == 200:
        #         # print(response)
        #         location = response.get('response').get('features')[0].get('geometry').get('coordinates') # extract the latitude and longitude coordinates from the response
        #         _LOGGER.debug(f"geocode lat: {location[1]}, lon {location[0]}")
        #         return location
        #     else:
        #         _LOGGER.error(f"ERROR: {location}, country_code: {country_code}, postalcode: {postal_code}")
        #         return None
        # except:
        #     _LOGGER.error(f"ERROR: {response.text}")
        #     return None

            response = self.s.get(f"{self.GEOAPIFY_BASE_URL}/search?text={address}&api_key={self.API_KEY_GEOAPIFY}&format=json")

            # Check if the request was successful
            if response.status_code == 200:
                data = response.json()
                
                # Extract the first result's coordinates
                if data['results'] and len(data['results']) > 0:
                    location = [data['results'][0]['lon'],data['results'][0]['lat']] # extract the latitude and longitude coordinates from the response
                    _LOGGER.debug(f"geocode lat: {location[1]}, lon {location[0]}")
                    return location
                else:
                    return None
            else:
                return None, f"Error searching: {address}: {response.status_code}: {response.text}"
        except Exception as e:
            _LOGGER.error(f"ERROR: geocode : {e}")
            return None
        
    
     
    # NOT USED by services on route
    @sleep_and_retry
    @limits(calls=1, period=1)
    def geocodeOSMNominatim(self, country_code, postal_code):
        _LOGGER.debug(f"geocodeOSM request: country_code: {country_code}, postalcode: {postal_code}")
        # header = {"Content-Type": "application/x-www-form-urlencoded"}
        # header = {"Accept-Language": "nl-BE"}

        geocode_url = 'https://nominatim.openstreetmap.org/search'
        params = {'format': 'json', 'postalcode': postal_code, 'country': country_code, 'limit': 1}
        response = self.s.get(geocode_url, params=params)
        geocode_data = response.json()
        if geocode_data:
            location = (geocode_data[0]['lat'], geocode_data[0]['lon'])
            _LOGGER.debug(f"geocodeOSM lat: {location[0]}, lon {location[1]}")
            return location
        else:
            _LOGGER.error(f"ERROR: {response.text}")
            return None       
    
    # NOT USED
    @sleep_and_retry
    @limits(calls=100, period=60)
    def reverseGeocodeORS(self, location, ors_api_key):
        header = {"Content-Type": "application/x-www-form-urlencoded"}
        # header = {"Accept-Language": "nl-BE"}
        
        response = self.make_api_request(f"https://api.openrouteservice.org/geocode/reverse?api_key={ors_api_key}&point.lat={location.get('latitude')}&point.lon={location.get('longitude')}",headers=header,timeout=30)
        if response.status_code != 200:
            _LOGGER.error(f"ERROR: {response.text}")
        assert response.status_code == 200
        # parse the response as JSON
        response_json = json.loads(response.text)
        if response_json['features'][0]['properties'].get('postalcode'):
            return response_json['features'][0]['properties']['postalcode']
        else:
            return
    
    #USED for different countries to create a bounding box
    @sleep_and_retry
    @limits(calls=1, period=2)
    def searchGeocode(self, postalcode, city, country):
        try:
            address = f"{postalcode}, {city}, {country}"

            # GEOCODIFY
            # response = self.s.get(f"{self.GEOCODIFY_BASE_URL}geocode?api_key={self.API_KEY_GEOCODIFY}&q={address}")
            
            # response = response.json()
            # status = response.get('meta').get('code')
            # if response and status == 200:
            #     # print(response)
            #     location = response.get('response').get('features')[0].get('geometry').get('coordinates') # extract the latitude and longitude coordinates from the response
            #     _LOGGER.debug(f"geocode lat: {location[1]}, lon {location[0]}")
            #     bbox = response.get('response').get('bbox')
            #     return {"lat": location[1], "lon": location[0], "boundingbox": [bbox[1],bbox[0],bbox[3],bbox[2]]}


            if self.API_KEY_GEOAPIFY in ["","GEO_API_KEY"]:
                raise Exception("Geocode failed: GEO_API_KEY not set!")
            # GEOAPIFY
            response = self.s.get(f"{self.GEOAPIFY_BASE_URL}/search?text={address}&api_key={self.API_KEY_GEOAPIFY}&format=json")

            # Check if the request was successful
            if response.status_code == 200:
                data = response.json()
                
                # Extract the first result's coordinates
                if data['results'] and len(data['results']) > 0:
                    location = [data['results'][0]['lon'],data['results'][0]['lat']] # extract the latitude and longitude coordinates from the response
                    bbox = data['results'][0]['bbox']
                    return {"lat": location[1], "lon": location[0], "boundingbox": [bbox['lat1'],bbox['lon1'],bbox['lat2'],bbox['lon2']]}
                else:
                    return None
            else:
                return None, f"Error searching: {address}: {response.status_code}: {response.text}"
        except Exception as e:
            _LOGGER.error(f"ERROR: searchGeocode : {e}")
    
    #NOT USED for different countries to create a bounding box
    @sleep_and_retry
    @limits(calls=1, period=2)
    def searchGeocodeOSMNominatim(self, postalcode, city, country):

        # https://nominatim.openstreetmap.org/search?postalcode=1212VG&city=Hilversum&country=Netherlands&format=json
        # [{"place_id":351015506,"licence":"Data © OpenStreetMap contributors, ODbL 1.0. https://osm.org/copyright","osm_type":"relation","osm_id":271108,"boundingbox":["52.1776807","52.2855452","5.1020133","5.2189603"],"lat":"52.2241375","lon":"5.1719396","display_name":"Hilversum, North Holland, Netherlands","class":"boundary","type":"administrative","importance":0.7750020206490176,"icon":"https://nominatim.openstreetmap.org/ui/mapicons/poi_boundary_administrative.p.20.png"},{"place_id":351015507,"licence":"Data © OpenStreetMap contributors, ODbL 1.0. https://osm.org/copyright","osm_type":"relation","osm_id":419190,"boundingbox":["52.1776807","52.2855452","5.1020133","5.2189603"],"lat":"52.23158695","lon":"5.173493524521531","display_name":"Hilversum, North Holland, Netherlands","class":"boundary","type":"administrative","importance":0.7750020206490176,"icon":"https://nominatim.openstreetmap.org/ui/mapicons/poi_boundary_administrative.p.20.png"}]
        nominatim_url = f"https://nominatim.openstreetmap.org/search?postalcode={postalcode}&city={city}&country={country}&format=json"
        nominatim_response = self.s.get(nominatim_url)
        nominatim_data = nominatim_response.json()
        # _LOGGER.debug(f"nominatim_data {nominatim_data}")
        location = []
        if len(nominatim_data) > 0:
            location = nominatim_data[0]
            # lat = location.get('lat')
            # lon = location.get('lon')
            # boundingbox = location.get('boundingbox')
            # min_lat = boundingbox[0]
            # max_lat = boundingbox[1]
            # min_lon = boundingbox[2]
            # max_lon = boundingbox[3]
            return location
    
    # NOT USED for converting lat lon to postal code
    @sleep_and_retry
    @limits(calls=1, period=2)
    def reverseGeocodeOSMNominatim(self, longitude, latitude):
        nominatim_url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={latitude}&lon={longitude}"
        nominatim_response = self.s.get(nominatim_url)
        nominatim_data = nominatim_response.json()
        # _LOGGER.debug(f"nominatim_data {nominatim_data}")

        # Extract the postal code from the Nominatim response
        postal_code = nominatim_data['address'].get('postcode', None)
        country_code = nominatim_data['address'].get('country_code', None)
        town = nominatim_data['address'].get('town', None)
        address = nominatim_data['address']
        # _LOGGER.debug(f"nominatim_data postal_code {postal_code}, country_code {country_code}, town {town}")

        return (postal_code, country_code, town, address)
    
    # USED for converting lat lon to postal code
    @sleep_and_retry
    @limits(calls=1, period=2)
    def reverseGeocode(self, longitude, latitude):
        try:
            # GECODIFY
            # response = self.s.get(f"{self.GEOCODIFY_BASE_URL}reverse?api_key={self.API_KEY_GEOCODIFY}&lat={latitude}&lng={longitude}")
            
            # response = response.json()
            # status = response.get('meta').get('code')
            # if response and status == 200:
            #     # print(response)

            #     # Extract the postal code from the response
            #     extracted_response = {
            #         "postal_code": response.get('response').get('features')[0].get('properties').get('postalcode'),
            #         "country_code": response.get('response').get('features')[0].get('properties').get('country_code'),
            #         "town": response.get('response').get('features')[0].get('properties').get('locality'),
            #         "address": f"{response.get('response').get('features')[0].get('properties').get('street')} {response.get('response').get('features')[0].get('properties').get('housenumber')}, {response.get('response').get('features')[0].get('properties').get('postalcode')} {response.get('response').get('features')[0].get('properties').get('locality')}, {response.get('response').get('features')[0].get('properties').get('country')}",
            #         "region": response.get('response').get('features')[0].get('properties').get('region')
            #     }
            #     _LOGGER.debug(f"geodata extracted_response {extracted_response}")

            #     return extracted_response

            # GEOAPIFY
            
            response = self.s.get(f"{self.GEOAPIFY_BASE_URL}/reverse?lat={latitude}&lon={longitude}&api_key={self.API_KEY_GEOAPIFY}&format=json")

            _LOGGER.debug(f"reverseGeocode geodata response {response}, {self.GEOAPIFY_BASE_URL}/reverse?lat={latitude}&lon={longitude}&api_key={self.API_KEY_GEOAPIFY}&format=json")
            # Check if the request was successful
            if response.status_code == 200:
                data = response.json()
                
                # Extract the first result's coordinates
                if data['results'] and len(data['results']) > 0:
                    # Extract the postal code from the response
                    extracted_response = {
                        "postal_code": data['results'][0].get('postcode',''),
                        "country_code": data['results'][0].get('country_code',''),
                        "town": data['results'][0].get('city',''),
                        "address": data['results'][0].get('formatted',''),
                        "region": data['results'][0].get('state','')
                    }
                    return extracted_response
                else:
                    return None
        except Exception as e:
            _LOGGER.error(f"ERROR: reverseGeocode: {e}")


    # NOT USED for converting lat lon to postal code
    @sleep_and_retry
    @limits(calls=1, period=2)
    def reverseGeocodeNominatim(self, longitude, latitude):
        nominatim_url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={latitude}&lon={longitude}"
        nominatim_response = self.s.get(nominatim_url)
        nominatim_data = nominatim_response.json()
        # _LOGGER.debug(f"nominatim_data {nominatim_data}")

        # Extract the postal code from the Nominatim response
        postal_code = nominatim_data['address'].get('postcode', None)
        country_code = nominatim_data['address'].get('country_code', None)
        town = nominatim_data['address'].get('town', None)
        address = nominatim_data['address']
        # _LOGGER.debug(f"nominatim_data postal_code {postal_code}, country_code {country_code}, town {town}")

        return (postal_code, country_code, town, address)

    # NOT USED
    @sleep_and_retry
    @limits(calls=1, period=15)
    def getOrsRoute(self, from_location, to_location, ors_api_key):

        header = {
            'Accept': 'application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8',
            'Authorization': ors_api_key,
            'Content-Type': 'application/json; charset=utf-8'
        }
        # # header = {"Accept-Language": "nl-BE"}
        # # set the minimum distance between locations in meters
        # min_distance = 10000

        # # set the radius around each waypoint
        # radius = min_distance / 2

        # # set the parameters for the OpenRouteService routing API
        # params = {
        #     "coordinates": [[from_location.get('longitude'),from_location.get('latitude')],[to_location.get('longitude'),to_location.get('latitude')]],
        #     "radiuses": [5000]
        # }
        # url = "https://api.openrouteservice.org/v2/directions/driving-car/json"
        # response = self.s.post(url, json=params, headers=header, timeout=30)
        response = self.make_api_request(f"https://api.openrouteservice.org/v2/directions/driving-car?api_key={ors_api_key}&start={from_location.get('longitude')},{from_location.get('latitude')}&end={to_location.get('longitude')},{to_location.get('latitude')}",headers=header,timeout=30)
        if response.status_code != 200:
            _LOGGER.error(f"ERROR: {response.text}")
        assert response.status_code == 200
        response_json = json.loads(response.text)
        
        # Extract the geometry (i.e. the points along the route) from the response
        geometry = response_json["features"][0]["geometry"]["coordinates"]
        return geometry

    #  USED by services on route 
    @sleep_and_retry
    @limits(calls=1, period=15)
    def getOSMRoute(self, from_location, to_location):

        #location expected (lat, lon)

        # Request the route from OpenStreetMap API
        # 'https://router.project-osrm.org/route/v1/driving/<from_lon>,<from_lat>;<to_lon>,<to_lat>?steps=true
        
        header = {"Content-Type": "application/x-www-form-urlencoded"}
        self.s.headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
        url = f'https://router.project-osrm.org/route/v1/driving/{from_location[1]},{from_location[0]};{to_location[1]},{to_location[0]}?steps=true'
        _LOGGER.debug(f"getOSMRoute: {url}")
        response = self.s.get(url,headers=header, timeout=30)
        route_data = response.json()
        _LOGGER.debug(f"route_data {route_data}")


        if route_data.get('routes') is None:
            _LOGGER.error(f"ERROR: route not found: {route_data}")
            return
        # Extract the waypoints (towns) along the route
        waypoints = route_data['routes'][0]['legs'][0]['steps']
        
        _LOGGER.debug(f"waypoints {waypoints}")
        return waypoints

    #  NOT USED by services on route 
    @sleep_and_retry
    @limits(calls=1, period=15)
    def getRoute(self, from_location, to_location):

        #location expected (lat (50.XX), lon (4.XX))

        # Request the route from GeoApify.com API
        
        # 'https://router.project-osrm.org/route/v1/driving/<from_lon>,<from_lat>;<to_lon>,<to_lat>?steps=true
        url = f'https://router.project-osrm.org/route/v1/driving/{from_location[1]},{from_location[0]};{to_location[1]},{to_location[0]}?steps=true'
        url = f"https://api.geoapify.com/v1/routing?waypoints={from_location[0]},{from_location[1]}|{to_location[0]},{to_location[1]}&mode=drive&apiKey={self.API_KEY_GEOAPIFY}"
        #NOT WORKING: steps contain no coordinates
        response = self.s.get(url)
        route_data = response.json()
        _LOGGER.debug(f"route_data {route_data}")
        
        # Extract the waypoints (towns) along the route
        waypoints = route_data['routes'][0]['legs'][0]['steps']
        
        _LOGGER.debug(f"waypoints {waypoints}")
        return waypoints    


    def haversine_distance(self, lat1, lon1, lat2, lon2):
        # Radius of the Earth in kilometers
        earth_radius = 6371

        # Convert latitude and longitude from degrees to radians
        lat1 = math.radians(lat1)
        lon1 = math.radians(lon1)
        lat2 = math.radians(lat2)
        lon2 = math.radians(lon2)

        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        # Calculate the distance
        distance = round(earth_radius * c, 2)

        return distance

        # # Example usage
        # lat1 = 52.5200  # Latitude of location 1
        # lon1 = 13.4050  # Longitude of location 1
        # lat2 = 48.8566  # Latitude of location 2
        # lon2 = 2.3522   # Longitude of location 2

        # distance = haversine_distance(lat1, lon1, lat2, lon2)
        # print(f"Approximate distance: {distance:.2f} km")

    def add_station_distance(self, stations, stationLatName, stationLonName, lat, lon):
        for station in stations:
            latitude = str(self.get_nested_element(station, stationLatName))
            longitude = str(self.get_nested_element(station, stationLonName))
            distance = self.haversine_distance(float(str(latitude).replace(',','.')), float(str(longitude).replace(',','.')), lat, lon)
            station["distance"] = distance
    def get_nested_element(self, json_obj, key_string):
        keys = key_string.split('.')
        nested_value = json_obj
        try:
            for key in keys:
                nested_value = nested_value[key]
            return nested_value
        except (KeyError, TypeError):
            return None
    

#manual tests - enable debug logging

# _LOGGER = logging.getLogger(__name__)
# _LOGGER.setLevel(logging.DEBUG)
# if not logging.getLogger().hasHandlers():
#     logging.basicConfig(level=logging.DEBUG)
# _LOGGER.debug("Debug logging is now enabled.")

# session = ComponentSession("GEO_API_KEY")

#LOCAL TESTS

# session.geocode("BE", "1000")

#  test route
# print(session.getPriceOnRoute("BE", FuelType.DIESEL, 1000, 2000))


# test nl official
# session.getFuelOfficial(FuelType.DIESEL_OFFICIAL_B7, "NL")
# session.getFuelOfficial(FuelType.LPG_OFFICIAL, "BE")

#test US
# ZIP Code 10001 - New York, New York
# ZIP Code 90210 - Beverly Hills, California
# ZIP Code 60611 - Chicago, Illinois
# ZIP Code 02110 - Boston, Massachusetts
# ZIP Code 33109 - Miami Beach, Florida

# locationinfo= session.convertLocationBoundingBox("90210", "US", "Beverly Hills")
# print(session.getFuelPrices("90210", "US", "Beverly Hills", locationinfo, FuelType.DIESEL, False))


#test SP


# locationinfo= session.convertLocationBoundingBox("28500", "ES", "Madrid")
# print(session.getFuelPrices("28500", "ES", "Madrid", locationinfo, FuelType.DIESEL, False))

# #test BE
# locationinfo= session.convertPostalCode("3300", "BE", "Bost")
# print(session.getOilPrice(locationinfo.get("id"), 1000, FuelType.OILSTD.code))
# locationinfo= session.convertPostalCode("3300", "BE", "Bost")
# print(session.getFuelPrices("3300", "BE", "Bost", locationinfo.get("id"), FuelType.LPG, False))
# #test2
# locationinfo= session.convertPostalCode("8380", "BE", "Brugge")
# if locationinfo:
#     print(session.getFuelPrices("8380", "BE", "Brugge", locationinfo.get("id"), FuelType.SUPER95, False))
# #test3
# locationinfo= session.convertPostalCode("31830", "FR")
# if locationinfo:
#     # print(session.getFuelPrices("31830", "FR", "Plaisance-du-Touch", locationinfo.get("id"), FuelType.SUPER95, True))
#     print(session.getStationInfo("31830", "FR", FuelType.SUPER95, "Plaisance-du-Touch", 0, "", True))
# test IT
# locationinfo= session.convertLocationBoundingBox("07021", "IT", "Arzachena")
# print(session.getFuelPrices("07021", "IT", "Arzachena", locationinfo, FuelType.SUPER95, False))
#locationinfo= session.convertLocationBoundingBox("09040", "IT", "Settimo San Pietro")
#print(session.getFuelPrices("09040", "IT", "Settimo San Pietro", locationinfo, FuelType.SUPER95, False))
# test NL
# locationinfo= session.convertLocationBoundingBox("2627AR", "NL", "Delft")
# if len(locationinfo) > 0: 
#     print(session.getFuelPrices("2627AR", "NL", "Delft", locationinfo, FuelType.DIESEL, False))
    # print(session.getStationInfo("2627AR", "NL", FuelType.DIESEL, "Delft", 0, "", False))
            
# print(FuelType.DIESEL.code)
# print(FuelType.SUPER95_PREDICTION.code)
# print("FuelType.DIESEL_OFFICIAL_B10")
# print(session.getFuelOfficial(FuelType.DIESEL_OFFICIAL_B10, "NL"))
# print("FuelType.SUPER95_OFFICIAL_E10")
# print(session.getFuelOfficial(FuelType.SUPER95_OFFICIAL_E10, "NL"))

# print(FuelType.DIESEL.code)
