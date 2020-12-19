# COPYRIGHT 2020 BY EXTRAHOP NETWORKS, INC.
#
# This file is subject to the terms and conditions defined in
# file 'LICENSE', which is part of this source code package.

#!/usr/bin/env python
import argparse
import datetime
import csv
import json
import logging
import os
import ssl
import sys
import urllib.request
import time

from urllib.parse import urlencode

DAY_MS = 86400000

MALICIOUS_HOST_REGEX = (
    "/\\.(avsvmcloud|freescanonline|deftsecurity|thedoccloud|incomeupdate"
    "|zupertech|databasegalore|panhardware|websitetheme|highdatabase"
    "|virtualdataserver)\\.com$/"
)

if hasattr(ssl, "_create_unverified_context"):
    ssl._create_default_https_context = ssl._create_unverified_context


def tstr(t):
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t // 1000))


def get_time_ms(dt_str):
    dt = datetime.datetime.strptime(dt_str, "%Y-%m-%d")
    return int(time.mktime(dt.timetuple()) * 1000)


def get_query_intervals(from_time, until_time, interval_size):
    next_until = from_time + interval_size - 1
    while from_time < until_time:
        yield (from_time, next_until)
        from_time += interval_size
        next_until = from_time + interval_size - 1
        if next_until > until_time:
            next_until = until_time


def api_request(args, path, body=None, method=None):
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
    if method:
        req.method = method
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


