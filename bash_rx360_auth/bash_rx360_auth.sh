#!/bin/bash -x

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

curl -v -H "Authorization: Bearer ${ACCESS_TOKEN}" ${HOST}/api/v1/devices
curl -v -H "Authorization: Bearer ${ACCESS_TOKEN}" ${HOST}/api/v1/devicegroups
