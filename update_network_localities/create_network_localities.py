#!/usr/bin/python3.8

# COPYRIGHT 2022 BY EXTRAHOP NETWORKS, INC.
#
# This file is subject to the terms and conditions defined in
# file 'LICENSE', which is part of this source code package.
from typing import Dict, List, Union

import argparse
import csv
import requests
import sys
import util

from ipaddress import ip_network
from urllib.parse import urlunparse


def validate_and_transform_entry(entry: dict) -> dict:
    """
    Function that transforms data from the CSV file into a format that can be
    sent to the REST API.

    Parameters:
        entry (dict): The original data from the CSV row

    Returns:
        cleaned_entry (dict): The transformed data
    """
    cleaned_entry = {}
    cleaned_entry["name"] = entry.get("name", "")

    # Networks
    networks = entry.get("networks")
    try:
        nets = [ip_network(n, strict=False) for n in networks.split("|")]
    except Exception:
        raise Exception(
            f"Failed to convert network list: {networks}. Check that they are "
            "formatted as one or more valid IP addresses delimited by pipes"
        )
    cleaned_entry["networks"] = [str(n) for n in nets]

    external = entry.get("external", "")
    # The string "true" (case insensitive) is interpreted as true. All other
    # strings are interpreted as false.
    cleaned_entry["external"] = True if external.lower() == "true" else False

    cleaned_entry["description"] = entry.get("description", "")

    return cleaned_entry


parser = argparse.ArgumentParser(description="Create Network Locality Entries")
parser.add_argument(
    "host",
    type=str,
    help="The hostname of the console, sensor, or Reveal(x) 360 API.",
)
parser.add_argument(
    "--input",
    "-i",
    type=str,
    default="localities.csv",
    help="The path of the CSV file.",
)
parser.add_argument(
    "--group",
    "-g",
    type=str,
    choices=["description", "external"],
    default=None,
    help="Consolidates network localities based on the specified field. If two "
    "or more localities have the same value for the field in the CSV file, "
    "those localities are consolidated into a single locality on the target "
    "console, sensor, or Reveal(x) 360.",
)
util.add_api_args(parser)
args = parser.parse_args()

url = urlunparse(("https", args.host, "/api/v1/networklocalities", "", "", ""))
headers = {
    "Content-Type": "application/json",
    "Authorization": util.get_auth_header(args),
}

try:
    # Delete all network locality entries on the sensor or console
    rsp = requests.get(url, headers=headers)
    entries = rsp.json()
    for entry in entries:
        id = entry["id"]
        rsp = requests.delete(f"{url}/{id}", headers=headers)
    if entries:
        print(
            "Preparing for locality entry upload by deleting existing entries"
        )

    # Transform data from the CSV file into a format that can be sent to the
    # REST API
    valid_entries: List[Dict] = []
    with open(args.input, "r") as file:
        csv_file = csv.DictReader(file)

        for row in csv_file:
            try:
                cleaned_entry = validate_and_transform_entry(row)
            except Exception as e:
                print(e)
                sys.exit()
            valid_entries.append(cleaned_entry)

    # Combine entries by the specified group parameter
    if args.group:
        print(f"Grouping entries by '{args.group}' field")

        grouped: Dict[Union[str, bool], Dict] = dict()
        for entry in valid_entries:
            key = entry[args.group]
            if key in grouped:
                grouped[key]["networks"].extend(entry["networks"])
            else:
                grouped[key] = entry
            if (name := entry.get("name")) and not grouped[key]["name"]:
                grouped[key]["name"] = name
        valid_entries = list(grouped.values())

    # Create new network localities on the sensor or console
    for entry in valid_entries:
        rsp = requests.post(url, headers=headers, json=entry)
        if rsp.ok:
            print(f"Successfully uploaded entry {entry['name']}")
        else:
            print(f"Failed to upload entry {entry['name']}")
            print(f"{rsp.status_code}: {rsp.text}")
            sys.exit()

except KeyboardInterrupt:
    sys.exit()
