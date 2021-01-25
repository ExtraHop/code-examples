# COPYRIGHT 2021 BY EXTRAHOP NETWORKS, INC.
#
# This file is subject to the terms and conditions defined in
# file 'LICENSE', which is part of this source code package.

#!/usr/bin/python3

import json
import http.client
import csv
import os.path

# The IP address or hostname of the ExtraHop system.
HOST = "extrahop.example.com"
# The API key.
APIKEY = "123456789abcdefghijklmnop"
# The path of the CSV file relative to the location of the script file.
CSV_FILE = "device_list.csv"

headers = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Authorization": "ExtraHop apikey=%s" % APIKEY,
}


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
    """
    conn = http.client.HTTPSConnection(HOST)
    conn.request(
        "POST",
        "/api/v1/customdevices",
        body=json.dumps(device),
        headers=headers,
    )
    resp = conn.getresponse()
    if resp.status != 201:
        print("Could not create device: " + device["name"])
        print("    " + json.loads(resp.read())["error_message"])
    else:
        print("Created custom device: " + device["name"])
        device_id = os.path.basename(resp.getheader("location"))


devices = readCSV()
for device in devices:
    createDevice(device)
