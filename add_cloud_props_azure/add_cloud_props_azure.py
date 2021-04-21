# COPYRIGHT 2021 BY EXTRAHOP NETWORKS, INC.
#
# This file is subject to the terms and conditions defined in
# file 'LICENSE', which is part of this source code package.

#!/usr/bin/python3

from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.common.credentials import ServicePrincipalCredentials
import os
import json
import sys
import requests
from urllib.parse import urlunparse

# The IP address or hostname of the ExtraHop system.
HOST = "extrahop.example.com"
# The ExtraHop API key.
APIKEY = "123456789abcdefghijklmnop"

subscription_id = os.environ.get("AZURE_SUBSCRIPTION_ID")
credentials = ServicePrincipalCredentials(
    client_id=os.environ["AZURE_CLIENT_ID"],
    secret=os.environ["AZURE_CLIENT_SECRET"],
    tenant=os.environ["AZURE_TENANT_ID"],
)
compute_client = ComputeManagementClient(credentials, subscription_id)
network_client = NetworkManagementClient(credentials, subscription_id)
region = "eastus"


result_list_pub = compute_client.virtual_machine_images.list_publishers(region,)


def addEHids(mac_addresses, mapping):
    """
    Method that retrieves ExtraHop device IDs and maps them to Azure network interfaces.

        Parameters:
            mac_addresses (list): List of Azure network interface MAC addresses
            mapping (list): List of dictionaries containing Azure network interface metadata

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
        macaddr = device["macaddr"]
        if device["is_l3"] == True:
            continue
        if macaddr in mac_id_map:
            mac_id_map[macaddr].append(device["id"])
        else:
            mac_id_map[macaddr] = [device["id"]]
    return_list = []
    for instance in mapping:
        aws_mac = instance["macaddr"]
        if aws_mac in mac_id_map:
            instance["id"] = mac_id_map[aws_mac]
            instance.pop("macaddr")
            return_list.append(instance)
        else:
            print(
                "MAC address: "
                + instance["macaddr"]
                + " not found on the ExtraHop system"
            )
    return return_list


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


az_map = []
for vm in compute_client.virtual_machines.list_all():
    vm_name = vm.name
    vm_id = vm.vm_id
    vm_size = vm.hardware_profile.vm_size
    subscription_id = vm.id.split("/")[2]
    for interface in vm.network_profile.network_interfaces:
        name = interface.id.split("/")[-1]
        subnet = interface.id.split("/")[4]
        nic_group = interface.id.split("/")[-5]
        nic = network_client.network_interfaces.get(nic_group, name)
        macaddr = nic.mac_address.replace("-", ":")
        vnet_name = nic.ip_configurations[0].subnet.id.split("/")[-3]
        az_map.append(
            {
                "macaddr": macaddr,
                "cloud_instance_name": vm_name,
                "cloud_instance_type": vm_size,
                "cloud_instance_id": vm_id,
                "cloud_account": subscription_id,
                "vpc_id": vnet_name,
            }
        )

mac_addresses = [x["macaddr"] for x in az_map]
az_map = addEHids(mac_addresses, az_map)

updates = []
failed = []
for device in az_map:
    ids = device.pop("id")
    for i in ids:
        success = updateMeta(device, i)
        if success:
            updates.append("Device ID: " + str(i))
        else:
            failed.append("Device ID: " + str(i))

if updates:
    print("Updated cloud properties for the following devices:")
    for u in updates:
        print("    " + u)
if failed:
    print("Failed to update cloud properties for the following devices:")
    for f in failed:
        print("    " + f)
