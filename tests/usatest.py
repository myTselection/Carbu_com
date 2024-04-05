"""GasBuddy USA data source."""
import logging
import json
import uuid
import requests

# use these-united-states for geocoding to states
import united_states
# from geopy import distance

ANDROID_USER_AGENT = "Dalvik/2.1.0 (Linux; U; Android 13; Pixel 4 XL Build/TQ3A.230705.001.B4)"


# Here is a list of US state abbreviations:

# Alabama - AL
# Alaska - AK
# Arizona - AZ
# Arkansas - AR
# California - CA
# Colorado - CO
# Connecticut - CT
# Delaware - DE
# Florida - FL
# Georgia - GA
# Hawaii - HI
# Idaho - ID
# Illinois - IL
# Indiana - IN
# Iowa - IA
# Kansas - KS
# Kentucky - KY
# Louisiana - LA
# Maine - ME
# Maryland - MD
# Massachusetts - MA
# Michigan - MI
# Minnesota - MN
# Mississippi - MS
# Missouri - MO
# Montana - MT
# Nebraska - NE
# Nevada - NV
# New Hampshire - NH
# New Jersey - NJ
# New Mexico - NM
# New York - NY
# North Carolina - NC
# North Dakota - ND
# Ohio - OH
# Oklahoma - OK
# Oregon - OR
# Pennsylvania - PA
# Rhode Island - RI
# South Carolina - SC
# South Dakota - SD
# Tennessee - TN
# Texas - TX
# Utah - UT
# Vermont - VT
# Virginia - VA
# Washington - WA
# West Virginia - WV
# Wisconsin - WI
# Wyoming - WY

_headers = {
    "apikey": "56c57e8f1132465d817d6a753c59387e",
    "User-Agent": ANDROID_USER_AGENT
}

_url = f"https://services.gasbuddy.com/mobile-orchestration/stations?authid={str(uuid.uuid4())}&country=US&distance_format=km&limit=10&region=WA&lat=38.906316&lng=-77.054750"
_LOGGER = logging.getLogger(__name__)

_LOGGER.debug("Starting usatest.py")
print("Starting usatest.py")
print("Url: " + _url)
print(str(uuid.uuid4()))

s = requests.Session()

response = s.get(url=_url, headers=_headers)
# print(response.text)
# Check if request was successful (status code 200)
if response.status_code == 200:
    # Define the filename
    filename = 'tests/response_content.txt'

    # Write the response content into a file
    with open(filename, 'wb') as f:
        f.write(response.content)

    print("Response content saved to:", filename)
else:
    print("GET request failed with status code:", response.status_code)