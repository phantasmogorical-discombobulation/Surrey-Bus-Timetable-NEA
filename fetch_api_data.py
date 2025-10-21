import requests # Enable accessing of API
from zipfile import ZipFile, ZIP_DEFLATED # Enable manipulation of .zip files
import json
import os
from dotenv import load_dotenv

class GrabFiles:
    def __init__(self):
        # Store url of API and API key
        load_dotenv()
        self.API_KEY = os.getenv("BUS_API_KEY")
        self.url = f"https://data.bus-data.dft.gov.uk/api/v1/dataset/?adminArea=400&limit=120&api_key={self.API_KEY}"
        self.is_API_request = False
        self.response_contents = None

        # Fetch API contents with error handling
        try:
            self.response = requests.get(self.url)
            self.response.raise_for_status()  # Raise error for bad responses (4xx, 5xx)
            # Convert it to JSON to make it easier to parse
            self.response_contents = self.response.json()
            # Fetch the relevant contents, 'results'
            self.results = self.response_contents["results"]
            self.is_API_request = True # Successful data retrieval

        except (requests.RequestException, requests.ConnectionError, requests.Timeout):
            self.is_API_request = False # Unsuccessful data retrieval

    def download_timetables(self): 
        print("Downloading...") # Notifies start of download

        # Keeps track of downloaded files, to help prevent duplicate files
        downloaded_files_info = []

        # Create a zip file to store all the bus files
        with ZipFile("bus_services.zip", 'w', ZIP_DEFLATED) as bus_service_files:

            # Goes through each bus service in the API
            for result in reversed(self.results):

                # Check if info of bus file is in the list
                # i.e. if file of same bus line(s) and operator had already been downloaded
                if [result["operatorName"], result["lines"]] in downloaded_files_info:
                    continue # Skip to next bus operator

                # Fetch the contents in the file from the 'url' 
                url_content = requests.get(result["url"])

                # Use the API to check if the link is a .zip file
                if result["extension"] == "zip":
                    # Create a filename for the .zip file
                    filename = f"{result["operatorName"]}_{result["id"]}.zip"

                    # Create a file with the name of filename...
                    with bus_service_files.open(filename,"w") as file:
                        # and store the contents in there
                        file.write(url_content.content)

                    # Add info of downloaded file to list
                    downloaded_files_info.append([result["operatorName"], result["lines"]])

                # Use the API to check if the link is an .xml file
                elif result["extension"] == "xml":
                    # Create a filename for the .xml file
                    filename = f"{result["operatorName"]}_{result["id"]}_{result["lines"][0]}.xml"

                    # Create a file with the name of filename...
                    with bus_service_files.open(filename,"w") as file:
                        # and store the contents in there
                        file.write(url_content.content)

                    # Add info of downloaded file to list
                    downloaded_files_info.append([result["operatorName"], result["lines"]])

        print("Downloading complete") # Notifies end of download

    def check_for_updates(self):
        # Look for file storing copy of API json recently fetched
        if not os.path.exists("API_copy.json"):

            # Create API copy json file if file not found
            with open("API_copy.json","w") as datafile:
                json.dump(self.response_contents, datafile, indent=4)
                #print("API_copy.json created")

        else:
            # Load up the json file
            with open("API_copy.json","r") as datafile:
                data = json.load(datafile)

            # Checking if API has updated since last time
            if self.response_contents != data:
                #print("API has changed")      
                with open("API_copy.json","w") as datafile:
                    json.dump(self.response_contents, datafile, indent=4)
                self.download_timetables()
                
            else:
                pass
                #print("API has not changed")

