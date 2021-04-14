# COPYRIGHT 2021 BY EXTRAHOP NETWORKS, INC.
#
# This file is subject to the terms and conditions defined in
# file 'LICENSE', which is part of this source code package.

#!/usr/bin/python3

import json
import requests
import sys
import logging
import base64

# The hostname of the ExtraHop system you are migrating detection
# hiding rules from
SOURCE_HOST = "https://zebraman"
# The API KEY on the ExtraHop system you are migrating detection
# hiding rules from
SOURCE_API_KEY = "aNXQ2--8dszqlX_ZBFDQ-eIiw5zJ701-WV_-kI-g9kk"
# The hostname of the Reveal(x) 360 API you are migrating detection
# hiding rules to.
TARGET_HOST = "https://example.api.com"
# The ID of the REST API credentials for Reveal(x) 360
TARGET_ID = "abcdefg123456789"
# The secret of the REST API credentials for Reveal(x) 360
TARGET_SECRET = "123456789abcdefg987654321abcdefg"


def getRules():
    """
    Method that retrieves detection hiding rules from the source
    ExtraHop system.

        Returns:
            rules (list): List of rule objects
    """
    url = f"{SOURCE_HOST}/api/v1/detections/rules/hiding"
    headers = {
        "Authorization": f"ExtraHop apikey={SOURCE_API_KEY}",
        "Content-Type": "application/json",
    }
    r = requests.get(url, headers=headers)
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


def getToken():
    """
    Method that generates and retrieves a temporary API access token for Reveal(x) 360 authentication.
        Returns:
            str: A temporary API access token
    """
    auth = base64.b64encode(
        bytes(TARGET_ID + ":" + TARGET_SECRET, "utf-8")
    ).decode("utf-8")
    headers = {
        "Authorization": "Basic " + auth,
        "Content-Type": "application/x-www-form-urlencoded",
    }
    r = requests.post(
        "%s/oauth2/token" % (TARGET_HOST),
        headers=headers,
        data="grant_type=client_credentials",
    )
    return r.json()["access_token"]


def replaceId(participant, token):
    """
    Method that replaces a device or device group ID in a participant object with the
    equivalent ID on Reveal(x) 360.

        Parameters:
            participant (dict): The participant object
            token (str): A temporary access token for Reveal(x) 360 authentication
        Returns:
            participant (dict): The updated participant object
    """
    if participant["object_type"] == "device":
        macaddr = getMac(participant["object_id"])
        if macaddr != -1:
            new_id = getDevId(macaddr, token)
        else:
            return {}
        if new_id != -1:
            participant["object_id"] = new_id
        else:
            return {}
    elif participant["object_type"] == "device_group":
        group_name = getName(participant["object_id"])
        if group_name != "":
            new_id = getGroupId(group_name, token)
        else:
            return {}
        if new_id != -1:
            participant["object_id"] = new_id
        else:
            return {}
    return participant


def getMac(dev_id):
    """
    Method that retrieves the MAC address for a device

        Parameters:
            dev_id (int): The numerical identifier of the device

        Returns:
            str: The MAC address of the device
    """
    url = f"{SOURCE_HOST}/api/v1/devices/{dev_id}"
    headers = {
        "Authorization": f"ExtraHop apikey={SOURCE_API_KEY}",
        "Content-Type": "application/json",
    }
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        return r.json()["macaddr"]
    else:
        logging.warning(r.status_code)
        logging.warning(r.text)
        logging.warning(f"Unable to retrieve MAC address for {dev_id}")
        return -1


