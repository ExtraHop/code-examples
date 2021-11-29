#!/usr/bin/python3
  
# COPYRIGHT 2021 BY EXTRAHOP NETWORKS, INC.
#
# This file is subject to the terms and conditions defined in
# file 'LICENSE', which is part of this source code package.

import requests
import csv
import sys
from urllib.parse import urlunparse

# The IP address or hostname of the ExtraHop system.
HOST = "extrahop.example.com"
# The API key.
API_KEY = "123456789abcdefghijklmnop"
# The file that contains the list of IP addresses.
CUSTOM_CONFIG = "custom_config.csv"


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
            f"/api/v1/devices?limit=100&search_type=ip%20address&value={ip}",
            "",
            "",
            "",
        )
    )
    headers = {"Authorization": "ExtraHop apikey=%s" % API_KEY}
    r = requests.get(url, headers=headers)
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
    headers = {"Authorization": "ExtraHop apikey=%s" % API_KEY}
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
