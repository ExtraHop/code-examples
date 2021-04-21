# COPYRIGHT 2021 BY EXTRAHOP NETWORKS, INC.
#
# This file is subject to the terms and conditions defined in
# file 'LICENSE', which is part of this source code package.

#!/usr/bin/python3

import boto3
import json
import requests
import os
import sys
from botocore.config import Config
from urllib.parse import urlunparse

# The private IP address or hostname of the EC2 instance of the ExtraHop system.
HOST = "extrahop.example.com"
# The ExtraHop API key.
APIKEY = "123456789abcdefghijklmnop"


def addEHids(mac_addresses, mapping):
    """
    Method that retrieves ExtraHop device IDs and maps them to EC2 network interfaces.

        Parameters:
            mac_addresses (list): List of EC2 network interface MAC addresses
            mapping (list): List of dictionaries containing EC2 network interface metadata

        Returns:
            to_do (list): List of network interfaces that have been mapped to ExtraHop device IDs
            not_found (list): List of network interface MAC addresses that were not found on the ExtraHop system
    """
    url = urlunparse(("https", HOST, "/api/v1/devices/search", "", "", ""))
    headers = {"Authorization": "ExtraHop apikey=%s" % APIKEY}
    rules = []
    for macaddr in mac_addresses:
        rules.append({"field": "macaddr", "operand": macaddr, "operator": "="})
    search = {"filter": {"operator": "or", "rules": rules}}
    r = requests.post(
        url, headers=headers, verify=False, data=json.dumps(search)
    )
    if r.status_code != 200:
        print("Error! Unable to retrieve devices from ExtraHop.")
        print(r.text)
        sys.exit()
    mac_id_map = {}
    for device in r.json():
        macaddr = device["macaddr"].lower()
        if device["is_l3"] == True:
            continue
        if macaddr in mac_id_map:
            mac_id_map[macaddr].append(device["id"])
        else:
            mac_id_map[macaddr] = [device["id"]]
    to_do = []
    not_found = []
    for instance in mapping:
        aws_mac = instance["macaddr"]
        if aws_mac in mac_id_map:
            instance["id"] = mac_id_map[aws_mac]
            instance.pop("macaddr")
            to_do.append(instance)
        else:
            not_found.append(aws_mac)
    return to_do, not_found


def updateMeta(device, dev_id):
    """
    Method that adds cloud properties to devices in the ExtraHop system.

        Parameters:
            device (dict): The cloud properties of the device
            dev_id (str): The ID of the device

        Returns:
            bool: Indicates whether the request was successful
    """
    url = urlunparse(
        ("https", HOST, f"/api/v1/devices/{str(dev_id)}", "", "", "")
    )
    headers = {"Authorization": "ExtraHop apikey=%s" % APIKEY}
    r = requests.patch(url, headers=headers, data=json.dumps(device))
    if r.status_code != 204:
        return False
    else:
        return True


def lambda_handler(event, context):
    aws_map = []
    print("start")
    ec2 = boto3.client(
        "ec2",
        config=Config(
            connect_timeout=10,
            read_timeout=10,
            retries={"total_max_attempts": 50},
        ),
    )
    response = ec2.describe_instances()
    reservations = response["Reservations"]
    for reservation in reservations:
        for instance in reservation["Instances"]:
            instance_id = instance["InstanceId"]
            instance_type = instance["InstanceType"]
            instance_name = ""
            for tag in instance["Tags"]:
                if tag["Key"] == "Name":
                    instance_name = tag["Value"]
            for interface in instance["NetworkInterfaces"]:
                instance_owner = interface["OwnerId"]
                vpc_id = interface["VpcId"]
                macaddr = interface["MacAddress"]
                aws_map.append(
                    {
                        "macaddr": macaddr,
                        "cloud_instance_id": instance_id,
                        "cloud_instance_type": instance_type,
                        "cloud_instance_name": instance_name,
                        "cloud_account": instance_owner,
                        "vpc_id": vpc_id,
                    }
                )
    mac_addresses = [x["macaddr"] for x in aws_map]
    aws_map, not_found = addEHids(mac_addresses, aws_map)
    updates = []
    failed = []
    for device in aws_map:
        ids = device.pop("id")
        for i in ids:
            success = updateMeta(device, i)
            if success:
                updates.append(str(i))
            else:
                failed.append(str(i))
    results = {
        "updated_device_ids": updates,
        "update_failed_device_ids": failed,
        "macaddr_not_found_on_eh": not_found,
    }
    return {"statusCode": 200, "body": json.dumps(results)}
