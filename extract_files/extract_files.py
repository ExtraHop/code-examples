#!/usr/bin/python3

# COPYRIGHT 2024 BY EXTRAHOP NETWORKS, INC.
#
# This file is subject to the terms and conditions defined in
# file 'LICENSE', which is part of this source code package.

import requests
import json
import csv
import datetime
import sys
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

# The parameters of the packet search
SEARCH = {"from": "-30m", "output": "extract", "ip1": "10.10.10.10"}


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


def fileSearch(search):
    """
    Method that extracts files from packets that match the specified search parameters.

        Parameters:
            search(dict): A dictionary that specifies the packet search parameters.

        Returns:
            device_list(list): A list of all devices on the system
    """
    url = urlunparse(
        (
            "https",
            HOST,
            f"/api/v1/packets/search",
            "",
            "",
            "",
        )
    )
    headers = {
        "Authorization": getAuthHeader(),
        "Accept": "application/json",
    }
    r = requests.post(url, headers=headers, json=search)
    if r.status_code == 200:
        return r.content
    else:
        print("Unable to retrieve files")
        print(r.status_code)
        print(r.text)
        sys.exit()


def main():
    output_filename = "extracted_files.zip"
    extracted_files = fileSearch(SEARCH)
    with open(output_filename, "wb") as file:
        file.write(extracted_files)
    print(f"Wrote extracted files to {output_filename}.")


if __name__ == "__main__":
    main()
