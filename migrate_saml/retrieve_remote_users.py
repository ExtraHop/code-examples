#!/usr/bin/python3

# COPYRIGHT 2021 BY EXTRAHOP NETWORKS, INC.
#
# This file is subject to the terms and conditions defined in
# file 'LICENSE', which is part of this source code package.

import json
import requests
import sys
import os

# Retrieves the IP address or hostname of the ExtraHop system from an environment variable.
HOST = os.environ['EXTRAHOP_HOST']

# Retrieves the API key from an environment variable.
API_KEY = os.environ['EXTRAHOP_API_KEY']

OUTPUT_FILE = "user_map.json"
headers = {"Authorization": "ExtraHop apikey=%s" % API_KEY}


def getUsers():
    """
    Method that retrieves metadata for every user.

        Returns:
            list: List of dictionaries containing user metadata
    """
    url = HOST + "/api/v1/users"
    r = requests.get(url, headers=headers)
    return r.json()


# Function that checks for duplicate usernames
def checkDuplicates(u_list):
    """
    Method that finds duplicate usernames.

        Parameters:
            u_list (list): List of usernames

        Returns:
            s (list): List of duplicate usernames
    """
    checked = []
    duplicates = set()
    for user in u_list:
        for c in checked:
            if user.lower() == c.lower():
                duplicates.add(user)
                duplicates.add(c)
        checked.append(user)
    s = sorted(duplicates, key=str.lower)
    return s


users = getUsers()
user_map = []
u_list = []
for user in users:
    if user["type"] != "local":
        user["remote_username"] = user["username"]
        user_map.append(user)
        u_list.append(user["username"])

duplicates = checkDuplicates(u_list)
if duplicates:
    print("Error: The following duplicate remote usernames were found:")
    for user in duplicates:
        print("    " + user)
    print(
        "Local and SAML user accounts cannot share usernames, regardless of case. Rename or delete duplicates before continuing."
    )
    sys.exit()

with open(OUTPUT_FILE, "w") as outfile:
    json.dump(user_map, outfile)
