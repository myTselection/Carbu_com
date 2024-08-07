
import logging
import requests
from ratelimit import limits, sleep_and_retry

_LOGGER = logging.getLogger(__name__)
class Geocoder:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.geocodify.com/v2"

    @sleep_and_retry
    @limits(calls=1, period=1)
    def geocode(self, country_code, postal_code, city=None):
        _LOGGER.debug(f"geocode request: country_code: {country_code}, postalcode: {postal_code}, city: {city}")

        try:
            # Construct the query parameters
            params = {
                'api_key': self.api_key,
                'country': country_code,
                'postalcode': postal_code,
                'limit': 1
            }
            if city:
                params['city'] = city

            # Send the request to Geocodify.com
            response = requests.get(f"{self.base_url}/geocode", params=params)
            response.raise_for_status()
            data = response.json()

            if data and data['response']['results']:
                result = data['response']['results'][0]
                lat_lon = (result['location']['lat'], result['location']['lng'])
                bounding_box = result.get('boundingbox', None)
                _LOGGER.debug(f"geocode lat: {lat_lon[0]}, lon: {lat_lon[1]}, bounding_box: {bounding_box}")
                return lat_lon, bounding_box
            else:
                _LOGGER.error("ERROR: No geocode data returned")
                return None, None
        except requests.exceptions.RequestException as e:
            _LOGGER.error(f"ERROR: Geocoding request failed: {str(e)}")
            return None, None

    @sleep_and_retry
    @limits(calls=1, period=1)
    def reverse_geocode(self, lat, lon):
        _LOGGER.debug(f"reverse geocode request: lat: {lat}, lon: {lon}")

        try:
            # Construct the query parameters
            params = {
                'api_key': self.api_key,
                'lat': lat,
                'lng': lon,
                'limit': 1
            }

            # Send the request to Geocodify.com
            response = requests.get(f"{self.base_url}/reverse", params=params)
            response.raise_for_status()
            data = response.json()

            if data and data['response']['results']:
                result = data['response']['results'][0]
                address = result['formatted']
                _LOGGER.debug(f"reverse geocode address: {address}")
                return address
            else:
                _LOGGER.error("ERROR: No reverse geocode data returned")
                return None
        except requests.exceptions.RequestException as e:
            _LOGGER.error(f"ERROR: Reverse geocoding request failed: {str(e)}")
            return None

# Example usage
# API_KEY = "YOUR_GEOCODIFY_API_KEY"
API_KEY = "RUhWH7FwquRnpHWy0Gey77GkyrTBpxPt"
geocoder = Geocoder(API_KEY)
location, bounding_box = geocoder.geocode('BE', '1000', 'Brussels')
if location:
    print(f"Latitude: {location[0]}, Longitude: {location[1]}")
    print(f"Bounding Box: {bounding_box}")

if location:
    address = geocoder.reverse_geocode(location[0], location[1])
    if address:
        print(f"Address: {address}")