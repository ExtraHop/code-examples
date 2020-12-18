# COPYRIGHT 2020 BY EXTRAHOP NETWORKS, INC.
#
# This file is subject to the terms and conditions defined in
# file 'LICENSE', which is part of this source code package.

#!/usr/bin/env python
import argparse
import csv
import json
import ssl
import sys
import urllib.request

DAY_MS = 86400000

MALICIOUS_HOST_REGEX = (
    "/\\.(avsvmcloud|freescanonline|deftsecurity|thedoccloud|incomeupdate"
    "|zupertech|databasegalore|panhardware|websitetheme|highdatabase"
    "|virtualdataserver)\\.com$/"
)

if hasattr(ssl, "_create_unverified_context"):
    ssl._create_default_https_context = ssl._create_unverified_context


def get_current_capture_time(args):
    body = json.dumps({"method": "config.getCaptures", "params": [0]}).encode(
        "utf-8"
    )
    req = urllib.request.Request(
        f"https://{args.target}/a/",
        headers={
            "Accept": "application/json",
            "Authorization": f"ExtraHop apikey={args.api_key}",
            "Content-Type": "application/json",
        },
        data=body,
    )
    with urllib.request.urlopen(req) as rsp:
        rsp = json.loads(rsp.read().decode("utf-8"))
    return max(c["publicized_time"] for c in rsp["result"])


def get_query_intervals(from_time, until_time, interval_size):
    next_until = until_time
    next_from = until_time - interval_size + 1
    remaining = (until_time - from_time) - interval_size

    while remaining >= 0:
        yield (next_from, next_until)
        next_until = next_until - interval_size
        next_from = max(next_from - interval_size, from_time)
        remaining -= interval_size


def api_request(args, path, body=None):
    if body:
        body = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        f"https://{args.target}/api/v1/{path}",
        headers={
            "Accept": "application/json",
            "Authorization": f"ExtraHop apikey={args.api_key}",
            "Content-Type": "application/json",
        },
        data=body,
    )
    with urllib.request.urlopen(req) as rsp:
        rsp = json.loads(rsp.read().decode("utf-8"))
    return rsp


device_cache = {}
appliance_id_cache = {}


def get_device(args, oid):
    global device_cache
    if oid in device_cache:
        return device_cache[oid]
    try:
        device = api_request(args, f"/devices/{oid}")
        device_cache[oid] = device
        return device
    except urllib.error.HTTPError:
        return None


def get_device_oids_by_cidr(args):
    global device_cache
    try:
        devices = api_request(
            args,
            "/devices/search",
            {
                "filter": {
                    "field": "ipaddr",
                    "operand": args.device_cidr,
                    "operator": "=",
                }
            },
        )
        oids = []
        for device in devices:
            oid = device["id"]
            oids.append(oid)
            device_cache[oid] = device
        return oids
    except urllib.error.HTTPError:
        return []


def get_appliance_id(args, node_id):
    global appliance_id_cache
    if node_id in appliance_id_cache:
        return appliance_id_cache[node_id]
    try:
        appliance = api_request(args, f"/appliances/{node_id}")
    except urllib.error.HTTPError:
        return None
    appliance_id = appliance["uuid"].replace("-", "")
    appliance_id_cache[node_id] = appliance_id
    return appliance_id


def get_uri_interval(stat_time):
    # Subtract 6 hours for context
    # NB: UI uses seconds for absolute intervals
    from_time = (stat_time - (6 * 60 * 60 * 1000)) // 1000
    until_time = stat_time // 1000
    return (from_time, until_time)


def get_device_host_uri(args, oid, time, host):
    from_time, until_time = get_uri_interval(time)
    device = get_device(args, oid)
    node_id = oid >> 32
    device_id = device["discovery_id"]
    appliance_id = get_appliance_id(args, node_id)
    if not appliance_id:
        return None
    return (
        f"https://{args.target}/extrahop/#/metrics/devices/"
        f"{appliance_id}.{device_id}/dns-client"
        "?d.drilldown=Host%20Query&d.metric=extrahop.device.dns_client%3Areq"
        f"&d.sources%5B0%5D.applianceId={appliance_id}"
        f"&d.sources%5B0%5D.discoveryId={device_id}"
        "&d.sources%5B0%5D.objectType=device"
        f"&d.tagFilters%5B0%5D.operand={host}"
        "&d.tagFilters%5B0%5D.operator=matches"
        "&d.tagFilters%5B0%5D.subject=label%3AHost%20Query"
        f"&d.v=7.2&delta_type&from={from_time}&interval_type=DT"
        f"&sites%5B0%5D=any&until={until_time}"
    )


