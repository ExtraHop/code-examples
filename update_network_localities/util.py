#!/usr/bin/python3

# COPYRIGHT 2022 BY EXTRAHOP NETWORKS, INC.
#
# This file is subject to the terms and conditions defined in
# file 'LICENSE', which is part of this source code package.
import requests
from urllib.parse import urlunparse
import base64
import sys


def add_api_args(parser):
    parser.add_argument(
        "--apikey",
        type=str,
        default="",
        help="The REST API key for the console or sensor.",
    )
    parser.add_argument(
        "--id",
        type=str,
        default="",
        help="The ID of the Reveal(x) 360 REST API credentials.",
    )
    parser.add_argument(
        "--secret",
        type=str,
        default="",
        help="The secret of the Reveal(x) 360 REST API credentials.",
    )


def get_token(args):
    """
    Method that generates and retrieves a temporary API access token for Reveal(x) 360 authentication.

        Returns:
            str: A temporary API access token
    """
    auth = base64.b64encode(bytes(args.id + ":" + args.secret, "utf-8")).decode(
        "utf-8"
    )
    headers = {
        "Authorization": "Basic " + auth,
        "Content-Type": "application/x-www-form-urlencoded",
    }
    url = urlunparse(("https", args.host, "/oauth2/token", "", "", ""))
    r = requests.post(
        url,
        headers=headers,
        data="grant_type=client_credentials",
    )
    try:
        return r.json()["access_token"]
    except:
        print(r.text)
        print(r.status_code)
        print("Error retrieving token from Reveal(x) 360")
        sys.exit()


def get_auth_header(args):
    """
    Method that adds an authorization header for a request. For Reveal(x) 360, adds a temporary access
    token. For self-managed appliances, adds an API key.

        Parameters:
            force_token_gen (bool): If true, always generates a new temporary API access token for the request

        Returns:
            header (str): The value for the header key in the headers dictionary
    """
    if args.apikey:
        return f"ExtraHop apikey={args.apikey}"
    else:
        token = get_token(args)
        return f"Bearer {token}"
