#!/usr/bin/python3

# COPYRIGHT 2021 BY EXTRAHOP NETWORKS, INC.
#
# This file is subject to the terms and conditions defined in
# file 'LICENSE', which is part of this source code package.

import base64
import json
import requests
import unicodecsv as csv
from urllib.parse import urlunparse

# The IP address or hostname of the ExtraHop appliance or RevealX 360 API
HOST = "extrahop.example.com"

# For RevealX 360 authentication
# The ID of the REST API credentials.
ID = "abcdefg123456789"
# The secret of the REST API credentials.
SECRET = "123456789abcdefg987654321abcdefg"
# A global variable for the temporary API access token (leave blank)
TOKEN = ""

# For self-managed appliance authentication
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

def getToken():
    """
    Method that generates and retrieves a temporary API access token for RevealX 360 authentication.

        Returns:
            str: A temporary API access token
    """
    auth = base64.b64encode(bytes(ID + ":" + SECRET, "utf-8")).decode("utf-8")
    headers = {
        "Authorization": "Basic " + auth,
        "Content-Type": "application/x-www-form-urlencoded",
    }
    url = urlunparse(("https", HOST, "/oauth2/token", "", "", ""))
    r = requests.post(
        url,
        headers=headers,
        data="grant_type=client_credentials",
    )
    try:
        return r.json()["access_token"]
    except:
        print(r.text)
        print(r.status_code)
        print("Error retrieving token from RevealX 360")
        sys.exit()

def getAuthHeader(force_token_gen=False):
    """
    Method that adds an authorization header for a request. For RevealX 360, adds a temporary access
    token. For self-managed appliances, adds an API key.

        Parameters:
            force_token_gen (bool): If true, always generates a new temporary API access token for the request

        Returns:
            str: The value for the header key in the headers dictionary
    """
    global TOKEN
    if API_KEY != "123456789abcdefghijklmnop" and API_KEY != "":
        return f"ExtraHop apikey={API_KEY}"
    else:
        if TOKEN == "" or force_token_gen == True:
            TOKEN = getToken()
        return f"Bearer {TOKEN}"

def recordQuery(query):
    """
    Method that queries records from the ExtraHop system.

        Parameters:
            query (dict): The record query parameters

        Returns:
            dict: The records that matched the query parameters
    """
    url = urlunparse(("https", HOST, "/api/v1/records/search", "", "", ""))
    headers = {
        "Authorization": getAuthHeader(),
        "Accept": "application/json",
    }
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