def get_device_ip_uri(args, oid, time, ip):
    from_time, until_time = get_uri_interval(time)
    device = get_device(args, oid)
    node_id = oid >> 32
    device_id = device["discovery_id"]
    appliance_id = get_appliance_id(args, node_id)
    if not appliance_id:
        return None
    return (
        f"https://{args.target}/extrahop/#/metrics"
        f"/devices/{appliance_id}.{device_id}"
        "/network?d.drilldown=IP&d.metric=extrahop.device.net%3Abytes_in"
        "&d.sort.direction=desc"
        "&d.sort.field=metric%3Anet_detail%3Abytes_out.count.null%2Fbase"
        f"&d.sources%5B0%5D.applianceId={appliance_id}"
        f"&d.sources%5B0%5D.discoveryId={device_id}"
        f"&d.tagFilters%5B0%5D.operand={ip}&d.tagFilters%5B0%5D.operator=matches"
        "&d.tagFilters%5B0%5D.subject=special%3AIP%20Address&d.v=7.2&delta_type"
        "&d.sources%5B0%5D.objectType=device"
        f"&interval_type=DT&from={from_time}&until={until_time}"
        f"&sites%5B0%5D=any"
    )


def get_application_host_uri(args, oid, time, host):
    from_time, until_time = get_uri_interval(time)
    node_id = oid >> 32
    appliance_id = get_appliance_id(args, node_id)
    if not appliance_id:
        return None
    return (
        f"https://{args.target}/extrahop/#/metrics/applications/"
        f"{appliance_id}._default/dns"
        "?d.drilldown=Host%20Query&d.metric=extrahop.application.dns%3Arsp"
        f"&d.sources%5B0%5D.applianceId={appliance_id}"
        "&d.sources%5B0%5D.discoveryId=_default"
        "&d.sources%5B0%5D.objectType=application"
        f"&d.tagFilters%5B0%5D.operand={host}"
        "&d.tagFilters%5B0%5D.operator=matches"
        "&d.tagFilters%5B0%5D.subject=label%3AHost%20Query"
        f"&d.v=7.2&delta_type&from={from_time}&interval_type=DT"
        f"&sites%5B0%5D=any&until={until_time}"
    )


def show_device_ip_metrics(args, w, oids):
    """
    Searches the target for suspicious activity by device ip metrics
    """
    # load in the suspect ip addresses file
    with open(args.threat_list, "r") as f:
        ti_ips = json.load(f)
    found = False

    ip_regexp = "/^(" + "|".join(ti_ips) + ")$/"
    ip_regexp = ip_regexp.replace(".", "\\.")

    for from_time, until_time in get_query_intervals(
        args.from_time, args.until_time, args.query_batch_size
    ):
        for i in range(0, len(oids), args.oid_batch_size):
            device_batch = oids[i : min(i + args.oid_batch_size, len(oids))]
            resp = api_request(
                args,
                "/metrics",
                body={
                    "cycle": args.cycle,
                    "from": args.from_time,
                    "until": args.until_time,
                    "metric_category": "net_detail",
                    "object_type": "device",
                    "metric_specs": [{"name": "bytes_out", "key1": ip_regexp}],
                    "object_ids": device_batch,
                },
            )

        # parse the stats
        for stat in resp["stats"]:
            oid = stat["oid"]
            for entry in stat["values"][0]:
                device = get_device(args, oid)
                if not device:
                    print(
                        f"Failed to look up matching device with id {oid}",
                        file=sys.stderr,
                    )
                    continue
                found = True
                ipaddr = entry["key"]["addr"]
                w.writerow(
                    {
                        "time": stat["time"],
                        "object_type": "device",
                        "object_id": oid,
                        "name": device["display_name"],
                        "ipaddr": device["ipaddr4"] or device["ipaddr6"],
                        "macaddr": device["macaddr"],
                        "indicator": ipaddr,
                        "count": entry["value"],
                        "uri": get_device_ip_uri(
                            args, oid, stat["time"], ipaddr
                        ),
                    }
                )
    if found:
        print(
            "Found Sunburst IP indicators in device metrics"
            f" (see {args.output})."
        )


