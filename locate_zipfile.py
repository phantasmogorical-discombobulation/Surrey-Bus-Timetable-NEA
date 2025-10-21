from zipfile import ZipFile
from io import BytesIO
import os
import json
from processing_timetable_data import ProcessData

class LocateBusFile:
    def __init__(self, bus_stop_data):
        # Get the bus stop data dictionary
        self.bus_stop_data = bus_stop_data
        self.bus_operators_dataset = self.get_json_data()
        self.results = self.bus_operators_dataset["results"]
        self.all_bus_timetables = []

    # Get data from the API copy instead of requesting
    def get_json_data(self):
        with open("API_copy.json","r") as BODSData:
            bus_operators_dataset = json.load(BODSData)
        return bus_operators_dataset

    def find_bus_service_zipfile(self):
        bus_services_zip_path = "bus_services.zip"
        if os.path.exists(bus_services_zip_path):
            print("Zipfile found")
        else:
            print("Zipfile not found")

    def find_relevant_operators_by_place(self):
        relevant_zip_files = [] # List to store name of relevant zip files
        relevant_xml_files = [] # List to store name of relevant xml files
        relevant_files_info = [] # Keep track of selected files, makes sure no duplicate files selected
        stop_gazetteer_id = self.bus_stop_data['gazetteer_id'] # Get gazetteer ID of bus stop

        # Search through the bus operators in reverse order
        for result in reversed(self.results):
            
            # Check if file of same operator and same bus line has been selected
            if [result["operatorName"], result["lines"]] in relevant_files_info:
                    continue # Skip to next bus operator
            
            # Search through the list of places the bus company operates
            for place in result["localities"]:

                # If bus company does operate in the same area as bus stop, get name of zip/xml file
                if place["gazetteer_id"] == stop_gazetteer_id: 
                    if result["extension"] == "zip":
                        # Add relevant filename to list
                        relevant_zip_files.append(f'{result["operatorName"]}_{result["id"]}.{result["extension"]}')

                        # Add info of relevant file to list
                        relevant_files_info.append([result["operatorName"], result["lines"]])

                    elif result["extension"] == "xml":
                        # Add relevant filename to list
                        relevant_xml_files.append(f'{result["operatorName"]}_{result["id"]}_{result["lines"][0]}.{result["extension"]}')

                        # Add info of relevant file to list
                        relevant_files_info.append([result["operatorName"], result["lines"]])

                    break # Move on to next bus operator instead of checking the next locality code

        return relevant_zip_files, relevant_xml_files
    
    def get_bus_stop_timetable(self):
        all_bus_timetables = [] # Collect all bus arrival times at the target stop
        arrival_times = [] # Collect arrival times of a bus
        relevant_zip_files, relevant_xml_files = self.find_relevant_operators_by_place() # Get names of relevant files

        # Search through bus_services.zip containing all bus files operating in Surrey
        with ZipFile("bus_services.zip",'r') as bus_services_zip:
            # Search through xml files first
            for file in relevant_xml_files:

                # Fetch xml content of the xml file
                with bus_services_zip.open(file,'r') as bus_file:
                    xml_content = bus_file.read()

                # Initialise object for retrieving data about the bus
                bus_data = ProcessData(xml_content, self.bus_stop_data['atco_code'])

                # Get arrival times
                arrival_times = bus_data.find_arrival_times_by_destination()
                
                # Check if arrival times retrieval was successful
                if arrival_times:

                    # Get line number
                    lineNumber = bus_data.get_line_number()

                    # Add line number and its associated times to timetable list
                    bus_info = {'line':lineNumber, 'arrival_times': arrival_times}
                    all_bus_timetables.append(bus_info)

            # Search through zip files
            for zip_file in relevant_zip_files:

                # List to keep track of bus lines already checked
                checked_lines = []

                with bus_services_zip.open(zip_file, 'r') as zf:

                    # Store its contents in memory in order to access it
                    zipfile_contents = BytesIO(zf.read())
                    with ZipFile(zipfile_contents,'r') as operator_zip:
                        
                        # Go through all xml files in reverse order
                        for xml_file in reversed(operator_zip.namelist()):

                            # Fetch xml content of the xml file
                            with operator_zip.open(xml_file,'r') as bus_file:
                                xml_content = bus_file.read()

                            # Initialise object for retrieving data about the bus
                            bus_data = ProcessData(xml_content, self.bus_stop_data['atco_code'])

                            # Get line number
                            lineNumber = bus_data.get_line_number()

                            # Check if data of that bus line was already retrieved
                            if lineNumber in checked_lines:
                                continue # Skip to the next bus line file

                            # Get arrival times
                            arrival_times = bus_data.find_arrival_times_by_destination()
                            
                            # Check if arrival times retrieval was successful
                            if arrival_times:
                                checked_lines.append(lineNumber) # 'Tick off' the line number

                                # Add line number and its associated times to timetable list
                                bus_info = {'line':lineNumber, 'arrival_times': arrival_times}
                                all_bus_timetables.append(bus_info)
                            
        return all_bus_timetables


