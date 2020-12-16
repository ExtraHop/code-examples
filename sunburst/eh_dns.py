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


MALICIOUS_URL_REGEX = (
    "/\\.(avsvmcloud|freescanonline|deftsecurity|thedoccloud|incomeupdate"
    "|zupertech|databasegalore|panhardware|websitetheme|highdatabase)\\.com$/"
)

if hasattr(ssl, "_create_unverified_context"):
    ssl._create_default_https_context = ssl._create_unverified_context


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
        "-o",
        "--object_ids",
        default=[0],
        type=int,
        nargs="+",
        help="The list of numeric values that represent unique identifiers "
        "for networks, devices, applications, VLANs, device groups, or "
        "activity groups. "
        "default: %(default)s",
    )
    args = p.parse_args()

    headers = {
        "accept": "application/json",
        "Authorization": f"ExtraHop apikey={args.api_key}",
        "Content-Type": "application/json",
    }

    """ Get all DNS Clients """
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
            {"name": "host_query", "key1": f"{MALICIOUS_URL_REGEX}"}
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

    """ print the request map """
    pp(request_map)


if __name__ == "__main__":
    main()
