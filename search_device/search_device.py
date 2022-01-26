#!/usr/bin/python3

# COPYRIGHT 2021 BY EXTRAHOP NETWORKS, INC.
#
# This file is subject to the terms and conditions defined in
# file 'LICENSE', which is part of this source code package.

import json
import requests
from urllib.parse import urlunparse

# The IP address or hostname of the ExtraHop system.
HOST = "extrahop.example.com"
# The API key.
APIKEY = "123456789abcdefghijklmnop"
# An array of IP addresses.
IP_ADDR_LIST = ["10.10.10.200", "10.10.10.201", "10.10.10.202", "10.10.10.203"]


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
    headers = {"Authorization": "ExtraHop apikey=%s" % APIKEY}
    r = requests.post(
        url, headers=headers, data=json.dumps(search)
    )
    return r.json()[0]


for ip in IP_ADDR_LIST:
    search_filter = {
        "filter": {"field": "ipaddr", "operand": ip, "operator": "="}
    }
    device = searchDevice(search_filter)
    print(ip)
    print("    " + device["discovery_id"])
