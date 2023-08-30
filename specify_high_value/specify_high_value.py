# This file is subject to the terms and conditions defined in
# file 'LICENSE', which is part of this source code package.

import requests
import csv
import sys
from urllib.parse import urlunparse
import base64
import sys

# The IP address or hostname of the ExtraHop appliance or Reveal(x) 360 API
HOST = "extrahop.example.com"

# For Reveal(x) 360 authentication
# The ID of the REST API credentials.
ID = "abcdefg123456789"
# The secret of the REST API credentials.
SECRET = "123456789abcdefg987654321abcdefg"
# A global variable for the temporary API access token (leave blank)
TOKEN = ""

# For self-managed appliance authentication
# The API key.
API_KEY = "123456789abcdefghijklmnop"

# The file that contains the list of IP addresses.
IP_LIST = "ip_list.csv"


def getToken():
    """
    Method that generates and retrieves a temporary API access token for Reveal(x) 360 authentication.

        Returns:
            str: A temporary API access token
    """
    auth = base64.b64encode(bytes(ID + ":" + SECRET, "utf-8")).decode("utf-8")
    headers = {
        "Authorization": "Basic " + auth,
        "Content-Type": "application/x-www-form-urlencoded",
    }
    url = urlunparse(("https", HOST, "/oauth2/token", "", "", ""))
    r = requests.post(
        url,
        headers=headers,
        data="grant_type=client_credentials",
    )
    try:
        return r.json()["access_token"]
    except:
        print(r.text)
        print(r.status_code)
        print("Error retrieveing token from Reveal(x) 360")
        sys.exit()


def getAuthHeader(force_token_gen=False):
    """
    Method that adds an authorization header for a request. For Reveal(x) 360, adds a temporary access
    token. For self-managed appliances, adds an API key.

        Parameters:
            force_token_gen (bool): If true, always generates a new temporary API access token for the request

        Returns:
            header (str): The value for the header key in the headers dictionary
    """
    global TOKEN
    if API_KEY != "123456789abcdefghijklmnop" and API_KEY != "":
        return f"ExtraHop apikey={API_KEY}"
    else:
        if TOKEN == "" or force_token_gen == True:
            TOKEN = getToken()
        return f"Bearer {TOKEN}"


def readCSV(filepath):
    """
    Method that reads a list of values from a CSV file

        Parameters:
            filepath (str): The path of the CSV file

        Returns:
            values (list): The list of values
    """
    values = []
    with open(IP_LIST, "rt", encoding="ascii") as f:
        reader = csv.reader(f)
        for row in reader:
            for item in row:
                values.append(item)
    return values


def getDevicesByIp(ip):
    """
    Method that retrieves the devices with a specified IP address

        Parameters:
            ip (str): The IP address

        Returns:
            devices (list): The device objects
    """
    url = urlunparse(
        (
            "https",
            HOST,
            f"/api/v1/devices/search",
            "",
            "",
            "",
        )
    )
    headers = {"Authorization": getAuthHeader()}
    data = {
        "filter": {
            "field": "ipaddr",
            "operand": ip,
            "operator": "="
        }
    }
    r = requests.post(url, headers=headers, json=data)
    if r.status_code == 200:
        devices = []
        for device in r.json():
            devices.append(device)
        return devices
    else:
        print("Unable to retrieve tags")
        print(r.status_code)
        print(r.text)
        sys.exit()


def idHighValue(device):
    """
    Method that specifies a device as high value.

        Parameters:
            device (dict): The device dictionary
    """
    url = urlunparse(
        (
            "https",
            HOST,
            f"/api/v1/devices/{device['id']}",
            "",
            "",
            "",
        )
    )
    headers = {"Authorization": getAuthHeader()}
    data = {"custom_criticality": "critical"}
    r = requests.patch(url, headers=headers, json=data)
    if r.status_code == 204:
        print(f"Successfully specified {device['display_name']} as high value")
    else:
        print(f"Failed to specify {device['display_name']} as high value")
        print(r.status_code)
        print(r.text)


def main():
    device_ips = readCSV(IP_LIST)
    devices = []
    # Retrieve IDs of devices with the specified IPs
    for ip in device_ips:
        devices += getDevicesByIp(ip)
    for device in devices:
        if device["custom_criticality"] != "critical":
            idHighValue(device)
        else:
            print(
                f"Skipping {device['display_name']} because the device has already been specified as high value"
            )


if __name__ == "__main__":
    main()
