#!/usr/bin/python3

# COPYRIGHT 2021 BY EXTRAHOP NETWORKS, INC.
#
# This file is subject to the terms and conditions defined in
# file 'LICENSE', which is part of this source code package.

import requests
import csv
from urllib.parse import urlunparse
import threading
import time
import json
import argparse

SYSTEM_LIST = "systems.csv"


def parse_arguments():
    """
    Function that parses command line arguments.

        Returns:
            argparse.Namespace: An object containing the argument values
    """
    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        "--max-threads",
        dest="max_threads",
        default=2,
        type=int,
        help="The maximum number of concurrent threads",
    )
    argparser.add_argument(
        "--wait",
        dest="wait",
        default=0.5,
        type=float,
        help="The number of minutes to wait between checking upgrade progress",
    )
    return argparser.parse_args()


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
        The URL to retrieve the firmware from
    wait : float
        The number of minutes to wait between checking upgrade progress
    """

    def __init__(self, host, api_key, firmware, wait):
        threading.Thread.__init__(self)
        self.host = host
        self.api_key = api_key
        self.firmware = firmware
        self.wait = wait

    def run(self):
        print(f"Starting upgrade thread for {self.host}")
        job_location = self._upgradeFirmware()
        if job_location:
            self._monitorStatus(job_location, "Firmware upgrade")

    def _upgradeFirmware(self):
        """
        Method that downloads and upgrades firmware on an ExtraHop system.

            Returns:
                str: The relative URL of the job status
        """
        headers = {"Authorization": "ExtraHop apikey=%s" % self.api_key}
        url = urlunparse(
            (
                "https",
                self.host,
                "/api/v1/extrahop/firmware/download/url",
                "",
                "",
                "",
            )
        )
        data = {"firmware_url": self.firmware, "upgrade": True}
        r = requests.post(url, json=data, headers=headers)
        if r.status_code == 202:
            print(f"Started firmware upgrade process on {self.host}")
            if "Location" in r.headers:
                return r.headers["Location"]
            else:
                return None
        else:
            print(f"Failed to upgrade firmware on {self.host}")
            print(r.status_code)
            try:
                print(r.json())
            except:
                pass
            return None

    def _monitorStatus(self, job_location, job_name="Job"):
        """
        Method that periodically retrieves the status of a job until the job
        is completed.

            Parameters:
                job_location (str): The relative URL of the job status

            Returns:
                bool: Indicates whether the job completed successfully
        """
        headers = {"Authorization": "ExtraHop apikey=%s" % self.api_key}
        url = urlunparse(("https", self.host, job_location, "", "", ""))
        step_number = None
        total_steps = None
        step_description = None
        while True:
            # Catch connection errors
            try:
                r = requests.get(url, headers=headers)
            except requests.exceptions.ConnectionError:
                print(f"Connection refused by {self.host}")
                time.sleep(self.wait * 60)
                continue
            if r.status_code == 200:
                parsed_resp = r.json()
                status = parsed_resp["status"]
                if status == "DONE":
                    print(f"{job_name} for {self.host} is {status}.")
                    return True
                elif status == "FAILED":
                    print(f"{job_name} for {self.host} {status}.")
                    print(json.dumps(parsed_resp, indent=4))
                    return False
                elif status == "TIMEOUT":
                    print(
                        f"{job_name} for {self.host} timed out because the job took longer than expected."
                    )
                    return False
                else:
                    try:
                        step_number = parsed_resp["step_number"]
                        total_steps = parsed_resp["total_steps"]
                        step_description = parsed_resp["step_description"]
                    except:
                        pass
                    print(f"{job_name} for {self.host} is {status}.")
                    if step_number:
                        print(f"    Step {step_number} of {total_steps}: {step_description}")
            else:
                print(
                    f"Failed to retrieve status for {job_name} on {self.host}."
                )
                print(r.status_code)
                try:
                    print(r.json())
                except:
                    pass
            time.sleep(self.wait * 60)


if __name__ == "__main__":
    args = parse_arguments()
    max_threads = args.max_threads
    wait = args.wait
    # Retrieve appliance URLs, API keys, and firmware URLs
    systems = []
    with open(SYSTEM_LIST, "rt", encoding="ascii") as f:
        reader = csv.reader(f)
        for row in reader:
            system = {"host": row[0], "api_key": row[1], "firmware": row[2]}
            systems.append(system)

    for system in systems:
        host = system["host"]
        api_key = system["api_key"]
        firmware = system["firmware"]

        while threading.activeCount() > max_threads:
            time.sleep(0.1)

        u = Upgrader(host, api_key, firmware, wait)
        u.start()
