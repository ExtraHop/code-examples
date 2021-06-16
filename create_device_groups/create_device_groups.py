#!/usr/bin/python3

# COPYRIGHT 2020 BY EXTRAHOP NETWORKS, INC.
#
# This file is subject to the terms and conditions defined in
# file 'LICENSE', which is part of this source code package.

import json
import requests
import csv
import os.path
from urllib.parse import urlunparse

HOST = "extrahop.example.com"
API_KEY = "123456789abcdefghijklmnop"
CSV_FILE = "device_group_list.csv"

headers = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Authorization": "ExtraHop apikey=%s" % API_KEY,
}


def readCSV():
    devices = []
    with open(CSV_FILE, "rt", encoding="ascii") as f:
        reader = csv.reader(f)
        for row in reader:
            device = {}
            device["name"] = row.pop(0)
            device["description"] = row.pop(0)
            rules = []
            for ip in row:
                rules.append(
                    {"field": "ipaddr", "operand": ip, "operator": "="}
                )
            device["filter"] = {"rules": rules, "operator": "or"}
            devices.append(device)
    return devices


def createDevice(device):
    url = urlunparse(("https", HOST, "/api/v1/devicegroups", "", "", ""))
    r = requests.post(url, headers=headers, data=json.dumps(device))
    if r.status_code != 201:
        print("Could not create device: " + device["name"])
        print(r.status_code)
        print(r.json())
    else:
        print("Created custom device: " + device["name"])


devices = readCSV()
for device in devices:
    createDevice(device)
