# COPYRIGHT 2021 BY EXTRAHOP NETWORKS, INC.
#
# This file is subject to the terms and conditions defined in
# file 'LICENSE', which is part of this source code package.

#!/usr/bin/python3

import json
import requests
import os

# Retrieves the IP address or hostname of the ExtraHop system from an environment variable.
HOST = os.environ['EXTRAHOP_HOST']

# Retrieves the API key from an environment variable.
API_KEY = os.environ['EXTRAHOP_API_KEY']

# The type of customization metadata to retrieve.
#     The following values are valid: 'dashboards', 'activitymaps'
OBJECT_TYPE = "dashboards"

# The name of the JSON file to save customization metadata in.
#     The following values are valid: 'dashboards', 'activitymaps'
OUTPUT_FILE = "dashboards.json"

headers = {"Authorization": "ExtraHop apikey=%s" % API_KEY}


def getObjects():
    """
    Method that retrieves metadata for every object.

        Returns:
            list: A list of each object
    """
    url = HOST + "/api/v1/" + OBJECT_TYPE
    r = requests.get(url, headers=headers, verify=False)
    return r.json()


# Function that retrieves sharing settings for a specified object ID
def getSharing(object_id):
    """
    Method that retrieves sharing settings for an object.

        Parameters:
            object_id (str): The ID of the object

        Returns:
            dict: The sharing settings of the object
    """
    url = HOST + "/api/v1/" + OBJECT_TYPE + "/" + str(object_id) + "/sharing"
    r = requests.get(url, headers=headers, verify=False)
    if r.status_code == 200:
        return r.json()
    else:
        print(
            "Unable to retrieve sharing information for object ID "
            + str(object_id)
        )
        print(r.status_code)
        print(r.text)
        return None


eh_objects = getObjects()
for eh_object in eh_objects:
    object_id = eh_object["id"]
    eh_object["sharing"] = getSharing(object_id)

with open(OUTPUT_FILE, "w") as outfile:
    json.dump(eh_objects, outfile)