def getDevId(macaddr, token):
    """
    Method that returns the ID of a device with a given MAC address on Reveal(x) 360

        Parameters:
            macaddr (str): The MAC address of the device
            token (str): A temporary access token for Reveal(x) 360 authentication

        Returns:
            int: The numerical ID of the device
    """
    url = f"{TARGET_HOST}/api/v1/devices/search"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    data = {"filter": {"field": "macaddr", "operand": macaddr, "operator": "="}}
    r = requests.post(url, headers=headers, json=data)
    if r.status_code == 200:
        devices = r.json()
        if len(devices) == 0:
            logging.warning(
                f"No equivalent device exists on Reveal(x)360 for {dev_id}"
            )
            return -1
        if len(devices) > 1:
            # If there are more than one device with the given MAC address, return
            # the L2 device.
            for device in devices:
                if device["is_l3"] == False:
                    return device["id"]
            logging.warning(f"No L2 device found for {devi_id}")
            return -1
        else:
            return devices[0]["id"]
    else:
        logging.warning(r.status_code)
        logging.warning(r.text)
        logging.warning(f"Unable to retrieve device ID for {dev_id}")
        return -1


def getName(group_id):
    """
    Method that retrieves the name of a device group.

        Parameters:
            group_id (int): The numerical identifier of the device group

        Returns:
            str: The name of the device group
    """
    url = f"{SOURCE_HOST}/api/v1/devicegroups/{group_id}"
    headers = {
        "Authorization": f"ExtraHop apikey={SOURCE_API_KEY}",
        "Content-Type": "application/json",
    }
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        return r.json()["name"]
    else:
        logging.warning(r.status_code)
        logging.warning(r.text)
        logging.warning(f"Unable to retrieve MAC address for {dev_id}")
        return ""


def getGroupId(group_name, token):
    """
    Method that returns the ID of a device group with a given name

        Parameters:
            group_name (str): The name of the device group
            token (str): A temporary access token for Reveal(x) 360 authentication

        Returns:
            int: The ID of the device group
    """
    url = f"{TARGET_HOST}/api/v1/devicegroups"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    r = requests.get(url, headers=headers)
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


def makeRule(rule, token):
    """
    Method that creates a detection hiding rule on the target
    ExtraHop system.

        Parameters:
            rule (dict): The rule properties.
            token (str): A temporary access token for Reveal(x) 360 authentication

        Returns:
            bool: Indicates whether the rule was successfully created
    """
    rule_id = rule["id"]
    # Rule descriptions cannot be null in POST requests, so we
    # need to remove null descriptions
    if rule["description"] == None:
        rule.pop("description")
    url = f"{TARGET_HOST}/api/v1/detections/rules/hiding"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    r = requests.post(url, headers=headers, json=rule)
    if r.status_code == 201:
        logging.info(f"Successfully migrated rule {rule_id}")
        return True
    else:
        logging.warning(r.status_code)
        logging.warning(r.text)
        logging.warning(f"Failed to create rule {rule_id}")
        return False


def updateParticipants(rule, token):
    """
    Method that updates participant objects in a rule by updating device
    and device group IDs.

        Parameters:
            rule (dict): The rule to be updated
            token (str): A temporary access token for Reveal(x) 360 authentication

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
            if (
                participant["object_type"] == "device"
                or participant["object_type"] == "device_group"
            ):
                participant = replaceId(participant, token)
                if participant == {}:
                    return {}
                else:
                    rule[role] = participant
    return rule


def main():
    rules = getRules()
    num_rules = str(len(rules))
    logging.info(f"Migrating {num_rules} detection hiding rules")
    token = getToken()
    # Find equivalent IDs for participants
    updated_rules = []
    not_found = []
    for rule in rules:
        rule = updateParticipants(rule, token)
        if rule:
            updated_rules.append(rule)
        else:
            not_found.append(rule)
    c = "y"
    # If unable to retrieve equivalent IDs for participants, warn user before
    # continuing
    if not_found:
        total_nf = str(len(not_found))
        total_up = str(len(updated_rules))
        logging.warning(
            f"\nFailed to find equivalent participant devices for {total_nf} rules."
        )
        logging.warning(f"Do you want to migrate the other {total_up} rules?")
        c = input("(y/n)")
    if c == "y":
        # Create new rules on target Reveal(x) 360 system
        for rule in updated_rules:
            success = makeRule(rule, token)


if __name__ == "__main__":
    logging.basicConfig(
        format="%(message)s",
        handlers=[logging.StreamHandler(sys.stdout),],
        level=logging.INFO,
    )
    main()
