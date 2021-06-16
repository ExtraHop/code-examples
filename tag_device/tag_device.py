#!/usr/bin/python3

# COPYRIGHT 2021 BY EXTRAHOP NETWORKS, INC.
#
# This file is subject to the terms and conditions defined in
# file 'LICENSE', which is part of this source code package.

import http.client
import json
import csv

# The IP address or hostname of the ExtraHop system.
HOST = "extrahop.example.com"
# The API key.
APIKEY = "123456789abcdefghijklmnop"
# The name of the tag.
TAG = "new-tag"
# The file that contains the list of IP addresses.
IP_LIST = "ip_list.csv"

headers = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Authorization": "ExtraHop apikey=%s" % APIKEY,
}


def get_tag_id(tag):
    """
    Method that retrieves the ID of a device tag.

        Parameters:
            tag (str): The name of the device tag

        Returns:
            tag_id (str): The ID of the device tag
    """
    tag_id = ""
    conn = http.client.HTTPSConnection(HOST, context=context)
    conn.request("GET", "/api/v1/tags", headers=headers)
    resp = conn.getresponse()
    tags = json.loads(resp.read())
    tag_index = 0
    while tag_id == "" and tag_index < len(tags):
        if tags[tag_index]["name"] == tag:
            tag_id = tags[tag_index]["id"]
        tag_index += 1
    return tag_id


# If the tag does not already exist, create it
tag_id = get_tag_id(TAG)
if tag_id != "":
    print(TAG + " already exists")
else:
    print("Creating " + TAG + " tag")
    body = {"name": TAG}
    conn = http.client.HTTPSConnection(HOST, context=context)
    conn.request("POST", "/api/v1/tags", headers=headers, body=json.dumps(body))
    resp = conn.getresponse()
    if resp.status == 201:
        print(TAG + " tag created successfully!")
    else:
        print("Error: could not create " + TAG + " tag")
        sys.exit()
    tag_id = get_tag_id(TAG)

# Retrieve IPs from CSV file
device_ips = []
with open(IP_LIST, "rt", encoding="ascii") as f:
    reader = csv.reader(f)
    for row in reader:
        for item in row:
            device_ips.append(item)

# Retrieve IDs of devices with the specified IPs
device_ids = []
tagged_devices = []
for ip in device_ips:
    conn = http.client.HTTPSConnection(HOST, context=context)
    url = "/api/v1/devices?limit=100&search_type=ip%20address&value=" + ip
    conn.request("GET", url, headers=headers)
    resp = conn.getresponse()
    try:
        devices = json.loads(resp.read())
    except:
        continue
    for device in devices:
        device_ids.append(device["id"])
        tagged_devices.append(device["display_name"])

# Add the tag to each device
body = {"assign": device_ids}
conn = http.client.HTTPSConnection(HOST, context=context)
url = "/api/v1/tags/%d/devices" % tag_id
conn.request("POST", url, headers=headers, body=json.dumps(body))
resp = conn.getresponse()
if resp.status == 204:
    print("Success! Assigned %s to the following devices:" % TAG)
    for name in tagged_devices:
        print("    " + name)
    print("Assigned %s to %d devices" % (TAG, len(device_ids)))
else:
    print("Error! Failed to tag specified devices")
