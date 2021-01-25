# COPYRIGHT 2021 BY EXTRAHOP NETWORKS, INC.
#
# This file is subject to the terms and conditions defined in
# file 'LICENSE', which is part of this source code package.

#!/usr/bin/python3

import json
import requests
import unicodecsv as csv

# The IP address or hostname of the ExtraHop system.
HOST = "extrahop.example.com"
# The API key.
API_KEY = "123456789abcdefghijklmnop"
# The file that output is written to.
FILENAME = "records.csv"
# The maximum number of records to retrieve at a time.
LIMIT = 1000
# The record query parameters.
QUERY = {
    "from": 1586273860000,
    "until": 1586273860500,
    "limit": LIMIT,
    "filter": {
        "field": "ex.isSuspicious",
        "operator": "=",
        "operand": {"type": "boolean", "value": "true"},
    },
    "sort": [{"direction": "asc", "field": "ipaddr"}],
}
# The record fields that are written to the CSV output file.
COLUMNS = [
    "timestamp",
    "sender",
    "senderAddr",
    "senderPort",
    "receiver",
    "receiverAddr",
    "receiverPort",
    "age",
    "proto",
    "l7proto",
    "bytes",
    "pkts",
    "rto",
    "ex",
]


def recordQuery(query):
    """
    Method that queries records from the ExtraHop system.

        Parameters:
            query (dict): The record query parameters

        Returns:
            dict: The records that matched the query parameters
    """
    url = HOST + "/api/v1/records/search"
    headers = {"Authorization": "ExtraHop apikey=%s" % API_KEY}
    r = requests.post(url, headers=headers, data=json.dumps(query))
    try:
        return json.loads(r.text)
    except:
        print("Record query failed")
        print(r.text)
        print(r.status_code)


# Query records
response = recordQuery(QUERY)
total = response["total"]
records = response["records"]
offset = LIMIT
print("Retrieved " + str(len(records)) + " out of " + str(total) + " records")
while total > offset:
    QUERY["offset"] = offset
    response = recordQuery(QUERY)
    new_records = response["records"]
    records = records + new_records
    offset = offset + LIMIT
    print(
        "Retrieved " + str(len(records)) + " out of " + str(total) + " records"
    )

# Simplify and format records for CSV
table = []
for record in records:
    row = {}
    fields = record["_source"]
    for column in COLUMNS:
        try:
            value = fields[column]
            # Retrieve isSuspicious field from ex object
            if column == "ex":
                try:
                    row["isSuspicious"] = value["isSuspicious"]
                except:
                    row[column] = value
            # Concatenate values returned as lists
            elif type(value) is list:
                row[column] = " ".join(value)
            # Retrieve values from dict objects
            elif type(value) is dict:
                try:
                    # If value is a list, concatenate list
                    if type(value["value"]) is list:
                        row[column] = " ".join(value["value"])
                    else:
                        row[column] = value["value"]
                except:
                    row[column] = value
            else:
                row[column] = value
        except:
            row[column] = ""
    table.append(row)

# Write records to CSV file
if len(table) > 0:
    with open(FILENAME, "wb") as csvfile:
        csvwriter = csv.writer(csvfile, encoding="utf-8")
        csvwriter.writerow(list(table[0].keys()))
        for row in table:
            csvwriter.writerow(list(row.values()))
