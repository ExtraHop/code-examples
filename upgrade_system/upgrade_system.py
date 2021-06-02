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
        has_jobs = checkForJobsEndpoint(self.host, self.api_key)
        upload_success = uploadFirmware(
            self.host, self.api_key, self.firmware, 0
        )
        if upload_success:
            job_location = upgradeFirmware(self.host, self.api_key, has_jobs)
            if has_jobs and job_location:
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
def upgradeFirmware(host, api_key, has_jobs):
    """
    Method that upgrades firmware on an ExtraHop system

        Parameters:
            host (str): The IP address or hostname of the ExtraHop system
            api_key (str): An API key on the ExtraHop system
            has_jobs (bool): Indicates whether the ExtraHop system has the /jobs endpoint

        Returns:
            str: The relative URL of the job status
    """
    headers = {"Authorization": "ExtraHop apikey=%s" % api_key}
    url = urlunparse(
        ("https", host, "/api/v1/extrahop/firmware/latest/upgrade", "", "", "")
    )
    r = requests.post(url, headers=headers)
    if r.status_code == 202 or r.status_code == 201:
        print("Started firmware upgrade process on " + host)
        if has_jobs:
            return r.headers["Location"]
        else:
            return None
    else:
        print("Failed to upgrade firmware on " + host)
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
                print(f"Upgrade for {host} timed out because the job took longer than expected.\nTo verify the progress of the upgrade, go to the ExtraHop system in a web browser.")
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


def checkForJobsEndpoint(host, api_key):
    """
    Method that finds whether the firmware running on a system
    has the /jobs endpoint by checking the firmware version.

        Parameters:
            host (str): The IP address or hostname of the ExtraHop system
            api_key (str): An API key on the ExtraHop system

        Returns:
            bool: Indicates whether the /jobs endpoint exists on the system
    """
    firmware_version = getFirmware(host, api_key)
    return version.parse(firmware_version) >= version.parse("8.5.0")


if __name__ == "__main__":
    for system in systems:
        host = system["host"]
        api_key = system["api_key"]
        firmware = system["firmware"]

        while threading.activeCount() > MAX_THREADS:
            time.sleep(0.1)

        u = Upgrader(host, api_key, firmware)
        u.start()
