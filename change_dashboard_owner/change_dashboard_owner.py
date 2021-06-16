#!/usr/bin/python3

# COPYRIGHT 2021 BY EXTRAHOP NETWORKS, INC.
#
# This file is subject to the terms and conditions defined in
# file 'LICENSE', which is part of this source code package.

import http.client
import json

# The IP address or hostname of the ExtraHop system.
HOST = "extrahop.example.com"
# The API key.
APIKEY = "123456789abcdefghijklmnop"
# The username of the current dashboard owner.
CURRENT = "marksmith"
# The username of the new dashboard owner.
NEW = "paulanderson"

headers = {
    "Accept": "application/json",
    "Authorization": "ExtraHop apikey=%s" % APIKEY,
}
conn = http.client.HTTPSConnection(HOST)
conn.request("GET", "/api/v1/dashboards", headers=headers)
resp = conn.getresponse()
parsed_resp = json.loads(resp.read())

for dashboard in parsed_resp:
    if dashboard["owner"] == CURRENT:
        print(
            "Dashboard {id} owned by " + CURRENT + "."
            " Switching ownership...".format(id=dashboard["id"])
        )
        config = {"owner": NEW}
        conn.request(
            "PATCH",
            "/api/v1/dashboards/{id}".format(id=dashboard["id"]),
            json.dumps(config),
            headers=headers,
        )
        resp = conn.getresponse()
        resp.read()
