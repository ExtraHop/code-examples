#!/usr/bin/python3

# COPYRIGHT 2021 BY EXTRAHOP NETWORKS, INC.
#
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
CUSTOM_CONFIG = "custom_config.csv"


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
    Method that reads a table of IP addresses, models, and makes from a CSV file.
    The first row is discarded.

        Parameters:
            filepath (str): The path of the CSV file

        Returns:
            devices (list): A list of dictionaries containing the custom make and model for each IP address
    """
    devices = []
    with open(filepath, "rt", encoding="ascii") as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            device = {
                "ipaddr": row[0],
                "custom_make": row[1],
                "custom_model": row[2],
            }
            devices.append(device)
    return devices


def getDevicesByIp(ip):
    """
    Method that retrieves the devices associated with a specified IP address

        Parameters:
            ip (str): The IP address

        Returns:
            devices (list): The list of device dictionaries
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
        print("Unable to retrieve devices")
        print(r.status_code)
        print(r.text)
        sys.exit()


def specifyMakeModel(device):
    """
    Method that specifies a custom make and model for a device.

        Parameters:
            device (dict): The device dictionary
    """
    headers = {"Authorization": getAuthHeader()}
    data = {
        "custom_make": device["custom_make"],
        "custom_model": device["custom_model"],
    }
    for dev_id in device["ids"]:
        url = urlunparse(
            (
                "https",
                HOST,
                f"/api/v1/devices/{dev_id}",
                "",
                "",
                "",
            )
        )
        r = requests.patch(url, headers=headers, json=data)
        if r.status_code == 204:
            print(f"Successfully updated device {device['display_name']}")
            print(f"    Custom Make: {device['custom_make']}")
            print(f"    Custom Model: {device['custom_model']}")
        else:
            print(
                f"Failed to update custom make and model for {device['display_name']}"
            )
            print(r.status_code)
            print(r.text)


def main():
    devices = readCSV(CUSTOM_CONFIG)
    # Retrieve IDs of devices with the specified IPs
    for device in devices:
        device_specs = getDevicesByIp(device["ipaddr"])
        ids = []
        for spec in device_specs:
            # Only add IDs for devices that do not already have the specified custom make and model
            if (
                device["custom_make"] != spec["custom_make"]
                and device["custom_model"] != spec["custom_model"]
            ):
                ids.append(spec["id"])
        device["ids"] = ids
        device["display_name"] = spec["display_name"]
    for device in devices:
        if device["ids"]:
            specifyMakeModel(device)
        else:
            print(
                f"Skipping {device['display_name']} because the device has already been assigned the specified custom make and model: {device['custom_make']} {device['custom_model']}"
            )


if __name__ == "__main__":
    main()
