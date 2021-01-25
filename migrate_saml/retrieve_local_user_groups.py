# COPYRIGHT 2021 BY EXTRAHOP NETWORKS, INC.
#
# This file is subject to the terms and conditions defined in
# file 'LICENSE', which is part of this source code package.

#!/usr/bin/python3

import json
import requests

# The IP address or hostname of the ExtraHop system.
HOST = "https://extrahop.example.com"
# The API key generated from the ExtraHop system.
API_KEY = "123456789abcdefghijklmnop"


OUTPUT_FILE = "user_groups.json"
headers = {"Authorization": "ExtraHop apikey=%s" % API_KEY}


def getGroups():
    """
    Method that retrieves metadata for every user group.

        Returns:
            list: List of dictionaries containing user group metadata
    """
    url = HOST + "/api/v1/usergroups"
    r = requests.get(url, headers=headers)
    return r.json()


# Function that retrieves members of the specified group
def getMembers(group_id):
    """
    Method that retrieves the members of a user group.

        Parameters:
            group_id (str): The ID of the user group

        Returns:
            list: The list of group members
    """
    url = HOST + "/api/v1/usergroups/" + str(group_id) + "/members"
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        return r.json()
    else:
        print("Unable to retrieve members of group " + str(group_id))
        print(r.status_code)
        print(r.text)
        return None


groups = getGroups()
final_groups = []
for group in groups:
    if not group["is_remote"]:
        group_id = group["id"]
        group["members"] = getMembers(group_id)
        final_groups.append(group)

with open(OUTPUT_FILE, "w") as outfile:
    json.dump(final_groups, outfile)
