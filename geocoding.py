import requests
import xml.etree.ElementTree as ET
import os
import hashlib

class NearbyStops:
    def __init__(self, postcode):
        self.is_in_Surrey = False
        self.is_postcode_request = False
        self.is_bus_stop_request = False
        self.postcode_lat = 0
        self.postcode_lon = 0
        self.check_bus_stops_data()
        self.check_postcode(postcode)

    def check_bus_stops_data(self):
        # Look for 400.xml, check if it exists
        try:
            # Retrieve Surrey bus stop data
            self.stops_content_request = requests.get("https://naptan.api.dft.gov.uk/v1/access-nodes?dataFormat=xml&atcoAreaCodes=400")
            file_path = "400.xml"
            self.stops_content_request.raise_for_status()  # Raises an error for bad responses (4xx and 5xx)
            xml_content = self.stops_content_request.text

            # Compute hash of new data
            new_hash = hashlib.md5(xml_content.encode()).hexdigest()

            # If file does not exist, write the new content
            if not os.path.exists(file_path):
                with open(file_path, "w") as datafile:
                    datafile.write(xml_content)

            # Read existing file and compare hash values
            with open(file_path, "r") as datafile:
                existing_hash = hashlib.md5(datafile.read().encode()).hexdigest()

            if new_hash != existing_hash:
                with open(file_path, "w") as datafile:
                    datafile.write(xml_content)

            self.is_bus_stop_request = True

        except (requests.RequestException, requests.ConnectionError, requests.Timeout):
            self.is_bus_stop_request = False

    def check_postcode(self, postcode):
        try:
            # Retrieve data on the postcode which the user will input
            self.postcode_request = requests.get(f"https://findthatpostcode.uk/postcodes/{postcode}.json")
            # Retrieve and store latitude and longitude of postcode if postcode input is correct
            if self.postcode_request.status_code == 200:
                self.is_postcode_request = True
                # Retrieve and store latitude and longitude of postcode if it is in Surrey
                self.postcode_data = self.postcode_request.json() # Convert to json data
                if self.postcode_data["data"]["attributes"]["cty"]=="E10000030": # Check if postcode data has county code of Surrey
                    self.postcode_lat = self.postcode_data["data"]["attributes"]["location"]["lat"]
                    self.postcode_lon = self.postcode_data["data"]["attributes"]["location"]["lon"]
                    self.is_in_Surrey = True
                else:
                    self.is_in_Surrey = False
            else:
                self.is_postcode_request = False
        except (requests.RequestException, requests.ConnectionError, requests.Timeout):
            self.is_postcode_request = False
    
    # Parse XML and find the nearest bus stops
    def find_nearest_bus_stops(self):
        # Representing XML docs as tree structure, where each node is an element
        tree = ET.parse("400.xml")
        root = tree.getroot() # Get the root of the XML tree structure
        
        # Enable access to elements in a namespace
        namespace = {"n": "http://www.naptan.org.uk/"}
        # Initialise list to store relevant bus stops
        bus_stops = []

        # Setting boundaries in which relevant bus stops can be output
        maxLat = self.postcode_lat + 0.005
        minLat = self.postcode_lat - 0.005
        maxLong = self.postcode_lon + 0.005
        minLong = self.postcode_lon - 0.005
        
        # Iterate through all StopPoint elements
        for stop_point in root.findall(".//n:StopPoint", namespace):
            status = stop_point.get("Status") # Gets status of bus stop
            if status != "active":
                continue  # Skip inactive stops

            # Extract ATCO code
            atco_code = stop_point.find("n:AtcoCode", namespace)
            atco_code = atco_code.text if atco_code is not None else "Unknown"
            
            # Extract common name
            common_name = stop_point.find(".//n:Descriptor/n:CommonName", namespace)
            common_name = common_name.text if common_name is not None else "Unnamed Stop"

            # Extract locality reference ID
            nptg_locality_ref = stop_point.find(".//n:Place/n:NptgLocalityRef", namespace)
            nptg_locality_ref = nptg_locality_ref.text if nptg_locality_ref is not None else "Unknown"
            
            # Extract location
            location = stop_point.find(".//n:Location/n:Translation", namespace)
            if location is not None: # If there is location data...
                # Get latitude and longitude of bus stop
                latitude = float(location.find("n:Latitude", namespace).text)
                longitude = float(location.find("n:Longitude", namespace).text)

                # If the bus stop is within the set boundaries...
                if minLat < latitude < maxLat and minLong < longitude < maxLong:
                    # Append stop details as dictionary
                    bus_stops.append({
                        "name": common_name,
                        "atco_code": atco_code,
                        "gazetteer_id": nptg_locality_ref,
                        "latitude": latitude,
                        "longitude": longitude
                    })
        
        # Return the nearest bus stops
        return bus_stops


