import unittest
import requests
import logging
import json
import sys
sys.path.append('../custom_components/carbu_com/')
from utils import ComponentSession



import zlib


_LOGGER = logging.getLogger(__name__)

#run this test on command line with: python -m unittest test_component_session

logging.basicConfig(level=logging.DEBUG)

class TestComponentSession(unittest.TestCase):
    def setUp(self):
        self.session = ComponentSession()
        self.locationinfo = None
        
    # def test_crc(self):
        # filename = "C:\\Users\\Sil\\Documents\\Tweaks\\IoT\\HA_CustomComponent\\Carbu.com\\main-e91191c6b0.js"
        # filename = "C:\\Users\\Sil\\Documents\\Tweaks\\IoT\\HA_CustomComponent\\Carbu.com\\test.html"
        # filename = "C:\\Users\\Sil\\Documents\\Tweaks\\IoT\\HA_CustomComponent\\Carbu.com\\rc-consent-67d63bd6fd.js"
        # # replace with the name of your file
        # with open(filename, "rb") as f:
            # file_content = f.read()
            # # file_content = "https://mazout.com/dist/scripts/main-e91191c6b0.js"
            # crc32 = zlib.crc32(file_content)
            # crc32_str = hex(crc32)[1:]  # convert the hash to a hexadecimal string and remove the "0x" prefix
            # crc32_str_sliced = crc32_str[1:]  # slice the string from index 1 to the end
            # _LOGGER.debug(f"hex(crc32) {hex(crc32)} {int(hex(crc32),16)} crc32 {crc32} sliced {crc32_str_sliced} crc32 sliced int {int(crc32_str_sliced,16)}")
            # # prints the CRC32 hash as a hexadecimal string

    def skip_test_convertPostalCode(self):
        # Test successful login
        self.locationinfo = self.session.convertPostalCode("1831", "BE")
        _LOGGER.debug(f"locationinfo {self.locationinfo}")
        self.assertIsNotNone(self.locationinfo)
        
    def skip_test_getPrice(self):
        # Test successful login
        priceinfo = self.session.getFuelPrice("1831", "BE","Diegem","BE_bf_279","GO")
        _LOGGER.debug(f"priceinfo {priceinfo}")
        self.assertIsNotNone(priceinfo)
        
    def skip_test_getOilPrice(self):
        # Test successful login
        priceinfo = self.session.getOilPrice("BE_bf_279", "1000","7")
        _LOGGER.debug(f"priceinfo {priceinfo}")
        self.assertIsNotNone(priceinfo)
        
    def test_getFuelPredictionDiesel(self):
        # Test successful login
        priceinfo = self.session.getFuelPrediction("D")
        _LOGGER.debug(f"priceinfo {priceinfo}")
        self.assertIsNotNone(priceinfo)
        
    def test_getFuelPredictionE95(self):
        # Test successful login
        priceinfo = self.session.getFuelPrediction("E95")
        _LOGGER.debug(f"priceinfo {priceinfo}")
        self.assertIsNotNone(priceinfo)
        
        
if __name__ == '__main__':
    unittest.main()