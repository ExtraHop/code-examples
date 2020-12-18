# SUNBURST

## sunburst_detect.py

This Python script searches the ExtraHop system for the following.
* All DNS queries that reference the Command and Control domains associated with the SUNBURST backdoor attack, such as avsvmcloud[.]com.
* Every time that a device on your network contacted an IP address associated with the SUNBURST backdoor attack.

After you have downloaded the script and threats.json, run the following command from the directory where you saved the script.

```
python3 ~/sunburst_detect.py -t HOST -a API_KEY
```

*Note*: In the above command, replace the following configuration variables with information from your environment:

* *HOST*: The hostname of your ExtraHop system
* *API_KEY*: Your API key. If you do not have an API key, see [Generate an API key](https://docs.extrahop.com/current/rest-api-guide/#generate-an-api-key).

By default the script checks from now back to 2020-07-31. You can specify a different time period with the --from-time and --until-time parameters. For example, values of --from-time 2020-11-01 --until-time 2020-12-01 checks from November 1st to December 1st.

The command displays progress output similar to the following text:

```
Getting all active devices between 1596178800000 - 1608325832555
Requesting 0
Requesting 1000
...
Querying against 6387 devices
Fetching application host metrics.
Processing 3052 stats
Devices batch 0 of 6387
Devices batch 200 of 6387
...
```

Once the command completes, check the output CSV file (output.csv) for any DNS or IP matches:

For more information, see [How to Hunt for, Detect, and Respond to SUNBURST](https://www.extrahop.com/company/blog/2020/detect-and-respond-to-sunburst/) and
[Analyzing the SolarWinds Orion SUNBURST Attack Campaign For Threat Intelligence](https://www.extrahop.com/company/blog/2020/analyzing-sunburst/).

## threats.json

This file contains a list of suspicious IP addresses associated with the SUNBURST backdoor attack.

For more information, see [Analyzing the SolarWinds Orion SUNBURST Attack Campaign For Threat Intelligence](https://www.extrahop.com/company/blog/2020/analyzing-sunburst/).
