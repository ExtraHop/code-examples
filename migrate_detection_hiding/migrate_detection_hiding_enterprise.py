#!/usr/bin/python3

# COPYRIGHT 2021 BY EXTRAHOP NETWORKS, INC.
#
# This file is subject to the terms and conditions defined in
# file 'LICENSE', which is part of this source code package.

import json
import requests
import sys
import logging
import base64
from urllib.parse import urlunparse

# The hostname of the ExtraHop system you are migrating detection
# hiding rules from
SOURCE_HOST = ""
# The API KEY on the ExtraHop system you are migrating detection
# hiding rules from
SOURCE_API_KEY = ""
# The hostname of the ExtraHop system you are migrating detection
# hiding rules to
TARGET_HOST = ""
# The API KEY on the ExtraHop system you are migrating detection
# hiding rules to
TARGET_API_KEY = ""

source_headers = {
        "Authorization": f"ExtraHop apikey={SOURCE_API_KEY}",
        "Content-Type": "application/json",
    }

target_headers = {
        "Authorization": f"ExtraHop apikey={TARGET_API_KEY}",
        "Content-Type": "application/json",
    }


def getRules():
    """
    Method that retrieves detection hiding rules from the source
    ExtraHop system.
        Returns:
            rules (list): List of rule objects
    """
    url = urlunparse(
        ("https", SOURCE_HOST, "/api/v1/detections/rules/hiding", "", "", "")
    )

    r = requests.get(url, headers=source_headers)
    if r.status_code == 200:
        rules = []
        for rule in r.json():
            if rule["enabled"]:
                rules.append(rule)
        return rules
    else:
        logging.error(r.status_code)
        logging.error(r.text)
        raise RuntimeError("Unable to retrieve rules")


def replaceId(participant):
    """
    Method that replaces a device or device group ID in a participant object with the
    equivalent ID on the target appliance.

        Parameters:
            participant (dict): The participant object
        Returns:
            participant (dict): The updated participant object
    """
    if participant["object_type"] == "device":
        macaddr = getMac(participant["object_id"])
        if macaddr == None:
            return {}
        else:
            new_id = getDevId(macaddr)
        if new_id == -1:
            return {}
        else:
            participant["object_id"] = new_id
    elif participant["object_type"] == "device_group":
        group_name = getName(participant["object_id"])
        if group_name == "":
            return {}
        else:
            new_id = getGroupId(group_name)
        if new_id == -1:
            return {}
        else:
            participant["object_id"] = new_id
    elif participant["object_type"] == "network_locality":
        networks = getNetworks(participant["object_id"])
        if networks == []:
            return {}
        else:
            new_id = getLocalityId(networks)
        if new_id == -1:
            return {}
        else:
            participant["object_id"] = new_id
    return participant

def getLocalityId(networks):
    """
    Method that searches the target appliance for a network locality
    that contains all of the specified networks and returns
    the ID of that locality.

        Parameters:
            networks (list): A list of CIDR blocks and IP addresses

        Returns:
            int: The numerical ID of the network locality
    """
    url = urlunparse(
        ("https", TARGET_HOST, "/api/v1/networklocalities", "", "", "")
    )
    r = requests.get(url, headers=target_headers)
    if r.status_code == 200:
        for locality in r.json():
            if set(networks) == set(locality["networks"]):
                return locality["id"]
        logging.warning(
            f"No equivalent network locality exists on the target appliance with the following IP addresses and CIDR blocks {networks}"
        )
        return -1
    else:
        logging.warning(r.status_code)
        logging.warning(r.text)
        logging.warning(
            f"Unable to retrieve network localities from the target appliance"
        )
        return -1

def getNetworks(locality_id):
    """
    Method that returns the networks in the specified network locality.

        Parameters:
            locality_id (int): The numeric identifier of the locality

        Returns:
            list: The list of IP addresses and CIDR blocks
    """
    url = urlunparse(
        (
            "https",
            SOURCE_HOST,
            f"/api/v1/networklocalities/{locality_id}",
            "",
            "",
            "",
        )
    )
    headers = {
        "Authorization": f"ExtraHop apikey={SOURCE_API_KEY}",
        "Content-Type": "application/json",
    }
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        return r.json()["networks"]
    else:
        logging.warning(r.status_code)
        logging.warning(r.text)
        logging.warning(f"Unable to retrieve networks for {locality_id}")
        return []

def getMac(dev_id):
    """
    Method that retrieves the MAC address for a device
        Parameters:
            dev_id (int): The numerical identifier of the device
        Returns:
            str: The MAC address of the device
    """
    url = urlunparse(
        ("https", SOURCE_HOST, f"/api/v1/devices/{dev_id}", "", "", "")
    )

    r = requests.get(url, headers=source_headers)
    if r.status_code == 200:
        return r.json()["macaddr"]
    else:
        logging.warning(r.status_code)
        logging.warning(r.text)
        logging.warning(f"Unable to retrieve MAC address for {dev_id}")
        return None


