# SUNBURST

## sunburst_detect.py

This Python script searches the ExtraHop system for the following data.
* All DNS queries that reference the Command and Control domains associated with the SUNBURST backdoor attack, such as avsvmcloud[.]com.
* Every time that a device on your network contacted an IP address associated with the SUNBURST backdoor attack.

At least Python version 3.6 is required.

After you have downloaded the script and threats.json, on Windows, run the following command from the directory where you saved the script.

```
py .\sunburst_detect.py -t HOST -a API_KEY
```

On Linux and Mac OS X, run the following command from the directory where you saved the script.

```
python3 ./sunburst_detect.py -t HOST -a API_KEY
```

*Note*: In the above command, replace the following configuration variables with information from your environment:

* *HOST*: The hostname of your ExtraHop system
* *API_KEY*: Your API key. If you do not have an API key, see [Generate an API key](https://docs.extrahop.com/current/rest-api-guide/#generate-an-api-key).

By default the script checks from the current date to 2020-07-31. You can specify a different time period with the --from-time and --until-time parameters. For example, values of --from-time 2020-11-01 --until-time 2020-12-01 check from November 1st to December 1st.

The command displays progress output similar to the following text:

```
Getting all active devices between 2020-07-31 00:00:00 - 2020-12-18 16:46:32
Requesting 0
Requesting 1000
...
Querying against 6402 devices
Fetching application host metrics.
Processing 3055 stats
Getting device host metrics: 2020-12-17 16:46:32 - 2020-12-18 16:46:32
 getting metrics for 1-200 of 6402 devices
 getting metrics for 201-400 of 6402 devices
...
```

First the list of all devices are fetched in blocks of 1000. Then devices are processed in blocks of 200, a day at a time.

After the command completes, if there are any DNS or IP address matches, the final output will be similar to the following:

```
Found Sunburst host indicators in application metrics (see output.csv).
```

Check the output CSV file (output.csv) for details of any DNS or IP address matches similar to the following:

```
time,object_type,object_id,name,ipaddr,macaddr,indicator,count,uri
2020-12-17 17:45:00,device,1510,exampledomain.com,10.4.1.6,00:12:34:56:78:90,www.avsvmcloud.com,2,
```

For more information, see [How to Hunt for, Detect, and Respond to SUNBURST](https://www.extrahop.com/company/blog/2020/detect-and-respond-to-sunburst/) and
[Analyzing the SolarWinds Orion SUNBURST Attack Campaign For Threat Intelligence](https://www.extrahop.com/company/blog/2020/analyzing-sunburst/).

## threats.json

This file contains a list of suspicious IP addresses associated with the SUNBURST backdoor attack.