def process_application_host_stats(args, w, resp_data):
    stats = resp_data.get("stats", [])
    logging.info(f"Processing {len(stats)} stats")
    found = False
    for stat in stats:
        if not stat["values"][0]:
            continue
        oid = stat["oid"]
        for entry in stat["values"][0]:
            host = entry["key"]["str"]
            count = entry["value"]
            if not count:
                continue
            found = True
            w.writerow(
                {
                    "time": tstr(stat["time"]),
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
    return found


def get_all_active_devices(args):
    logging.info(
        "Getting all active devices between %s - %s",
        tstr(args.from_time),
        tstr(args.until_time),
    )
    global device_cache
    LIMIT = 1000
    offset = 0
    oids = []
    while True:
        try:
            body = {
                "active_from": args.from_time,
                "active_until": args.until_time,
                "limit": LIMIT,
                "offset": offset,
            }
            devices = api_request(
                args, f"/devices?{urlencode(body)}", method="GET"
            )
            if len(devices) == 0:
                break

            for device in devices:
                oid = device["id"]
                oids.append(oid)
                device_cache[oid] = device

            logging.info(f"Requesting {offset}")

            offset += len(devices)
        except urllib.error.HTTPError as e:
            logging.info(f"ERROR retrieving /devices {str(e)}")
            return oids
    return oids


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


def process_device_net_detail_stats(args, w, resp):
    found = False
    # parse the stats
    for stat in resp["stats"]:
        if not stat["values"][0]:
            continue
        oid = stat["oid"]
        device = get_device(args, oid)
        if not device:
            logging.info(f"Failed to look up matching device with id {oid}")
            continue
        for entry in stat["values"][0]:
            found = True
            ipaddr = entry["key"]["addr"]
            w.writerow(
                {
                    "time": tstr(stat["time"]),
                    "object_type": "device",
                    "object_id": oid,
                    "name": device["display_name"],
                    "ipaddr": device["ipaddr4"] or device["ipaddr6"],
                    "macaddr": device["macaddr"],
                    "indicator": ipaddr,
                    "count": entry["value"],
                    "uri": get_device_ip_uri(args, oid, stat["time"], ipaddr),
                }
            )
    return found


def show_device_metrics(args, w, category, specs, oids, process_fn):
    found = False

    for from_time, until_time in get_query_intervals(
        args.from_time, args.until_time, args.query_batch_size
    ):
        for i in range(0, len(oids), args.oid_batch_size):
            device_batch = oids[i : i + args.oid_batch_size]
            logging.info(
                "Getting %s metrics from %s - %s for %d-%d of %d devices",
                category,
                tstr(from_time),
                tstr(until_time),
                i + 1,
                i + len(device_batch),
                len(oids),
            )
            resp = api_request(
                args,
                "/metrics",
                body={
                    "cycle": args.cycle,
                    "from": from_time,
                    "until": until_time,
                    "metric_category": category,
                    "object_type": "device",
                    "metric_specs": specs,
                    "object_ids": device_batch,
                },
            )
            found |= for_each_eda(args, w, resp, process_fn)

    return found


def show_device_ip_metrics(args, w, ti_ips, oids):
    """
    Searches the target for suspicious activity by device ip metrics
    """
    ip_regexp = "/^(" + "|".join(ti_ips) + ")$/"
    ip_regexp = ip_regexp.replace(".", "\\.")
    metric_specs = [{"name": "bytes_out", "key1": ip_regexp}]

    return show_device_metrics(
        args,
        w,
        "net_detail",
        metric_specs,
        oids,
        process_device_net_detail_stats,
    )


def show_application_host_metrics(args, w):
    logging.info("Fetching application host metrics.")
    found = False
    try:
        oids = [
            application["id"]
            for application in api_request(args, "/applications")
            if application["discovery_id"] == "_default"
        ]
    except urllib.error.HTTPError:
        logging.info("WARNING: failed to retrieve default applications")
        return

    body = {
        "cycle": args.cycle,
        "from": args.from_time,
        "until": args.until_time,
        "metric_category": "dns_host_query_detail",
        "metric_specs": [{"name": "req", "key1": f"{args.host_regex}"}],
        "object_type": "application",
        "object_ids": oids,
    }
    resp_data = api_request(args, "/metrics", body=body)

    found = for_each_eda(args, w, resp_data, process_application_host_stats)
    return found


def process_device_dns_host_stats(args, w, resp):
    found = False
    for stat in resp["stats"]:
        if stat["values"][0]:
            found = True
            time = stat["time"]
            oid = stat["oid"]
            device = get_device(args, oid)
            if not device:
                logging.info(f"Failed to look up matching device with id {oid}")
                continue
            for entry in stat["values"][0]:
                host = entry["key"]["str"]
                count = entry["value"]
                w.writerow(
                    {
                        "time": tstr(time),
                        "object_type": "device",
                        "object_id": oid,
                        "name": device["display_name"],
                        "ipaddr": device["ipaddr4"] or device["ipaddr6"],
                        "macaddr": device["macaddr"],
                        "indicator": host,
                        "count": count,
                    }
                )
    return found


def for_each_eda(args, w, first_metrics_resp, process_fn):
    found = False
    xid = first_metrics_resp.get("xid")
    if xid is not None:
        # running on an ECA
        eda_count = first_metrics_resp.get("num_results", 0)
        for i in range(eda_count):
            logging.info(
                f"Requesting Data from EDA {i+1}/{eda_count}... Please Wait"
            )
            while True:
                resp_data = api_request(
                    args, f"/metrics/next/{xid}", method="GET"
                )
                if resp_data != "again":
                    break
                time.sleep(0.05)
            eda_found = process_fn(args, w, resp_data)
            found |= eda_found
    else:
        found = process_fn(args, w, first_metrics_resp)
    return found


def show_device_host_metrics(args, w, oids):
    metric_specs = [{"name": "host_query", "key1": f"{args.host_regex}"}]
    return show_device_metrics(
        args, w, "dns_client", metric_specs, oids, process_device_dns_host_stats
    )


def show_records_host_link(args):
    logging.info("Link to records with possible Sunburst activity:")
    logging.info("------------------------------------------------")
    from_time = args.from_time // 1000
    until_time = args.until_time // 1000
    logging.info(
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


def setup_logging(args):
    logger = logging.getLogger("")
    logger.setLevel(logging.INFO)
    console_handler = logging.StreamHandler()
    logger.addHandler(console_handler)
    if args.log_file:
        formatter = logging.Formatter("%(asctime)s %(message)s")
        file_handler = logging.FileHandler(args.log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)


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
        "-H",
        "--host-regex",
        default=MALICIOUS_HOST_REGEX,
        help="Regular expression for malicious hosts",
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
        default="2020-07-31",
        type=str,
        help="The beginning date for the request. Expressed as YYYY-MM-DD "
        "default: %(default)s",
    )
    p.add_argument(
        "-u",
        "--until-time",
        default=None,
        help="The ending date for the request. Return "
        "only metrics collected before this time. Follows the same time value "
        "guidelines as the from parameter. If unspecified, default to now."
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
        default=200,
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
    p.add_argument(
        "--log-file",
        type=str,
        help="Name of file to log messages to: %(default)s",
    )
    args = p.parse_args()

    setup_logging(args)

    if args.device_oids and args.device_cidr:
        print(
            "Must specify either device oids or CIDR, not both", file=sys.stderr
        )
        exit(1)

    # Convert string times to milliseconds since epoch
    try:
        args.from_time = get_time_ms(args.from_time)
    except:
        print("FATAL: invalid from time", args.from_time, file=sys.stderr)
        exit(1)
    if args.until_time:
        try:
            args.until_time = get_time_ms(args.until_time)
        except:
            print("FATAL: invalid until time", args.until_time, file=sys.stderr)
            exit(1)
    else:
        args.until_time = int(time.time() * 1000)

    # load in the suspect ip addresses file
    if not os.path.exists(args.threat_list):
        print("FATAL: threat list", args.threat_list, "does not exist")
        exit(1)
    with open(args.threat_list, "r") as f:
        try:
            ti_ips = json.load(f)
        except:
            print("FATAL: invalid threat list file", args.threat_list)
            exit(1)

    logging.info("Starting...")

    if args.device_cidr:
        device_oids = get_device_oids_by_cidr(args)
    elif args.device_oids:
        device_oids = args.device_oids
    else:
        device_oids = get_all_active_devices(args)
    logging.info(f"Querying against {len(device_oids)} devices")

    f_found_app_host = False
    f_found_device_host = False
    f_found_device_ip = False

    with open(args.output, "w", encoding="utf-8", buffering=1) as csvfile:
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
        f_found_app_host = show_application_host_metrics(args, w)
        if device_oids:
            f_found_device_host = show_device_host_metrics(args, w, device_oids)
            f_found_device_ip = show_device_ip_metrics(
                args, w, ti_ips, device_oids
            )
        else:
            logging.info("WARNING: found no devices on which to query metrics")

    if f_found_app_host or f_found_device_host or f_found_device_ip:
        logging.info("------------------------------------------------")
    if f_found_app_host:
        logging.info(
            "Found Sunburst host indicators in application metrics"
            f" (see {args.output})."
        )
    if f_found_device_host:
        logging.info(
            "Found Sunburst host indicators in device metrics"
            f" (see {args.output})."
        )
    if f_found_device_ip:
        logging.info(
            "Found Sunburst IP indicators in device metrics"
            f" (see {args.output})."
        )
    if args.show_records_link:
        show_records_host_link(args)

    logging.info("Complete")


if __name__ == "__main__":
    main()
