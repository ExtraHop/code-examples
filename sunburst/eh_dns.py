# COPYRIGHT 2020 BY EXTRAHOP NETWORKS, INC.
#
# This file is subject to the terms and conditions defined in
# file 'LICENSE', which is part of this source code package.

#!/usr/bin/env python
import argparse
import json
import ssl
import urllib.request

from pprint import pprint as pp


MALICIOUS_HOST_REGEX = (
    "/\\.(avsvmcloud|freescanonline|deftsecurity|thedoccloud|incomeupdate"
    "|zupertech|databasegalore|panhardware|websitetheme|highdatabase"
    "|virtualdataserver)\\.com$/"
)

if hasattr(ssl, "_create_unverified_context"):
    ssl._create_default_https_context = ssl._create_unverified_context


def show_devices_ip_metrics(args):
    """
    Searches the target for suspicious activity by device ip metrics
    """
    # load in the suspect ip addresses file
    with open(args.threat_list, "r") as f:
        ti_ips = set(json.load(f))

    headers = {
        "accept": "application/json",
        "Authorization": f"ExtraHop apikey={args.api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "cycle": args.cycle,
        "from": args.from_time,
        "until": args.until_time,
        "metric_category": "net_detail",
        "object_type": "device",
        "metric_specs": [{"name": "bytes_out"}],
        "object_ids": args.device_oids,
    }
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        f"https://{args.target}/api/v1/metrics", data=data, headers=headers
    )
    with urllib.request.urlopen(req) as resp:
        resp = json.loads(resp.read().decode("utf-8"))

    # parse the stats
    results = {oid: {"hits": []} for oid in args.device_oids}
    for time_slice in resp["stats"]:
        oid = time_slice["oid"]
        for entry in time_slice["values"][0]:
            if entry["key"]["addr"] in ti_ips:
                results[oid]["hits"].append(
                    {
                        "host": entry["key"].get("host", ""),
                        "time": time_slice["time"],
                        "addr": entry["key"]["addr"],
                        "count": entry["value"],
                    }
                )
    results = {k: v for k, v in results.items() if v["hits"]}
    if results:
        print("Found Sunburst IP indicators in device metrics:")
        pp(results)
    else:
        print("No Sunburst IP indicators found in device metrics.")


def show_application_host_metrics(args):
    headers = {
        "accept": "application/json",
        "Authorization": f"ExtraHop apikey={args.api_key}",
        "Content-Type": "application/json",
    }

    body = {
        "cycle": args.cycle,
        "from": args.from_time,
        "until": args.until_time,
        "metric_category": "dns_host_query_detail",
        "metric_specs": [{"name": "req", "key1": f"{MALICIOUS_HOST_REGEX}"}],
        "object_type": "application",
        "object_ids": args.application_oids,
    }

    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        f"https://{args.target}/api/v1/metrics", data=data, headers=headers
    )
    with urllib.request.urlopen(req) as resp:
        resp_data = json.loads(resp.read().decode("utf-8"))

    matches = []
    for stat in resp_data["stats"]:
        if stat["values"][0]:
            host = stat["values"][0][0]["key"]["str"]
            count = stat["values"][0][0]["value"]
            if not count:
                continue
            matches.append({"host": host, "count": count})
    if matches:
        print("Found Sunburst host indicators in application metrics:")
        pp(matches)
    else:
        print("No Sunburst host indicators found in application metrics.")


def show_device_host_metrics(args):
    """ Get all DNS Clients """
    headers = {
        "accept": "application/json",
        "Authorization": f"ExtraHop apikey={args.api_key}",
        "Content-Type": "application/json",
    }

    body = {
        "active_from": args.from_time,
        "active_until": args.until_time,
        "filter": {
            "field": "activity",
            "operand": "dns_client",
            "operator": "=",
        },
    }
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        f"https://{args.target}/api/v1/devices/search",
        data=data,
        headers=headers,
    )
    with urllib.request.urlopen(req) as resp:
        clients = json.loads(resp.read().decode("utf-8"))

    """ Initialize a device to dns request map. """
    request_map = dict()
    oids = []
    for c in clients:
        request_map[c["id"]] = {
            "display_name": c["display_name"],
            "ipaddr4": c["ipaddr4"],
            "macaddr": c["macaddr"],
            "matches": [],
        }
        oids.append(c["id"])

    """ Get metrics for each dns client """
    body = {
        "cycle": args.cycle,
        "from": args.from_time,
        "until": args.until_time,
        "metric_category": "dns_client",
        "metric_specs": [
            {"name": "host_query", "key1": f"{MALICIOUS_HOST_REGEX}"}
        ],
        "object_type": "device",
        "object_ids": oids,
    }
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        f"https://{args.target}/api/v1/metrics", data=data, headers=headers,
    )
    with urllib.request.urlopen(req) as resp:
        resp = json.loads(resp.read().decode("utf-8"))

    """ Parse the stats and update the device to request map """
    for stat in resp["stats"]:
        if stat["values"][0]:
            host = stat["values"][0][0]["key"]["str"]
            count = stat["values"][0][0]["value"]
            time = stat["time"]
            request_map[stat["oid"]]["matches"].append(
                {"time": time, "host": host, "count": count}
            )

    # Only show positive matches
    request_map = {k: v for k, v in request_map.items() if v["matches"]}
    """ print the request map """
    if request_map:
        print("Found Sunburst host indicators in device metrics:")
        pp(request_map)
    else:
        print("No Sunburst host indicators found in device metrics.")


