import json
import logging
import requests
import re
from bs4 import BeautifulSoup
import urllib.parse

import voluptuous as vol

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
        


class ComponentSession(object):
    def __init__(self):
        self.s = requests.Session()
        self.s.headers["User-Agent"] = "Python/3"
        
    # Country = country code: BE/FR/LU
    def convertPostalCode(self, postalcode, country, town = ''):
        _LOGGER.debug(f"convertPostalCode: postalcode: {postalcode}, country: {country}, town: {town}")
        header = {"Content-Type": "application/x-www-form-urlencoded"}
        # https://carbu.com//commonFunctions/getlocation/controller.getlocation_JSON.php?location=1831&SHRT=1
        # {"id":"FR_24_18_183_1813_18085","area_code":"FR_24_18_183_1813_18085","name":"Dampierre-en-GraÃ§ay","parent_name":"Centre","area_level":"","area_levelName":"","country":"FR","country_name":"France","lat":"47.18111","lng":"1.9425","postcode":"18310","region_name":""},{"id":"FR_24_18_183_1813_18100","area_code":"FR_24_18_183_1813_18100","name":"Genouilly","parent_name":"Centre","area_level":"","area_levelName":"","country":"FR","country_name":"France","lat":"47.19194","lng":"1.88417","postcode":"18310","region_name":""},{"id":"FR_24_18_183_1813_18103","area_code":"FR_24_18_183_1813_18103","name":"GraÃ§ay","parent_name":"Centre","area_level":"","area_levelName":"","country":"FR","country_name":"France","lat":"47.14389","lng":"1.84694","postcode":"18310","region_name":""},{"id":"FR_24_18_183_1813_18167","area_code":"FR_24_18_183_1813_18167","name":"Nohant-en-GraÃ§ay","parent_name":"Centre","area_level":"","area_levelName":"","country":"FR","country_name":"France","lat":"47.13667","lng":"1.89361","postcode":"18310","region_name":""},{"id":"FR_24_18_183_1813_18228","area_code":"FR_24_18_183_1813_18228","name":"Saint-Outrille","parent_name":"Centre","area_level":"","area_levelName":"","country":"FR","country_name":"France","lat":"47.14361","lng":"1.84","postcode":"18310","region_name":""},{"id":"BE_bf_279","area_code":"BE_bf_279","name":"Diegem","parent_name":"Machelen","area_level":"","area_levelName":"","country":"BE","country_name":"Belgique","lat":"50.892365","lng":"4.446127","postcode":"1831","region_name":""},{"id":"LU_lx_3287","area_code":"LU_lx_3287","name":"Luxembourg","parent_name":"Luxembourg","area_level":"","area_levelName":"","country":"LU","country_name":"Luxembourg","lat":"49.610004","lng":"6.129596","postcode":"1831","region_name":""}
        data ={"location":postalcode,"SHRT":1}
        response = self.s.get(f"https://carbu.com//commonFunctions/getlocation/controller.getlocation_JSON.php?location={postalcode}&SHRT=1",headers=header,timeout=30)
        assert response.status_code == 200
        locationinfo = json.loads(response.text)
        _LOGGER.debug(f"location info : {locationinfo}")
        for info_dict in locationinfo:
            _LOGGER.debug(f"loop location info found: {info_dict}")
            if info_dict["c"] is not None and info_dict["pc"] is not None:
                if town is not None and town.strip() != '' and info_dict["n"] is not None:
                    if info_dict["n"].lower() == town.lower() and info_dict["c"].lower() == country.lower() and info_dict["pc"] == postalcode:
                        _LOGGER.debug(f"location info found: {info_dict}, matching town {town}, postal {postalcode} and country {country}")
                        return info_dict
                else:
                    if info_dict["c"].lower() == country.lower() and info_dict["pc"] == postalcode:
                        _LOGGER.debug(f"location info found: {info_dict}, matching postal {postalcode} and country {country}")
                        return info_dict
        return False        
        
    def getFuelPrice(self, postalcode, country, town, locationid, fueltypecode, single):
        header = {"Content-Type": "application/x-www-form-urlencoded"}
        # https://carbu.com/belgie//liste-stations-service/GO/Diegem/1831/BE_bf_279

        response = self.s.get(f"https://carbu.com/belgie//liste-stations-service/{fueltypecode}/{town}/{postalcode}/{locationid}",headers=header,timeout=30)
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
                
                stationdetails.append({"id":stationid,"name":name,"url":url,"logo_url":logo_url,"brand":brand,"address":address,"locality":locality,"price":price,"lat":lat,"lon":lng,"fuelname":fuelname,"distance":distance,"date":date})
                
                # _LOGGER.debug(f"stationdetails: {stationdetails}")
                if single:
                    break
            if single:
                break
        return stationdetails
        
    def getFuelPrediction(self, fueltype_prediction_code):
        header = {"Content-Type": "application/x-www-form-urlencoded"}
        # Super 95: https://carbu.com/belgie//index.php/voorspellingen?p=M&C=E95
        # Diesel: https://carbu.com/belgie//index.php/voorspellingen?p=M&C=D

        response = self.s.get(f"https://carbu.com/belgie//index.php/voorspellingen?p=M&C={fueltype_prediction_code}",headers=header,timeout=30)
        assert response.status_code == 200
        
        last_category = None
        last_data = None
        soup = BeautifulSoup(response.text, 'html.parser')
        # Find the Highchart series data
        highchart_series = soup.find_all('script')
        value = 0
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
                
        return value
        
    def getOilPrice(self, locationid, volume, oiltypecode):
        header = {"Content-Type": "application/x-www-form-urlencoded"}
        header = {"Accept-Language": "nl-BE"}
        # https://mazout.com/belgie/offers?areaCode=BE_bf_279&by=quantity&for=2000&productId=7
        # https://mazout.com/config.378173423.json
        # https://api.carbu.com/mazout/v1/offers?api_key=elPb39PWhWJj9K2t73tlxyRL0cxEcTCr0cgceQ8q&areaCode=BE_bf_223&productId=7&quantity=1000&sk=T211ck5hWEtySXFMRTlXRys5KzVydz09

        response = self.s.get(f"https://mazout.com/config.378173423.json",headers=header,timeout=30)
        assert response.status_code == 200
        api_details = response.json()
        api_key = api_details.get("api").get("accessToken").get("val")
        sk = api_details.get("api").get("appId").get("val") #x.api.appId.val
        url = api_details.get("api").get("url")
        namespace = api_details.get("api").get("namespace")
        offers = api_details.get("api").get("routes").get("offers") #x.api.routes.offers
        oildetails_url = f"{url}{namespace}{offers}?api_key={api_key}&sk={sk}&areaCode={locationid}&productId={oiltypecode}&quantity={volume}&locale=nl-BE"
        
        response = self.s.get(oildetails_url,headers=header,timeout=30, verify=False)
        assert response.status_code == 200
        oildetails = response.json()
        
        return oildetails
        
    def getOilPrediction(self):
        header = {"Content-Type": "application/x-www-form-urlencoded"}
        header = {"Accept-Language": "nl-BE"}
        # https://mazout.com/belgie/offers?areaCode=BE_bf_279&by=quantity&for=2000&productId=7
        # https://mazout.com/config.378173423.json
        # https://api.carbu.com/mazout/v1/price-summary?api_key=elPb39PWhWJj9K2t73tlxyRL0cxEcTCr0cgceQ8q&sk=T211ck5hWEtySXFMRTlXRys5KzVydz09

        response = self.s.get(f"https://mazout.com/config.378173423.json",headers=header,timeout=30)
        assert response.status_code == 200
        api_details = response.json()
        api_key = api_details.get("api").get("accessToken").get("val")
        sk = api_details.get("api").get("appId").get("val") #x.api.appId.val
        url = api_details.get("api").get("url")
        namespace = api_details.get("api").get("namespace")
        oildetails_url = f"{url}{namespace}/price-summary?api_key={api_key}&sk={sk}"
        
        response = self.s.get(oildetails_url,headers=header,timeout=30, verify=False)
        assert response.status_code == 200
        oildetails = response.json()
        
        return oildetails


