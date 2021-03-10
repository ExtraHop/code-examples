# COPYRIGHT 2021 BY EXTRAHOP NETWORKS, INC.
#
# This file is subject to the terms and conditions defined in
# file 'LICENSE', which is part of this source code package.

#!/usr/bin/python3

import json
import requests
import os

# The IP address or hostname of the ExtraHop system. Set via OS env variable.
# If desired, replace with hardcoded value, e.g. HOST = "https://extrahop.example.com"
HOST = os.environ['EXTRAHOP_HOST']

# The API key generated from the ExtraHop system. Set via OS env variable.
# If desired, replace with hardcoded value, e.g. API_KEY = "123456789abcdefghijklmnop"
API_KEY = os.environ['EXTRAHOP_API_KEY']


USER_MAP_FILE = "user_map.json"
# Function that deletes a user
def deleteUser(remote_user, saml_user):
    """
    Method that deletes a user account.

        Parameters:
            remote_user (str): The name of the remote user to delete
            saml_user (str): The name of the SAML user to transfer customizations to

        Returns:
            str: Indicates whether the request was successful
    """
    url = HOST + "/api/v1/users/" + remote_user + "?dest_user=" + saml_user
    headers = {"Authorization": "ExtraHop apikey=%s" % API_KEY}
    r = requests.delete(url, headers=headers)
    if r.status_code == 204:
        return "success"
    else:
        return r.json()


# Create a list of remote users
remote_users = {}
with open(USER_MAP_FILE) as json_file:
    user_map = json.load(json_file)
    for user in user_map:
        remote_users[user["remote_username"]] = user["saml_username"]

# Delete remote user accounts
success = []
fail = []
for user in remote_users:
    updated = deleteUser(user, remote_users[user])
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
