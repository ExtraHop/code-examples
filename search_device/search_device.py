#!/usr/bin/python3

# COPYRIGHT 2021 BY EXTRAHOP NETWORKS, INC.
#
# This file is subject to the terms and conditions defined in
# file 'LICENSE', which is part of this source code package.

import json
import requests
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

# An array of IP addresses.
IP_ADDR_LIST = ["10.10.10.200", "10.10.10.201", "10.10.10.202", "10.10.10.203"]


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


def searchDevice(search):
    """
    Method that searches the ExtraHop system for a device that
    matches the specified search criteria

        Parameters:
            search (dict): The device search criteria

        Returns:
            dict: The metadata of the device that matches the criteria
    """
    url = urlunparse(("https", HOST, "/api/v1/devices/search", "", "", ""))
    headers = {"Authorization": getAuthHeader()}
    r = requests.post(url, headers=headers, data=json.dumps(search))
    try:
        devices = r.json()
        if len(devices) == 0:
            print("No devices match criteria:")
            print(json.dumps(search, indent=4))
            return None
        elif len(devices) == 1:
            return devices[0]
        else:
            print(f"Warning: More than one device matches criteria:")
            print(json.dumps(search, indent=4))
            return devices[0]
    except:
        print("Search failed for device with criteria:")
        print(json.dumps(search, indent=4))
        print(r.status_code)
        print(r.text)


for ip in IP_ADDR_LIST:
    search_filter = {
        "filter": {"field": "ipaddr", "operand": ip, "operator": "="}
    }
    device = searchDevice(search_filter)
    if device:
        print(ip)
        print("    " + device["discovery_id"])