def show_records_host_link(args):
    print("Link to records with possible Sunburst activity:")
    print("------------------------------------------------")
    # Positive times in the UI refer to the past
    from_time = str(args.from_time).strip("-")
    until_time = str(args.until_time).strip("-")
    print(
        f"https://{args.target}/extrahop/#/Records/create?from={from_time}&interval_type=mSEC&"
        "r.filter=W3sib3BlcmF0b3IiOiJvciIsInJ1bGVzIjpbeyJmaWVsZCI6InFuYW1lOnN0cmluZyIsIm9wZXJh"
        "dG9yIjoifiIsIm9wZXJhbmQiOiJhdnN2bWNsb3VkLmNvbSJ9LHsiZmllbGQiOiJxbmFtZTpzdHJpbmciLCJvc"
        "GVyYW5kIjoiZnJlZXNjYW5vbmxpbmUuY29tIiwib3BlcmF0b3IiOiJ-In0seyJmaWVsZCI6InFuYW1lOnN0cm"
        "luZyIsIm9wZXJhbmQiOiJkZWZ0c2VjdXJpdHkuY29tIiwib3BlcmF0b3IiOiJ-In0seyJmaWVsZCI6InFuYW1"
        "lOnN0cmluZyIsIm9wZXJhbmQiOiJ0aGVkb2NjbG91ZC5jb20iLCJvcGVyYXRvciI6In4ifSx7ImZpZWxkIjoi"
        "cW5hbWU6c3RyaW5nIiwib3BlcmFuZCI6ImluY29tZXVwZGF0ZS5jb20iLCJvcGVyYXRvciI6In4ifSx7ImZpZ"
        "WxkIjoicW5hbWU6c3RyaW5nIiwib3BlcmFuZCI6Inp1cGVydGVjaC5jb20iLCJvcGVyYXRvciI6In4ifSx7Im"
        "ZpZWxkIjoicW5hbWU6c3RyaW5nIiwib3BlcmFuZCI6ImRhdGFiYXNlZ2Fsb3JlLmNvbSIsIm9wZXJhdG9yIjo"
        "ifiJ9LHsiZmllbGQiOiJxbmFtZTpzdHJpbmciLCJvcGVyYW5kIjoicGFuaGFyZHdhcmUuY29tIiwib3BlcmF0"
        "b3IiOiJ-In0seyJmaWVsZCI6InFuYW1lOnN0cmluZyIsIm9wZXJhbmQiOiJ3ZWJzaXRldGhlbWUuY29tIiwib"
        "3BlcmF0b3IiOiJ-In0seyJmaWVsZCI6InFuYW1lOnN0cmluZyIsIm9wZXJhbmQiOiJoaWdoZGF0YWJhc2UuY2"
        "9tIiwib3BlcmF0b3IiOiJ-In0seyJmaWVsZCI6InFuYW1lOnN0cmluZyIsIm9wZXJhbmQiOiJ2aXJ0dWFsZGF"
        "0YXNlcnZlci5jb20iLCJvcGVyYXRvciI6In4ifV0sImxhYmVsIjoiU1VOQlVSU1QgRG9tYWluIEFjdGl2aXR5In1d&"
        "r.limit=50&r.offset=0&r.sort%5B0%5D.direction=desc&r.sort%5B0%5D.field=timestamp&"
        f"r.types%5B0%5D=~dns_request&r.v=8.0&return=clear&until={until_time}"
    )


def main():
    p = argparse.ArgumentParser(
        description="Queries an EDA/ECA for DNS Metrics"
    )
    p.add_argument(
        "-t",
        "--target",
        required=True,
        help="The target appliance to query against.",
    )
    p.add_argument(
        "--threat-list",
        default="threats.json",
        help="A JSON file with a list of IOC IPs",
    )
    p.add_argument(
        "-a",
        "--api-key",
        required=True,
        help="API key for the target appliance.",
    )
    p.add_argument(
        "-f",
        "--from-time",
        default=-1800000,
        help="The beginning timestamp for the request. Time is expressed in "
        "milliseconds since the epoch. 0 indicates the time of the request. "
        "A negative value is evaluated relative to the current time. "
        "default: %(default)s",
    )
    p.add_argument(
        "-u",
        "--until-time",
        default=0,
        help="The ending timestamp for the request. Return "
        "only metrics collected before this time. Follows the same time value "
        "guidelines as the from parameter. "
        "default: %(default)s",
    )
    p.add_argument(
        "-c",
        "--cycle",
        default="auto",
        help="The aggregation period for metrics. Supported values: "
        "'auto', '1sec', '30sec', '5min', '1hr', '24hr'. "
        "default: %(default)s",
    )
    p.add_argument(
        "--device-oids",
        default=[],
        type=int,
        nargs="+",
        help="The list of numeric values that represent unique identifiers "
        "for devices default: %(default)s",
    )
    p.add_argument(
        "--application-oids",
        default=[0],
        type=int,
        nargs="+",
        help="The list of numeric values that represent unique identifiers "
        "for applications, default: %(default)s",
    )
    args = p.parse_args()
    if args.device_oids:
        show_devices_ip_metrics(args)
    show_application_host_metrics(args)
    show_device_host_metrics(args)
    show_records_host_link(args)


if __name__ == "__main__":
    main()
