#!/bin/bash -x

# COPYRIGHT 2021 BY EXTRAHOP NETWORKS, INC.
#
# This file is subject to the terms and conditions defined in
# file 'LICENSE', which is part of this source code package.

# The hostname of the Reveal(x) 360 API. This hostname is displayed in Reveal(x)
# 360 on the API Access page under API Endpoint. The hostname does not
# include the /oauth/token.
HOST="https://example.api.com"
# The ID of the REST API credentials.
ID="abcdefg123456789"
# The secret of the REST API credentials.
SECRET="123456789abcdefg987654321abcdefg"

# Note: Remove the --wrap=0 option if running on a Mac machine. The option is required
# only on Linux machines.
AUTH=$(printf "$ID:$SECRET" | base64 --wrap=0)

ACCESS_TOKEN=$(curl -s \
    -H "Authorization: Basic ${AUTH}" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    --request POST \
     ${HOST}/oauth2/token \
    -d "grant_type=client_credentials" \
    | jq -r '.access_token')

curl -v -X POST -H "Authorization: Bearer ${ACCESS_TOKEN}" --header "Content-Type: application/json" -d "{ \"active_from\": 1, \"active_until\": 0, \"limit\": 100}" ${HOST}/api/v1/devices/search
curl -v -H "Authorization: Bearer ${ACCESS_TOKEN}" ${HOST}/api/v1/devicegroups
