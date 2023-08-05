import json
import logging
import requests
import re
from bs4 import BeautifulSoup
from ratelimit import limits, sleep_and_retry
from datetime import date
import urllib.parse
from enum import Enum

import voluptuous as vol

# logging.basicConfig(level=logging.DEBUG)
_LOGGER = logging.getLogger(__name__)

_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.0%z"

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
    SUPER95 = ("E10", 5, "benzina", "euro95")
    SUPER95_Prediction = ("E95")
    SUPER98 = ("SP98", 6, "benzina","superplus")
    DIESEL = ("GO",3,"diesel","diesel")
    DIESEL_Prediction = ("D")
    OILSTD = ("7")
    OILSTD_Prediction = ("mazout50s")
    OILEXTRA = ("2")
    OILEXTRA_Prediction = ("extra")
    
    def __init__(self, code, de_code=0, it_name="",nl_name=""):
        self.code = code
        self.de_code = de_code
        self.it_name = it_name
        self.nl_name = nl_name

    @property
    def name_lowercase(self):
        return self.name.lower()

class ComponentSession(object):
    def __init__(self):
        self.s = requests.Session()
        self.s.headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        
    # Country = country code: BE/FR/LU/DE/IT
    
    @sleep_and_retry
    @limits(calls=1, period=5)
    def convertPostalCode(self, postalcode, country, town = ''):
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
        for info_dict in locationinfo:
            _LOGGER.debug(f"loop location info found: {info_dict}")
            if info_dict.get('c') is not None and info_dict.get('pc') is not None:
                if town is not None and town.strip() != '' and info_dict.get("n") is not None:
                    if info_dict.get("n",'').lower() == town.lower() and info_dict.get("c",'').lower() == country.lower() and info_dict.get("pc",'') == str(postalcode):
                        _LOGGER.debug(f"location info found: {info_dict}, matching town {town}, postal {postalcode} and country {country}")
                        return info_dict
                else:
                    if info_dict.get("c",'').lower() == country.lower() and info_dict.get("pc",'') == str(postalcode):
                        _LOGGER.debug(f"location info found: {info_dict}, matching postal {postalcode} and country {country}")
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
                    if info_dict.get("n",'').lower() == town.lower() and info_dict.get("c",'').lower() == country.lower() and info_dict.get("pc",'') == str(postalcode):
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
        orig_location = self.searchGeocodeOSM(postalcode, town, country_name)
        if orig_location is None:
            return []
        orig_boundingbox = orig_location.get('boundingbox')
        boundingboxes = [orig_boundingbox, [float(orig_boundingbox[0])-0.045, float(orig_boundingbox[1])+0.045, float(orig_boundingbox[2])-0.045, float(orig_boundingbox[3])+0.045], [float(orig_boundingbox[0])-0.09, float(orig_boundingbox[1])+0.09, float(orig_boundingbox[2])-0.09, float(orig_boundingbox[3])+0.09]]
        return boundingboxes
    
    
    def convertLatLonBoundingBox(self, lat, lon):
        f_lat = float(lat)
        f_lon = float(lon)
        boundingboxes = [[f_lat-0.020, f_lat+0.020,f_lon-0.020, f_lon+0.02], [f_lat-0.045, f_lat+0.045, f_lon-0.045, f_lon+0.045], [f_lat-0.09, f_lat+0.09, f_lon-0.09, f_lon+0.09]]
        return boundingboxes
    

    @sleep_and_retry
    @limits(calls=1, period=1)
    def getFuelPrices(self, postalcode, country, town, locationinfo, fueltype: FuelType, single):
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
                
                stationdetails.append({"id":stationid,"name":name,"url":url,"logo_url":logo_url,"brand":brand,"address":', '.join(el for el in address),"postalcode": address_postalcode, "locality":locality,"price":price,"lat":lat,"lon":lng,"fuelname":fuelname,"distance":distance,"date":date, "country": country})
                
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
            station_name = block.find('span', class_='fuel-station-location-name').text.strip()
            station_street = block.find('div', class_='fuel-station-location-street').text.strip()
            station_city = block.find('div', class_='fuel-station-location-city').text.strip()
            station_postalcode, station_locality = station_city.split(maxsplit=1)
            price_text = block.find('div', class_='price-text')
            if price_text != None:
                price_text = price_text.text.strip()
            else:
                continue
            price_changed = [span.text.strip() for span in block.find_all('span', class_='price-changed')]
            logo_url = block.find('img', class_='mtsk-logo')['src']
            distance = float(block.find('div', class_='fuel-station-location-distance').text.strip().replace(' km',''))
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
                'date': current_date, 
                'country': country
            }
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
        radius = 0.023
        for boundingbox in locationinfo:
            #TODO check if needs to be retrieved 3 times 0, 5 & 10km or radius can be set to 0.09 to get all at once
            nl_url = f"https://www.brandstof-zoeker.nl/ajax/stations/?pageType=geo%2FpostalCode&type={fueltype.nl_name}&latitude={locationinfo[0][0]}&longitude={locationinfo[0][2]}&radius={radius}"
            # _LOGGER.debug(f"NL URL: {nl_url}")
            response = self.s.get(nl_url,headers=header,timeout=50)
            if response.status_code != 200:
                _LOGGER.error(f"ERROR: {response.text}")
            assert response.status_code == 200
            radius = radius + 0.045

            nl_prices = response.json()
            all_stations.extend(nl_prices)


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
                'postalcode': f"{block.get('station').get('pc_cijfer')}{block.get('station').get('pc_letter')}",
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
                if postalcode == f"{block.get('station').get('pc_cijfer')}{block.get('station').get('pc_letter')}":
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
        for boundingbox in locationinfo:
            response = self.s.get(f"https://api3.prezzibenzina.it/?do=pb_get_prices&output=json&os=android&appname=AndroidFuel&sdk=33&platform=SM-S906B&udid=dlwHryfCRXy-zJWX6mMN22&appversion=3.22.08.14&loc_perm=foreground&network=mobile&limit=5000&offset=1&min_lat={boundingbox[0]}&max_lat={boundingbox[1]}&min_long={boundingbox[2]}&max_long={boundingbox[3]}",headers=header,timeout=50)
            if response.status_code != 200:
                _LOGGER.error(f"ERROR: {response.text}")
            assert response.status_code == 200

            pb_get_prices = response.json()
            pb_get_prices = pb_get_prices.get('pb_get_prices')
            pb_get_prices_price = pb_get_prices.get('prices').get('price')

            # Filter the list to keep only items containing "diesel" in the "fuel" value
            diesel_items = [item for item in pb_get_prices_price if fueltype.it_name in item["fuel"].lower()]

            # Sort the filtered list by the "price" key in ascending order
            sorted_diesel_items = sorted(diesel_items, key=lambda x: float(x["price"]))

            # Extract all the station IDs into a list
            station_ids = [item["station"] for item in sorted_diesel_items]
            comma_separated_station_ids = ",".join(station_ids)
            
            response = self.s.get(f"https://api3.prezzibenzina.it/?do=pb_get_stations&output=json&appname=PrezziBenzinaWidget&ids={comma_separated_station_ids}&prices=on&minprice=1&fuels=d&apiversion=3.1",headers=header,timeout=50)
            if response.status_code != 200:
                _LOGGER.error(f"ERROR: {response.text}")
            assert response.status_code == 200

            stationdetails_prezzibenzina = response.json()
            stationdetails_prezzibenzina = stationdetails_prezzibenzina.get('pb_get_stations')
            stationdetails_prezzibenzina_stations = stationdetails_prezzibenzina.get("stations").get("station")
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
                    continue
                block_data = {
                    'id': block.get('id'),
                    'name': block.get('name'),
                    'url': block.get('url'),
                    'logo_url': f"https://www.prezzibenzina.it/www2/marker.php?brand={block.get('co')}&status=AP&price={fuel_price_items[0].get('price')}&certified=0&marker_type=1",
                    'brand': block.get('co_name'),
                    'address': block.get('address'),
                    'postalcode': block.get('zip'),
                    'locality': block.get('city_name'),
                    'price': fuel_price_items[0].get('price'),
                    'price_changed': fuel_price_items[0].get('date'),
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
    def getFuelPrediction(self, fueltype_prediction_code):
        header = {"Content-Type": "application/x-www-form-urlencoded"}
        # Super 95: https://carbu.com/belgie//index.php/voorspellingen?p=M&C=E95
        # Diesel: https://carbu.com/belgie//index.php/voorspellingen?p=M&C=D

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
                
        return value
        
    @sleep_and_retry
    @limits(calls=1, period=1)
    def getOilPrice(self, locationinfo, volume, oiltypecode):
        header = {"Content-Type": "application/x-www-form-urlencoded"}
        header = {"Accept-Language": "nl-BE"}
        # https://mazout.com/belgie/offers?areaCode=BE_bf_279&by=quantity&for=2000&productId=7
        # https://mazout.com/config.378173423.json
        # https://api.carbu.com/mazout/v1/offers?api_key=elPb39PWhWJj9K2t73tlxyRL0cxEcTCr0cgceQ8q&areaCode=BE_bf_223&productId=7&quantity=1000&sk=T211ck5hWEtySXFMRTlXRys5KzVydz09

        response = self.s.get(f"https://mazout.com/config.378173423.json",headers=header,timeout=30)
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

        response = self.s.get(f"https://mazout.com/config.378173423.json",headers=header,timeout=30)
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
    def getStationInfo(self, postalcode, country, fuel_type: FuelType, town="", max_distance=0, filter=""):
        town = None
        locationinfo = None
        single = True if max_distance == 0 else False
        if country.lower() in ["be","fr","lu"]:
            carbuLocationInfo = self.convertPostalCode(postalcode, country, town)
            if not carbuLocationInfo:
                raise Exception(f"Location not found country: {country}, postalcode: {postalcode}, town: {town}")
            town = carbuLocationInfo.get("n")
            city = carbuLocationInfo.get("pn")
            countryname = carbuLocationInfo.get("cn")
            locationinfo = carbuLocationInfo.get("id")
            _LOGGER.debug(f"convertPostalCode postalcode: {postalcode}, town: {town}, city: {city}, countryname: {countryname}, locationinfo: {locationinfo}")
        if country.lower() in ["it","nl"]:
            itLocationInfo = self.convertLocationBoundingBox(postalcode, country, town)
            locationinfo = itLocationInfo

        price_info = self.getFuelPrices(postalcode, country, town, locationinfo, fuel_type, single)
        # _LOGGER.debug(f"price_info {fuel_type.name} {price_info}")
        return self.getStationInfoFromPriceInfo(price_info, postalcode, fuel_type, max_distance, filter)
    
    

    @sleep_and_retry
    @limits(calls=1, period=1)
    def getStationInfoLatLon(self,latitude, longitude, fuel_type: FuelType, max_distance=0, filter=""):
        postal_code_country = self.reverseGeocodeOSM((longitude, latitude))
        town = None
        locationinfo = None
        if postal_code_country[1].lower() in ["be","fr","lu"]:        
            carbuLocationInfo = self.convertPostalCode(postal_code_country[0], postal_code_country[1])
            if not carbuLocationInfo:
                raise Exception(f"Location not found country: {postal_code_country[1]}, postalcode: {postal_code_country[0]}")
            town = carbuLocationInfo.get("n")
            city = carbuLocationInfo.get("pn")
            countryname = carbuLocationInfo.get("cn")
            locationinfo = carbuLocationInfo.get("id")
            _LOGGER.debug(f"convertPostalCode postalcode: {postal_code_country[0]}, town: {town}, city: {city}, countryname: {countryname}, locationinfo: {locationinfo}")
        if postal_code_country[1].lower() in ["it"]: 
            #TODO calc boudingboxes for known lat lon
            postal_code_country = self.reverseGeocodeOSM((longitude, latitude))
            town = postal_code_country[2]
            itLocationInfo = self.convertLocationBoundingBox(postal_code_country[0], postal_code_country[1], town)
            locationinfo = itLocationInfo
        price_info = self.getFuelPrices(postal_code_country[0], postal_code_country[1], town, locationinfo, fuel_type, False)
        # _LOGGER.debug(f"price_info {fuel_type.name} {price_info}")
        return self.getStationInfoFromPriceInfo(price_info, postal_code_country[0], fuel_type, max_distance, filter)
        

    def getStationInfoFromPriceInfo(self,price_info, postalcode, fuel_type: FuelType, max_distance=0, filter=""):
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
            "country": None
        }
        # _LOGGER.debug(f"getStationInfoFromPriceInfo {fuel_type.name}, postalcode: {postalcode}, max_distance : {max_distance}, filter: {filter}, price_info: {price_info}")

        filterSet = False
        if filter is not None and filter.strip() != "":
            filterSet = filter.strip().lower()

        for station in price_info:
            # _LOGGER.debug(f"getStationInfoFromPriceInfo station: {station}")
            if filterSet:
                match = re.search(filterSet, station.get("brand").lower())
                if not match:
                    continue
            # if max_distance == 0 and str(postalcode) not in station.get("address"):
            #     break
            try:
                currDistance = float(station.get("distance"))
                currPrice = float(station.get("price"))
            except ValueError:
                continue
            if (max_distance == 0 or currDistance <= max_distance) and (data.get("price") is None or currPrice < data.get("price")):
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
                # _LOGGER.debug(f"before break {max_distance}, country: {station.get('country') }, postalcode: {station.get('postalcode')} required postalcode {postalcode}")
                if max_distance == 0:
                        # _LOGGER.debug(f"break {max_distance}, country: {station.get('country') }, postalcode: {station.get('postalcode')} required postalcode {postalcode}")
                        break
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
        from_location = self.geocodeOSM(country, from_postalcode)
        assert from_location is not None
        if to_country == "":
            to_country = country
        to_location = self.geocodeOSM(to_country, to_postalcode)
        assert to_location is not None
        return self.getPriceOnRouteLatLon(fuel_type, from_location[0], from_location[1], to_location[0], to_location[1], filter)

    
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
            postal_code_country = self.reverseGeocodeOSM((route[i]['maneuver']['location'][0], route[i]['maneuver']['location'][1]))
            if postal_code_country[0] is not None and postal_code_country[0] not in processedPostalCodes:
                _LOGGER.debug(f"Get route postalcode {postal_code_country[0]}, processedPostalCodes {processedPostalCodes}")
                bestAroundPostalCode = self.getStationInfo(postal_code_country[0], postal_code_country[1], fuel_type, postal_code_country[2], 3, filter)
                if bestAroundPostalCode is None:
                    continue
                processedPostalCodes.extend(bestAroundPostalCode.get('postalcodes'))                    
                if (bestPriceOnRoute is None) or (bestAroundPostalCode.get('price') is not None and bestAroundPostalCode.get('price',999) < bestPriceOnRoute):
                    bestStationOnRoute = bestAroundPostalCode
                    bestPriceOnRoute = bestAroundPostalCode.get('price',999)
            else:
                _LOGGER.debug(f"skipped route postalcode {postal_code_country[0]}, processedPostalCodes {processedPostalCodes}")

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
    
    @sleep_and_retry
    @limits(calls=1, period=1)
    def geocodeOSM(self, country_code, postal_code):
        _LOGGER.debug(f"geocodeOSM request: country_code: {country_code}, postalcode: {postal_code}")
        # header = {"Content-Type": "application/x-www-form-urlencoded"}
        # header = {"Accept-Language": "nl-BE"}

        geocode_url = 'https://nominatim.openstreetmap.org/search'
        params = {'format': 'json', 'postalcode': postal_code, 'country': country_code, 'limit': 1}
        response = requests.get(geocode_url, params=params)
        geocode_data = response.json()
        if geocode_data:
            location = (geocode_data[0]['lat'], geocode_data[0]['lon'])
            _LOGGER.debug(f"geocodeOSM lat: {location[0]}, lon {location[1]}")
            return location
        else:
            _LOGGER.error(f"ERROR: {response.text}")
            return None
        
    
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
    
    
    @sleep_and_retry
    @limits(calls=1, period=2)
    def searchGeocodeOSM(self, postalcode, city, country):
        nominatim_url = f"https://nominatim.openstreetmap.org/search?postalcode={postalcode}&city={city}&country={country}&format=json"
        nominatim_response = requests.get(nominatim_url)
        nominatim_data = nominatim_response.json()
        _LOGGER.debug(f"nominatim_data {nominatim_data}")
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
    
    @sleep_and_retry
    @limits(calls=1, period=2)
    def reverseGeocodeOSM(self, location):
        nominatim_url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={location[1]}&lon={location[0]}"
        nominatim_response = requests.get(nominatim_url)
        nominatim_data = nominatim_response.json()
        _LOGGER.debug(f"nominatim_data {nominatim_data}")

        # Extract the postal code from the Nominatim response
        postal_code = nominatim_data['address'].get('postcode', None)
        country_code = nominatim_data['address'].get('country_code', None)
        town = nominatim_data['address'].get('town', None)
        _LOGGER.debug(f"nominatim_data postal_code {postal_code}, country_code {country_code}, town {town}")

        return (postal_code, country_code, town)
    
    
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

    @sleep_and_retry
    @limits(calls=1, period=15)
    def getOSMRoute(self, from_location, to_location):

        #location expected (lat, lon)

        # Request the route from OpenStreetMap API
        # 'https://router.project-osrm.org/route/v1/driving/<from_lon>,<from_lat>;<to_lon>,<to_lat>?steps=true
        url = f'https://router.project-osrm.org/route/v1/driving/{from_location[1]},{from_location[0]};{to_location[1]},{to_location[0]}?steps=true'
        response = requests.get(url)
        route_data = response.json()
        _LOGGER.debug(f"route_data {route_data}")
        
        # Extract the waypoints (towns) along the route
        waypoints = route_data['routes'][0]['legs'][0]['steps']
        
        _LOGGER.debug(f"waypoints {waypoints}")
        return waypoints
    
session = ComponentSession()
# test IT
# locationinfo= session.convertLocationBoundingBox("07021", "IT", "Arzachena")
# session.getFuelPrices("07021", "IT", "Arzachena", locationinfo, FuelType.DIESEL, False)
# test NL
# locationinfo= session.convertLocationBoundingBox("2627AR", "NL", "Delft")
# session.getFuelPrices("2627AR", "NL", "Delft", locationinfo, FuelType.DIESEL, False)