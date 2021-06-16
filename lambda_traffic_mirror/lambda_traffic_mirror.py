#!/usr/bin/python3

# COPYRIGHT 2021 BY EXTRAHOP NETWORKS, INC.
#
# This file is subject to the terms and conditions defined in
# file 'LICENSE', which is part of this source code package.

import json
import boto3
import os
from netaddr import IPNetwork, IPAddress

EC2_CLIENT = boto3.client("ec2")
# The ID of the traffic mirror filter.
FILTER_ID = os.environ["filter_id"]
# The IDs of the traffic mirror targets for your ExtraHop sensors.
TARGETS = ["tmt-abcdefg0123456789"]
# Determines whether the function will mirror traffic across availabilty
# zones. If set to True, and there are no traffic mirror targets in the
# availability zone of the source EC2 instance, the function does not create
# a mirror session.
LOCAL_ZONE_ONLY = True


def create_mirror(interface_id, targets):
    """
    Method that creates a traffic mirror session for a network interface (ENI).
    The method selects the best traffic mirror target by looking for a target
    within the current availability zone with the lowest mirror sessions. Targets
    that do not allow traffic on required ports and protocols are not selected.

        Parameters:
            interface_id (str): The ID of the ENI
            targets (list): A list of traffic mirror target IDs

        Returns:
            name (str): The name of the newly created traffic mirror session
    """
    targets = find_local_targets(interface_id, targets)
    if len(targets) == 0:
        return {
            "error": "None of the specified traffic mirror targets are in the same availability zone as "
            + interface_id
        }
    targets = find_allowed_targets(interface_id, targets, ["udp"], [4789])
    if len(targets) == 0:
        return {
            "error": "None of the traffic mirror targets support UDP traffic on port 4789"
        }
    target_id = find_target_with_lowest(targets)
    # Create a name by combining network interface ID and target ID. For example:
    # interface_id = eni-055061bf5573d0a3b
    # target_id = tmt-0bce8038d06d6c745
    name = "eh-mirror-" + interface_id[4:8] + target_id[4:8]
    tags = [
        {
            "ResourceType": "traffic-mirror-session",
            "Tags": [{"Key": "Name", "Value": name}],
        }
    ]
    response = EC2_CLIENT.create_traffic_mirror_session(
        NetworkInterfaceId=interface_id,
        TrafficMirrorTargetId=target_id,
        TrafficMirrorFilterId=FILTER_ID,
        SessionNumber=1,
        TagSpecifications=tags,
    )
    return {"name": name}


def find_local_targets(interface_id, targets):
    """
    Method that returns a list of mirror targets that are in the same availability
    zone as the specified network interface. If none of the specified mirror targets
    are in the availability zone and LOCAL_ZONE_ONLY is false, the method returns
    the original list; if LOCAL_ZONE_ONLY is true, the method returns an empty list.

        Parameters:
            interface_id (str): The ID of the ENI
            targets (list): A list of traffic mirror target IDs

        Returns:
            local (list): A list of local traffic mirror target IDs
            targets (list): The original list of traffic mirror target IDs
    """
    source_zone = EC2_CLIENT.describe_network_interfaces(
        NetworkInterfaceIds=[interface_id]
    )["NetworkInterfaces"][0]["AvailabilityZone"]
    local = []
    # Create a list of all targets that are in the same
    # availability zone as the interface
    for target in targets:
        eni = EC2_CLIENT.describe_traffic_mirror_targets(
            Filters=[{"Name": "traffic-mirror-target-id", "Values": [target]}]
        )["TrafficMirrorTargets"][0]["NetworkInterfaceId"]
        target_zone = EC2_CLIENT.describe_network_interfaces(
            NetworkInterfaceIds=[eni]
        )["NetworkInterfaces"][0]["AvailabilityZone"]
        if target_zone == source_zone:
            local.append(target)
    if local:
        return local
    # If there are no targets in the same zone, and LOCAL_ZONE_ONLY is true,
    # return an empty list
    elif LOCAL_ZONE_ONLY:
        return []
    # If there are no targets in the same zone, but LOCAL_ZONE_ONLY is false,
    # return the original list
    else:
        return targets