def show_application_host_metrics(args, w):
    found = False
    try:
        oids = [
            application["id"]
            for application in api_request(args, "/applications")
            if application["discovery_id"] == "_default"
        ]
    except urllib.error.HTTPError:
        print("WARNING: failed to retrieve default applications")
        return

    body = {
        "cycle": args.cycle,
        "from": args.from_time,
        "until": args.until_time,
        "metric_category": "dns_host_query_detail",
        "metric_specs": [{"name": "req", "key1": f"{MALICIOUS_HOST_REGEX}"}],
        "object_type": "application",
        "object_ids": oids,
    }
    resp_data = api_request(args, "/metrics", body=body)
    for stat in resp_data["stats"]:
        if stat["values"][0]:
            oid = stat["oid"]
            host = stat["values"][0][0]["key"]["str"]
            count = stat["values"][0][0]["value"]
            if not count:
                continue
            found = True
            w.writerow(
                {
                    "time": stat["time"],
                    "object_type": "application",
                    "object_id": oid,
                    "name": "All Activity",
                    "indicator": host,
                    "count": count,
                    "uri": get_application_host_uri(
                        args, oid, stat["time"], host
                    ),
                }
            )
    if found:
        print(
            "Found Sunburst host indicators in application metrics"
            f" (see {args.output})."
        )


def show_device_host_metrics(args, w, oids):
    found = False
    for from_time, until_time in get_query_intervals(
        args.from_time, args.until_time, args.query_batch_size
    ):
        # Get metrics for each device
        resp = api_request(
            args,
            "/metrics",
            body={
                "cycle": args.cycle,
                "from": args.from_time,
                "until": args.until_time,
                "metric_category": "dns_client",
                "metric_specs": [
                    {"name": "host_query", "key1": f"{MALICIOUS_HOST_REGEX}"}
                ],
                "object_type": "device",
                "object_ids": oids,
            },
        )

        # Process matches
        for stat in resp["stats"]:
            if stat["values"][0]:
                found = True
                host = stat["values"][0][0]["key"]["str"]
                count = stat["values"][0][0]["value"]
                time = stat["time"]
                oid = stat["oid"]
                device = get_device(args, oid)
                if not device:
                    print(
                        f"Failed to look up matching device with id {oid}",
                        file=sys.stderr,
                    )
                    continue
                w.writerow(
                    {
                        "time": time,
                        "object_type": "device",
                        "object_id": oid,
                        "name": device["display_name"],
                        "ipaddr": device["ipaddr4"] or device["ipaddr6"],
                        "macaddr": device["macaddr"],
                        "indicator": host,
                        "count": count,
                    }
                )
    if found:
        print(
            "Found Sunburst host indicators in device metrics"
            f" (see {args.output})."
        )


def show_records_host_link(args):
    print("Link to records with possible Sunburst activity:")
    print("------------------------------------------------")
    from_time = args.from_time // 1000
    until_time = args.until_time // 1000
    print(
        f"https://{args.target}/extrahop/#/Records/create?from={from_time}&interval_type=DT&"
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
        default=-1 * DAY_MS * 7 * 20,
        type=int,
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
        "--oid-batch-size",
        type=int,
        default=50,
        help="Dictates the OID batch size to use for device "
        "queries default: %(default)s",
    )
    p.add_argument(
        "--device-cidr",
        default=None,
        type=str,
        help="CIDR of ExtraHop devices to query for Sunburst indicators",
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
        "--output",
        default="output.csv",
        type=str,
        help="File to write matches (CSV), default: %(default)s",
    )
    p.add_argument(
        "--show-records-link",
        action="store_true",
        help="Print a link to records in specified time interval"
        "(default %(default)s",
    )
    p.add_argument(
        "--query-batch-size",
        type=int,
        default=DAY_MS,
        help="Query interval to use in milliseconds default: %(default)s",
    )
    args = p.parse_args()
    if args.device_oids and args.device_cidr:
        print(
            "Must specify either device oids or CIDR, not both", file=sys.stderr
        )
        exit(1)

    try:
        capture_time = get_current_capture_time(args)
    except Exception:
        print(
            "FATAL: failed to get capture time",
            file=sys.stderr,
        )
        exit(1)

    # Converting relative FROM and UNTIL times to absolute time
    if args.from_time <= 0:
        args.from_time = capture_time + args.from_time
    if args.until_time <= 0:
        args.until_time = capture_time + args.until_time

    if args.device_cidr:
        device_oids = get_device_oids_by_cidr(args)
    else:
        device_oids = args.device_oids

    with open(args.output, "w") as csvfile:
        w = csv.DictWriter(
            csvfile,
            fieldnames=[
                "time",
                "object_type",
                "object_id",
                "name",
                "ipaddr",
                "macaddr",
                "indicator",
                "count",
                "uri",
            ],
        )
        w.writeheader()
        show_application_host_metrics(args, w)
        if device_oids:
            show_device_host_metrics(args, w, device_oids)
            show_device_ip_metrics(args, w, device_oids)
        else:
            print(
                "WARNING: found no devices on which to query metrics",
                file=sys.stderr,
            )

    if args.show_records_link:
        show_records_host_link(args)


if __name__ == "__main__":
    main()
