#!/usr/bin/python3

# COPYRIGHT 2021 BY EXTRAHOP NETWORKS, INC.
#
# This file is subject to the terms and conditions defined in
# file 'LICENSE', which is part of this source code package.

import json
import csv
import time
import requests
from urllib.parse import urlunparse
import base64
import sys

# The IP address or hostname of the ExtraHop appliance or Reveal(x) 360 API
HOST = "extrahop.example.com"

# For Reveal(x) 360 authentication
# The ID of the REST API credentials.
ID = "abcdefg123456789"
# The secret of the REST API credentials.
SECRET = "123456789abcdefg987654321abcdefg"
# A global variable for the temporary API access token (leave blank)
TOKEN = ""

# For self-managed appliance authentication
# The API key.
API_KEY = "123456789abcdefghijklmnop"

# The filepath of the CSV file to save metrics to
FILENAME = "output.csv"


def getToken():
    """
    Method that generates and retrieves a temporary API access token for Reveal(x) 360 authentication.

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
        print("Error retrieveing token from Reveal(x) 360")
        sys.exit()


def getAuthHeader(force_token_gen=False):
    """
    Method that adds an authorization header for a request. For Reveal(x) 360, adds a temporary access
    token. For self-managed appliances, adds an API key.

        Parameters:
            force_token_gen (bool): If true, always generates a new temporary API access token for the request

        Returns:
            header (str): The value for the header key in the headers dictionary
    """
    global TOKEN
    if API_KEY != "123456789abcdefghijklmnop" and API_KEY != "":
        return f"ExtraHop apikey={API_KEY}"
    else:
        if TOKEN == "" or force_token_gen == True:
            TOKEN = getToken()
        return f"Bearer {TOKEN}"


def getMetrics(object_type, metric_category, name, object_ids, cycle):
    """
    Method that retrieves metrics from the ExtraHop system

        Parameters:
            object_type (str): The type of object to retrieve metrics for
            metric_category (str): The category of object to retrieve metrics for
            name (str): The name of the metric to retrieve
            object_ids (list): A list of numeric IDs that identify the objects to retrieve metrics for
            cycle (str): The aggregation period for metrics

        Returns:
            metrics (list): A list of metric objects
    """
    data = {
        "object_type": object_type,
        "metric_category": metric_category,
        "metric_specs": [{"name": name}],
        "object_ids": object_ids,
        "cycle": cycle,
    }
    headers = {"Authorization": getAuthHeader()}
    url = urlunparse(("https", HOST, "/api/v1/metrics", "", "", ""))
    r = requests.post(url, headers=headers, json=data)
    if r.status_code == 200:
        j = r.json()
        print(
            f'Extracted {str(len(j["stats"]))} metrics from {str(j["from"])} until {str(j["until"])}'
        )
        return j["stats"]
    else:
        print("Failed to retrieve metrics")
        print(r.status_code)
        print(r.text)


def saveMetrics(metrics, filename):
    """
    Method that saves metrics to a CSV file.

        Parameters:
            metrics (list): The list of metric objects
            filename (str): The filename of the CSV file
    """
    with open(filename, "w") as csvfile:
        csvwriter = csv.writer(csvfile, dialect="excel")
        headers = []
        for header in metrics[0]:
            headers.append(header)
        csvwriter.writerow(headers)
        for metric in metrics:
            metric["time"] = time.strftime(
                "%Y-%m-%d %H:%M:%S", time.localtime(metric["time"] / 1000)
            )
            metric["values"] = str(metric["values"][0])
            csvwriter.writerow(list(metric.values()))


def main():
    metrics = getMetrics("device", "http_server", "rsp", [1907], "1hr")
    saveMetrics(metrics, FILENAME)


if __name__ == "__main__":
    main()
