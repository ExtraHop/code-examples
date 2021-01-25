# ExtraHop code examples

This repository includes example scripts that configure and automate interactions with ExtraHop systems through the REST and Trigger APIs. These scripts demonstrate functionality that can help developers write their own integrations and tools. These scripts are not intended to be deployed in production environments.

## Scripts

This repository contains the following example scripts.

### add-cloud-props-azure

This Python script imports Azure device properties into the ExtraHop system. The script assigns cloud device properties to every device discovered by the ExtraHop system with a MAC address that belongs to an Azure VM network interface.

For more information, see [Add device cloud instance properties through the REST API](https://docs.extrahop.com/current/rest-add-cloud-prop/).

### add-cloud-props-lambda

This Python script imports AWS EC2 instance properties into the ExtraHop system. The script maps network interfaces of EC2 instances to devices discovered on the ExtraHop system by MAC address.

For more information, see [Add device cloud instance properties through the REST API](https://docs.extrahop.com/current/rest-add-cloud-prop/).

### add-observations

This Python script creates associations on the ExtraHop system based on a CSV log file from OpenVPN.

For more information, see [Add observations through the REST API](https://docs.extrahop.com/current/rest-add-observation/)

### bash-rx360-auth

This Bash script generates a temporary API access token with the cURL command and then authenticates two simple requests with the token that retrieve devices and device groups from the Reveal(x) 360 REST API.

For more information, see [Generate a REST API token](https://docs.extrahop.com/current/rx360-rest-api/#generate-a-rest-api-token)

### change-dashboard-owner

This Python script searches for all dashboards owned by a given user account and changes the owner to a new user account.

For more information, see [Change a dashboard owner through the REST API](https://docs.extrahop.com/current/rest-change-dashboard-ownership/)

### create-backup

This Python script creates backups of ExtraHop system customizations, such as bundles, triggers, dashboards, and users through the REST API. The script creates the backups on the ExtraHop system and then downloads each backup to the local machine.

For more information, see [Back up the ExtraHop system through the REST API](https://docs.extrahop.com/current/rest-backup/).

### create-custom-device

This Python script creates custom devices by reading criteria from a CSV file.

For more information, see [Create custom devices through the REST API](https://docs.extrahop.com/current/rest-create-custom-devices/)

### create-device-groups

This Python script creates device groups through the REST API. The script creates each device group by reading a list of IP addresses and CIDR blocks from a CSV file.

For more information, see [Create a device group through the REST API](https://docs.extrahop.com/current/rest-create-device-group/).

### extract-device-list

This Python script extracts the device list, including all device metadata, and writes the list to a CSV file.

For more information, see [Extract the device list through the REST API](https://docs.extrahop.com/current/rest-extract-devices/).

### extract-metrics

This Python script extracts the total count of HTTP responses a server with an ID of 1298 sent over five minute time intervals and then writes the values to a csv file.

For more information, see [Extract metrics through the REST API](https://docs.extrahop.com/current/rest-extract-metrics/).

### lambda-traffic-mirror

This Python script automatically mirrors traffic from EC2 instances to your ExtraHop Reveal(x) 360 sensors.

For more information, see [Automate traffic mirroring for Reveal(x) 360 with Lambda](https://docs.extrahop.com/current/lambda-traffic-mirror/).

### migrate-saml

The Python scripts in this directory migrate user customizations from remote users to SAML through the REST API.

For more information, see [Migrate to SAML from LDAP through the REST API](https://docs.extrahop.com/current/migrate-saml-rest/).

### py-rx360-auth

This Python script generates a temporary API access token and then authenticates two simple requests with the token that retrieve devices and device groups from the Reveal(x) 360 REST API.

For more information, see [Generate a REST API token](https://docs.extrahop.com/current/rx360-rest-api/#generate-a-rest-api-token).

### query-records-explore

This Python script retrieves records from an Explore appliance.

For more information, see [Query for records through the REST API](https://docs.extrahop.com/current/rest-query-records/).

### query-records-third-party

This Python script retrieves records from a third-party recordstore.

For more information, see [Query for records through the REST API](https://docs.extrahop.com/current/rest-query-records/).

### search-device

This Python script searches for a list of devices by IP address. The script then outputs the ExtraHop discovery ID for each IP address.

For more information, see [Search for a device through the REST API](https://docs.extrahop.com/current/rest-search-for-device/).

### self-managed-sensor-rx360-connect

This Python script connects a list of sensors to Reveal(x) 360 through the REST API. The script reads a list of sensor URLs and Reveal(x) 360 tokens from a CSV file. You must [generate the Reveal(x) 360 tokens](https://docs.extrahop.com/current/configure-ccp/#generate-a-token) before running the script.

For more information, see [Connect to Reveal(x) 360 from self-managed sensors through the REST API](https://docs.extrahop.com/current/rest-connect-ccp/).

### sunburst

The Python scripts and JSON file in this directory search the ExtraHop system for indicators of the SUNBURST backdoor attack through the REST API. The SUNBURST trojan is dormant for long periods of time and might only occasionally contact external resources. To search for the large number of suspicious hostnames and IP addresses over a long period of time, we recommend that you query metrics through the REST API.

### tag-device

This Python script creates a device tag and then assigns the tag to all devices with the IP addresses specified in a CSV file.

For more information, see [Tag a device through the REST API](https://docs.extrahop.com/current/rest-tag-device/).

### upgrade-system

This Python script upgrades multiple ExtraHop systems by reading URLs, API keys, and firmware file paths from a CSV file.

For more information, see [Upgrade ExtraHop firmware through the REST API](https://docs.extrahop.com/current/rest-upgrade-firmware/).

### upload-stix

This Python script uploads all STIX files in a given directory to a list of ExtraHop systems

For more information, see [Upload STIX files through the REST API](https://docs.extrahop.com/current/rest-upload-stix/).

## Related resources

* [ExtraHop API documentation](https://docs.extrahop.com/current/api/)
* [Trigger API Reference](https://docs.extrahop.com/current/extrahop-trigger-api/)
* [REST API Guide](https://docs.extrahop.com/current/rest-api-guide/)
* [ExtraHop product documentation](https://docs.extrahop.com/current/)
* [ExtraHop corporate site](https://www.extrahop.com/)
