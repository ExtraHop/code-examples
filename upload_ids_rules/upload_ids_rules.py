import requests
from urllib.parse import urlunparse
import csv

# The path of the CSV file
CSV_PATH = "ids.csv"


def readCSV(filepath):
    """
    Function that reads a list of ExtraHop system hostnames,
    API keys, and IDS filenames from a CSV file

        Parameters:
            filepath (str): The path of the CSV file

        Returns:
            list: A list of objects containing the hostnames, API keys, and filenames
    """
    with open(filepath, "r") as f:
        csv_reader = csv.DictReader(f)
        return [row for row in csv_reader]


def uploadIds(host, api_key, ids_file_path):
    """
    Function that uploads a specified IDS file to an ExtraHop appliance.
    The function can upload IDS ruleset files to sensors and IDS resource
    files to consoles.

        Parameters:
            host (str): The hostname or IP address of the appliance
            api_key (str): The API key for the appliance
            ids_file (str): The path of the IDS ruleset or resource file
    """
    url = urlunparse(
        ("https", host, "/api/v1/extrahop/cloudresources", "", "", "")
    )
    headers = {
        "Authorization": f"ExtraHop apikey={api_key}",
        "accept": "application/json",
    }
    with open(ids_file_path, "rb") as ids_file:
        r = requests.post(
            url,
            data=ids_file,
            headers=headers,
        )
    if r.status_code == 202:
        print(f"{ids_file_path} was successfully uploaded to {host}")
        print()
    else:
        print("IDS upload failed")
        print(r.status_code)
        print(r.text)
        print()


def main():
    appliances = readCSV(CSV_PATH)
    for appliance in appliances:
        uploadIds(
            appliance["host"], appliance["api_key"], appliance["ids_file"]
        )


if __name__ == "__main__":
    main()
