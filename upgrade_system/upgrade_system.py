# COPYRIGHT 2021 BY EXTRAHOP NETWORKS, INC.
#
# This file is subject to the terms and conditions defined in
# file 'LICENSE', which is part of this source code package.

#!/usr/bin/python3

import os
import requests
import csv
from urllib.parse import urlunparse
import threading
import time

SYSTEM_LIST = "systems.csv"
# The maximum number of times to retry uploading the firmware
MAX_RETRIES = 5
# The maximum number of concurrent threads
MAX_THREADS = 2

# Retrieve URLs, API keys, and firmware file paths
systems = []
with open(SYSTEM_LIST, "rt", encoding="ascii") as f:
    reader = csv.reader(f)
    for row in reader:
        system = {"host": row[0], "api_key": row[1], "firmware": row[2]}
        systems.append(system)


class Upgrader(threading.Thread):
    """
    A class for a thread that upgrades an appliance.

    Attributes
    ----------
    host : str
        The IP address or hostname of the ExtraHop system
    api_key : str
        An API key on the ExtraHop system
    firmware : str
        The path of the firmware .tar file
    """

    def __init__(self, host, api_key, firmware):
        threading.Thread.__init__(self)
        self.host = host
        self.api_key = api_key
        self.firmware = firmware

    def run(self):
        print(f"Starting upgrade thread for {self.host}")
        upload_success = uploadFirmware(
            self.host, self.api_key, self.firmware, 0
        )
        if upload_success:
            upgradeFirmware(self.host, self.api_key)


def uploadFirmware(host, api_key, firmware, retry):
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
    url = urlunparse(("https", host, "/api/v1/extrahop/firmware", "", "", ""))
    file_path = os.path.join(firmware)
    data = open(file_path, "rb")
    r = requests.post(url, data=data, headers=headers)
    if r.status_code == 201:
        print("Uploaded firmware to " + host)
        return True
    elif retry < MAX_RETRIES:
        print("Failed to upload firmware to " + host)
        print("Retrying firmware upload")
        uploadFirmware(host, api_key, firmware, retry + 1)
    else:
        print("Firmware upload to " + host + " failed")
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
    url = urlunparse(
        ("https", host, "/api/v1/extrahop/firmware/latest/upgrade", "", "", "")
    )
    r = requests.post(url, headers=headers)
    print(r.status_code)
    if r.status_code == 202:
        print("Started firmware upgrade process on " + host)
        return True
    else:
        print("Failed to upgrade firmware on " + host)
        print(r.text)
        return False


if __name__ == "__main__":
    for system in systems:
        host = system["host"]
        api_key = system["api_key"]
        firmware = system["firmware"]

        while threading.activeCount() > MAX_THREADS:
            time.sleep(0.1)

        u = Upgrader(host, api_key, firmware)
        u.start()