def find_allowed_targets(interface_id, targets, protocols, port_range):
    """
    Method that returns a list of mirror targets that can accept traffic from the
    specified ENI on the specified port range over the specified protocols.
    The method checks both the security group of the EC2 instance and the ACLs
    of the subnet that the EC2 instance is on.

        Parameters:
            interface_id (str): The ID of the ENI
            targets (list): A list of traffic mirror target IDs

        Returns:
            str: The ID of the mirror target with the least mirror sessions
    """
    source_interface = EC2_CLIENT.describe_network_interfaces(
        NetworkInterfaceIds=[interface_id]
    )["NetworkInterfaces"][0]
    # Find all IP addresses for the interface
    source_ips = []
    for addr in source_interface["PrivateIpAddresses"]:
        if addr["PrivateIpAddress"]:
            source_ips.append(addr["PrivateIpAddress"])
        if addr["Association"]["PublicIp"]:
            source_ips.append(addr["Association"]["PublicIp"])
    eligible_targets = []
    for target in targets:
        target_interface_id = EC2_CLIENT.describe_traffic_mirror_targets(
            TrafficMirrorTargetIds=[target]
        )["TrafficMirrorTargets"][0]["NetworkInterfaceId"]
        target_interface = EC2_CLIENT.describe_network_interfaces(
            NetworkInterfaceIds=[target_interface_id]
        )["NetworkInterfaces"][0]
        # Check if source and target are on the same VPC. If so, don't check the ACL
        same_vpc = False
        source_vpc_id = source_interface["VpcId"]
        target_vpc_id = target_interface["VpcId"]
        if source_vpc_id == target_vpc_id:
            same_vpc = True
        if not same_vpc:
            if not aclAllow(
                target_interface,
                port_range,
                source_ips,
                protocols,
                target_vpc_id,
            ):
                continue
        interface_groups = target_interface["Groups"]
        if groupsAllow(source_ips, port_range, interface_groups, protocols):
            eligible_targets.append(target)
    return eligible_targets


def aclAllow(
    target_interface, required_range, source_ips, protocols, target_vpc_id
):
    """
    Method that indicates whether at least one IP address in a list can send
    traffic through the ACL of the specified target interface over the given protocols
    on at least one port in the required range.

        Parameters:
            target_interface (obj): The target interface
            required_range (range or list): The range of ports
            source_ips (list): The list of IP addresses
            protocols (list): The list of protocols

        Returns:
            bool: Whether the ACLs allow the communication
    """
    confirmed_protocols = []
    subnet_id = target_interface["SubnetId"]
    acls = EC2_CLIENT.describe_network_acls(
        Filters=[{"Name": "vpc-id", "Values": [target_vpc_id]}]
    )["NetworkAcls"]
    acl = findSubnetAcl(subnet_id, acls)
    if acl == None:
        return confirmed_protocols
    for entry in acl["Entries"]:
        # Skip outbound rules
        if entry["Egress"] == True:
            continue
        proto = entry["Protocol"]
        if proto == "-1" or proto in protocols:
            # Skip rules that do not apply to the required port range
            if "PortRange" in entry:
                rule_range = range(
                    entry["PortRange"]["From"], permission["PortRange"]["To"]
                )
                if len(rule_range) == 0:
                    rule_range = [entry["PortRange"]["From"]]
                port_matches = False
                for port in rule_range:
                    if port in required_range:
                        port_matches = True
                        break
                if port_matches == False:
                    continue
            for source_ip in source_ips:
                if "CidrBlock" in entry:
                    block = entry["CidrBlock"]
                else:
                    block = entry["Ipv6CidrBlock"]
                if IPAddress(source_ip) in IPNetwork(block):
                    if entry["RuleAction"] == "allow":
                        if proto == "-1":
                            return True
                        else:
                            confirmed_protocols.append(proto)
                            if set(confirmed_protocols) == set(protocols):
                                return True
                    # If there is a rule denying this particular IP
                    # move on to the next IP address, since any allow rules
                    # after this will be ignored
                    if entry["RuleAction"] == "deny":
                        continue
    return False


