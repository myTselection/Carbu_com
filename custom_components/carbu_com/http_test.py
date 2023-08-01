import sys
import requests
import socket
from datetime import datetime
import logging

logging.basicConfig(level=logging.DEBUG)
_LOGGER = logging.getLogger(__name__)

def send_http_get_request(url):
    try:
        start_time = datetime.now()
        with requests.Session() as session:
            response = session.get(url)
            end_time = datetime.now()
            log_response_details(response, start_time, end_time)
    except requests.exceptions.RequestException as e:
        print(f"Error sending HTTP GET request: {e}")

def send_http_post_request(url,data):
    try:
        start_time = datetime.now()
        with requests.Session() as session:
            response = session.post(url,data)
            end_time = datetime.now()
            log_response_details(response, start_time, end_time)
    except requests.exceptions.RequestException as e:
        print(f"Error sending HTTP POST request: {e}")

def get_client_ip():
    try:
        # Connect to a dummy socket to get the local IP address
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        client_ip = s.getsockname()[0]
        s.close()
        return client_ip
    except socket.error:
        return "Unknown"

def log_response_details(response, start_time, end_time):
    print("Response Details:")
    print(f"Status Code: {response.status_code}")
    print("Headers:")
    for key, value in response.headers.items():
        print(f"{key}: {value}")
    print("Cookies:")
    for cookie in response.cookies:
        print(f"{cookie.name}: {cookie.value}")
    print("Session Details:")
    for key, value in response.request.headers.items():
        print(f"{key}: {value}")
    print(f"Content: {response.text}")
    
    print("Additional Request Details:")
    print(f"Request URL: {response.url}")
    print(f"Request Method: {response.request.method}")
    print(f"Request Timestamp: {start_time.isoformat()}")
    print(f"Request IP Address: {get_client_ip()}")
    print(f"Request User-Agent: {response.request.headers['User-Agent']}")
    print(f"Request Timing (in seconds): {round((end_time - start_time).total_seconds(), 2)}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage to send GET request:: python http_test.py <url>")
        print("Usage to send POST request: python http_test.py <url> <data>")
        url = "https://www.prezzibenzina.it/www2/develop/tech/handlers/search_handler.php?brand=&compact=1&fuels=b&max_lat=48.2086&max_long=24.7836&min_lat=36.4372&min_long=-1.5836&sel=getStations&rand=1690877107123"
        send_http_get_request(url)
    elif len(sys.argv) < 3:
        url = sys.argv[1]
        send_http_get_request(url)
    else:
        url = sys.argv[1]
        data = sys.argv[2]
        send_http_post_request(url,data)
