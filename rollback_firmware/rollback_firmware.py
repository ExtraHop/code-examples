#!/usr/bin/python3

# COPYRIGHT 2021 BY EXTRAHOP NETWORKS, INC.
#
# This file is subject to the terms and conditions defined in
# file 'LICENSE', which is part of this source code package.

import requests
import csv
import logging
import sys
from urllib.parse import urlunparse

SYSTEM_LIST = "systems.csv"


def getRollbackVersion(system):
    """
    Method that retrieves and displays which version of firmware is available for rollback.

        Parameters:
            system (dict): The object that contains the system host and api key

        Returns:
            bool: Indicates whether the firmware can be rolled back on the system
    """
    headers = {"Authorization": f"ExtraHop apikey={system['api_key']}"}
    url = urlunparse(
        (
            "https",
            system["host"],
            "/api/v1/extrahop/firmware/previous",
            "",
            "",
            "",
        )
    )

    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        print(
            f"{system['host']} will be rolled back to version {r.json()['version']}"
        )
        return True
    else:
        print(
            f"{system['host']} cannot be rolled back because {r.json()['error_message']}"
        )
        return False


def rollbackFirmware(system):
    """
    Method that rolls back firmware on an ExtraHop system.

        Parameters:
            system (dict): The object that contains the system host and api key
    """
    headers = {"Authorization": f"ExtraHop apikey={system['api_key']}"}
    url = urlunparse(
        (
            "https",
            system["host"],
            "/api/v1/extrahop/firmware/previous/rollback",
            "",
            "",
            "",
        )
    )
    r = requests.post(url, headers=headers)
    if r.status_code == 202:
        print(f"Started rollback process on {system['host']}")
    else:
        print(
            f"Failed to rollback firmware on {system['host']} because {r.json()['error_message']}"
        )


def main():
    # Retrieve URLs and API keys from CSV file
    systems = []
    with open(SYSTEM_LIST, "rt", encoding="ascii") as f:
        reader = csv.reader(f)
        for row in reader:
            system = {"host": row[0], "api_key": row[1]}
            systems.append(system)

    # Show which firmware versions will be rolled back to
    for system in systems:
        system["ready"] = getRollbackVersion(system)
    c = input("Do you want to continue? (y/n)")

    # Roll back firmware
    if c == "y" or c == "yes":
        for system in systems:
            if system["ready"] == False:
                continue
            else:
                rollbackFirmware(system)


if __name__ == "__main__":
    logging.basicConfig(
        format="%(message)s",
        handlers=[logging.StreamHandler(sys.stdout),],
        level=logging.INFO,
    )
    main()
