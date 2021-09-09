#!/usr/bin/python3

# COPYRIGHT 2021 BY EXTRAHOP NETWORKS, INC.
#
# This file is subject to the terms and conditions defined in
# file 'LICENSE', which is part of this source code package.

import json
import requests
from urllib.parse import urlunparse

# The IP address or hostname of the ExtraHop system.
HOST = "extrahop.example.com"
# The API key.
API_KEY = "123456789abcdefghijklmnop"
# The username of the current dashboard owner.
CURRENT = "marksmith"
# The username of the new dashboard owner.
NEW = "paulanderson"


def getDashboards():
    """
    Method that retrieves all dashboards from an ExtraHop system.

        Returns:
            list: The dashboards on the ExtraHop system
    """
    url = urlunparse(("https", HOST, "/api/v1/dashboards", "", "", ""))
    headers = {"Authorization": "ExtraHop apikey=%s" % API_KEY}
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        return r.json()
    else:
        print("Failed to retrieve dashboards")
        print(r.text)
        print(status_code)


def changeOwner(dashboard):
    """
    Method that changes the owner of a dashboard.

        Parameters:
            dashboard (dict): The dashboard dictionary
    """
    url = urlunparse(
        ("https", HOST, f"/api/v1/dashboards/{dashboard['id']}", "", "", "")
    )
    headers = {"Authorization": "ExtraHop apikey=%s" % API_KEY}
    data = {"owner": NEW}
    r = requests.patch(url, headers=headers, json=data)
    if r.status_code == 204:
        print(f"Switching owner of {dashboard['name']} from {CURRENT} to {NEW}")
    else:
        print(f"Failed to update owner of dashboard {dashboard['name']}")
        print(r.text)
        print(status_code)


def main():
    dashboards = getDashboards()
    for dashboard in dashboards:
        if dashboard["owner"] == CURRENT:
            changeOwner(dashboard)


if __name__ == "__main__":
    main()
