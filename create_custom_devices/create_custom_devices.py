#!/usr/bin/python3

# COPYRIGHT 2021 BY EXTRAHOP NETWORKS, INC.
#
# This file is subject to the terms and conditions defined in
# file 'LICENSE', which is part of this source code package.

import json
import requests
from urllib.parse import urlunparse
import csv
import os.path

# The IP address or hostname of the ExtraHop system.
HOST = "extrahop.example.com"
# The API key.
API_KEY = "123456789abcdefghijklmnop"
# The path of the CSV file relative to the location of the script file.
CSV_FILE = "device_list.csv"


def readCSV():
    """
    Method that reads custom device criteria from a CSV file.

        Returns:
            devices (list): A list of device dictionaries
    """
    devices = []
    with open(CSV_FILE, "rt", encoding="ascii") as f:
        reader = csv.reader(f)
        for row in reader:
            device = {}
            ips = []
            device["name"] = row.pop(0)
            device["extrahop_id"] = row.pop(0)
            device["description"] = row.pop(0)
            for ip in row:
                ips.append({"ipaddr": ip})
            device["criteria"] = ips
            devices.append(device)
    return devices


def createDevice(device):
    """
    Method that creates a custom device.

        Parameters:
            device(dict): A device dictionary

        Returns:
            dev_id(string): The ID of the custom device
    """
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": "ExtraHop apikey=%s" % API_KEY,
    }
    url = urlunparse(("https", HOST, "/api/v1/customdevices", "", "", ""))
    r = requests.post(url, headers=headers, json=device)
    if r.status_code == 201:
        dev_id = os.path.basename(r.headers["location"])
        print(f"Created custom device: {device['name']}")
        return dev_id
    else:
        print(f"Failed to create custom device: {device['name']}")
        print(r.text)
        print(r.status_code)


def main():
    devices = readCSV()
    for device in devices:
        dev_id = createDevice(device)


if __name__ == "__main__":
    main()
