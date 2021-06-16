#!/usr/bin/python3

# COPYRIGHT 2021 BY EXTRAHOP NETWORKS, INC.
#
# This file is subject to the terms and conditions defined in
# file 'LICENSE', which is part of this source code package.

import os
import requests
import csv
from urllib.parse import urlunparse
import threading
import time
from packaging import version

SYSTEM_LIST = "systems.csv"
# The maximum number of times to retry uploading the firmware
MAX_RETRIES = 5
# The maximum number of concurrent threads
MAX_THREADS = 2
# The number of minutes to wait between checking upgrade progress
# This variable is valid only for upgrades from firmware 8.5 and later
WAIT = 0.5

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
            job_location = upgradeFirmware(self.host, self.api_key)
            if job_location:
                monitorStatus(self.host, self.api_key, job_location)


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
    print(f"Uploading firmware to {host}")
    r = requests.post(url, data=data, headers=headers)
    if r.status_code == 201:
        print(f"Uploaded firmware to {host}")
        return True
    elif retry < MAX_RETRIES:
        print(f"Failed to upload firmware to {host}")
        print("Retrying firmware upload")
        uploadFirmware(host, api_key, firmware, retry + 1)
    else:
        print(f"Firmware upload to {host} failed")
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
            str: The relative URL of the job status
    """
    headers = {"Authorization": "ExtraHop apikey=%s" % api_key}
    url = urlunparse(
        ("https", host, "/api/v1/extrahop/firmware/latest/upgrade", "", "", "")
    )
    r = requests.post(url, headers=headers)
    if r.status_code == 202:
        print(f"Started firmware upgrade process on {host}")
        if "Location" in r.headers:
            return r.headers["Location"]
        else:
            return None
    else:
        print(f"Failed to upgrade firmware on {host}")
        print(r.status_code)
        return None


def monitorStatus(host, api_key, job_location):
    """
    Method that periodically retrieves the status of a job until the job
    is completed.

        Parameters:
            host (str): The IP address or hostname of the ExtraHop system
            api_key (str): An API key on the ExtraHop system
            job_location (str): The relative URL of the job status
    """
    headers = {"Authorization": "ExtraHop apikey=%s" % api_key}
    url = urlunparse(("https", host, job_location, "", "", ""))
    while True:
        # Catch connection errors
        try:
            r = requests.get(url, headers=headers)
        except requests.exceptions.ConnectionError:
            print(f"Connection refused by {host}")
            time.sleep(WAIT * 60)
            continue
        if r.status_code == 200:
            parsed_resp = r.json()
            status = parsed_resp["status"]
            if status == "DONE":
                print(f"Upgrade for {host} is {status}.")
                return
            elif status == "FAILED":
                print(f"Upgrade for {host} {status}.")
                return
            elif status == "TIMEOUT":
                print(
                    f"Upgrade for {host} timed out because the job took longer than expected.\nTo verify the progress of the upgrade, go to the ExtraHop system in a web browser."
                )
                return
            else:
                print(f"Upgrade for {host} is {status}.")
        else:
            print(f"Failed to retrieve status for upgrade on {host}.")
            print(r.status_code)
            try:
                print(r.json())
            except:
                pass
        time.sleep(WAIT * 60)


def getFirmware(host, api_key):
    """
    Method that retrieves the version of firmware running on
    the ExtraHop system.

        Parameters:
            host (str): The IP address or hostname of the ExtraHop system
            api_key (str): An API key on the ExtraHop system

        Returns:
            str: The firmware version
    """
    headers = {"Authorization": "ExtraHop apikey=%s" % api_key}
    url = urlunparse(("https", host, "/api/v1/extrahop/", "", "", ""))
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        parsed_resp = r.json()
        return parsed_resp["version"]
    else:
        print(f"Failed to retrieve firmware version from {host}")
        print(r.status_code)
        return "8.4.0"


if __name__ == "__main__":
    for system in systems:
        host = system["host"]
        api_key = system["api_key"]
        firmware = system["firmware"]

        while threading.activeCount() > MAX_THREADS:
            time.sleep(0.1)

        u = Upgrader(host, api_key, firmware)
        u.start()
