#!/usr/bin/python3

# COPYRIGHT 2026 BY EXTRAHOP NETWORKS, INC.
#
# This file is subject to the terms and conditions defined in
# file 'LICENSE', which is part of this source code package.

import base64
import json
import requests
import sys
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
FILENAME = "detection_logs.csv"
# The maximum number of log entries to retrieve at a time.
LIMIT = 1000
# The EQL query.
EQL = "victimAddr = '10.10.10.10' | sort by startTime desc"

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
        data="grant_type=client_credentials"
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
    if TOKEN == "" or force_token_gen == True:
        TOKEN = getToken()
    return f"Bearer {TOKEN}"

def detectionLogQuery(eql, offset=0):
    """
    Method that runs an EQL query for detection log entries.

        Parameters:
            eql (str): The EQL query

        Returns:
            dict: The detection log entries that matched the query parameters
    """
    url = urlunparse(("https", HOST, "/api/v1/search/eql/detectionlogs", "", "", ""))
    headers = {
        "Authorization": getAuthHeader(),
        "Accept": "application/json",
    }
    data = {
        "eql": eql,
        "limit": LIMIT
    }
    if offset:
        data["offset"] = offset
    r = requests.post(url, headers=headers, data=json.dumps(data))
    if r.ok:
        return json.loads(r.text)
    else:
        print("Query failed")
        print(r.text)
        print(r.status_code)
        sys.exit()

def main():
    # Query logs 
    response = detectionLogQuery(EQL)
    total = response["total"]
    logs = response["results"]
    offset = LIMIT
    print("Retrieved " + str(len(logs)) + " out of " + str(total) + " detection log entries")
    while total > offset:
        response = detectionLogQuery(EQL, offset)
        new_logs = response["results"]
        logs = logs + new_logs
        offset = offset + LIMIT
        print(
            "Retrieved " + str(len(logs)) + " out of " + str(total) + " detection log entries"
        )

    # Write logs to CSV file
    if len(logs) > 0:
        with open(FILENAME, "wb") as csvfile:
            csvwriter = csv.writer(csvfile, encoding="utf-8")
            csvwriter.writerow(list(logs[0].keys()))
            for log in logs:
                csvwriter.writerow(list(log.values()))

if __name__ == "__main__":
    main() 
