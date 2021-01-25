# COPYRIGHT 2021 BY EXTRAHOP NETWORKS, INC.
#
# This file is subject to the terms and conditions defined in
# file 'LICENSE', which is part of this source code package.

#!/usr/bin/python3

import os
import requests
import csv

SYSTEM_LIST = "systems.csv"

# Retrieve URLs, API keys, and firmware file paths
systems = []
with open(SYSTEM_LIST, "rt", encoding="ascii") as f:
    reader = csv.reader(f)
    for row in reader:
        system = {"host": row[0], "api_key": row[1], "firmware": row[2]}
        systems.append(system)


def uploadFirmware(host, api_key, firmware):
    """
    Method that uploads firmware to an ExtraHop system.

        Parameters:
            host (str): The IP address or hostname of the ExtraHop system
            api_key (str): An API key on the ExtraHop system
            firmware (str): The path of the firmware .tar file

        Returns:
            bool: Indicates whether the upload was successful
    """
    headers = {
        "Authorization": "ExtraHop apikey=%s" % api_key,
        "Content-Type": "application/vnd.extrahop.firmware",
    }
    url = host + "api/v1/extrahop/firmware"
    file_path = os.path.join(firmware)
    data = open(file_path, "rb")
    r = requests.post(url, data=data, headers=headers)
    if r.status_code == 201:
        print("Uploaded firmware to " + host)
        return True
    else:
        print("Failed to upload firmware to " + host)
        print(r.text)
        return False


# Function that upgrades firmware on system
def upgradeFirmware(host, api_key):
    """
    Method that upgrades firmware on an ExtraHop system

        Parameters:
            host (str): The IP address or hostname of the ExtraHop system
            api_key (str): An API key on the ExtraHop system

        Returns:
            bool: Indicates whether the upgrade was successful
    """
    headers = {"Authorization": "ExtraHop apikey=%s" % api_key}
    url = host + "api/v1/extrahop/firmware/latest/upgrade"
    r = requests.post(url, headers=headers)
    print(r.status_code)
    if r.status_code == 202:
        print("Upgraded firmware on " + host)
        return True
    else:
        print("Failed to upgrade firmware on " + host)
        print(r.text)
        return False


# Upgrade firmware for each system
for system in systems:
    host = system["host"]
    api_key = system["api_key"]
    firmware = system["firmware"]
    upload_success = uploadFirmware(host, api_key, firmware)
    if upload_success:
        upgradeFirmware(host, api_key)
