# COPYRIGHT 2020 BY EXTRAHOP NETWORKS, INC.
#
# This file is subject to the terms and conditions defined in
# file 'LICENSE', which is part of this source code package.

#!/usr/bin/python3

import requests
import csv
import json

SENSORS_LIST = 'sensors.csv'

# Read sensor hostnames and connection tokens from CSV
sensors = []
with open(SENSORS_LIST, 'r') as f:
    reader = csv.reader(f)
    for row in reader:
        sensor = {
            'host': row[0],
            'api_key': row[1],
            'token': row[2]
        }
        sensors.append(sensor)

# Function that connects a sensor to CCP
def connectSensor(sensor):
    url = sensor['host'] + '/api/v1/cloud/connect'
    headers = {'Authorization': 'ExtraHop apikey=%s' % sensor['api_key']}
    data = {
        "cloud_token": sensor['token']
    }
    r = requests.post(url, headers=headers, data=json.dumps(data))
    if r.status_code == 201:
        print('Successfully paired ' + sensor['host'])
    else:
        print('Error! Failed to pair ' + sensor['host'])
        print(r.text)

for sensor in sensors:
    connectSensor(sensor)
