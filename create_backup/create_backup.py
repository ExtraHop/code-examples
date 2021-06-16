#!/usr/bin/python3

# COPYRIGHT 2020 BY EXTRAHOP NETWORKS, INC.
#
# This file is subject to the terms and conditions defined in
# file 'LICENSE', which is part of this source code package.

import json
import requests
import sys
from urllib.parse import urlunparse

HOST = "extrahop.example.com"
API_KEY = "123456789abcdefghijklmnop"
BACKUP_NAME = "mybackup"


def createBackup(BACKUP_NAME):
    url = urlunparse(("https", HOST, "/api/v1/customizations", "", "", ""))
    headers = {
        "Authorization": "ExtraHop apikey=%s" % API_KEY,
        "Content-Type": "application/json",
    }
    data = {"name": BACKUP_NAME}
    r = requests.post(url, headers=headers, data=json.dumps(data))
    if r.status_code == 201:
        return True
    else:
        print("Unable to create backup")
        print(r.text)
        print(r.status_code)
        sys.exit()


def getIdName(BACKUP_NAME):
    url = urlunparse(("https", HOST, "/api/v1/customizations", "", "", ""))
    headers = {
        "Authorization": "ExtraHop apikey=%s" % API_KEY,
        "Content-Type": "application/json",
    }
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        backups = json.loads(r.text)
        for b in reversed(backups):
            if BACKUP_NAME in b["name"]:
                return b["id"], b["name"]
            else:
                continue
        print("Unable to retrieve ID for specified backup")
        sys.exit()
    else:
        print("Unable to retrieve backup IDs")
        print(r.text)
        print(r.status_code)
        sys.exit()


def downloadBackup(backup_id):
    url = urlunparse(
        (
            "https",
            HOST,
            f"/api/v1/customizations/{str(backup_id)}/download",
            "",
            "",
            "",
        )
    )
    headers = {
        "Authorization": "ExtraHop apikey=%s" % API_KEY,
        "accept": "application/exbk",
    }
    r = requests.post(url, headers=headers)
    if r.status_code == 200:
        return r.content
    else:
        print("Unable to download backup")
        print(r.status_code)
        print(r.text)
        sys.exit()


def writeBackup(backup, BACKUP_NAME):
    new_name = BACKUP_NAME.replace(":", "")
    filepath = new_name + ".exbk"
    with open(filepath, "wb") as b:
        b.write(bytes(backup))
    print("Success! Backup file name:")
    print(filepath)


createBackup(BACKUP_NAME)
backup_id, BACKUP_NAME = getIdName(BACKUP_NAME)
backup = downloadBackup(backup_id)
writeBackup(backup, BACKUP_NAME)
