import json
import logging
import requests
import re
from bs4 import BeautifulSoup
from ratelimit import limits, sleep_and_retry
import urllib.parse
from enum import Enum

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
        

class FuelType(Enum):
    SUPER95 = ("E10")
    SUPER95_Prediction = ("E95")
    SUPER98 = ("SP98")
    DIESEL = ("GO")
    DIESEL_Prediction = ("D")
    OILSTD = ("7")
    OILSTD_Prediction = ("mazout50s")
    OILEXTRA = ("2")
    OILEXTRA_Prediction = ("extra")
    
    def __init__(self, code):
        self.code = code

    @property
    def name_lowercase(self):
        return self.name.lower()

class ComponentSession(object):
    def __init__(self):
        self.s = requests.Session()
        self.s.headers["User-Agent"] = "Python/3"
        
    # Country = country code: BE/FR/LU
    
    @sleep_and_retry
    @limits(calls=1, period=1)
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
    def getFuelPrices(self, postalcode, country, town, locationid, fueltypecode, single):
        header = {"Content-Type": "application/x-www-form-urlencoded"}
        # https://carbu.com/belgie//liste-stations-service/GO/Diegem/1831/BE_bf_279

        response = self.s.get(f"https://carbu.com/belgie//liste-stations-service/{fueltypecode}/{town}/{postalcode}/{locationid}",headers=header,timeout=50)
        if response.status_code != 200:
            _LOGGER.error(f"ERROR: {response.text}")
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
                
                stationdetails.append({"id":stationid,"name":name,"url":url,"logo_url":logo_url,"brand":brand,"address":', '.join(el for el in address),"postalcode": address_postalcode, "locality":locality,"price":price,"lat":lat,"lon":lng,"fuelname":fuelname,"distance":distance,"date":date})
                
                # _LOGGER.debug(f"stationdetails: {stationdetails}")
                if single:
                    break
            if single:
                break
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
    def getOilPrice(self, locationid, volume, oiltypecode):
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
        oildetails_url = f"{url}{namespace}{offers}?api_key={api_key}&sk={sk}&areaCode={locationid}&productId={oiltypecode}&quantity={volume}&locale=nl-BE"
        
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

    def getStationInfo(self,postalcode, country, fuel_type: FuelType, town="", max_distance=0, filter=""):
        
        carbuLocationInfo = self.convertPostalCode(postalcode, country, town)
        if not carbuLocationInfo:
            raise Exception(f"Location not found country: {country}, postalcode: {postalcode}, town: {town}")
        town = carbuLocationInfo.get("n")
        city = carbuLocationInfo.get("pn")
        countryname = carbuLocationInfo.get("cn")
        locationid = carbuLocationInfo.get("id")
        _LOGGER.debug(f"convertPostalCode postalcode: {postalcode}, town: {town}, city: {city}, countryname: {countryname}, locationid: {locationid}")
        price_info = self.getFuelPrices(postalcode, country, town, locationid, fuel_type.code, False)
        # _LOGGER.debug(f"price_info {fuel_type.name} {price_info}")
        return self.getStationInfoFromPriceInfo(price_info, postalcode, fuel_type, max_distance, filter)

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
            "postalcodes" : [],
            "city" : None,
            "latitude" : None,
            "longitude" : None,
            "fuelname" : None,
            "fueltype" : fuel_type,
            "date" : None
        }
        _LOGGER.debug(f"getStationInfoFromPriceInfo {fuel_type.name}, postalcode: {postalcode}, max_distance : {max_distance}, filter: {filter}, price_info: {price_info}")

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
                data["diffPct"] = round(100*((data["price"] - data["localPrice"])/data["price"]),3)
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
                if max_distance == 0:
                    break
        if data["supplier"] is None and filterSet:
            _LOGGER.warning(f"{postalcode} the station filter '{filter}' may result in no results found, if needed, please review filter")
        
        _LOGGER.debug(f"get_lowest_fuel_price info found: {data}")
        return data
        
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
    
    def getPriceOnRoute(self, country, fuel_type: FuelType, from_postalcode, to_postalcode, ors_api_key, filter = "", here_api_key= ""):
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

        for i in range(1, len(route), 5):
            # response = requests.get(f"https://revgeocode.search.hereapi.com/v1/revgeocode?at={point[1]},{point[0]}&lang=en-US&apiKey={here_api_key}")
            _LOGGER.debug(f"point: {route[i]}")
            postal_code = self.reverseGeocodeORS({"latitude":route[i][1], "longitude": route[i][0]}, ors_api_key)
            if postal_code not in processedPostalCodes:
                bestAroundPostalCode = self.getStationInfo(postal_code, country, fuel_type, '', 5, filter)
                processedPostalCodes.append(bestAroundPostalCode.get('postalcodes'))                    
                if bestPriceOnRoute is None or bestAroundPostalCode.get('price') < bestPriceOnRoute:
                    bestStationOnRoute = bestAroundPostalCode

        _LOGGER.debug(f"handle_get_lowest_fuel_price_on_route info found: {processedPostalCodes}")


        return bestStationOnRoute

    
    # set the maximum number of requests per minute
    @sleep_and_retry
    @limits(calls=100, period=60)
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
    @limits(calls=40, period=60)
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
