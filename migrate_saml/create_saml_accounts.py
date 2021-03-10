# COPYRIGHT 2021 BY EXTRAHOP NETWORKS, INC.
#
# This file is subject to the terms and conditions defined in
# file 'LICENSE', which is part of this source code package.

#!/usr/bin/python3

import json
import requests
import csv
import sys
import os

# The IP address or hostname of the ExtraHop system. Set via OS env variable.
# If desired, replace with hardcoded value, e.g. HOST = "https://extrahop.example.com"
HOST = os.environ['EXTRAHOP_HOST']

# The API key generated from the ExtraHop system. Set via OS env variable.
# If desired, replace with hardcoded value, e.g. API_KEY = "123456789abcdefghijklmnop"
API_KEY = os.environ['EXTRAHOP_API_KEY']

# Determines whether SAML account names are retrieved from a CSV file.
READ_CSV_FILE = False
# The name of the CSV file that SAML account names are retrieved from if READ_CSV_FILE is set to True.
CSV_FILE = "remote_to_saml.csv"

USER_FILE = "user_map.json"

csv_mapping = {}
if READ_CSV_FILE:
    with open(CSV_FILE, "rt", encoding="ascii") as f:
        reader = csv.reader(f)
        for row in reader:
            csv_mapping[row.pop()] = row.pop()


def generateName(name):
    """
    Method that returns the name of the SAML user account for a remote user account.

        Parameters:
            name (str): The name of the remote user account

        Returns:
            str: The name of the SAML user account
    """
    if csv_mapping:
        if name in csv_mapping:
            return csv_mapping[name]
        else:
            print("Error: Specified user " + name + " not found in " + CSV_FILE)
            sys.exit()
    else:
        return name + "@extrahop.com"


# Function that creates a SAML account for the specified user
def createUser(new_name, user):
    """
    Method that creates a SAML user account on the ExtraHop system.

        Parameters:
            new_name (str): The name of the SAML user account
            user (dict): Metadata about the remote user account

        Returns:
            r (Response): The response from the ExtraHop system
    """
    url = HOST + "/api/v1/users"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": "ExtraHop apikey=%s" % API_KEY,
    }
    user_params = {
        "username": new_name,
        "enabled": user["enabled"],
        "name": user["name"],
        "type": "remote",
    }
    r = requests.post(url, headers=headers, data=json.dumps(user_params))
    return r


with open(USER_FILE) as json_file:
    user_map = json.load(json_file)

failed = []
for user in user_map:
    username = user["remote_username"]
    new_name = generateName(username)
    r = createUser(new_name, user)
    if r.status_code == 201:
        user["saml_username"] = new_name
        print(
            "Successfully created new user account for "
            + username
            + ": "
            + new_name
        )
    else:
        failed.append([username, r.status_code, r.text])

if failed:
    print("")
    print(
        "Failed to create duplicate local user accounts for the following users:"
    )
    for error in failed:
        print("")
        for message in error:
            print(message)

with open(USER_FILE, "w") as outfile:
    json.dump(user_map, outfile)
