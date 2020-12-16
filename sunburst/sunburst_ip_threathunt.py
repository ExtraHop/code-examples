import argparse

import http.client
from urllib.parse import urlencode
import ssl

import json
import datetime

# requests.packages.urllib3.disable_warnings()

parser = argparse.ArgumentParser(description='Match ExtraHop curated SUNBURST IP IOCs')
parser.add_argument('-t', '--host', dest='host', help='EDA or ECA Host', default="extrahop")
parser.add_argument('-k', '--apikey', dest='apikey', help='ExtraHop API Key', required=True)
parser.add_argument('-l', '--lookback', dest='lookback', help='lookback, in weeks, to query', type=int, default=10)
parser.add_argument('-v', '--verbose', dest='verbose', help='Control output', type=bool, default=False)

parser.add_argument('--starttime', dest='starttime', help='Absolute search start time, in Epoch milliseconds', type=int, default=None)
parser.add_argument('--endtime', dest='endtime', help='Absolute search end time, in Epoch milliseconds', type=int, default=None)

parser.add_argument('--devicesfile', dest='devicesfile', help='File of devices to be searched', default=None)

parser.add_argument('--output-prefix', dest='prefix', help='Prefix for output files', default='')
parser.add_argument('--threat-list', dest='ti_file', default='threats.json', help = 'A JSON file with a list of IPs')

args = parser.parse_args()


############################ USER CONFIGURATIONS ###############################
api_key = args.apikey
host = args.host

if args.starttime and args.endtime:
    if args.lookback:
        print(f'Both relative and absolute time search. Defaulting to absolute.')
    relative_time = args.starttime
    timestamp_end = args.endtime
else:
    relative_time = -1 *  args.lookback * 7 * 24 * 60 * 60 * 1000   # N weeks in milliseconds
    timestamp_end = 0                               # Current time

metric_category = "net_detail"
object_type = "device"
metric_spec_name = "bytes_out"

ip_file = 'ip_threats_sorted.txt'
########################## END USER CONFIGURATIONS #############################

context = ssl._create_unverified_context()
conn = http.client.HTTPSConnection(host, context=context)

headers = {'Content-Type': 'application/json',
           'Accept': 'application/json',
           'Authorization': 'ExtraHop apikey=' + api_key}


print(f'Quering {host} for data...')

device_details = {}
if args.devicesfile is None:
    print(f'Gathering devices...')

    limit = 1000

    params = {
        'active_from': relative_time,
        'active_until': timestamp_end,
        'limit': limit,
        'offset': 0
    }

    while True:
        try:
            conn.request('GET', f'/api/v1/devices?{urlencode(params)}', headers=headers)
            response = conn.getresponse()

        except Exception as e:
            raise e
        if response.status != 200:
            raise ValueError("cursor returned %s" % rsp.status_code)

        devices = json.loads(response.read().decode())
        if len(devices) == 0:
            break

        params['offset'] = params['offset'] + limit
        for device in devices:
            device_details[device['id']] = {
                'extrahop_id':  device['extrahop_id'],
                'display_name': device['display_name'],
                'macaddr': device['macaddr'],
                'ipaddr': device['ipaddr4'] if device['ipaddr4'] else device['ipaddr6'] if device['ipaddr6'] else ''
            }

    with open(f'./{args.prefix}_device_ids.csv', 'w') as f:
        f.write('id,extrahop_id,display_name,macaddr,ipaddr\n')
        f.writelines([f'{device},{device_details[device]["extrahop_id"]},' +
            f'{device_details[device]["display_name"]},{device_details[device]["macaddr"]},'+
            f'{device_details[device]["ipaddr"]}\n' for device in device_details])

    print(f'Found {len(device_details)} devices. Writing them to ./output/device_ids.txt')
else:
    with open(args.devicesfile, 'r') as f:
        line = f.readline().strip()
        if line[:2] != 'id':  # No header
            line = line.split(',')
            device_details[int(line[0])] = {
                'extrahop_id':  line[1],
                'display_name': line[2],
                'macaddr': line[3],
                'ipaddr': line[4],
            }
        for line in f.readlines():
            line = line.strip().split(',')
            device_details[int(line[0])] = {
                'extrahop_id':  line[1],
                'display_name': line[2],
                'macaddr': line[3],
                'ipaddr': line[4],
            }
    print(f'Read {len(device_details)} devices from  {args.devicesfile}')
print(f'Iterating through devices and searching for IP hits against ExtraHop IP IOC')

with open(args.ti_file, 'r') as f:
    ti_ips = json.load(f)

with open(f'./{args.prefix}_extrahop_sunburst_ip_hits.csv', 'w') as f:
    f.write('timestamp,id,extrahop_id,display_name,macaddr,device_ipaddr,sunburst_ipaddr\n')
    for device_id in device_details:
        if args.verbose:
            print(f'Searching device {device_id}.', end='')
        url = 'https://' + host + '/api/v1/metrics'
        data = {
            "cycle": "auto",
            "from": relative_time,
            "metric_category": metric_category,
            "object_type": object_type,
            "metric_specs": [
                {
                    "name": metric_spec_name
                }
            ],
            "object_ids": [
                device_id
            ],
            "until": timestamp_end
        }

        conn.request('POST', f'/api/v1/metrics', json.dumps(data), headers=headers)
        response = conn.getresponse()
        rsp_json = json.loads(response.read().decode())

        for time_slice in rsp_json['stats']:
            for entry in time_slice['values'][0]:
                if entry['key']['addr'] in ti_ips:
                    ts = datetime.datetime.fromtimestamp(time_slice['time'] / 1000).strftime('%Y-%m-%d %H:%M:%S')
                    print(f'[{ts}] {device_id} ({device_details[device_id]["extrahop_id"]}) -> {entry["key"]["addr"]}')
                    f.write(f'{ts},{device_id},{device_details[device_id]["extrahop_id"]},'+
                        f'{device_details[device_id]["display_name"]},{device_details[device_id]["macaddr"]},'+
                        f'{device_details[device_id]["ipaddr"]},{entry["key"]["addr"]}\n')

            if args.verbose:
                print('.', end='')
        if args.verbose:
            print()
