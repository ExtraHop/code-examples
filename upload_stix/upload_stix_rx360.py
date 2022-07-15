#!/usr/bin/python3

# COPYRIGHT 2021 BY EXTRAHOP NETWORKS, INC.
#
# This file is subject to the terms and conditions defined in
# file 'LICENSE', which is part of this source code package.

import json
import os
import requests
import csv
from urllib.parse import urlunparse
import base64
import sys

# The IP address or hostname of the Reveal(x) 360 API
HOST = "extrahop.example.com"

# The ID of the REST API credentials.
ID = "abcdefg123456789"
# The secret of the REST API credentials.
SECRET = "123456789abcdefg987654321abcdefg"
# A global variable for the temporary API access token (leave blank)
TOKEN = ""

# The path of the directory that contains the STIX files.
STIX_DIR = "stix_dir"


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
    Method that adds an authorization header for a request.

        Parameters:
            force_token_gen (bool): If true, always generates a new temporary API access token for the request

        Returns:
            header (str): The value for the header key in the headers dictionary
    """
    global TOKEN
    if TOKEN == "" or force_token_gen == True:
        TOKEN = getToken()
    return f"Bearer {TOKEN}"


def getCollections(host):
    """
    Method that retrieves every threat collection on the ExtraHop system.
        Parameters:
            host (str): The IP address or hostname of the ExtraHop system

        Returns:
            list: A list of threat collection dictionaries
    """
    headers = {"Authorization": getAuthHeader()}
    url = urlunparse(("https", host, "/api/v1/threatcollections", "", "", ""))
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        return r.json()
    else:
        print("Error: Unable to retrieve existing threat collections.")
        print(r.status_code)
        print(r.text)
        sys.exit()


# Function that checks which STIX files have already been uploaded
def check_files(collections):
    """
    Method that finds out which STIX files in the STIX_DIR directory
    have already been uploaded to the ExtraHop system.

        Parameters:
            collections (list): A list of threat collection dictionaries

        Returns:
            upload_list (list): A list of STIX filenames that have not been uploaded
            skip_list (list): A list of threat collection dictionaries for the STIX files that have already been uploaded
    """
    upload_list = []
    skip_list = []
    # Get a list of all stix files in the STIX_DIR directory
    upload_list = []
    collection_names = [c["name"] for c in collections]
    for dir, subdirs, files in os.walk(STIX_DIR):
        for file in files:
            if file.endswith((".tar")) or file.endswith(".tgz"):
                name = file.split(".")[0]
                if name in collection_names:
                    obj = {}
                    for c in collections:
                        if c["name"] == name:
                            obj["user_key"] = c["user_key"]
                    obj["filename"] = file
                    skip_list.append(obj)
                else:
                    upload_list.append(file)
    return upload_list, skip_list


def process_files(upload_files, skip_list, host):
    """
    Method that processes each file in the STIX_DIR directory. If a file has not been
    uploaded before, the method creates a new threat collection for the file. If a
    file has been uploaded before, the method updates the threat collection for that
    file with with the latest file contents.

        Parameters:
            upload_files (list): A list of STIX filenames to upload
            skip_list (list): A list of threat collection dictionaries for the STIX files that have already been uploaded
            host (str): The IP address or hostname of the ExtraHop system
    """
    for f in upload_files:
        upload_new(f"{STIX_DIR}/{f}", host)
    for s in skip_list:
        update_old(f"{STIX_DIR}/{s['filename']}", s["user_key"], host)


def upload_new(file_path, host):
    """
    Method that uploads a new threat collection.

        Parameters:
            file_path (str): The filepath of the STIX file
            host (str): The IP address or hostname of the ExtraHop system
    """
    print("Uploading " + file_path + " on " + host)
    url = urlunparse(("https", host, "/api/v1/threatcollections", "", "", ""))
    name = file_path.split("/")[-1]
    name = name.split(".")[0]
    files = {"file": open(file_path, "rb")}
    values = {"name": name}
    headers = {"Authorization": getAuthHeader()}
    r = requests.post(url, data=values, files=files, headers=headers)
    if r.status_code == 204:
        print("Upload complete")
    else:
        print("Upload failed")
        print(r.status_code)
        print(r.text)


# Function that updates an existing threat collection
def update_old(file_path, user_key, host):
    """
    Method that updates an existing threat collection.

        Parameters:
            file (str): The filenpath of the STIX file
            user_key (str): The user key of the threat collection
            host (str): The IP address or hostname of the Reveal(x) 360 API
    """
    print("Updating " + file_path + " on " + host)
    url = urlunparse(
        (
            "https",
            HOST,
            f"api/v1/threatcollections/~{str(user_key)}",
            "",
            "",
            "",
        )
    )
    files = {"file": open(file_path, "rb")}
    headers = {"Authorization": getAuthHeader()}
    r = requests.put(url, files=files, headers=headers)
    if r.status_code == 204:
        print("Update complete")
    else:
        print("Update failed")
        print(r.status_code)
        print(r.text)


# Process STIX files
collections = getCollections(HOST)
upload_files, skip_list = check_files(collections)
print(f"{str(len(upload_files))} to upload")
print(f"{str(len(skip_list))} to update")
process_files(upload_files, skip_list, HOST)
