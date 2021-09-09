#!/usr/bin/python3

# COPYRIGHT 2021 BY EXTRAHOP NETWORKS, INC.
#
# This file is subject to the terms and conditions defined in
# file 'LICENSE', which is part of this source code package.

import requests
import json
import csv
import datetime
import sys
from urllib.parse import urlunparse

# The IP address or hostname of the ExtraHop system.
HOST = "extrahop.example.com"
# The API key.
APIKEY = "123456789abcdefghijklmnop"
# The file that output will be written to.
FILENAME = "devices.csv"
# The maximum number of devices to retrieve with each GET request.
LIMIT = 1000
# Determines whether L2 parent devices are retrieved.
SAVEL2 = False
# Retrieves only devices that are currently under advanced analysis.
ADVANCED_ONLY = False
# Retrieves only devices that have been identified as critical by the ExtraHop system.
CRITICAL_ONLY = False


def getAllDevices():
    """
    Method that retrieves all devices from the ExtraHop system.

        Returns:
            device_list(list): A list of all devices on the system
    """
    continue_search = True
    offset = 0
    device_list = []
    while continue_search:
        new_devices = getDevices(LIMIT, offset)
        device_list += new_devices
        if len(new_devices) > 0:
            offset += LIMIT
        else:
            continue_search = False
    return device_list


def getDevices(limit, offset):
    """
    Method that retrieves a set of devices from the ExtraHop system.

        Parameters:
            limit (int): The maximum number of devices to retrieve
            offset (int): The number of device results to skip

        Returns:
            devices (list): A list of device dictionaries
    """
    url = urlunparse(
        (
            "https",
            HOST,
            f"/api/v1/devices?limit={LIMIT}&offset={offset}&search_type=any",
            "",
            "",
            "",
        )
    )
    headers = {
        "Authorization": f"ExtraHop apikey={API_KEY}",
        "Accept": "application/json",
    }
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        return r.json()
    else:
        print("Error retrieving Device list")
        print(r.status_code)
        print(r.text)
        sys.exit()


def saveToCSV(devices):
    """
    Method that saves a list of device dictionaries to a CSV file.

        Parameters:
            devices (list): The device dictionaries

        Returns:
            saved (list): A list of devices that were saved to the CSV file
            skipped (list): A list of devices that were not saved to the CSV file
    """
    print(f"Saving {len(devices)} devices to CSV file")
    with open(FILENAME, "w") as csvfile:
        csvwriter = csv.writer(csvfile, dialect="excel")
        csvwriter.writerow(list(devices[0].keys()))
        saved = []
        skipped = []
        for device in devices:
            if ADVANCED_ONLY == False or (
                ADVANCED_ONLY == True and device["analysis"] == "advanced"
            ):
                if CRITICAL_ONLY == False or (
                    CRITICAL_ONLY == True and device["critical"] == True
                ):
                    if device["is_l3"] | SAVEL2:
                        saved.append(device)
                        device["mod_time"] = datetime.datetime.fromtimestamp(
                            device["mod_time"] / 1000.0
                        )
                        device[
                            "user_mod_time"
                        ] = datetime.datetime.fromtimestamp(
                            device["user_mod_time"] / 1000.0
                        )
                        device[
                            "discover_time"
                        ] = datetime.datetime.fromtimestamp(
                            device["discover_time"] / 1000.0
                        )
                        csvwriter.writerow(list(device.values()))
                    else:
                        skipped.append(device)
                else:
                    skipped.append(device)
            else:
                skipped.append(device)
        return saved, skipped


def main():
    devices = getAllDevices()
    if devices:
        saved, skipped = saveToCSV(devices)
        print(
            f"Saved {str(len(saved))} devices, skipped {str(len(skipped))} devices to {FILENAME}."
        )


if __name__ == "__main__":
    main()
