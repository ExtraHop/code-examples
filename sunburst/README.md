# SUNBURST

## eh_dns.py

This Python script searches the ExtraHop system for all DNS queries that reference the Command and Control domains associated with the SUNBURST backdoor attack, such as avsvmcloud[.]com.

After you have downloaded the script, run the following command from the directory where you saved the script.

```
python3 ~/eh_dns.py -t HOST -a API_KEY
```

*Note*: In the above command, replace the following configuration variables with information from your environment:

* *HOST*: The hostname of your ExtraHop system
* *API_KEY*: Your API key. If you do not have an API key, see [Generate an API key](https://docs.extrahop.com/current/rest-api-guide/#generate-an-api-key).

If the command displays no output, the script did not find any queries for the command and control servers in the specified time period. The default time period is the last 30 minutes. You can specify a different time period with the --from-time parameter. For example, a value of -3600000 changes the time window to the last hour.

If the command displays output similar to the following text, you might have been compromised and should investigate further:

```
{'uri': 'foo.thedoccloud.com', 'count': 6}
{'uri': 'bar.thedoccloud.com', 'count': 6}
{'uri': 'www.freescanonline.com', 'count': 6}
{'uri': 'www4.freescanonline.com', 'count': 3}
```

For more information, see [How to Hunt for, Detect, and Respond to SUNBURST](https://www.extrahop.com/company/blog/2020/detect-and-respond-to-sunburst/).

## sunburst_ip_threathunt.py

This Python script searches the ExtraHop system for every time that a device on your network contacted an IP address associated with the SUNBURST backdoor attack.

After you have downloaded the script, run the following command from the directory where you saved the script.

```
python3 sunburst_ip_threathunt.py --host HOST --apikey API_KEY
```

*Note*: In the above command, replace the following configuration variables with information from your environment:

* *HOST*: The hostname of your ExtraHop system
* *API_KEY*: Your API key. If you do not have an API key, see [Generate an API key](https://docs.extrahop.com/current/rest-api-guide/#generate-an-api-key).

If the command displays no output, the script did not find any suspicious activity in the specified time period. The default time period is 10 weeks. You can specify a different time window with the --lookback parameter. For example, a value of 20 changes the time window to 20 weeks.

If the command displays output similar to the following text, you might have been compromised and should check the output CSV file (extrahop_sunburst_ip_hits.csv) to investigate further:

```
[2020-11-30 16:09:00] 5678 (c83a6b2c314f0000) -> 13.56.226.124
```

*Warning*: This script can consume significant system resources. The script retrieves all of the devices on the ExtraHop system and inspects metrics over a long period of time.

For more information, see [Analyzing the SolarWinds Orion SUNBURST Attack Campaign For Threat Intelligence](https://www.extrahop.com/company/blog/2020/analyzing-sunburst/).

## threats.json

This file contains a list of suspicious IP addresses associated with the SUNBURST backdoor attack.

For more information, see [Analyzing the SolarWinds Orion SUNBURST Attack Campaign For Threat Intelligence](https://www.extrahop.com/company/blog/2020/analyzing-sunburst/).
