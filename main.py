from kivy.app import App
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy_garden.mapview import MapView, MapMarkerPopup
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup 
from kivy.uix.scrollview import ScrollView
from geocoding import NearbyStops
from fetch_api_data import GrabFiles
from locate_zipfile import LocateBusFile

class BusStopMarkerPopup(MapMarkerPopup):
    def __init__(self, stop_data, **kwargs):
        super().__init__(**kwargs) # Inherit all methods and attributes from MapMarkerPopup class
        self.stop_data = stop_data # Initialise stop data

        # Create the popup content layout
        popup_layout = BoxLayout(orientation="vertical", size_hint=(None, None), size=(200, 100))

        # Add a label for the bus stop name
        title_label = Label(text=self.stop_data['name'], size_hint=(1, 0.7), outline_width = 2)
        popup_layout.add_widget(title_label)

        # Add a button to view the timetable
        view_button = Button(text="View Timetable", 
                                 size_hint=(1, 0.3), 
                                 background_normal='', # Gets rid of default dark shade
                                 background_color=(4/255, 76/255, 54/255, 1), # Green 'Surrey' colour
                                 )
        # Set button so when pressed, gives stop data to function
        view_button.bind(on_press=self.view_timetable)
        popup_layout.add_widget(view_button)

        # Set the popup content
        self.add_widget(popup_layout)  

    def view_timetable(self, instance):
        timetable = LocateBusFile(self.stop_data).get_bus_stop_timetable()
        timetable_popup = DisplayTimetable(timetable, self.stop_data)
        timetable_popup.open()
        #print(self.stop_data)

class InputPostcode(Screen):
    def __init__ (self,**kwargs):
        super().__init__(**kwargs)
        # Check for updates and download data if needed
        update = GrabFiles()
        # Check for internet connection
        if update.is_API_request:
            update.check_for_updates()
        else:
            layout = FloatLayout()
            error_label = Label(text = "An error occured. Please make sure you are connected to the internet.",
                                size_hint = (None, None),
                                size = (200,50),
                                pos_hint={'center_x': 0.5, 'center_y': 0.7}, text_size=(300,None))
            layout.add_widget(error_label)
            no_internet_popup = Popup(title = "Error", 
                                content = layout, size_hint=(None, None), 
                                size=(400, 400),
                                background_color=[4/255, 76/255, 54/255, 1], # Green 'Surrey' colour
                                auto_dismiss = False)       
            no_internet_popup.open()
            return
        
        # Set up a layout to add widgets on the window
        self.layout = FloatLayout()
        self.add_widget(self.layout)

        self.postcode_latitude = 0.0
        self.postcode_longitude = 0.0
        self.bus_stops = []  # Define bus_stops as an instance attribute

        self.map_view = MapView(zoom=10, lat=51.25, lon=-0.33)  # Surrey coordinates
        self.layout.add_widget(self.map_view) # Add map to window

        # Text input for postcode (with hint text inside)
        self.text_input = TextInput(
            size_hint=(0.7, 0.1),
            pos_hint={"x": 0, "y": 0.02}, # Position at the bottom
            multiline=False, # Only one single line since postcode only needs one line
            hint_text="Enter a postcode e.g. SW1A 1AA"  # Hint text inside the text box
        )
        # Add textbox for entering postcode onto the window
        self.layout.add_widget(self.text_input)
        
        # Search button
        self.search_button = Button(
            text="Search", # Button will say "Search" on it
            size_hint=(0.3, 0.1),
            pos_hint={"x": 0.7, "y": 0.02}, # Position at the bottom
            background_normal='', # Gets rid of default dark shade
            background_color=(4/255, 76/255, 54/255, 1), # Green 'Surrey' colour
            color=(1, 1, 1, 1)  # White text
        )
        # Add search button onto the window
        self.search_button.bind(on_press = self.search)
        self.layout.add_widget(self.search_button)

    def search(self, instance):
        postcodeInfo = NearbyStops(self.text_input.text)
        self.postcode_latitude = postcodeInfo.postcode_lat
        self.postcode_longitude = postcodeInfo.postcode_lon
        if postcodeInfo.is_in_Surrey and postcodeInfo.is_bus_stop_request:
            # Correct postcode, move on
            self.bus_stops = postcodeInfo.find_nearest_bus_stops()
            self.manager.current = "BusStops"
        elif postcodeInfo.is_postcode_request:
            # Notify user to put Surrey postcode
            self.error_message(self.search_button, "The postcode you have entered is not in Surrey", "Close")
        elif not postcodeInfo.is_postcode_request:
            # Notify user to enter an existing postcode
            self.error_message(self.search_button, "Postcode is not found", "Close")
        elif not postcodeInfo.is_bus_stop_request:
            self.error_message(self.search_button, "An error occurred. Please try again.", "Close")

    def error_message(self, instance, message, button_text):
        layout = FloatLayout()
        popup_label = Label(text = message,
                            size_hint = (None, None),
                            size = (200,50),
                            pos_hint={'center_x': 0.5, 'center_y': 0.7}, text_size=(300,None))
        close_button = Button(text = button_text,
                              size_hint = (0.8,0.2),
                              pos_hint = {"x":0.1,"y":0.1},
                              background_normal='', # Gets rid of default dark shade
                              background_color=(4/255, 76/255, 54/255, 1), # Green 'Surrey' colour
                              )
        layout.add_widget(popup_label)
        layout.add_widget(close_button)
        error_popup = Popup(title = "Invalid postcode", 
                            content = layout, size_hint=(None, None), 
                            size=(400, 400),
                            background_color=[4/255, 76/255, 54/255, 1], # Green 'Surrey' colour
                            auto_dismiss = False)       
        error_popup.open()
        close_button.bind(on_press=error_popup.dismiss)

