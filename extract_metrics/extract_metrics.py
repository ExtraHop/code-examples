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

# The IP address or hostname of the ExtraHop system.
HOST = "extrahop.example.com"
# The API key.
APIKEY = "123456789abcdefghijklmnop"
# The filepath of the CSV file to save metrics to
FILENAME = "output.csv"


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
    headers = {"Authorization": f"ExtraHop apikey={API_KEY}"}
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
