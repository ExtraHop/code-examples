#!/usr/bin/python3

# COPYRIGHT 2025 BY EXTRAHOP NETWORKS, INC.
#
# This file is subject to the terms and conditions defined in
# file 'LICENSE', which is part of this source code package.

import json
import requests
from urllib.parse import urlunparse
import base64

# The IP address or hostname of the ExtraHop appliance or RevealX 360 API
HOST = "extrahop.example.com"

# For RevealX 360 authentication
# The ID of the REST API credentials.
ID = "abcdefg123456789"
# The secret of the REST API credentials.
SECRET = "123456789abcdefg987654321abcdefg"
# A global variable for the temporary API access token (leave blank)
TOKEN = ""

# For self-managed appliance authentication
# The API key.
API_KEY = "123456789abcdefghijklmnop"


def getToken():
    """
    Method that generates and retrieves a temporary API access token for RevealX 360 authentication.

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
        print("Error retrieveing token from RevealX 360")
        sys.exit()


def getAuthHeader(force_token_gen=False):
    """
    Method that adds an authorization header for a request. For RevealX 360, adds a temporary access
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


# Method that updates detections on an ExtraHop system
def updateDetection(detection):
    url = urlunparse(
        (
            "https",
            HOST,
            f"/api/v1/detections/{detection['detection_id']}",
            "",
            "",
            "",
        )
    )
    del detection["detection_id"]
    data = json.dumps(detection)
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": getAuthHeader(),
    }
    r = requests.patch(url, data=data, headers=headers)
    print(r.status_code)
    print(r.text)


# Array of detection information
detections = [
    {
        "detection_id": "1",
        "ticket_id": "TK-16982",
        "status": "new",
        "assignee": "sally",
        "resolution": None,
    },
    {
        "detection_id": "2",
        "ticket_id": "TK-2078",
        "status": None,
        "assignee": "jim",
        "resolution": None,
    },
    {
        "detection_id": "3",
        "ticket_id": "TK-3452",
        "status": None,
        "assignee": "alex",
        "resolution": None,
    },
]

for detection in detections:
    updateDetection(detection)
