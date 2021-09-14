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
IP_LIST = "ip_list.csv"


def readCSV(filepath):
    """
    Method that reads a list of values from a CSV file

        Parameters:
            filepath (str): The path of the CSV file

        Returns:
            values (list): The list of values
    """
    values = []
    with open(IP_LIST, "rt", encoding="ascii") as f:
        reader = csv.reader(f)
        for row in reader:
            for item in row:
                values.append(item)
    return values


def getDevicesByIp(ip):
    """
    Method that retrieves the devices with a specified IP address

        Parameters:
            ip (str): The IP address

        Returns:
            devices (list): The device objects
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
        print("Unable to retrieve tags")
        print(r.status_code)
        print(r.text)
        sys.exit()


def idHighValue(device):
    """
    Method that specifies a device as high value.

        Parameters:
            device (dict): The device dictionary
    """
    url = urlunparse(
        (
            "https",
            HOST,
            f"/api/v1/devices/{device['id']}",
            "",
            "",
            "",
        )
    )
    headers = {"Authorization": "ExtraHop apikey=%s" % API_KEY}
    data = {"custom_criticality": "critical"}
    r = requests.patch(url, headers=headers, json=data)
    if r.status_code == 204:
        print(f"Successfully specified {device['display_name']} as high value")
    else:
        print(f"Failed to specify {device['display_name']} as high value")
        print(r.status_code)
        print(r.text)


def main():
    device_ips = readCSV(IP_LIST)
    devices = []
    # Retrieve IDs of devices with the specified IPs
    for ip in device_ips:
        devices += getDevicesByIp(ip)
    for device in devices:
        if device["custom_criticality"] != "critical":
            idHighValue(device)
        else:
            print(
                f"Skipping {device['display_name']} because the device has already been specified as high value"
            )


if __name__ == "__main__":
    main()
