#!/usr/bin/python3

# COPYRIGHT 2022 BY EXTRAHOP NETWORKS, INC.
#
# This file is subject to the terms and conditions defined in
# file 'LICENSE', which is part of this source code package.

import requests
import csv
from urllib.parse import urlunparse
import threading
import time
import sys
import argparse
import json


# The system config list
SYSTEM_LIST = "systems.csv"


def parse_arguments():
    """
    Function that parses command line arguments.

        Returns:
            argparse.Namespace: An object containing the argument values
    """
    argparser = argparse.ArgumentParser()
    group = argparser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--latest-hotfix",
        dest="latest_hotfix",
        action="store_true",
        help="Upgrade to the latest version in the current release",
    )
    group.add_argument(
        "--latest-release",
        dest="latest_release",
        action="store_true",
        help="Upgrade to the latest version in the latest release",
    )
    group.add_argument(
        "--version",
        dest="version",
        help="Upgrade to the specified version",
    )
    argparser.add_argument(
        "--force",
        dest="force",
        action="store_true",
        help="Upgrade systems without prompting for confirmation",
    )
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


def getNextFirmware(host, api_key, firmware_target):
    """
    Function that retrieves the firmware version to upgrade the ExtraHop system to.

        Parameters:
            host (str): The IP address or hostname of the ExtraHop system
            api_key (str): An API key on the ExtraHop system
            firmware_target (str): The command-line argument that specifies the target firmware version

        Returns:
            n_firmware (str): The firmware version
    """
    url = urlunparse(
        ("https", host, "/api/v1/extrahop/firmware/next", "", "", "")
    )
    headers = {
        "Authorization": f"ExtraHop apikey={api_key}",
    }
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        n_firmware = parseReleases(r.json(), firmware_target, host)
        return n_firmware
    else:
        try:
            print(json.dumps(r.json()))
        except:
            pass
        raise RuntimeError(f"Failed to retrieve list of available versions from {host}. \nStatus code:{r.status_code}")


def parseReleases(releases, firmware_target, host):
    """
    Function that parses the list of firmware versions that you can upgrade the ExtraHop system to
    and selects the correct version based on the specified firmware_target.

        Parameters:
            releases (list): The list of releases that that you can upgrade the ExtraHop system to
            firmware_target (str): The command-line argument that specifies the target firmware version
            host (str): The IP address or hostname of the ExtraHop system

        Returns:
            version (str): The version to upgrade to
    """
    if not releases:
        return None
    if firmware_target == "latest-release":
        return releases[0]["versions"][0]
    elif firmware_target == "latest-hotfix":
        for release in releases:
            if release["current_release"] == True:
                return release["versions"][0]
        return None
    else:
        for release in releases:
            for version in release["versions"]:
                if firmware_target == version:
                    return version
        return None


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
        The firmware version to upgrade the ExtraHop system to
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
        download_job = self._downloadFirmware()
        if download_job:
            download_success = self._monitorStatus(
                download_job, "Firmware download"
            )
            if download_success:
                upgrade_job = self._upgradeFirmware()
                if upgrade_job:
                    upgrade_success = self._monitorStatus(
                        upgrade_job, "Upgrade"
                    )

    def _downloadFirmware(self):
        """
        Method that downloads firmware from ExtraHop Cloud Services to an ExtraHop system.

            Returns:
                str: The relative URL of the job status
        """
        headers = {"Authorization": "ExtraHop apikey=%s" % self.api_key}
        url = urlunparse(
            (
                "https",
                self.host,
                "/api/v1/extrahop/firmware/download/version",
                "",
                "",
                "",
            )
        )
        data = {"version": self.firmware}
        r = requests.post(url, json=data, headers=headers)
        if r.status_code == 202:
            print(f"Started firmware download process on {self.host}")
            if "Location" in r.headers:
                return r.headers["Location"]
            else:
                return None
        else:
            print(f"Firmware download to {self.host} failed")
            print(r.text)
            return None

    def _upgradeFirmware(self):
        """
        Method that upgrades firmware on an ExtraHop system

            Returns:
                str: The relative URL of the job status
        """
        headers = {"Authorization": "ExtraHop apikey=%s" % self.api_key}
        url = urlunparse(
            (
                "https",
                self.host,
                "/api/v1/extrahop/firmware/latest/upgrade",
                "",
                "",
                "",
            )
        )
        r = requests.post(url, headers=headers)
        if r.status_code == 202:
            print(f"Started firmware upgrade process on {self.host}")
            if "Location" in r.headers:
                return r.headers["Location"]
            else:
                return None
        else:
            print(f"Failed to upgrade firmware on {self.host}")
            print(r.status_code)
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
                    print(f"{job_name} for {self.host} is {status}.")
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
    target_firmware = ""
    force = False
    args = parse_arguments()
    if args.latest_hotfix:
        firmware_target = "latest-hotfix"
    elif args.latest_release:
        firmware_target = "latest-release"
    else:
        firmware_target = args.version
    if args.force:
        force = True
    max_threads = args.max_threads
    wait = args.wait
    systems = []
    no_upgrade = []
    with open(SYSTEM_LIST, "rt", encoding="ascii") as f:
        reader = csv.reader(f)
        for row in reader:
            system = {"host": row[0], "api_key": row[1]}
            system["next_firmware"] = getNextFirmware(
                system["host"], system["api_key"], firmware_target
            )
            if system["next_firmware"]:
                systems.append(system)
            else:
                no_upgrade.append(system)

    # Print systems that are already upgraded
    if no_upgrade:
        if firmware_target == "latest-hotfix":
            print(
                f"The following systems have already been upgraded to the latest hotfix:"
            )
        elif firmware_target == "latest-release":
            print(
                f"The following systems have already been upgraded to the latest release:"
            )
        else:
            print(
                f"The following systems cannot be upgraded to version {firmware_target}:"
            )
        for system in no_upgrade:
            print(f"    {system['host']}")

    # If there are no systems to upgrade, exit
    if not systems:
        sys.exit()

    # If force has not been specified, ask for confirmation before continuing
    if not force:
        print("The following systems will be upgraded:")
        for system in systems:
            print(f"    {system['host']}: {system['next_firmware']}")
        print("Do you want to continue?")
        c = input("y/n")
        if c.lower() != "y" and c.lower() != "yes":
            sys.exit()

    # Create an upgrade thread for each system
    for system in systems:
        while threading.activeCount() > max_threads:
            time.sleep(0.1)

        u = Upgrader(
            system["host"], system["api_key"], system["next_firmware"], wait
        )
        u.start()
