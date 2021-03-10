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
GROUPS_FILE = "user_groups.json"


def updateMembers(group, members):
    """
    Method that updates the membership of a user group.

        Parameters:
            group (dict): The group metadata
            members (dict): The members of the group

        Returns:
            str: Indicates whether the request was successful
    """
    url = HOST + "/api/v1/usergroups/" + group["id"] + "/members"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": "ExtraHop apikey=%s" % API_KEY,
    }
    r = requests.put(url, headers=headers, data=json.dumps(members))
    if r.status_code == 204:
        return "success"
    else:
        return r.json


def getSamlNames(members, user_map, remote_users):
    """
    Method that replaces old remote usernames with new SAML usernames.

        Parameters:
            members (dict): The members of a user group
            user_map (list): User metadata
            remote_users (list): A list of remote user names

        Returns:
            members (dict): The members of a user group
    """
    users = members["users"]
    for user in users:
        if user in remote_users:
            userIndex = remote_users.index(user)
            saml_name = user_map[userIndex]["saml_username"]
            members["users"][saml_name] = members["users"].pop(user)
    return members


# Create a list of deleted remote users
remote_users = []
with open(USER_MAP_FILE) as json_file:
    user_map = json.load(json_file)
    for user in user_map:
        remote_users.append(user["remote_username"])

with open(GROUPS_FILE) as json_file:
    groups = json.load(json_file)

# Create list of local groups with remote users
to_do = []
for group in groups:
    try:
        members = group["members"]["users"]
        for member in members:
            if member in remote_users:
                to_do.append(group)
                break
    except:
        continue
groups = to_do

# Update group membership
success = []
fail = []
for group in groups:
    members = group["members"]
    members = getSamlNames(members, user_map, remote_users)
    updated = updateMembers(group, members["users"])
    if updated == "success":
        success.append({"group": group, "users": members["users"]})
    else:
        fail.append([group, updated])

# Print out results of script
if success:
    print("Successfully updated membership of the following groups:")
    for update in success:
        print(update["group"]["name"])
        print("    Members:")
        for user in update["users"]:
            print("        " + user)
        print("")

if fail:
    print("Failed to update ownership of the following groups:")
    for failure in fail:
        print("    " + failure[0]["name"])
        print("    " + str(failure[1]))
        print("")

if success:
    with open(GROUPS_FILE, "w") as outfile:
        json.dump(groups, outfile)