class ShowBusStops(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = FloatLayout()
        self.add_widget(self.layout)

    def go_back_to_search_screen(self, instance):
        self.manager.current="InputPostcode"

    def show_instructions(self):
        instructions_layout = FloatLayout()
        popup_label = Label(text = "Click on a marker to view its bus stop name, then click on 'View Timetable' above the marker to view the timetable of the bus stop.",
                            size_hint = (0.6,0.2),
                            text_size = (300, None),
                            pos_hint={"x":0.2, "top":0.8})
        close_button = Button(text = "Got it",
                              size_hint = (0.8,0.2),
                              pos_hint = {"x":0.1,"y":0.1},
                              background_normal='', # Gets rid of default dark shade
                              background_color=(4/255, 76/255, 54/255, 1), # Green 'Surrey' colour
                              )
        instructions_layout.add_widget(popup_label)
        instructions_layout.add_widget(close_button)
        instructions_popup = Popup(title="Instructions", 
                                   content=instructions_layout, 
                                   size_hint=(None,None), size=(400,400), 
                                   background_color=(4/255, 76/255, 54/255, 1)) # Green 'Surrey' colour
        instructions_popup.open()
        close_button.bind(on_press=instructions_popup.dismiss)

    def get_midpoint_coor(self, bus_stop_list):
        latitudes = [stop_data['latitude'] for stop_data in bus_stop_list] # Getting all latitudes of nearby bus stops
        longitudes = [stop_data['longitude'] for stop_data in bus_stop_list] # Getting all longitudes of nearby bus stops
        # Return map coordinate: mean of latitude and mean of longitude
        return {'latitude':(sum(latitudes))/len(latitudes), 'longitude':(sum(longitudes))/len(longitudes)}

    def on_enter(self):
        # Fetching relevant data from InputPostcode class
        input_postcode_screen = self.manager.get_screen("InputPostcode")
        bus_stops = input_postcode_screen.bus_stops
        postcode_latitude = input_postcode_screen.postcode_latitude
        postcode_longitude = input_postcode_screen.postcode_longitude
        map_coor = self.get_midpoint_coor(bus_stops) # Getting the midpoint of the nearby bus stop coordinates

        # Set up a map to focus on midpoint coordinates
        self.map_view = MapView(zoom=16, lat=map_coor['latitude'], lon=map_coor['longitude'])
        # Plotting postcode location with a different marker
        self.postcode_marker = MapMarkerPopup(lat=postcode_latitude, lon=postcode_longitude, source='turquoise-map-marker.png')
        self.postcode_marker.add_widget(Label(text=input_postcode_screen.text_input.text, size_hint=(1, 0.7), outline_width = 2))
        self.layout.add_widget(self.map_view)
        self.map_view.add_widget(self.postcode_marker)

        # Loop through all the bus stops and plot onto map
        for stop in bus_stops:
            marker = BusStopMarkerPopup(stop_data=stop, lat=stop["latitude"], lon=stop["longitude"])
            self.map_view.add_widget(marker)

        # Back button to InputPostcode screen
        back_button = Button(text="Back", size_hint=(0.1,0.05), pos_hint={"x":0,"y":0.95}, 
                             background_normal='', # Gets rid of default dark shade
                             background_color=(4/255, 76/255, 54/255, 1)) # Green 'Surrey' colour
        back_button.bind(on_press=self.go_back_to_search_screen)
        self.layout.add_widget(back_button)
        self.show_instructions()

class DisplayTimetable(Popup):
    def __init__(self, timetable, stop_data, **kwargs):
        super().__init__(*kwargs)
        self.title = stop_data["name"] # Bus stop name
        self.size_hint = (0.8, 0.8)
        self.background_color=[4/255, 76/255, 54/255, 1] # Green 'Surrey' colour

        main_layout = BoxLayout(orientation="vertical")

        # Check if timetable is not empty
        if timetable:
            # Will contain whole table which will scroll horizontally
            whole_table_scroll = ScrollView(size_hint=(1, 1), do_scroll_x=True, do_scroll_y=False, bar_width="5dp")

            # Table layout created, two rows
            table_layout = GridLayout(rows=2, size_hint=(None, 1), height=50, padding=10, spacing=10, orientation='tb-lr')
            table_layout.bind(minimum_width=table_layout.setter("width"))
            
            # Loop through timetable data, looking at timetable of each bus line
            for bus in timetable:

                # Headings - line number
                heading_label = Label(text=bus["line"], bold=True, size_hint=(None, None), size=(250, 40), 
                                    text_size=(250, None), halign="center", valign="middle")
                table_layout.add_widget(heading_label)

                # Add a scrolling widget underneath the heading
                arrival_times_scroll = ScrollView()
                arrival_times_grid = GridLayout(cols=1, size_hint_y=None)
                arrival_times_grid.bind(minimum_height=arrival_times_grid.setter("height"))

                # Loop through timetable of the bus line
                for destination, times in bus["arrival_times"].items():
                    # Add destination name in bold, then the times underneath
                    destination_label = Label(text=destination, bold=True, size_hint_y=None, text_size=(250, None), halign="center")
                    destination_label.bind(texture_size=destination_label.setter('size'))
                    arrival_times_grid.add_widget(destination_label)
                    for time in times:
                        arrival_times_grid.add_widget(Label(text=time, size_hint_y=None, halign="center", height=40))

                arrival_times_scroll.add_widget(arrival_times_grid)
                table_layout.add_widget(arrival_times_scroll)

            whole_table_scroll.add_widget(table_layout)
            
            main_layout.add_widget(whole_table_scroll)
        else:
            # Message displayed in the same popup if timetable data is empty
            error_label = Label(text="There does not seem to be any buses stopping at this stop.", 
                                size_hint=(1, 0.5),
                                halign='center',
                                valign='middle')
            error_label.bind(size=error_label.setter('text_size'))
            main_layout.add_widget(error_label)

        # Close Button
        close_button = Button(text="Close", size_hint_y=None, height=50, background_normal='', # Gets rid of default dark shade
                        background_color=(4/255, 76/255, 54/255, 1)) # Green 'Surrey' colour
        close_button.bind(on_press=self.dismiss)
        main_layout.add_widget(close_button)

        self.content = main_layout


class BusTimetableApp(App):
    def build(self):
        my_screenmanager = ScreenManager()
        my_screenmanager.add_widget(InputPostcode(name='InputPostcode'))
        my_screenmanager.add_widget(ShowBusStops(name='BusStops'))
        return my_screenmanager
    
if __name__ == "__main__":
    BusTimetableApp().run()