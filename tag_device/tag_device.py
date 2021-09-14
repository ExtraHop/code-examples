#!/usr/bin/python3

# COPYRIGHT 2021 BY EXTRAHOP NETWORKS, INC.
#
# This file is subject to the terms and conditions defined in
# file 'LICENSE', which is part of this source code package.

import requests
import json
import csv
import sys
from urllib.parse import urlunparse

# The IP address or hostname of the ExtraHop system.
HOST = "extrahop.example.com"
# The API key.
API_KEY = "123456789abcdefghijklmnop"
# The name of the tag.
TAG = "new-tag"
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


def getTagId(tag_name):
    """
    Method that retrieves the ID of a device tag.

        Parameters:
            tag (str): The name of the device tag

        Returns:
            tag_id (str): The ID of the device tag
    """
    url = urlunparse(("https", HOST, "/api/v1/tags", "", "", ""))
    headers = {"Authorization": "ExtraHop apikey=%s" % API_KEY}
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        for tag in r.json():
            if tag["name"] == tag_name:
                return tag["id"]
    else:
        print("Unable to retrieve tags")
        print(r.status_code)
        print(r.text)
        sys.exit()


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


# Add the tag to each device
def assignTag(tag_id, tag_name, devices):
    """
    Method that assigns a tag to a list of devices

        Parameters:
            tag_id (int): The ID of the tag
            tag_name (str): The name of the tag
            devices (list): The list of device dictionaries
    """
    ids = [device["id"] for device in devices]
    data = {"assign": ids}
    url = urlunparse(
        ("https", HOST, f"/api/v1/tags/{tag_id}/devices", "", "", "")
    )
    headers = {"Authorization": "ExtraHop apikey=%s" % API_KEY}
    r = requests.post(url, headers=headers, json=data)
    if r.status_code == 204:
        print(f"Assigned {tag_name} tag to the following devices:")
        for device in devices:
            print(f'    {device["display_name"]}')
    elif r.status_code == 207:
        print("Assigned {tag_name} tag to a limited number of devices.")
        print(json.dumps(r.json(), indent=4))
    else:
        print(f"Failed to assign tag: {tag_name}")
        print(r.status_code)
        print(r.text)
        sys.exit()


def createTag(tag):
    """
    Method that creates a tag on the ExtraHop system.

        Parameters:
            tag (str): The name of the tag
    """
    url = urlunparse(("https", HOST, "/api/v1/tags", "", "", ""))
    headers = {"Authorization": "ExtraHop apikey=%s" % API_KEY}
    data = {"name": TAG}
    r = requests.post(url, headers=headers, json=data)
    if r.status_code == 201:
        print(f"Created tag {tag}")
    else:
        print("Failed to create tag")
        print(r.status_code)
        print(r.text)
        sys.exit()


def main():
    # If the tag does not already exist, create it
    tag_id = getTagId(TAG)
    if tag_id:
        print(f"{TAG} already exists")
    else:
        createTag(TAG)
        tag_id = getTagId(TAG)
    device_ips = readCSV(IP_LIST)
    devices = []
    # Retrieve IDs of devices with the specified IPs
    for ip in device_ips:
        devices += getDevicesByIp(ip)
    assignTag(tag_id, TAG, devices)


if __name__ == "__main__":
    main()
