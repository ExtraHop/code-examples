#!/usr/bin/python3

# COPYRIGHT 2021 BY EXTRAHOP NETWORKS, INC.
#
# This file is subject to the terms and conditions defined in
# file 'LICENSE', which is part of this source code package.

import json
import requests
import os

# Retrieves the IP address or hostname of the ExtraHop system from an environment variable.
HOST = os.environ['EXTRAHOP_HOST']

# Retrieves the API key from an environment variable.
API_KEY = os.environ['EXTRAHOP_API_KEY']


USER_MAP_FILE = "user_map.json"
# Function that deletes a user
def deleteUser(local_user, saml_user):
    """
    Method that deletes a user account.

        Parameters:
            local_user (str): The name of the temporary local user to delete
            saml_user (str): The name of the SAML user to transfer customizations to

        Returns:
            str: Indicates whether the request was successful
    """
    url = HOST + "/api/v1/users/" + local_user + "?dest_user=" + saml_user
    headers = {"Authorization": "ExtraHop apikey=%s" % API_KEY}
    r = requests.delete(url, headers=headers)
    if r.status_code == 204:
        return "success"
    else:
        return r.json()


# Create a list of remote users
local_users = {}
with open(USER_MAP_FILE) as json_file:
    user_map = json.load(json_file)
    for user in user_map:
        local_users[user["local_username"]] = user["saml_username"]

# Delete remote user accounts
success = []
fail = []
for user in local_users:
    updated = deleteUser(user, local_users[user])
    if updated == "success":
        success.append(user)
    else:
        fail.append([user, updated])

# Print out results of script
if success:
    print("Successfully deleted the following remote user accounts:")
    for update in success:
        print("    " + update)

if fail:
    print("Failed to delete the following remote user accounts:")
    for failure in fail:
        print("    " + failure[0])
        print("    " + str(failure[1]))
        print("")
