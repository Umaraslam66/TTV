import streamlit as st
import uuid
import pandas as pd
import io
import xlsxwriter
from io import BytesIO
import base64

from models.station import Station
from models.train import Train
from utils.time_utils import parse_time, minutes_to_hhmm
from utils.templates import (
    get_sample_templates, create_local_template, create_express_template,
    create_hourly_pattern, create_express_local_pattern,
    create_shuttle_pattern, create_peak_service_pattern
)
from utils.import_export import import_stations_from_text, export_stations_to_text

class DataManager:
    """
    Class to manage station and train data in the Streamlit app.
    """
    
    @staticmethod
    def initialize_session_state():
        """Initialize necessary session state variables if they don't exist."""
        if 'stations' not in st.session_state:
            st.session_state.stations = []
        
        if 'trains' not in st.session_state:
            st.session_state.trains = []
        
        if 'selected_train_idx' not in st.session_state:
            st.session_state.selected_train_idx = None
        
        if 'train_form_key' not in st.session_state:
            st.session_state.train_form_key = str(uuid.uuid4())
    
    @staticmethod
    def improved_time_input(label, value=None, key=None, help=None):
        """Custom time input widget with built-in validation"""
        col1, col2 = st.columns([1, 1])
        
        # Get hour and minute from value (if provided)
        hour = 0
        minute = 0
        if value is not None and isinstance(value, (int, float)):
            hour = int(value) // 60
            minute = int(value) % 60
        
        with col1:
            h = st.number_input(f"{label} (Hour)", min_value=0, max_value=23, value=hour, step=1, key=f"{key}_hour")
        with col2:
            m = st.number_input(f"{label} (Min)", min_value=0, max_value=59, value=minute, step=5, key=f"{key}_min")
        
        if help:
            st.caption(help)
        
        return h * 60 + m if h is not None and m is not None else None
    
    #
    # STATION MANAGEMENT METHODS
    #
    
    @staticmethod
    def manage_stations_ui():
        """Render the UI for managing stations."""
        st.header("Station Management")
        
        tabs = st.tabs(["Add Station", "Bulk Add Stations", "View Stations"])
        
        # Tab 1: Add individual station
        with tabs[0]:
            DataManager._add_station_ui()
        
        # Tab 2: Bulk add stations
        with tabs[1]:
            DataManager._bulk_add_stations_ui()
        
        # Tab 3: View/Delete stations
        with tabs[2]:
            DataManager._view_stations_ui()
    
    @staticmethod
    def _add_station_ui():
        """UI for adding a single station."""
        with st.form("add_station_form"):
            station_name = st.text_input("Station Name")
            submit = st.form_submit_button("Add Station")
            
            if submit and station_name:
                DataManager.add_station(station_name)
                st.success(f"Added station: {station_name}")
                
        # Quick add multiple stations
        st.write("---")
        st.write("Quick Add Multiple Stations:")
        col1, col2 = st.columns([3, 1])
        with col1:
            quick_stations = st.text_input("Enter stations separated by commas", 
                                          placeholder="Terminal, Central, Downtown, Uptown, Riverside")
        with col2:
            if st.button("Add All") and quick_stations:
                names = [name.strip() for name in quick_stations.split(",") if name.strip()]
                added = 0
                for name in names:
                    if DataManager.add_station(name):
                        added += 1
                if added > 0:
                    st.success(f"Added {added} stations")
                    st.experimental_rerun()
    
    @staticmethod
    def _bulk_add_stations_ui():
        """UI for adding multiple stations from text."""
        st.write("Enter stations, one per line:")
        stations_text = st.text_area("Stations", height=200)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Add Stations") and stations_text:
                new_stations = import_stations_from_text(stations_text)
                added = 0
                
                for station in new_stations:
                    if not any(s.name == station.name for s in st.session_state.stations):
                        st.session_state.stations.append(station)
                        added += 1
                
                if added > 0:
                    st.success(f"Added {added} stations")
                else:
                    st.info("No new stations added")
        
        with col2:
            if st.button("Clear All Stations"):
                st.session_state.stations = []
                st.success("All stations cleared")
    
    @staticmethod
    def _view_stations_ui():
        """UI for viewing and deleting stations."""
        if not st.session_state.stations:
            st.info("No stations added yet. Add some stations first.")
            return
        
        # Show stations in a dataframe
        station_data = [{"#": i+1, "Station": s.name} for i, s in enumerate(st.session_state.stations)]
        df = pd.DataFrame(station_data)
        st.dataframe(df, use_container_width=True)
        
        # Delete station option
        col1, col2 = st.columns(2)
        
        with col1:
            station_to_delete = st.selectbox(
                "Select station to delete",
                options=[s.name for s in st.session_state.stations]
            )
        
        with col2:
            if st.button("Delete Station") and station_to_delete:
                if DataManager.is_station_in_use(station_to_delete):
                    st.error(f"Cannot delete station {station_to_delete} because it is used in train schedules")
                else:
                    DataManager.delete_station(station_to_delete)
                    st.success(f"Deleted station: {station_to_delete}")
    
    @staticmethod
    def add_station(name):
        """
        Add a new station.
        
        Args:
            name (str): Station name.
            
        Returns:
            bool: True if added, False if already exists.
        """
        # Check if station already exists
        if any(s.name == name for s in st.session_state.stations):
            return False
        
        # Calculate position based on current stations
        position = 0
        if st.session_state.stations:
            position = len(st.session_state.stations) / (len(st.session_state.stations) + 1)
        
        # Create and add station
        station = Station(name=name, position=position)
        st.session_state.stations.append(station)
        
        # Recalculate all station positions
        DataManager._recalculate_station_positions()
        
        return True
    
    @staticmethod
    def delete_station(name):
        """
        Delete a station by name.
        
        Args:
            name (str): Station name to delete.
            
        Returns:
            bool: True if deleted, False if not found.
        """
        for i, station in enumerate(st.session_state.stations):
            if station.name == name:
                st.session_state.stations.pop(i)
                # Recalculate station positions
                DataManager._recalculate_station_positions()
                return True
        return False
    
    @staticmethod
    def _recalculate_station_positions():
        """Recalculate station positions to be evenly distributed."""
        if st.session_state.stations:
            for i, station in enumerate(st.session_state.stations):
                station.position = i / (len(st.session_state.stations) - 1 if len(st.session_state.stations) > 1 else 1)
    
    @staticmethod
    def is_station_in_use(station_name):
        """
        Check if a station is being used in any train schedule.
        
        Args:
            station_name (str): Station name to check.
            
        Returns:
            bool: True if in use, False otherwise.
        """
        for train in st.session_state.trains:
            for stop in train['schedule']:
                if stop['station'] == station_name:
                    return True
        return False
    
    #
    # TRAIN MANAGEMENT METHODS
    #
    
    @staticmethod
    def manage_trains_ui():
        """Render the UI for managing trains."""
        st.header("Train Schedule Management")
        
        if not st.session_state.stations:
            st.warning("No stations available. Please add stations first.")
            return
        
        tabs = st.tabs(["Table Editor", "Form Editor", "View Trains", "Import from Excel", "Service Pattern Generator"])
        
        # Tab 1: Table Editor (Excel-like)
        with tabs[0]:
            DataManager._train_table_ui()
        
        # Tab 2: Traditional Form Editor
        with tabs[1]:
            DataManager._train_form_ui()
        
        # Tab 3: View/Delete Trains
        with tabs[2]:
            DataManager._view_trains_ui()
            
        # Tab 4: Import from Excel
        with tabs[3]:
            DataManager._train_import_ui()
        
        # Tab 5: Service Pattern Generator
        with tabs[4]:
            DataManager.generate_service_patterns_ui()
    
    @staticmethod
    def _train_table_ui():
        """Improved Excel-like table UI for adding train schedules."""
        st.subheader("Table Editor (Excel-like)")
        
        # Train basic info
        col1, col2 = st.columns([3, 1])
        with col1:
            train_name = st.text_input("Train Name", key="table_train_name")
        with col2:
            train_color = st.color_picker("Train Color", value="#1f77b4", key="table_train_color")
        
        # Get available stations
        stations = [s.name for s in st.session_state.stations]
        
        # Initialize data if needed
        if 'train_table_data' not in st.session_state:
            data = []
            for station in stations:
                data.append({
                    "Station": station,
                    "Arrival Hour": None,
                    "Arrival Minute": None,
                    "Departure Hour": None,
                    "Departure Minute": None
                })
            st.session_state.train_table_data = pd.DataFrame(data)
        
        # Display the editable dataframe with proper number input columns
        edited_df = st.data_editor(
            st.session_state.train_table_data,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "Station": st.column_config.SelectboxColumn(
                    "Station",
                    help="Select station",
                    width="medium",
                    options=stations
                ),
                "Arrival Hour": st.column_config.NumberColumn(
                    "Arrival Hour",
                    help="Hour (0-23)",
                    min_value=0,
                    max_value=23,
                    step=1,
                    width="small"
                ),
                "Arrival Minute": st.column_config.NumberColumn(
                    "Arrival Min",
                    help="Minute (0-59)",
                    min_value=0,
                    max_value=59,
                    step=5,
                    width="small"
                ),
                "Departure Hour": st.column_config.NumberColumn(
                    "Departure Hour",
                    help="Hour (0-23)",
                    min_value=0,
                    max_value=23,
                    step=1,
                    width="small"
                ),
                "Departure Minute": st.column_config.NumberColumn(
                    "Departure Min",
                    help="Minute (0-59)",
                    min_value=0,
                    max_value=59,
                    step=5,
                    width="small"
                )
            },
            hide_index=True,
            key="train_table_editor"
        )
        
        # Update session state with edited data
        st.session_state.train_table_data = edited_df
        
        # Submit buttons
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            if st.button("Add Train", key="add_train_table"):
                if not train_name:
                    st.error("Train name is required")
                else:
                    # Extract and validate schedule
                    schedule = []
                    for _, row in edited_df.iterrows():
                        station = row["Station"]
                        
                        # Skip empty station rows
                        if not station:
                            continue
                        
                        # Calculate times in minutes
                        arrival_time = None
                        if pd.notna(row["Arrival Hour"]) and pd.notna(row["Arrival Minute"]):
                            arrival_time = int(row["Arrival Hour"]) * 60 + int(row["Arrival Minute"])
                        
                        departure_time = None
                        if pd.notna(row["Departure Hour"]) and pd.notna(row["Departure Minute"]):
                            departure_time = int(row["Departure Hour"]) * 60 + int(row["Departure Minute"])
                        
                        # Skip rows with no times
                        if arrival_time is None and departure_time is None:
                            continue
                        
                        # Add to schedule
                        schedule.append({
                            "station": station,
                            "arrival": arrival_time,
                            "departure": departure_time
                        })
                    
                    if not schedule:
                        st.error("No valid schedule entries. Please add at least one station with arrival or departure time.")
                    else:
                        # Create train
                        train = {
                            "name": train_name,
                            "color": train_color,
                            "schedule": schedule
                        }
                        
                        # Add to trains
                        st.session_state.trains.append(train)
                        st.success(f"Added train: {train_name}")
                        
                        # Reset the table
                        data = []
                        for station in stations:
                            data.append({
                                "Station": station,
                                "Arrival Hour": None,
                                "Arrival Minute": None,
                                "Departure Hour": None,
                                "Departure Minute": None
                            })
                        st.session_state.train_table_data = pd.DataFrame(data)
                        st.experimental_rerun()
        
        with col2:
            if st.button("Clear Table", key="clear_table"):
                # Reset the table
                data = []
                for station in stations:
                    data.append({
                        "Station": station,
                        "Arrival Hour": None,
                        "Arrival Minute": None,
                        "Departure Hour": None,
                        "Departure Minute": None
                    })
                st.session_state.train_table_data = pd.DataFrame(data)
                st.experimental_rerun()
                
        with col3:
            if st.button("Sort by Station Order", key="sort_table"):
                # Create a mapping of station order
                station_order = {station: i for i, station in enumerate(stations)}
                
                # Sort the dataframe by this order
                if not edited_df.empty:
                    edited_df["station_order"] = edited_df["Station"].map(station_order)
                    edited_df = edited_df.sort_values("station_order").drop("station_order", axis=1)
                    st.session_state.train_table_data = edited_df
                    st.experimental_rerun()
    
    @staticmethod
    def _train_form_ui():
        """Improved UI for adding or editing trains."""
        editing = st.session_state.selected_train_idx is not None
        
        # Get train data if editing
        train_data = {}
        if editing and 0 <= st.session_state.selected_train_idx < len(st.session_state.trains):
            train_data = st.session_state.trains[st.session_state.selected_train_idx]
        
        # Basic train info
        col1, col2 = st.columns([3, 1])
        with col1:
            train_name = st.text_input("Train Name", value=train_data.get('name', ''))
        with col2:
            train_color = st.color_picker("Train Color", value=train_data.get('color', '#1f77b4'))
        
        # Station selection
        stations_list = [s.name for s in st.session_state.stations]
        
        # Create a dynamic dataframe for schedule
        schedule_data = []
        
        if editing and 'schedule' in train_data:
            # Pre-populate with existing schedule
            for stop in train_data['schedule']:
                schedule_data.append({
                    "Station": stop.get('station', ''),
                    "Arrival Hour": stop.get('arrival', 0) // 60 if stop.get('arrival') is not None else None,
                    "Arrival Minute": stop.get('arrival', 0) % 60 if stop.get('arrival') is not None else None,
                    "Departure Hour": stop.get('departure', 0) // 60 if stop.get('departure') is not None else None,
                    "Departure Minute": stop.get('departure', 0) % 60 if stop.get('departure') is not None else None
                })
        else:
            # Start with empty row
            schedule_data.append({
                "Station": stations_list[0] if stations_list else '',
                "Arrival Hour": None,
                "Arrival Minute": None,
                "Departure Hour": 8,
                "Departure Minute": 0
            })
        
        # Convert to dataframe for editing
        df = pd.DataFrame(schedule_data)
        edited_df = st.data_editor(
            df,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "Station": st.column_config.SelectboxColumn(
                    "Station",
                    help="Select station",
                    width="large",
                    options=stations_list
                ),
                "Arrival Hour": st.column_config.NumberColumn(
                    "Arrival Hour",
                    help="Hour (0-23)",
                    min_value=0,
                    max_value=23,
                    step=1,
                    width="small"
                ),
                "Arrival Minute": st.column_config.NumberColumn(
                    "Arrival Min",
                    help="Minute (0-59)",
                    min_value=0,
                    max_value=59,
                    step=5,
                    width="small"
                ),
                "Departure Hour": st.column_config.NumberColumn(
                    "Departure Hour",
                    help="Hour (0-23)",
                    min_value=0,
                    max_value=23,
                    step=1,
                    width="small"
                ),
                "Departure Minute": st.column_config.NumberColumn(
                    "Departure Min",
                    help="Minute (0-59)",
                    min_value=0,
                    max_value=59,
                    step=5,
                    width="small"
                )
            }
        )
        
        # Add/Update Button
        action_label = "Update Train" if editing else "Add Train"
        if st.button(action_label):
            # Validate and process the schedule
            schedule = []
            for _, row in edited_df.iterrows():
                station = row["Station"]
                
                # Skip empty rows
                if not station:
                    continue
                
                # Calculate times in minutes
                arrival_time = None
                if pd.notna(row["Arrival Hour"]) and pd.notna(row["Arrival Minute"]):
                    arrival_time = int(row["Arrival Hour"]) * 60 + int(row["Arrival Minute"])
                
                departure_time = None
                if pd.notna(row["Departure Hour"]) and pd.notna(row["Departure Minute"]):
                    departure_time = int(row["Departure Hour"]) * 60 + int(row["Departure Minute"])
                
                # Skip empty rows
                if not station or (arrival_time is None and departure_time is None):
                    continue
                    
                schedule.append({
                    'station': station,
                    'arrival': arrival_time,
                    'departure': departure_time
                })
            
            # Validate schedule
            if not train_name:
                st.error("Train name is required")
            elif not schedule:
                st.error("Schedule must have at least one stop")
            else:
                # Create or update train
                train = {
                    'name': train_name,
                    'color': train_color,
                    'schedule': schedule
                }
                
                if editing:
                    st.session_state.trains[st.session_state.selected_train_idx] = train
                    st.success(f"Updated train: {train_name}")
                else:
                    st.session_state.trains.append(train)
                    st.success(f"Added train: {train_name}")
                
                # Reset
                st.session_state.selected_train_idx = None
                st.experimental_rerun()
        
        # Cancel button
        if editing and st.button("Cancel Editing"):
            st.session_state.selected_train_idx = None
            st.experimental_rerun()
    
    @staticmethod
    def generate_service_patterns_ui():
        """UI for generating service patterns."""
        st.subheader("Service Pattern Generation")
        
        if not st.session_state.stations:
            st.warning("No stations available. Please add stations first.")
            return
        
        # Get available stations
        stations = [s.name for s in st.session_state.stations]
        
        # Service pattern selection
        pattern_type = st.selectbox(
            "Select Pattern Type",
            [
                "Hourly Services", 
                "Express & Local", 
                "Shuttle Service",
                "Peak Hour Service"
            ]
        )
        
        # Common parameters
        col1, col2 = st.columns(2)
        
        with col1:
            base_hour = st.number_input("Base Hour", 0, 23, 8)
            base_minute = st.number_input("Base Minute", 0, 59, 0, step=5)
        
        base_time = base_hour * 60 + base_minute
        
        # Pattern-specific parameters
        if pattern_type == "Hourly Services":
            with col2:
                start_hour = st.number_input("Start Hour", 0, 23, 6)
                end_hour = st.number_input("End Hour", 0, 23, 22)
            
            # Template train for hourly service
            template = create_local_template(stations, base_time)
            
            if st.button("Generate Hourly Services"):
                if template:
                    # Generate hourly services
                    hourly_trains = create_hourly_pattern(
                        template, 
                        hours_range=(start_hour, end_hour)
                    )
                    
                    # Add base template as a train too
                    base_train = {
                        'name': f"{base_hour:02d}:{base_minute:02d} Service",
                        'color': '#1f77b4',  # Blue
                        'schedule': template
                    }
                    
                    all_trains = [base_train] + hourly_trains
                    
                    # Add to session state
                    added = 0
                    for train in all_trains:
                        if not any(t['name'] == train['name'] for t in st.session_state.trains):
                            st.session_state.trains.append(train)
                            added += 1
                    
                    if added > 0:
                        st.success(f"Added {added} hourly services")
                        st.experimental_rerun()
                    else:
                        st.info("No new services added")
        
        elif pattern_type == "Express & Local":
            with col2:
                interval = st.number_input("Interval between Express and Local (minutes)", 5, 30, 10)
            
            if st.button("Generate Express & Local Services"):
                # Generate express and local services
                express_local_trains = create_express_local_pattern(
                    stations,
                    base_time,
                    interval=interval
                )
                
                # Add to session state
                added = 0
                for train in express_local_trains:
                    if not any(t['name'] == train['name'] for t in st.session_state.trains):
                        st.session_state.trains.append(train)
                        added += 1
                
                if added > 0:
                    st.success(f"Added {added} express/local services")
                    st.experimental_rerun()
                else:
                    st.info("No new services added")
        
        elif pattern_type == "Shuttle Service":
            with col2:
                frequency = st.number_input("Frequency (minutes)", 5, 60, 20)
                service_end = st.number_input("Service End Hour", base_hour, 23, 22)
            
            if st.button("Generate Shuttle Services"):
                # Generate shuttle services
                shuttle_trains = create_shuttle_pattern(
                    stations,
                    base_time,
                    frequency=frequency,
                    duration=(base_hour, service_end)
                )
                
                # Add to session state
                added = 0
                for train in shuttle_trains:
                    if not any(t['name'] == train['name'] for t in st.session_state.trains):
                        st.session_state.trains.append(train)
                        added += 1
                
                if added > 0:
                    st.success(f"Added {added} shuttle services")
                    st.experimental_rerun()
                else:
                    st.info("No new services added")
        
        elif pattern_type == "Peak Hour Service":
            col1, col2 = st.columns(2)
            
            with col1:
                am_start = st.number_input("AM Peak Start Hour", 5, 12, 7)
                am_end = st.number_input("AM Peak End Hour", am_start, 12, 9)
            
            with col2:
                pm_start = st.number_input("PM Peak Start Hour", 12, 23, 16)
                pm_end = st.number_input("PM Peak End Hour", pm_start, 23, 18)
                
            frequency = st.number_input("Peak Service Frequency (minutes)", 5, 30, 10)
            
            if st.button("Generate Peak Hour Services"):
                # Generate peak hour services
                peak_trains = create_peak_service_pattern(
                    stations,
                    am_peak=(am_start, am_end),
                    pm_peak=(pm_start, pm_end),
                    frequency=frequency
                )
                
                # Add to session state
                added = 0
                for train in peak_trains:
                    if not any(t['name'] == train['name'] for t in st.session_state.trains):
                        st.session_state.trains.append(train)
                        added += 1
                
                if added > 0:
                    st.success(f"Added {added} peak hour services")
                    st.experimental_rerun()
                else:
                    st.info("No new services added")
    
    @staticmethod
    def _train_import_ui():
        """UI for importing train schedules from Excel."""
        st.subheader("Import from Excel")
        
        # Show expected Excel format
        with st.expander("Excel Format Instructions", expanded=True):
            st.markdown("""
            ### How to Format Your Excel File
            
            Your Excel file should have one of these formats:
            
            #### Option 1: One sheet per train
            Each sheet name will be used as the train name. Each sheet should have columns:
            - **Station**: Station name (must match existing stations)
            - **Arrival Hour**: Hour of arrival (0-23)
            - **Arrival Minute**: Minute of arrival (0-59)
            - **Departure Hour**: Hour of departure (0-23)
            - **Departure Minute**: Minute of departure (0-59)
            
            #### Option 2: Single sheet with multiple trains
            The sheet should have columns:
            - **Train**: Train name
            - **Station**: Station name (must match existing stations)
            - **Arrival Hour**: Hour of arrival (0-23)
            - **Arrival Minute**: Minute of arrival (0-59)
            - **Departure Hour**: Hour of departure (0-23)
            - **Departure Minute**: Minute of departure (0-59)
            
            #### Optional columns:
            - **Color**: Train color in hex format (e.g., #FF0000 for red)
            
            #### Notes:
            - Times should be in 24-hour format (0-23 for hours, 0-59 for minutes)
            - First station typically has only departure time
            - Last station typically has only arrival time
            """)
            
            # Download template button
            if st.button("Download Template Excel"):
                import io
                import xlsxwriter
                from io import BytesIO
                
                buffer = io.BytesIO()
                with xlsxwriter.Workbook(buffer) as workbook:
                    # Sample train 1
                    worksheet1 = workbook.add_worksheet("Express Train")
                    headers = ["Station", "Arrival Hour", "Arrival Minute", "Departure Hour", "Departure Minute"]
                    for col, header in enumerate(headers):
                        worksheet1.write(0, col, header)
                    
                    stations = [s.name for s in st.session_state.stations]
                    if not stations:
                        stations = ["Terminal", "Central", "Downtown", "Uptown", "Airport"]
                        
                    for row, station in enumerate(stations):
                        worksheet1.write(row+1, 0, station)
                        # Example times
                        if row > 0:  # Not first station
                            worksheet1.write(row+1, 1, 8+row)  # Arrival hour
                            worksheet1.write(row+1, 2, 0)      # Arrival minute
                        if row < len(stations)-1:  # Not last station
                            worksheet1.write(row+1, 3, 8+row)  # Departure hour
                            worksheet1.write(row+1, 4, 5)      # Departure minute
                    
                    # Sample train 2
                    worksheet2 = workbook.add_worksheet("Local Train")
                    for col, header in enumerate(headers):
                        worksheet2.write(0, col, header)
                    
                    for row, station in enumerate(stations):
                        worksheet2.write(row+1, 0, station)
                        # Example times
                        if row > 0:  # Not first station
                            worksheet2.write(row+1, 1, 9+row)  # Arrival hour
                            worksheet2.write(row+1, 2, 0)      # Arrival minute
                        if row < len(stations)-1:  # Not last station
                            worksheet2.write(row+1, 3, 9+row)  # Departure hour
                            worksheet2.write(row+1, 4, 10)     # Departure minute
                    
                    # Combined sheet
                    worksheet3 = workbook.add_worksheet("All Trains")
                    combined_headers = ["Train", "Station", "Arrival Hour", "Arrival Minute", 
                                        "Departure Hour", "Departure Minute", "Color"]
                    for col, header in enumerate(combined_headers):
                        worksheet3.write(0, col, header)
                    
                    row = 1
                    for train_idx, train_name in enumerate(["Express Train", "Local Train"]):
                        color = "#1f77b4" if train_idx == 0 else "#ff7f0e"
                        for station_idx, station in enumerate(stations):
                            worksheet3.write(row, 0, train_name)
                            worksheet3.write(row, 1, station)
                            if station_idx > 0:  # Not first station
                                worksheet3.write(row, 2, 8+train_idx+station_idx)  # Arrival hour
                                worksheet3.write(row, 3, 0)                        # Arrival minute
                            if station_idx < len(stations)-1:  # Not last station
                                worksheet3.write(row, 4, 8+train_idx+station_idx)  # Departure hour
                                worksheet3.write(row, 5, 5 if train_idx==0 else 10)  # Departure minute
                            worksheet3.write(row, 6, color)
                            row += 1
                
                st.download_button(
                    label="Download Excel Template",
                    data=buffer.getvalue(),
                    file_name="train_schedule_template.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        
        # Upload file
        uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx", "xls"])
        
        if uploaded_file is not None:
            try:
                # Read Excel file
                import pandas as pd
                
                # Try to read the Excel file
                excel_data = pd.ExcelFile(uploaded_file)
                sheet_names = excel_data.sheet_names
                
                # Display sheet selection
                selected_sheets = st.multiselect(
                    "Select sheets to import",
                    options=sheet_names,
                    default=sheet_names
                )
                
                if not selected_sheets:
                    st.warning("Please select at least one sheet to import")
                    return
                
                # Preview the selected sheets
                for sheet in selected_sheets:
                    st.write(f"Preview of sheet: {sheet}")
                    df = pd.read_excel(excel_data, sheet_name=sheet)
                    st.dataframe(df.head())
                
                # Import button
                if st.button("Import Selected Sheets"):
                    # Check if there are any existing stations
                    if not st.session_state.stations:
                        st.error("No stations available. Please add stations first.")
                        return
                    
                    # Get list of valid station names
                    valid_stations = [s.name for s in st.session_state.stations]
                    
                    imported_trains = 0
                    
                    for sheet in selected_sheets:
                        df = pd.read_excel(excel_data, sheet_name=sheet)
                        
                        # Check the format - does it have a 'Train' column?
                        if 'Train' in df.columns:
                            # Multiple trains in one sheet
                            train_names = df['Train'].unique()
                            
                            for train_name in train_names:
                                train_df = df[df['Train'] == train_name]
                                
                                # Check if train_df has required columns
                                if 'Station' not in train_df.columns:
                                    st.warning(f"Sheet {sheet} for train {train_name} is missing required columns. Skipping.")
                                    continue
                                
                                # Get color if available
                                train_color = "#1f77b4"  # Default color
                                if 'Color' in train_df.columns and not train_df['Color'].isna().all():
                                    colors = train_df['Color'].dropna().unique()
                                    if len(colors) > 0:
                                        train_color = colors[0]
                                
                                # Create schedule
                                schedule = []
                                for _, row in train_df.iterrows():
                                    station = row['Station']
                                    
                                    # Skip if station is not valid
                                    if station not in valid_stations:
                                        continue
                                    
                                    # Calculate times in minutes
                                    arrival_time = None
                                    if all(col in train_df.columns for col in ['Arrival Hour', 'Arrival Minute']):
                                        if pd.notna(row['Arrival Hour']) and pd.notna(row['Arrival Minute']):
                                            arrival_time = int(row['Arrival Hour']) * 60 + int(row['Arrival Minute'])
                                    
                                    departure_time = None
                                    if all(col in train_df.columns for col in ['Departure Hour', 'Departure Minute']):
                                        if pd.notna(row['Departure Hour']) and pd.notna(row['Departure Minute']):
                                            departure_time = int(row['Departure Hour']) * 60 + int(row['Departure Minute'])
                                    
                                    schedule.append({
                                        'station': station,
                                        'arrival': arrival_time,
                                        'departure': departure_time
                                    })
                                
                                if schedule:
                                    # Add train
                                    train = {
                                        'name': train_name,
                                        'color': train_color,
                                        'schedule': schedule
                                    }
                                    st.session_state.trains.append(train)
                                    imported_trains += 1
                        else:
                            # Assume one train per sheet
                            train_name = sheet
                            
                            # Check required columns
                            if 'Station' not in df.columns:
                                st.warning(f"Sheet {sheet} is missing required columns. Skipping.")
                                continue
                            
                            # Create schedule
                            schedule = []
                            for _, row in df.iterrows():
                                station = row['Station']
                                
                                # Skip if station is not valid
                                if station not in valid_stations:
                                    continue
                                
                                # Calculate times in minutes
                                arrival_time = None
                                if all(col in df.columns for col in ['Arrival Hour', 'Arrival Minute']):
                                    if pd.notna(row['Arrival Hour']) and pd.notna(row['Arrival Minute']):
                                        arrival_time = int(row['Arrival Hour']) * 60 + int(row['Arrival Minute'])
                                
                                departure_time = None
                                if all(col in df.columns for col in ['Departure Hour', 'Departure Minute']):
                                    if pd.notna(row['Departure Hour']) and pd.notna(row['Departure Minute']):
                                        departure_time = int(row['Departure Hour']) * 60 + int(row['Departure Minute'])
                                
                                schedule.append({
                                    'station': station,
                                    'arrival': arrival_time,
                                    'departure': departure_time
                                })
                            
                            if schedule:
                                # Add train
                                train = {
                                    'name': train_name,
                                    'color': '#1f77b4',  # Default color
                                    'schedule': schedule
                                }
                                st.session_state.trains.append(train)
                                imported_trains += 1
                    
                    if imported_trains > 0:
                        st.success(f"Successfully imported {imported_trains} trains")
                        st.experimental_rerun()
                    else:
                        st.error("No valid trains found in the selected sheets")
                    
            except Exception as e:
                st.error(f"Error importing Excel file: {str(e)}")
                st.exception(e)
    
    @staticmethod
    def _view_trains_ui():
        """UI for viewing and managing existing trains."""
        if not st.session_state.trains:
            st.info("No trains added yet. Create a train schedule first.")
            return
        
        # Display trains in a table
        train_data = []
        for i, train in enumerate(st.session_state.trains):
            train_data.append({
                "#": i+1,
                "Train": train['name'],
                "Stops": len(train['schedule']),
                "From": train['schedule'][0]['station'] if train['schedule'] else "-",
                "To": train['schedule'][-1]['station'] if train['schedule'] else "-"
            })
        
        df = pd.DataFrame(train_data)
        st.dataframe(df, use_container_width=True)
        
        # Train management options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            train_idx = st.selectbox(
                "Select train",
                options=range(len(st.session_state.trains)),
                format_func=lambda x: st.session_state.trains[x]['name']
            )
        
        with col2:
            if st.button("Edit Train") and train_idx is not None:
                st.session_state.selected_train_idx = train_idx
                st.session_state.train_form_key = str(uuid.uuid4())
                st.experimental_rerun()
        
        with col3:
            if st.button("Delete Train") and train_idx is not None:
                train_name = st.session_state.trains[train_idx]['name']
                st.session_state.trains.pop(train_idx)
                st.success(f"Deleted train: {train_name}")
                st.experimental_rerun()