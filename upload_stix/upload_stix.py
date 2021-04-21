# COPYRIGHT 2021 BY EXTRAHOP NETWORKS, INC.
#
# This file is subject to the terms and conditions defined in
# file 'LICENSE', which is part of this source code package.

#!/usr/bin/python3

import json
import os
import requests
import csv
from urllib.parse import urlunparse

# The path of the CSV file with the HTTPS URLs and API keys of the systems.
SYSTEM_LIST = "systems.csv"
# The path of the directory that contains the STIX files.
STIX_DIR = "stix_dir"

# Read system URLs and API keys from CSV file
systems = []
with open(SYSTEM_LIST, "rt", encoding="ascii") as f:
    reader = csv.reader(f)
    for row in reader:
        system = {"host": row[0], "api_key": row[1]}
        systems.append(system)


def getCollections(host):
    """
    Method that retrieves every threat collection on the ExtraHop system.
        Parameters:
            host (str): The IP address or hostname of the ExtraHop system

        Returns:
            list: A list of threat collection dictionaries
    """
    url = urlunparse(("https", host, "/api/v1/threatcollections", "", "", ""))
    r = requests.get(url, headers=headers)
    print(r.status_code)
    return r.json()


# Function that checks which STIX files have already been uploaded
def check_files(collections):
    """
    Method that finds out which STIX files in the STIX_DIR directory
    have already been uploaded to the ExtraHop system.

        Parameters:
            collections (list): A list of threat collection dictionaries

        Returns:
            update_list (list): A list of threat collection dictionaries for the STIX files that have already been uploaded
            skip_list (list): A list of STIX filenames that have already been uploaded
    """
    update_list = []
    skip_list = []
    # Get a list of all stix files in the STIX_DIR directory
    names = []
    for dir, subdirs, files in os.walk(STIX_DIR):
        for file in files:
            if file.endswith((".tar")):
                name = file.split(".")[0]
                names.append(name)
    # Check each threat collection for names that match the STIX file names
    for c in collections:
        c_name = c["name"]
        if c_name in names:
            update_list.append(c)
            skip_list.append(c_name)
    return update_list, skip_list


def process_files(update_files, skip_list, host):
    """
    Method that processes each file in the STIX_DIR directory. If a file has not been
    uploaded before, the method creates a new threat collection for the file. If a
    file has been uploaded before, the method updates the threat collection for that
    file with with the latest file contents.

        Parameters:
            update_files (list): A list of threat collection dictionaries for the STIX files that have already been uploaded
            skip_list (list): A list of STIX filenames that have already been uploaded
            host (str): The IP address or hostname of the ExtraHop system
    """
    for dir, subdirs, files in os.walk(STIX_DIR):
        for file in files:
            name = file.split(".")[0]
            if file.endswith((".tar")) and name not in skip_list:
                upload_new(file, dir, host)
            else:
                for c in update_files:
                    if c["name"] == name:
                        update_old(file, dir, c, host)


def upload_new(file, dir, host):
    """
    Method that uploads a new threat collection.

        Parameters:
            file (str): The filename of the STIX file
            dir (str): The directory of the STIX file
            host (str): The IP address or hostname of the ExtraHop system
    """
    print("Uploading " + file + " on " + host)
    url = urlunparse(("https", host, "/api/v1/threatcollections", "", "", ""))
    file_path = os.path.join(dir, file)
    name = file.split(".")[0]
    files = {"file": open(file_path, "rb")}
    values = {"name": name}
    r = requests.post(url, data=values, files=files, headers=headers)
    print(r.status_code)
    print(r.text)


# Function that updates an existing threat collection
def update_old(file, dir, c, host):
    """
    Method that updates an existing threat collection.

        Parameters:
            file (str): The filename of the STIX file
            dir (str): The directory of the STIX file
            c (dict): The threat collection dictionary for the STIX file
            host (str): The IP address or hostname of the ExtraHop system
    """
    print("Updating " + file + " on " + host)
    url = urlunparse(
        (
            "https",
            HOST,
            f"api/v1/threatcollections/~{str(c['user_key'])}",
            "",
            "",
            "",
        )
    )
    file_path = os.path.join(dir, file)
    files = {"file": open(file_path, "rb")}
    r = requests.put(url, files=files, headers=headers, verify=False)
    print(r.status_code)
    print(r.text)


# Process STIX files for each system
for system in systems:
    host = system["host"]
    api_key = system["api_key"]
    headers = {"Authorization": "ExtraHop apikey=%s" % api_key}
    collections = getCollections(host)
    update_files, skip_list = check_files(collections)
    process_files(update_files, skip_list, host)