def getDevId(macaddr):
    """
    Method that returns the ID of a device with a given MAC address on Target Appliance
        Parameters:
            macaddr (str): The MAC address of the device
        Returns:
            int: The numerical ID of the device
    """
    url = urlunparse(
        ("https", TARGET_HOST, "/api/v1/devices/search", "", "", "")
    )

    data = {"filter": {"field": "macaddr", "operand": macaddr, "operator": "="}}
    r = requests.post(url, headers=target_headers, json=data)
    if r.status_code == 200:
        devices = r.json()
        if len(devices) == 0:
            logging.warning(
                f"No equivalent device exists on Target Appliance for {macaddr}"
            )
            return -1
        if len(devices) > 1:
            # If there are more than one device with the given MAC address, return
            # the L2 device.
            for device in devices:
                if device["is_l3"] == False:
                    return device["id"]
            logging.warning(f"No L2 device found for {macaddr}")
            return -1
        else:
            return devices[0]["id"]
    else:
        logging.warning(r.status_code)
        logging.warning(r.text)
        logging.warning(f"Unable to retrieve device ID for {macaddr}")
        return -1


def getName(group_id):
    """
    Method that retrieves the name of a device group.
        Parameters:
            group_id (int): The numerical identifier of the device group
        Returns:
            str: The name of the device group
    """
    url = urlunparse(
        ("https", SOURCE_HOST, f"/api/v1/devicegroups/{group_id}", "", "", "")
    )

    r = requests.get(url, headers=source_headers)
    if r.status_code == 200:
        return r.json()["name"]
    else:
        logging.warning(r.status_code)
        logging.warning(r.text)
        logging.warning(f"Unable to retrieve name for {group_id}")
        return ""


def getGroupId(group_name):
    """
    Method that returns the ID of a device group with a given name
        Parameters:
            group_name (str): The name of the device group
        Returns:
            int: The ID of the device group
    """
    url = urlunparse(("https", TARGET_HOST, "/api/v1/devicegroups", "", "", ""))

    r = requests.get(url, headers=target_headers)
    if r.status_code == 200:
        groups = r.json()
        for group in groups:
            if group["name"] == group_name:
                return group["id"]
        logging.warning(
            f"Unable to find an equivalent device group for {group_name}"
        )
        return -1
    else:
        logging.warning(r.status_code)
        logging.warning(r.text)
        logging.warning(f"Unable to retrieve device groups")
        return -1


def makeRule(rule):
    """
    Method that creates a detection hiding rule on the Target Appliance.
        Parameters:
            rule (dict): The rule properties.
        Returns:
            bool: Indicates whether the rule was successfully created
    """
    rule_id = rule["id"]
    # Rule descriptions and properties cannot be null in POST requests, so we
    # need to remove null descriptions and properties
    if rule["description"] == None:
        rule.pop("description")
    if rule["properties"] == None:
        rule.pop("properties")
    url = urlunparse(
        ("https", TARGET_HOST, "/api/v1/detections/rules/hiding", "", "", "")
    )

    r = requests.post(url, headers=target_headers, json=rule)
    if r.status_code == 201:
        logging.info(f"Successfully migrated rule {rule_id}")
        return True
    else:
        logging.warning(r.status_code)
        logging.warning(r.text)
        logging.warning(f"Failed to create rule {rule_id}")
        return False


def updateParticipants(rule):
    """
    Method that updates participant objects in a rule by updating device
    and device group IDs.

        Parameters:
            rule (dict): The rule to be updated

        Returns:
            rule (dict): The updated rule
    """
    roles = ["victim", "offender"]
    for role in roles:
        if rule[role] != "Any":
            logging.info(
                f"Retrieving equivalent participant IDs for rule: {rule['id']}"
            )
            participant = rule[role]
            p_type = participant["object_type"]
            if (
                p_type == "device"
                or p_type == "device_group"
                or p_type == "network_locality"
            ):
                participant = replaceId(participant)
                if participant == {}:
                    return None
                else:
                    rule[role] = participant
            elif p_type == "locality_type":
                participant["object_locality"] = participant["object_value"]
    return rule

def main():
    rules = getRules()
    num_rules = str(len(rules))
    logging.info(f"Migrating {num_rules} detection hiding rules")

    # Find equivalent IDs for participants
    updated_rules = []
    not_found = []
    for rule in rules:
        new_rule = updateParticipants(rule)
        if new_rule:
            updated_rules.append(new_rule)
        else:
            not_found.append(rule["id"])
    c = "y"
    # If unable to retrieve equivalent IDs for participants, warn user before
    # continuing
    if not_found:
        total_up = str(len(updated_rules))
        logging.warning(
            f"\niFailed to find equivalent participant devices for rules with the following IDs: {not_found}"
        )
        logging.warning(f"Do you want to migrate the other {total_up} rules?")
        c = input("(y/n)")
    if c == "y":
        # Create new rules on Target Appliance
        for rule in updated_rules:
            success = makeRule(rule)


if __name__ == "__main__":
    logging.basicConfig(
        format="%(message)s",
        handlers=[logging.StreamHandler(sys.stdout),],
        level=logging.INFO,
    )
    main()
