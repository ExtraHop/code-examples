# COPYRIGHT 2021 BY EXTRAHOP NETWORKS, INC.
#
# This file is subject to the terms and conditions defined in
# file 'LICENSE', which is part of this source code package.

#!/usr/bin/python3

import json
import requests
import sys

# The IP address or hostname of the ExtraHop system.
HOST = "https://extrahop.example.com"
# The API key generated from the ExtraHop system.
API_KEY = "ac09e68cf6b5499697fe93d3930e41ed"
# The type of customization to transfer.
#     The following values are valid: 'dashboards', 'activitymaps', 'reports'
OBJECT_TYPE = "dashboards"
# The name of the JSON file that includes the customization metadata.
#     The following values are valid: 'dashboards.json', 'activity_maps.json', 'reports.json'
OBJECT_FILE = "dashboards.json"


USER_MAP_FILE = "user_map.json"


def sharedWithRemote(eh_object, remote_users, user_map):
    """
    Method that checks to see if the specified object was shared with
    deleted remote users. If so, returns a sharing dictionary
    with the SAML user account names.

        Parameters:
            eh_object (dict): Object metadata
            remote_users (list): The names of deleted remote user accounts
            user_map (list): User metadata

        Returns:
            updated (dict): A sharing dictionary with SAML user account names
    """
    sharing = eh_object["sharing"]
    updated = {"users": {}}
    if sharing != None:
        users_shared = sharing["users"]
        for user in users_shared:
            if user in remote_users:
                user_index = remote_users.index(user)
                saml_name = user_map[user_index]["saml_username"]
                updated["users"][saml_name] = sharing["users"][user]
    if updated["users"]:
        return updated
    else:
        return None


def updateSharing(eh_object, remoteShares):
    """
    Method that updates sharing options for a specified object.

        Parameters:
            eh_object (dict): Object metadata
            remoteShares (dict): A sharing dictionary with SAML user account names

        Returns:
            str: Indicates whether the request was successful
    """
    url = (
        HOST
        + "/api/v1/"
        + OBJECT_TYPE
        + "/"
        + str(eh_object["id"])
        + "/sharing"
    )
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": "ExtraHop apikey=%s" % API_KEY,
    }
    r = requests.patch(url, headers=headers, data=json.dumps(remoteShares))
    if r.status_code == 204:
        return "success"
    else:
        return r.json()


# Create a list of deleted remote users
remote_users = []
with open(USER_MAP_FILE) as json_file:
    user_map = json.load(json_file)
    for user in user_map:
        remote_users.append(user["remote_username"])

# Extract object metadata from JSON file
with open(OBJECT_FILE) as json_file:
    eh_objects = json.load(json_file)

success = []
fail = []
# Restore sharing options for deleted remote users
for eh_object in eh_objects:
    remoteShares = sharedWithRemote(eh_object, remote_users, user_map)
    if remoteShares:
        updated = updateSharing(eh_object, remoteShares)
        if updated == "success":
            success.append(
                {"eh_object": eh_object, "remoteShares": remoteShares}
            )
        else:
            fail.append([eh_object, updated])

# Print out results of script
if success:
    print(
        "Successfully updated sharing options the following "
        + OBJECT_TYPE
        + ":"
    )
    for update in success:
        print(update["eh_object"]["name"])
        print(update["remoteShares"])
        print("")

if fail:
    print("Failed to update ownership of the following " + OBJECT_TYPE + ":")
    for failure in fail:
        print("    " + failure[0]["name"])
        print("    " + str(failure[1]))
        print("")
