#!/usr/bin/python3

# COPYRIGHT 2020 BY EXTRAHOP NETWORKS, INC.
#
# This file is subject to the terms and conditions defined in
# file 'LICENSE', which is part of this source code package.

import json
import requests
import csv
import os.path
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

CSV_FILE = "device_group_list.csv"


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


def readCSV():
    devices = []
    with open(CSV_FILE, "rt", encoding="ascii") as f:
        reader = csv.reader(f)
        for row in reader:
            device = {}
            device["name"] = row.pop(0)
            device["description"] = row.pop(0)
            rules = []
            for ip in row:
                rules.append(
                    {"field": "ipaddr", "operand": ip, "operator": "="}
                )
            device["filter"] = {"rules": rules, "operator": "or"}
            devices.append(device)
    return devices


def createDevice(device):
    url = urlunparse(("https", HOST, "/api/v1/devicegroups", "", "", ""))
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": getAuthHeader(),
    }
    r = requests.post(url, headers=headers, data=json.dumps(device))
    if r.status_code != 201:
        print("Could not create device group: " + device["name"])
        print(r.status_code)
        print(r.json())
    else:
        print("Created custom device group: " + device["name"])


devices = readCSV()
for device in devices:
    createDevice(device)