def groupsAllow(source_ips, required_range, interface_groups, protocols):
    """
    Method that evaluates EC2 instance security groups to determine whether at
    least one IP address in a list can send traffic to the instance over the
    given protocols on at least one port in the required range.

        Parameters:
            source_ips (list): The list of IP addresses
            required_range (range or list): The range of ports
            interface_groups (list): The specified security groups
            protocols (list): The list of protocols

        Returns:
            bool: Whether the security groups allow the communication
    """
    confirmed_protocols = []
    for int_group in interface_groups:
        sec_groups = EC2_CLIENT.describe_security_groups(
            GroupIds=[int_group["GroupId"]]
        )["SecurityGroups"]
        for sec_group in sec_groups:
            for permission in sec_group["IpPermissions"]:
                proto = permission["IpProtocol"]
                # Skip non-UDP/TCP rules
                if proto == -1 or proto in protocols:
                    # Skip rules that do not apply to the required port range
                    rule_range = range(
                        permission["FromPort"], permission["ToPort"]
                    )
                    if len(rule_range) == 0:
                        rule_range = [permission["FromPort"]]
                    port_matches = False
                    for port in rule_range:
                        if port in required_range:
                            port_matches = True
                            break
                    if port_matches == False:
                        continue
                    for ip_range in permission["IpRanges"]:
                        for source_ip in source_ips:
                            if IPAddress(source_ip) in IPNetwork(
                                ip_range["CidrIp"]
                            ):
                                # If the rule applies to all protocols, then do not
                                # check for other protocols
                                if proto == -1:
                                    return True
                                else:
                                    confirmed_protocols.append(proto)
                                    if set(confirmed_protocols) == set(
                                        protocols
                                    ):
                                        return True
    return False


def findSubnetAcl(subnet_id, acls):
    """
    Method that returns the acl assigned to the specified subnet

        Parameters:
            subnet_id (str): The ID of the subnet
            acls (obj): The ACLs of a VPC

        Returns:
            acl (obj): The ACL assigned to the subnet
    """
    for acl in acls:
        for association in acl["Associations"]:
            if association["SubnetId"] == subnet_id:
                return acl
    return None


def find_target_with_lowest(targets):
    """
    Method that searches a list of mirror targets for the target with the least
    mirror sessions.

        Parameters:
            targets (list): A list of traffic mirror target IDs

        Returns:
            str: The ID of the mirror target with the least mirror sessions
    """
    t_map = {}
    for target in targets:
        sessions = EC2_CLIENT.describe_traffic_mirror_sessions(
            Filters=[{"Name": "traffic-mirror-target-id", "Values": [target]}]
        )["TrafficMirrorSessions"]
        t_map[target] = len(sessions)
    return min(t_map, key=t_map.get)


def lambda_handler(event, context):
    newId = event["detail"]["instance-id"]
    response = EC2_CLIENT.describe_instances(InstanceIds=[newId])
    for reservation in response["Reservations"]:
        for instance in reservation["Instances"]:
            for interface in instance["NetworkInterfaces"]:
                interface_id = interface["NetworkInterfaceId"]
                # Only create the mirror session if no mirror
                # session exists for this instance
                sessions = EC2_CLIENT.describe_traffic_mirror_sessions(
                    Filters=[
                        {
                            "Name": "network-interface-id",
                            "Values": [interface_id],
                        }
                    ]
                )["TrafficMirrorSessions"]
                if sessions:
                    return {
                        "statusCode": 200,
                        "body": json.dumps(
                            "Mirror session already exists for this instance"
                        ),
                    }
                else:
                    result = create_mirror(interface_id, TARGETS)
                    if "error" in result:
                        return {
                            "statusCode": 400,
                            "body": json.dumps("Error: " + result["error"]),
                        }
                    else:
                        return {
                            "statusCode": 200,
                            "body": json.dumps(
                                "Created traffic mirror: " + result["name"]
                            ),
                        }
