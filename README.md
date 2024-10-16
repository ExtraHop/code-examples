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

### cloudformation-traffic-mirror

This AWS CloudFormation template automatically mirrors traffic from EC2 instances to your ExtraHop sensors.

For more information, see [Automate AWS Traffic Mirroring with CloudFormation](https://docs.extrahop.com/current/lambda-traffic-mirror/).

### create-backup

This Python script creates backups of ExtraHop system customizations, such as bundles, triggers, dashboards, and users through the REST API. The script creates the backups on the ExtraHop system and then downloads each backup to the local machine.

For more information, see [Back up the ExtraHop system through the REST API](https://docs.extrahop.com/current/rest-backup/).

### create-custom-device

This Python script creates custom devices by reading criteria from a CSV file.

For more information, see [Create custom devices through the REST API](https://docs.extrahop.com/current/rest-create-custom-devices/)

### create-device-groups

This Python script creates device groups through the REST API. The script creates each device group by reading a list of IP addresses and CIDR blocks from a CSV file.

For more information, see [Create a device group through the REST API](https://docs.extrahop.com/current/rest-create-device-group/).

### deploy-kubernetes-daemon

This directory contains files that configure a Kubernetes DaemonSet that forwards packets from pods to the ExtraHop system.

For more information, see [Configure packet forwarding for Kubernetes pods](https://docs.extrahop.com/current/configure-rpcap-kubernetes). 

### extract-device-list

This Python script extracts the device list, including all device metadata, and writes the list to a CSV file.

For more information, see [Extract the device list through the REST API](https://docs.extrahop.com/current/rest-extract-devices/).

### extract-files

This Python script extracts files from packets that match a specified query.

For more information, see [Extract files from packets through the REST API](https://docs.extrahop.com/current/rest-extract-files/)

### extract-metrics

This Python script extracts the total count of HTTP responses a server with an ID of 1298 sent over five minute time intervals and then writes the values to a csv file.

For more information, see [Extract metrics through the REST API](https://docs.extrahop.com/current/rest-extract-metrics/).

### f5-irules

For more information about these iRules, see [Session key forwarding from an F5 LTM](https://docs.extrahop.com/current/customers/deploy-eda-f5ltm)

### lambda-traffic-mirror

This Python script automatically mirrors traffic from EC2 instances to your ExtraHop sensors. This script has been deprecated and is replaced by the traffic mirroring CloudFormation template.

For more information about this script, see [Automate traffic mirroring with AWS Lambda](https://docs.extrahop.com/9.5/lambda-traffic-mirror/). For information about the CloudFormation template, see [Automate AWS Traffic Mirroring with CloudFormation](https://docs.extrahop.com/current/lambda-traffic-mirror/).

### migrate-detection-hiding

The Python scripts in this directory migrate detection hiding rules. The migrate-detection-hiding.py script migrates tuning rules from an ECA VM to Reveal(x) 360. The migrate-detection-hiding-enterprise.py script migrates tuning rules from an ECA VM to another ECA VM.

For more information, see [Migrate detection hiding rules](rest-migrate-detection-rules).

### migrate-saml

The Python scripts in this directory migrate user customizations from remote users to SAML through the REST API.

For more information, see [Migrate to SAML from LDAP through the REST API](https://docs.extrahop.com/current/migrate-saml-rest/).

### ml-api-logger

This Go script recieves and writes logs sent from an ExtraHop sensor or console. The logs contain a record of all API interactions between the sensor or console and the ExtraHop Machine Learning Service.

For more information, see [Export logs for Machine Learning Service API interactions](https://docs.extrahop.com/current/export-ml-logs)

### py-rx360-auth

This Python script generates a temporary API access token and then authenticates two simple requests with the token that retrieve devices and device groups from the Reveal(x) 360 REST API.

For more information, see [Generate a REST API token](https://docs.extrahop.com/current/rx360-rest-api/#generate-a-rest-api-token).

### query-records-explore

This Python script retrieves records from an Explore appliance.

For more information, see [Query for records through the REST API](https://docs.extrahop.com/current/rest-query-records/).

### query-records-third-party

This Python script retrieves records from a third-party and cloud recordstores.

For more information, see [Query for records through the REST API](https://docs.extrahop.com/current/rest-query-records/).

### rollback-firmware

This Python script rolls back firmware on multiple ExtraHop systems by reading URLs and API keys from a CSV file. Rolling back the firmware on an appliance resets the datastore and removes all metrics.

For more information, see [Roll back firmware through the REST API](https://docs.extrahop.com/current/rest-rollback/)

### search-device

This Python script searches for a list of devices by IP address. The script then outputs the ExtraHop discovery ID for each IP address.

For more information, see [Search for a device through the REST API](https://docs.extrahop.com/current/rest-search-for-device/).

### self-managed-sensor-rx360-connect

This Python script connects a list of sensors to Reveal(x) 360 through the REST API. The script reads a list of sensor URLs and Reveal(x) 360 tokens from a CSV file. You must [generate the Reveal(x) 360 tokens](https://docs.extrahop.com/current/configure-ccp/#generate-a-token) before running the script.

For more information, see [Connect to Reveal(x) 360 from self-managed sensors through the REST API](https://docs.extrahop.com/current/rest-connect-ccp/).

### specify-custom-make-model

This Python script reads custom makes and models from a CSV file and adds them to devices with specified IP addresses.

For more information, see [Specify custom device makes and models through the REST API](https://docs.extrahop.com/current/rest-specify-custom-make-model/).

### specify-high-value

This Python script reads IP addresses from a CSV file and specifies all devices with those IP addresses as high value.

For more information, see [Specify devices as high value through the REST API](https://docs.extrahop.com/current/rest-specify-high-value/).

### sunburst

The Python scripts and JSON file in this directory search the ExtraHop system for indicators of the SUNBURST backdoor attack through the REST API. The SUNBURST trojan is dormant for long periods of time and might only occasionally contact external resources. To search for the large number of suspicious hostnames and IP addresses over a long period of time, we recommend that you query metrics through the REST API.

### tag-device

This Python script creates a device tag and then assigns the tag to all devices with the IP addresses specified in a CSV file.

For more information, see [Tag a device through the REST API](https://docs.extrahop.com/current/rest-tag-device/).

### update-network-localities

The Python scripts in this directory help consolidate and add descriptive names to network localities that were created before upgrading to ExtraHop firmware version 9.0.

For more information, see [Update network localities](https://docs.extrahop.com/current/update-network-localities/)

### upgrade-system

This Python script upgrades multiple ExtraHop systems by reading URLs, API keys, and firmware file paths from a CSV file.

For more information, see [Upgrade ExtraHop firmware through the REST API](https://docs.extrahop.com/8.6/rest-upgrade-firmware/).

### upgrade-system-cloud

This Python script downloads firmware from ExtraHop Cloud Services and upgrades multiple ExtraHop systems by reading URLs and API keys from a CSV file. This script is compatible with ExtraHop systems running firmware version 8.7 or later.

For more information, see [Upgrade ExtraHop firmware through the REST API with ExtraHop Cloud Services](https://docs.extrahop.com/current/rest-upgrade-cloud/).

### upgrade-system-url

This Python script downloads firmware images and upgrades multiple ExtraHop systems by reading URLs and API keys from a CSV file. Firmware is downloaded from a specified URL. This script is compatible with ExtraHop systems running firmware version 8.7 or later.

For more information, see [Upgrade ExtraHop firmware through the REST API](https://docs.extrahop.com/current/rest-upgrade-firmware/).

### upload-ids-rules

This Python script uploads a set of curated IDS rules from the ExtraHop Customer Portal to consoles and sensors.

For more information, see [Upload IDS rules to the ExtraHop system through the REST API](https://docs.extrahop.com/current/rest-upload-ids-rules/)

### upload-stix

This Python script uploads all STIX files in a given directory to a list of ExtraHop systems

For more information, see [Upload STIX files through the REST API](https://docs.extrahop.com/current/rest-upload-stix/).

## Related resources

* [ExtraHop API documentation](https://docs.extrahop.com/current/api/)
* [Trigger API Reference](https://docs.extrahop.com/current/extrahop-trigger-api/)
* [REST API Guide](https://docs.extrahop.com/current/rest-api-guide/)
* [ExtraHop product documentation](https://docs.extrahop.com/current/)
* [ExtraHop corporate site](https://www.extrahop.com/)
