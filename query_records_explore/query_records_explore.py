#!/usr/bin/python3

# COPYRIGHT 2021 BY EXTRAHOP NETWORKS, INC.
#
# This file is subject to the terms and conditions defined in
# file 'LICENSE', which is part of this source code package.

import json
import requests
import unicodecsv as csv
from urllib.parse import urlunparse

# The IP address or hostname of the ExtraHop system. Note that this hostname is not the hostname of the connected Explore appliance that the records are stored on.
HOST = "extrahop.example.com"
# The API key.
API_KEY = "123456789abcdefghijklmnop"
# The file that output is written to.
FILENAME = "records.csv"
# If the record query matches more than 100 records, the amount of time after the initial query that the remaining records can be retrieved from the system.
TIME_LIMIT = "1m"
# The record query parameters.
QUERY = {
    "context_ttl": TIME_LIMIT,
    "from": "-30m",
    "filter": {
        "field": "ex.isSuspicious",
        "operator": "=",
        "operand": {"type": "boolean", "value": "true"},
    },
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
    Method that performs an initial record query on an ExtraHop system.

        Parameters:
            query (dict): The record query parameters

        Returns:
            dict: The records that matched the query parameters
    """
    url = urlunparse(("https", HOST, "/api/v1/records/search", "", "", ""))
    headers = {"Authorization": "ExtraHop apikey=%s" % API_KEY}
    r = requests.post(url, headers=headers, data=json.dumps(query))
    try:
        return json.loads(r.text)
    except:
        print("Record query failed")
        print(r.text)
        print(r.status_code)


# Method that retrieves remaining records from a record query
def continueQuery(cursor):
    """
    Method that retrieves remaining records from a record query.

        Parameters:
            cursor (str): The unique identifier of the cursor that specifies the next page of results in the query

        Returns:
            dict: The records on this page of the query results
    """
    url = urlunparse(("https", HOST, "/api/v1/records/cursor", "", "", ""))
    headers = {"Authorization": "ExtraHop apikey=%s" % API_KEY}
    query = {"cursor": cursor}
    r = requests.post(url, headers=headers, data=json.dumps(query))
    try:
        return json.loads(r.text)
    except:
        print("Record query failed")
        print(r.text)
        print(r.status_code)


# Query records
response = recordQuery(QUERY)
records = response["records"]
if "cursor" in response:
    response_cursor = response["cursor"]
    retrieved = len(records)
    while retrieved > 0:
        print(
            "Retrieved  "
            + str(len(records))
            + " of "
            + str(response["total"])
            + " total records"
        )
        response = continueQuery(response_cursor)
        newRecords = response["records"]
        retrieved = len(newRecords)
        records = records + newRecords

print("Total records retrieved = " + str(len(records)))

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


# Write records to csv
with open(FILENAME, "wb") as csvfile:
    csvwriter = csv.writer(csvfile, encoding="utf-8")
    csvwriter.writerow(list(table[0].keys()))
    for row in table:
        csvwriter.writerow(list(row.values()))
