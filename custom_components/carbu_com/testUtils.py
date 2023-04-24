
from utils import *


country = "BE"
fuel_type = "diesel"
filter = ""
from_postalcode = 1650
from_town = ""
to_postalcode = 1830
to_town = ""
# here_api_key = call.data.get('here_api_key','')
ors_api_key = "5b3ce3597851110001cf6248e01585276b794475a75aa2bd85499743"

session = ComponentSession()

session.getStationInfo('1640','BE', FuelType.DIESEL,'',5,'')
from_location = session.geocodeORS(country, from_postalcode, ors_api_key)
print(f"from_location: {from_location}")
# reverse_from_location = session.reverseGeocodeORS(from_location, ors_api_key)
# print(f"reverse_from_location: {reverse_from_location}")
to_location = session.geocodeORS(country, to_postalcode, ors_api_key)
print(f"to_location: {to_location}")
# reverse_to_location = session.reverseGeocodeORS(to_location, ors_api_key)
# print(f"reverse_to_location: {reverse_to_location}")


route = session.getOrsRoute(from_location, to_location, ors_api_key)
print(f"route: {route}, lenght: {len(route)}")

postal_codes = {}
for i in range(1, len(route), 5):
    # response = requests.get(f"https://revgeocode.search.hereapi.com/v1/revgeocode?at={point[1]},{point[0]}&lang=en-US&apiKey={here_api_key}")
    print(f"{i} point: {route[i]}")
    # postal_code = self.reverseGeocodeORS({"latitude":route[i][1], "longitude": route[i][0]}, ors_api_key)
    # if postal_code:
        # postal_codes[postal_code]=postal_code

print(f"handle_get_lowest_fuel_price_on_route info found: {postal_codes}")