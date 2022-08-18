#!/usr/bin/python3.8

# COPYRIGHT 2022 BY EXTRAHOP NETWORKS, INC.
#
# This file is subject to the terms and conditions defined in
# file 'LICENSE', which is part of this source code package.
import argparse
import csv
import requests
import util

from urllib.parse import urlunparse

parser = argparse.ArgumentParser(description="Retrieve Network Locality Entries")
parser.add_argument("host", type=str, help="The hostname of the console, sensor, or Reveal(x) 360 API.")
parser.add_argument(
    "--output",
    "-o",
    type=str,
    default="localities.csv",
    help="The filename of the CSV file that output is saved to.",
)
util.add_api_args(parser)
args = parser.parse_args()

# Retrieve network localities
url = urlunparse(("https", args.host, "/api/v1/networklocalities", "", "", ""))
headers = {
    "Accept": "application/json",
    "Authorization": util.get_auth_header(args)
}

rsp = requests.get(url, headers=headers)
localities = rsp.json()


def get_name(locality):
    """
    After 9.0, a unique name is required for network locality names.

    On 9.0+ appliances, use the network locality name configured on the
    appliance.

    Otherwise, automatically generate a name for the network locality entry.
    """
    if (name := locality.get("name")) is not None:
        return name

    external_str = "External" if locality["external"] else "Internal"
    auto_name = f"[auto]: {external_str} - {locality['network']}"
    # If the generated name is longer than 40 characters, truncate the name.
    # Locality names cannot be longer than 40 characters.
    if len(auto_name) > 40:
        trunc_name = auto_name[:40]
        print(
            f"Warning: {auto_name} is greater than 40 characters. The "
            f"name is truncated to {trunc_name} in the CSV output file."
        )
        auto_name = trunc_name
    return auto_name


def get_networks(locality):
    """
    After 9.0, network locality entries can contain more than one network.
    """

    if (networks := locality.get("networks")) is not None:
        return ("|").join(networks)

    return locality["network"]


# Write network localities to CSV file
csv_headers = ("networks", "external", "description", "name")
with open(args.output, "w") as output:
    csv_writer = csv.writer(output)
    csv_writer.writerow(csv_headers)

    for locality in localities:
        networks = get_networks(locality)
        row = [networks]

        row.append(locality.get("external"))
        row.append(locality.get("description"))

        name = get_name(locality)
        row.append(name)

        csv_writer.writerow(row)

print("Successfully downloaded network localities.")
