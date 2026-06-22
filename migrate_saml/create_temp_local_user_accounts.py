#!/usr/bin/python3

# COPYRIGHT 2021 BY EXTRAHOP NETWORKS, INC.
#
# This file is subject to the terms and conditions defined in
# file 'LICENSE', which is part of this source code package.

import json
import requests
import sys
import os

# Retrieves the IP address or hostname of the ExtraHop system from an environment variable.
HOST = os.environ['EXTRAHOP_HOST']

# Retrieves the API key from an environment variable.
API_KEY = os.environ['EXTRAHOP_API_KEY']

PASSWORD = '64IxICj6F0z51ZvCLdGS'


USER_FILE = 'user_map.json'
TYPE_TO_COPY = 'remote_username'
TYPE_TO_CREATE = 'local_username'
USER_TYPE = 'local'

# Method that generates the name of the new user
# from the name of the user being copied
def generateName(name):
    return name + '_local'

# Method that creates a local account for the specified user
def createUser(new_name, user):
    url = HOST + '/api/v1/users'
    headers = {'Content-Type': 'application/json',
               'Accept': 'application/json',
               'Authorization': 'ExtraHop apikey=%s' % API_KEY}
    user_params = {'username': new_name,
                   'name': user['name'],
                   'granted_roles': {
                        "write": "personal",
                        "ndr": "full",
                        "npm": "full"
                    },
                   'type': USER_TYPE}
    user_params['password'] = PASSWORD
    r = requests.post(url, headers=headers, data=json.dumps(user_params))
    return r

# Method that checks for duplicate usernames
def checkDuplicates(u_list):
    checked = []
    duplicates = set()
    for user in u_list:
        for c in checked:
            if user.lower() == c.lower():
                duplicates.add(user)
                duplicates.add(c)
        checked.append(user)
    s = sorted(duplicates, key=str.lower)
    return s

with open(USER_FILE) as json_file:
    user_map = json.load(json_file)

u_list = []
for user in user_map:
    u_list.append(user[TYPE_TO_COPY])
duplicates = checkDuplicates(u_list)
if duplicates:
    print("Error: The following duplicate usernames were found:")
    for user in duplicates:
        print('    ' + user)
    print('Local and SAML user accounts cannot share usernames, regardless of case. Rename or delete duplicates before continuing.')
    sys.exit()

failed = []
for user in user_map:
    username = user[TYPE_TO_COPY]
    new_name = generateName(username)
    r = createUser(new_name, user)
    if r.status_code == 201:
        user[TYPE_TO_CREATE] = new_name
        print('Successfully created new user account for ' + username + ': ' + new_name)
    else:
        failed.append([username, r.status_code, r.text])

if failed:
    print('')
    print('Failed to create duplicate local user accounts for the following users:')
    for error in failed:
        print('')
        for message in error:
            print(message)

with open(USER_FILE, 'w') as outfile:
    json.dump(user_map, outfile)
