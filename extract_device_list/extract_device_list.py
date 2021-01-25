# COPYRIGHT 2021 BY EXTRAHOP NETWORKS, INC.
#
# This file is subject to the terms and conditions defined in
# file 'LICENSE', which is part of this source code package.

#!/usr/bin/python3

import http.client
import json
import csv
import datetime
import ssl
import sys

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

headers = {}
headers["Accept"] = "application/json"
headers["Authorization"] = "ExtraHop apikey=" + APIKEY


def getDevices(offset):
    """
    Method that retrieves devices from the ExtraHop system.

        Parameters:
            offset (int): The number of device results to skip.

        Returns:
            devices (list): A list of device dictionaries.
    """
    conn = http.client.HTTPSConnection(HOST)
    conn.request(
        "GET",
        "/api/v1/devices?limit=%d&offset=%d&search_type=any" % (LIMIT, offset),
        headers=headers,
    )
    resp = conn.getresponse()
    if resp.status == 200:
        devices = json.loads(resp.read())
        conn.close()
        return devices
    else:
        print("Error retrieving Device list")
        print(resp.status, resp.reason)
        resp.read()
        dTable = None
        conn.close()
        sys.exit()


continue_search = True
offset = 0
dTable = []
while continue_search:
    new_devices = getDevices(offset)
    offset += LIMIT
    dTable += new_devices
    if len(new_devices) > 0:
        continue_search = True
    else:
        continue_search = False

if dTable != None:
    print(" - Saving %d devices in CSV file" % len(dTable))
    with open(FILENAME, "w") as csvfile:
        csvwriter = csv.writer(csvfile, dialect="excel")
        csvwriter.writerow(list(dTable[0].keys()))
        w = 0
        s = 0
        for d in dTable:
            if ADVANCED_ONLY == False or (
                ADVANCED_ONLY == True and d["analysis"] == "advanced"
            ):
                if CRITICAL_ONLY == False or (
                    CRITICAL_ONLY == True and d["critical"] == True
                ):
                    if d["is_l3"] | SAVEL2:
                        w += 1
                        d["mod_time"] = datetime.datetime.fromtimestamp(
                            d["mod_time"] / 1000.0
                        )
                        d["user_mod_time"] = datetime.datetime.fromtimestamp(
                            d["user_mod_time"] / 1000.0
                        )
                        d["discover_time"] = datetime.datetime.fromtimestamp(
                            d["discover_time"] / 1000.0
                        )
                        csvwriter.writerow(list(d.values()))
                    else:
                        s += 1
                else:
                    s += 1
            else:
                s += 1
        print(" - Wrote %d devices, skipped %d devices " % (w, s))
