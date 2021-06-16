#!/usr/bin/python3

# COPYRIGHT 2021 BY EXTRAHOP NETWORKS, INC.
#
# This file is subject to the terms and conditions defined in
# file 'LICENSE', which is part of this source code package.

import http.client
import json
import csv
import time

# The IP address or hostname of the ExtraHop system.
HOST = "extrahop.example.com"
# The API key.
APIKEY = "123456789abcdefghijklmnop"

headers = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Authorization": "ExtraHop apikey=%s" % APIKEY,
}
body = r"""{
  "metric_category": "http_server",
  "metric_specs": [
    {
      "name": "rsp"
    }
  ],
  "object_type": "device",
  "object_ids": [
   14853
  ],
  "cycle": "1hr"
}"""

conn = http.client.HTTPSConnection(HOST)
conn.request("POST", "/api/v1/metrics", headers=headers, body=body)
resp = conn.getresponse()
parsed_resp = json.loads(resp.read())

output_file = "output.csv"
with open(output_file, "w") as csvfile:
    csvwriter = csv.writer(csvfile, dialect="excel")
    header = []
    v = 0
    for metric in parsed_resp["stats"][0]:
        header.append(metric)
    csvwriter.writerow(header)
    for metric in parsed_resp["stats"]:
        metric["time"] = time.strftime(
            "%Y-%m-%d %H:%M:%S", time.localtime(metric["time"] / 1000)
        )
        metric["values"] = str(metric["values"][0])
        v += 1
        csvwriter.writerow(list(metric.values()))
    print(
        "Extracted %s metrics from %s to %s"
        % (
            str(v),
            parsed_resp["stats"][0]["time"],
            parsed_resp["stats"][-1]["time"],
        )
    )
