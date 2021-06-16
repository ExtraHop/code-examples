#!/usr/bin/python3

# COPYRIGHT 2021 BY EXTRAHOP NETWORKS, INC.
#
# This file is subject to the terms and conditions defined in
# file 'LICENSE', which is part of this source code package.

import requests
import base64
import json
from urllib.parse import urlunparse

# The hostname of the Reveal(x) 360 API. This hostname is displayed in Reveal(x)
# 360 on the API Access page under API Endpoint. The hostname does not
# include the /oauth/token.
HOST = "example.api.com"
# The ID of the REST API credentials.
ID = "abcdefg123456789"
# The secret of the REST API credentials.
SECRET = "123456789abcdefg987654321abcdefg"


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
        url, headers=headers, data="grant_type=client_credentials",
    )
    return r.json()["access_token"]


def getDevices(token):
    """
    Method that sends a request to Reveal(x) 360 and authenticates the request with
    a REST API token. The request retrieves 100 active devices from the ExtraHop system.

        Returns
            list:  The list of active devices
    """
    headers = {"Authorization": "Bearer " + token}
    url = urlunparse(("https", HOST, "/api/v1/devices", "", "", ""))
    r = requests.get(url, headers=headers)
    return r.json()


def getDeviceGroups(token):
    """
    Method that sends a request to Reveal(x) 360 and authenticates the request with
    a REST API token. The request retrieves all device groups from the ExtraHop system.

        Returns
            list:  The list of device groups
    """
    headers = {"Authorization": "Bearer " + token}
    url = urlunparse(("https", HOST, "/api/v1/devicegroups", "", "", ""))
    r = requests.get(url, headers=headers)
    return r.json()


token = getToken()
devices = getDevices(token)
print(devices)
device_groups = getDeviceGroups(token)
print(device_groups)
