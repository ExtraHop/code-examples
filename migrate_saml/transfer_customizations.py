#!/usr/bin/python3

# COPYRIGHT 2021 BY EXTRAHOP NETWORKS, INC.
#
# This file is subject to the terms and conditions defined in
# file 'LICENSE', which is part of this source code package.
  
import json
import requests
import os

# Retrieves the IP address or hostname of the ExtraHop system from an environment variable.
HOST = os.environ['EXTRAHOP_HOST']

# Retrieves the API key from an environment variable.
API_KEY = os.environ['EXTRAHOP_API_KEY']

OBJECT_TYPE = 'activitymaps'
OBJECT_FILE = 'activity_maps.json'

USER_MAP_FILE = 'user_map.json'
TARGET_USER = 'local_username'
# Method that transfers object ownership to new users
def transferDash(eh_object, new_user):
    url = HOST + '/api/v1/' + OBJECT_TYPE + '/' + str(eh_object['id'])
    headers = {'Content-Type': 'application/json',
               'Accept': 'application/json',
               'Authorization': 'ExtraHop apikey=%s' % API_KEY}
    body = {'owner': new_user}
    r = requests.patch(url, headers=headers, data=json.dumps(body))
    if r.status_code == 204:
        return 'success'
    else:
        return r.json()

# Create a list of old users
old_users = []
with open(USER_MAP_FILE) as json_file:
    user_map = json.load(json_file)
    for user in user_map:
        old_users.append(user['remote_username'])

with open(OBJECT_FILE) as json_file:
    eh_objects = json.load(json_file)

# Create list of ExtraHop objects owned by users that will be deleted
to_do = []
for eh_object in eh_objects:
    try:
        if eh_object['owner'] in old_users:
            to_do.append(eh_object)
    except:
        continue
eh_objects = to_do

# Update ownership of each object
success = []
fail = []
for eh_object in eh_objects:
    userIndex = old_users.index(eh_object['owner'])
    user = user_map[userIndex]
    new_user = user[TARGET_USER]
    updated = transferDash(eh_object, new_user)
    if updated == 'success':
        success.append({'eh_object': eh_object,
                        'new_user': new_user})
    else:
        fail.append([eh_object, updated])

# Print out results of script
if success:
    print('Successfully updated ownership of the following ' + OBJECT_TYPE  + ':')
    for update in success:
        print(update['eh_object']['name'])
        print('    New owner: ' + update['new_user'])
        print('')

if fail:
    print('Failed to update ownership of the following ' + OBJECT_TYPE + ':')
    for failure in fail:
        print('    ' + failure[0]['name'])
        print('    ' + str(failure[1]))
        print('')
