# ExtraHop code examples

This repository includes example scripts that configure and automate interactions with ExtraHop systems through the REST and Trigger APIs. These scripts demonstrate functionality that can help developers write their own integrations and tools. These scripts are not intended to be deployed in production environments.

## Scripts

This repository contains the following example scripts.

### bash-rx360-auth

This Bash script generates a temporary API access token with the cURL command and then authenticates two simple requests with the token that retrieve devices and device groups from the Reveal(x) 360 REST API.

For more information, see [Authenticate with the Reveal(x) 360 REST API](https://docs.dev.extrahop.com/current/rest-rx360-auth/)

### create-backup

This Python script creates backups of ExtraHop system customizations, such as bundles, triggers, dashboards, and users through the REST API. The script creates the backups on the ExtraHop system and then downloads each backup to the local machine.

For more information, see [Back up the ExtraHop system through the REST API](https://docs.extrahop.com/current/rest-backup/).

### create-device-groups

This Python script creates device groups through the REST API. The script creates each device group by reading a list of IP addresses and CIDR blocks from a CSV file.

For more information, see [Create a device group through the REST API](https://docs.extrahop.com/current/rest-create-device-group/).

### lambda-traffic-mirror

This Python script automatically mirrors traffic from EC2 instances to your ExtraHop Reveal(x) 360 sensors.

For more information, see [Automate traffic mirroring for Reveal(x) 360 with Lambda](https://docs.dev.extrahop.com/current/rx360-lambda-traffic-mirror/)

### py-rx360-auth

This Python script generates a temporary API access token and then authenticates two simple requests with the token that retrieve devices and device groups from the Reveal(x) 360 REST API.

For more information, see [Authenticate with the Reveal(x) 360 REST API](https://docs.dev.extrahop.com/current/rest-rx360-auth/)

### self-managed-sensor-rx360-connect

This Python script connects a list of sensors to Reveal(x) 360 through the REST API. The script reads a list of sensor URLs and Reveal(x) 360 tokens from a CSV file. You must [generate the Reveal(x) 360 tokens](https://docs.extrahop.com/current/configure-ccp/#generate-a-token) before running the script.

For more information, see [Connect to Reveal(x) 360 from self-managed sensors through the REST API](https://docs.extrahop.com/current/rest-connect-ccp/).

### sunburst

The Python scripts and JSON file in this directory search the ExtraHop system for indicators of the SUNBURST backdoor attack through the REST API. The SUNBURST trojan is dormant for long periods of time and might only occasionally contact external resources. To search for the large number of suspicious hostnames and IP addresses over a long period of time, we recommend that you query metrics through the REST API.

## Related resources

* [ExtraHop API documentation](https://docs.extrahop.com/current/api/)
* [Trigger API Reference](https://docs.extrahop.com/current/extrahop-trigger-api/)
* [REST API Guide](https://docs.extrahop.com/current/rest-api-guide/)
* [ExtraHop product documentation](https://docs.extrahop.com/current/)
* [ExtraHop corporate site](https://www.extrahop.com/)
