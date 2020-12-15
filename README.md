# ExtraHop code examples

This repository includes example scripts that configure and automate interactions with ExtraHop systems through the REST and Trigger APIs. These scripts demonstrate functionality that can help developers write their own integrations and tools. These scripts are not intended to be deployed in production environments.

## Scripts

This repository contains the following example scripts.

### create-backup

This Python script creates backups of ExtraHop system customizations, such as bundles, triggers, dashboards, and users through the REST API. The script creates the backups on the ExtraHop system and then downloads each backup to the local machine.

For more information, see [Back up the ExtraHop system through the REST API](https://docs.extrahop.com/current/rest-backup/).

### create-device-groups

This Python script creates device groups through the REST API. The script creates each device group by reading a list of IP addresses and CIDR blocks from a CSV file.

For more information, see [Create a device group through the REST API](https://docs.extrahop.com/current/rest-create-device-group/).

### self-managed-sensor-rx360-connect

This Python script connects a list of sensors to Reveal(x) 360 through the REST API. The script reads a list of sensor URLs and Reveal(x) 360 tokens from a CSV file. You must [generate the Reveal(x) 360 tokens](https://docs.extrahop.com/current/configure-ccp/#generate-a-token) before running the script.

For more information, see [Connect to Reveal(x) 360 from self-managed sensors through the REST API](https://docs.extrahop.com/current/rest-connect-ccp/).

### sunburst

This Python script retrieves metrics about DNS queries for the Command and Control server domains associated with the SUNBURST backdoor attack.

For more information, see [How to Hunt for, Detect, and Respond to SUNBURST](https://www.extrahop.com/company/blog/2020/detect-and-respond-to-sunburst/).

## Related resources

* [ExtraHop API documentation](https://docs.extrahop.com/current/api/)
* [Trigger API Reference](https://docs.extrahop.com/current/extrahop-trigger-api/)
* [REST API Guide](https://docs.extrahop.com/current/rest-api-guide/)
* [ExtraHop product documentation](https://docs.extrahop.com/current/)
* [ExtraHop corporate site](https://www.extrahop.com/)
