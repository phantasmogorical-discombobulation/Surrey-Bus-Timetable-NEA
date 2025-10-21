import lxml.etree as ET
from datetime import datetime, timedelta
import isodate
from collections import defaultdict

class ProcessData:
    def __init__(self, file_contents, target_atco_code):
        # Parse the XML content using lxml
        self.root = ET.fromstring(file_contents)

        # Define the namespace mapping
        self.namespace = {'ns': 'http://www.transxchange.org.uk/'}

        self.target_atco_code = target_atco_code

    def get_line_number(self):
        # Extract Line Number from <Services> -> <Line> -> <LineName>
        line_number = self.root.xpath("//ns:Service/ns:Lines/ns:Line/ns:LineName", namespaces=self.namespace)[0].text
        return line_number
    
    # Function to check if the bus stops at the target stop
    def is_atco_code_there(self):
        # Search for the StopPointRef inside the XML
        stop_refs = self.root.xpath("//ns:StopPointRef", namespaces=self.namespace)

        # Check if the given ATCO code exists in any StopPointRef
        # and return 'True' if found, otherwise 'False'
        return any(stop.text == self.target_atco_code for stop in stop_refs)
    
    def find_arrival_times_by_destination(self):
        # Initialise dictionary to collect arrival times and destination(s) for each bus line
        arrival_times_by_destination = defaultdict(list)

        # Check if stop is in the file - if not, return empty list
        if not self.is_atco_code_there():
            return []
        
        # If the file does not match the expected structure, return empty list
        try:
            # Find all VehicleJourney elements
            vehicle_journeys = self.root.xpath('//ns:VehicleJourney', namespaces=self.namespace)

            # Loop through all vehicle journeys to extract data
            for vehicle_journey in vehicle_journeys:
                departure_time = vehicle_journey.find('ns:DepartureTime', namespaces=self.namespace).text
                journey_pattern_ref = vehicle_journey.find('ns:JourneyPatternRef', namespaces=self.namespace).text

                # Convert departure time to a datetime object
                current_time = datetime.strptime(departure_time, '%H:%M:%S')

                # Find the associated JourneyPattern using JourneyPatternRef
                journey_pattern = self.root.xpath(f"//ns:JourneyPattern[@id='{journey_pattern_ref}']", namespaces=self.namespace)

                # Find the destination name
                destination = journey_pattern[0].xpath('.//ns:DestinationDisplay', namespaces=self.namespace)[0].text.strip()

                # Find the JourneyPatternSectionRefs
                section_refs = journey_pattern[0].xpath('.//ns:JourneyPatternSectionRefs', namespaces=self.namespace)

                for section_ref in section_refs:
                    section_id = section_ref.text

                    # Find all the timing links in this section
                    section = self.root.xpath(f"//ns:JourneyPatternSection[@id='{section_id}']", namespaces=self.namespace)

                    timing_links = section[0].xpath('.//ns:JourneyPatternTimingLink', namespaces=self.namespace)

                    # Loop through each timing link to get the stop times
                    for timing_link in timing_links:
                        from_stop_ref = timing_link.find('ns:From/ns:StopPointRef', namespaces=self.namespace).text
                        run_time = timing_link.find('ns:RunTime', namespaces=self.namespace).text

                        # Calculate the arrival time by adding the runtime to the current time
                        seconds = isodate.parse_duration(run_time)
                        arrival_time = current_time + timedelta(seconds=seconds.total_seconds())

                        # Check if desired stop is found
                        if self.target_atco_code == from_stop_ref:

                            # {destination: arrival times}
                            arrival_times_by_destination[destination].append(arrival_time.strftime('%H:%M:%S'))        
                            break # Move onto the next section reference

                        # Update the current time for the next stop
                        current_time = arrival_time

        except:
            return []
        return arrival_times_by_destination
    
