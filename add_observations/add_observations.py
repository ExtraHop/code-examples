# COPYRIGHT 2021 BY EXTRAHOP NETWORKS, INC.
#
# This file is subject to the terms and conditions defined in
# file 'LICENSE', which is part of this source code package.

#!/usr/bin/python3

import json
import csv
import time
import requests
from urllib.parse import urlunparse

# The IP address or hostname of the ExtraHop system.
HOST = "extrahop.example.com"
# The API key.
API_KEY = "123456789abcdefghijklmnop"
# The name of the CSV file.
CSV_FILE = "log.csv"
# The source of the observations.
SOURCE = "OpenVPN"

# The name of the column in the CSV file that specifies the IP addresses of the VPN clients on your internal network.
ASSOCIATED_IPADDR = "Real IP"
# The name of the column in the CSV file that specifies the external IP addresses assigned to the users on the public internet.
IPADDR = "VPN IP"
# The name of the column in the CSV file that specifies the time that the observation was created by the source.
TIMESTAMP = "Start Time"


def readCSV(associated_ipaddr, ipaddr, timestamp):
    """
    Method that extracts observations from a CSV file.

        Parameters:
            associated_ipaddr (str): The name of the column that specifies IP addresses of VPN clients
            ipaddr (str): The name of the column that specifies IP addresses of users on the public internet
            timestamp (str): The name of the column that specifies the observation creation time

        Returns:
            observations (list): A list of observation dictionaries
    """
    observations = []
    with open(CSV_FILE, "rt", encoding="ascii") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        for row in reader:
            observations.append(
                {
                    "associated_ipaddr": row[header.index(associated_ipaddr)],
                    "ipaddr": row[header.index(ipaddr)],
                    "timestamp": translateTime(row[header.index(timestamp)]),
                }
            )
    return observations


def translateTime(t):
    """
    Method that translates a formatted timestamp into epoch time.

        Parameters:
            t (str): The formatted timestamp

        Returns:
            str: The epoch time
    """
    pattern = "%m/%d/%y %H:%M:%S"
    return int(time.mktime(time.strptime(t, pattern)))


def makeObservations(observations):
    """
    Method that sends observations to the ExtraHop system

        Parameters:
            observations (list): A list of observation dictionaries

    """
    url = urlunparse(("https", HOST, "/api/v1/observations/associatedipaddrs", "", "", ""))
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": "ExtraHop apikey=%s" % API_KEY,
    }
    data = {"observations": observations, "source": SOURCE}
    r = requests.post(url, headers=headers, data=json.dumps(data))
    if r.status_code == 202:
        print(r.text)
    else:
        print("Observation upload failed")
        print(r.text)


observations = readCSV(ASSOCIATED_IPADDR, IPADDR, TIMESTAMP)
makeObservations(observations)
