import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random
import colorsys
import re
import json
import uuid

# Set page config
st.set_page_config(
    page_title="Train Time-Space Diagram Visualizer",
    page_icon="🚆",
    layout="wide"
)

# Add custom CSS
st.markdown("""
<style>
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .info-box {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .section-header {
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid #dee2e6;
    }
    .train-color-dot {
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 5px;
    }
    .control-flex {
        display: flex;
        justify-content: space-between;
        margin-bottom: 1rem;
    }
    .control-item {
        flex: 1;
        margin-right: 10px;
    }
    .control-item:last-child {
        margin-right: 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'stations' not in st.session_state:
    st.session_state.stations = []
if 'trains' not in st.session_state:
    st.session_state.trains = []
if 'selected_train_idx' not in st.session_state:
    st.session_state.selected_train_idx = None
if 'time_on_x_axis' not in st.session_state:
    st.session_state.time_on_x_axis = True
if 'min_time' not in st.session_state:
    st.session_state.min_time = datetime.strptime("06:00", "%H:%M").time()
if 'max_time' not in st.session_state:
    st.session_state.max_time = datetime.strptime("22:00", "%H:%M").time()
if 'template_schedule' not in st.session_state:
    st.session_state.template_schedule = None
if 'train_form_key' not in st.session_state:
    st.session_state.train_form_key = str(uuid.uuid4())

# Utility functions
def parse_time(time_str):
    """Parse time string to datetime object."""
    if not time_str:
        return None
    try:
        return datetime.strptime(time_str, "%H:%M").time()
    except ValueError:
        return None

def generate_random_color():
    """Generate a random bright color."""
    h = random.random()
    s = 0.7 + random.random() * 0.3  # High saturation
    v = 0.7 + random.random() * 0.3  # High value
    r, g, b = [int(x * 255) for x in colorsys.hsv_to_rgb(h, s, v)]
    return f"#{r:02x}{g:02x}{b:02x}"

def time_to_minutes(time_obj):
    """Convert time object to minutes from midnight."""
    if time_obj is None:
        return None
    return time_obj.hour * 60 + time_obj.minute

def minutes_to_time_str(minutes):
    """Convert minutes from midnight to time string."""
    hours = int(minutes // 60)
    mins = int(minutes % 60)
    return f"{hours:02d}:{mins:02d}"

def parse_bulk_stations(text):
    """Parse bulk station input from text."""
    if not text:
        return []
    
    # Split by commas or newlines
    lines = re.split(r'[,\n]', text)
    stations = [line.strip() for line in lines if line.strip()]
    return stations

def create_template_schedule(template_type, stations):
    """Create a template schedule based on the selected type."""
    if not stations or len(stations) < 2:
        st.error("You need at least 2 stations to apply a template.")
        return None
    
    base_time = datetime.strptime("08:00", "%H:%M")
    schedule = []
    
    if template_type == "express":
        # Express train stops at first, last, and major stations only
        stop_indices = [0, len(stations) // 2, len(stations) - 1]
        current_station_idx = 0
        
        for i, station in enumerate(stations):
            if i in stop_indices:
                arrival_time = base_time.strftime("%H:%M")
                base_time += timedelta(minutes=2)  # Dwell time
                departure_time = base_time.strftime("%H:%M")
                schedule.append({
                    "station": station,
                    "arrival": arrival_time,
                    "departure": departure_time
                })
            
            if i < len(stations) - 1:
                base_time += timedelta(minutes=4)  # Journey time
    
    elif template_type == "local":
        # Local train stops at all stations
        for i, station in enumerate(stations):
            arrival_time = base_time.strftime("%H:%M")
            base_time += timedelta(minutes=1)  # Dwell time
            departure_time = base_time.strftime("%H:%M")
            schedule.append({
                "station": station,
                "arrival": arrival_time,
                "departure": departure_time
            })
            
            if i < len(stations) - 1:
                base_time += timedelta(minutes=5)  # Journey time
    
    elif template_type == "uptown":
        # Uptown train (skips some stations)
        for i, station in enumerate(stations):
            # Skip every other station except first and last
            if i == 0 or i == len(stations) - 1 or i % 2 == 0:
                arrival_time = base_time.strftime("%H:%M")
                base_time += timedelta(minutes=1)  # Dwell time
                departure_time = base_time.strftime("%H:%M")
                schedule.append({
                    "station": station,
                    "arrival": arrival_time,
                    "departure": departure_time
                })
            
            if i < len(stations) - 1:
                base_time += timedelta(minutes=4)  # Journey time
    
    elif template_type == "downtown":
        # Downtown train (reverse direction, starting from last station)
        base_time = datetime.strptime("14:00", "%H:%M")  # Later in the day
        reversed_stations = list(reversed(stations))
        
        for i, station in enumerate(reversed_stations):
            arrival_time = base_time.strftime("%H:%M")
            base_time += timedelta(minutes=2)  # Dwell time
            departure_time = base_time.strftime("%H:%M")
            schedule.append({
                "station": station,
                "arrival": arrival_time,
                "departure": departure_time
            })
            
            if i < len(reversed_stations) - 1:
                base_time += timedelta(minutes=5)  # Journey time
    
    return schedule

def reset_train_form():
    """Reset the train form by creating a new unique key."""
    st.session_state.train_form_key = str(uuid.uuid4())
    st.session_state.template_schedule = None

# Apply a template and store it in session state
def apply_template(template_type):
    st.session_state.template_schedule = create_template_schedule(template_type, st.session_state.stations)
    # Force form to update
    st.session_state.train_form_key = str(uuid.uuid4())
    st.rerun()

# Main app header
st.title("🚆 Train Time-Space Diagram Visualizer")
st.markdown("Visualize train schedules on a time-space diagram with interactive controls")

# No nested columns - directly add sections to the page
st.markdown("## 📍 Station Management")

# Tabs for single/bulk station entry
station_tab1, station_tab2 = st.tabs(["Single Station", "Bulk Stations"])

with station_tab1:
    # Single station input
    new_station = st.text_input("Station name", key="station_name")
    add_station = st.button("Add Station", use_container_width=True)
    
    if add_station and new_station:
        if new_station not in st.session_state.stations:
            st.session_state.stations.append(new_station)
            st.success(f"Added station: {new_station}")
        else:
            st.warning(f"Station '{new_station}' already exists")

with station_tab2:
    # Bulk station input
    bulk_stations = st.text_area("Enter multiple stations (one per line or comma-separated)")
    add_bulk = st.button("Add All Stations", use_container_width=True)
    add_sample = st.button("Add Sample Stations", use_container_width=True)
    
    if add_bulk:
        new_stations = parse_bulk_stations(bulk_stations)
        added_count = 0
        for station in new_stations:
            if station and station not in st.session_state.stations:
                st.session_state.stations.append(station)
                added_count += 1
        
        if added_count > 0:
            st.success(f"Added {added_count} new stations")
        else:
            st.info("No new stations were added")
    
    if add_sample:
        sample_stations = ['Terminal A', 'Downtown', 'Central', 'Midtown', 'Uptown', 'Suburb', 'Terminal B']
        added_count = 0
        for station in sample_stations:
            if station not in st.session_state.stations:
                st.session_state.stations.append(station)
                added_count += 1
        
        if added_count > 0:
            st.success(f"Added {added_count} sample stations")
        else:
            st.info("All sample stations already exist")

# Display current stations
if st.session_state.stations:
    st.markdown('### Current Stations')
    clear_stations = st.button("Clear All Stations", use_container_width=True)
    
    if clear_stations:
        if st.session_state.stations:
            if st.session_state.trains:
                st.warning("Clearing stations will also remove all train schedules.")
                clear_confirmed = st.button("Yes, clear everything", key="confirm_clear")
                if clear_confirmed:
                    st.session_state.stations = []
                    st.session_state.trains = []
                    st.session_state.selected_train_idx = None
                    st.success("All stations and trains have been cleared")
                    st.rerun()
            else:
                st.session_state.stations = []
                st.success("All stations have been cleared")
                st.rerun()
    
    # Display stations with delete buttons
    for i, station in enumerate(st.session_state.stations):
        st.text(f"{i+1}. {station}")
        delete_station = st.button("Delete", key=f"del_station_{i}")
        
        if delete_station:
            # Check if station is used in any train schedule
            used_in_trains = False
            for train in st.session_state.trains:
                for item in train['schedule']:
                    if item['station'] == station:
                        used_in_trains = True
                        break
                if used_in_trains:
                    break
            
            if used_in_trains:
                st.warning(f"Cannot delete '{station}' because it's used in train schedules")
            else:
                st.session_state.stations.remove(station)
                st.success(f"Removed station: {station}")
                st.rerun()
else:
    st.info("No stations added yet")

# Train schedule management
st.markdown("## 🚆 Train Schedule")

if not st.session_state.stations:
    st.warning("Please add stations first to create train schedules")
else:
    # Train details
    train_name = st.text_input("Train Name", value="New Train")
    train_color = st.color_picker("Train Color", value=generate_random_color())
    
    # Templates with HTML/CSS for layout
    st.markdown("### Quick Templates")
    
    # Use HTML/CSS for template buttons layout instead of columns
    st.markdown("""
    <div style="display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 15px;">
        <button id="express_template" style="flex: 1; padding: 10px; background-color: #e9ecef; border: none; border-radius: 5px; cursor: pointer;">Express</button>
        <button id="local_template" style="flex: 1; padding: 10px; background-color: #e9ecef; border: none; border-radius: 5px; cursor: pointer;">Local</button>
        <button id="uptown_template" style="flex: 1; padding: 10px; background-color: #e9ecef; border: none; border-radius: 5px; cursor: pointer;">Uptown</button>
        <button id="downtown_template" style="flex: 1; padding: 10px; background-color: #e9ecef; border: none; border-radius: 5px; cursor: pointer;">Downtown</button>
    </div>
    """, unsafe_allow_html=True)
    
    # Regular buttons for templates (the HTML buttons above are just for display)
    template_express = st.button("Express Template", key="express_btn")
    template_local = st.button("Local Template", key="local_btn")
    template_uptown = st.button("Uptown Template", key="uptown_btn")
    template_downtown = st.button("Downtown Template", key="downtown_btn")
    
    # Handle template buttons
    if template_express:
        apply_template("express")
    elif template_local:
        apply_template("local")
    elif template_uptown:
        apply_template("uptown")
    elif template_downtown:
        apply_template("downtown")
    
    # Create schedule form with dynamic key to force re-render after template selection
    with st.form(key=f"train_schedule_form_{st.session_state.train_form_key}"):
        st.markdown("### Train Schedule")
        st.markdown('Enter arrival and departure times (HH:MM) for each station. Leave empty to skip station.')
        
        # Prepare dictionary to collect schedule inputs
        schedule_inputs = []
        
        for i, station in enumerate(st.session_state.stations):
            st.markdown(f"**{station}**")
            
            # Get template values if available
            default_arrival = ""
            default_departure = ""
            
            if st.session_state.template_schedule:
                for item in st.session_state.template_schedule:
                    if item['station'] == station:
                        default_arrival = item['arrival']
                        default_departure = item['departure']
                        break
            
            # Use HTML/CSS for side-by-side input fields without columns
            st.markdown(f'''
            <div style="display: flex; gap: 10px; margin-bottom: 15px;">
                <div style="flex: 1;">
                    <label style="font-size: 0.8rem; color: #6c757d;">Arrival</label>
                </div>
                <div style="flex: 1;">
                    <label style="font-size: 0.8rem; color: #6c757d;">Departure</label>
                </div>
            </div>
            ''', unsafe_allow_html=True)
            
            # For the actual inputs, we still need to use Streamlit
            arrival = st.text_input(f"Arrival at {station}", key=f"arr_{i}", value=default_arrival, label_visibility="collapsed")
            departure = st.text_input(f"Departure from {station}", key=f"dep_{i}", value=default_departure, label_visibility="collapsed")
            
            if arrival or departure:
                schedule_inputs.append({
                    "station": station,
                    "arrival": arrival,
                    "departure": departure
                })
        
        submit_button = st.form_submit_button("Add Train Schedule")
        
        if submit_button:
            if not schedule_inputs:
                st.error("Please add at least one station time")
            else:
                # Filter out empty times and validate
                valid_schedule = []
                has_errors = False
                
                for item in schedule_inputs:
                    arrival = item['arrival'].strip() if item['arrival'] else ""
                    departure = item['departure'].strip() if item['departure'] else ""
                    
                    # If both empty, skip this station
                    if not arrival and not departure:
                        continue
                    
                    # Validate time formats
                    if arrival and not parse_time(arrival):
                        st.error(f"Invalid arrival time format for {item['station']}: {arrival}. Use HH:MM.")
                        has_errors = True
                    
                    if departure and not parse_time(departure):
                        st.error(f"Invalid departure time format for {item['station']}: {departure}. Use HH:MM.")
                        has_errors = True
                    
                    # If only one is provided, use it for both
                    if not arrival:
                        arrival = departure
                    if not departure:
                        departure = arrival
                    
                    valid_schedule.append({
                        "station": item['station'],
                        "arrival": arrival,
                        "departure": departure
                    })
                
                if valid_schedule and not has_errors:
                    # Add the train
                    st.session_state.trains.append({
                        "name": train_name,
                        "color": train_color,
                        "schedule": valid_schedule
                    })
                    st.success(f"Added train: {train_name}")
                    st.session_state.selected_train_idx = len(st.session_state.trains) - 1
                    
                    # Reset the form and template
                    reset_train_form()
                    st.rerun()
                elif not valid_schedule:
                    st.error("No valid schedule entries found")

# Visualization controls without nested columns
st.markdown("## 📊 Visualization Controls")

# Use HTML/CSS for control panel layout
st.markdown("""
<div class="control-flex">
    <div class="control-item">RESET_PLACEHOLDER</div>
    <div class="control-item">SWAP_PLACEHOLDER</div>
    <div class="control-item">START_PLACEHOLDER</div>
    <div class="control-item">END_PLACEHOLDER</div>
</div>
""", unsafe_allow_html=True)

# Add control elements directly - no columns
reset_btn = st.button("⟲ Reset View", key="reset_view")
swap_btn = st.button("⇄ Swap Axes" if st.session_state.time_on_x_axis else "⇄ Swap Back", key="swap_axes")
min_time_str = st.time_input("Start Time", value=st.session_state.min_time)
max_time_str = st.time_input("End Time", value=st.session_state.max_time)

# Handle control actions
if reset_btn:
    st.session_state.time_on_x_axis = True
    st.session_state.min_time = datetime.strptime("06:00", "%H:%M").time()
    st.session_state.max_time = datetime.strptime("22:00", "%H:%M").time()
    st.rerun()

if swap_btn:
    st.session_state.time_on_x_axis = not st.session_state.time_on_x_axis
    st.rerun()

# Update time range
st.session_state.min_time = min_time_str
st.session_state.max_time = max_time_str

# Main visualization
st.markdown("## 📊 Time-Space Diagram")

if not st.session_state.stations or not st.session_state.trains:
    st.info("Add stations and train schedules to visualize the timetable.")
else:
    # Create time-space diagram using Plotly
    fig = go.Figure()
    
    # Set axis properties based on orientation
    if st.session_state.time_on_x_axis:
        xaxis_title = "Time"
        yaxis_title = "Station"
        y_categories = st.session_state.stations
        
        # Set x-axis range to the specified time range
        min_minutes = time_to_minutes(st.session_state.min_time)
        max_minutes = time_to_minutes(st.session_state.max_time)
        
        # Ensure max is greater than min
        if max_minutes <= min_minutes:
            max_minutes = min_minutes + 60  # Default to 1 hour range
        
        # Add some padding for better visibility
        range_minutes = [min_minutes - 10, max_minutes + 10]
    else:
        xaxis_title = "Station"
        yaxis_title = "Time"
        x_categories = st.session_state.stations
        
        # Set y-axis range to the specified time range
        min_minutes = time_to_minutes(st.session_state.min_time)
        max_minutes = time_to_minutes(st.session_state.max_time)
        
        # Ensure max is greater than min
        if max_minutes <= min_minutes:
            max_minutes = min_minutes + 60  # Default to 1 hour range
            
        # Add some padding for better visibility
        range_minutes = [min_minutes - 10, max_minutes + 10]
    
    # Add train lines to the plot
    plotted_data = False  # Flag to track if any valid data was plotted
    
    for train_idx, train in enumerate(st.session_state.trains):
        # Skip trains with insufficient schedule
        if len(train['schedule']) < 2:
            continue
            
        # Sort the schedule by station order (important for proper plotting)
        if st.session_state.time_on_x_axis:
            sorted_schedule = sorted(train['schedule'], 
                                     key=lambda x: st.session_state.stations.index(x['station']) 
                                     if x['station'] in st.session_state.stations else float('inf'))
        else:
            # If time is on Y-axis, we may need to sort by time
            sorted_schedule = train['schedule']
        
        # Create traces for each segment between stations
        for i in range(len(sorted_schedule)):
            if i < len(sorted_schedule) - 1:
                from_station = sorted_schedule[i]['station']
                to_station = sorted_schedule[i+1]['station']
                
                try:
                    if st.session_state.time_on_x_axis:
                        # Time on X-axis, Station on Y-axis
                        x0 = time_to_minutes(parse_time(sorted_schedule[i]['departure']))
                        y0 = from_station
                        x1 = time_to_minutes(parse_time(sorted_schedule[i+1]['arrival']))
                        y1 = to_station
                    else:
                        # Station on X-axis, Time on Y-axis
                        x0 = from_station
                        y0 = time_to_minutes(parse_time(sorted_schedule[i]['departure']))
                        x1 = to_station
                        y1 = time_to_minutes(parse_time(sorted_schedule[i+1]['arrival']))
                    
                    # Check for missing time data
                    if None in [x0, y0, x1, y1]:
                        continue
                    
                    # Create line segment
                    line_width = 4 if train_idx == st.session_state.selected_train_idx else 2
                    
                    fig.add_trace(go.Scatter(
                        x=[x0, x1] if st.session_state.time_on_x_axis else [x0, x1],
                        y=[y0, y1] if st.session_state.time_on_x_axis else [y0, y1],
                        mode='lines',
                        line=dict(width=line_width, color=train['color']),
                        name=train['name'],
                        showlegend=i==0,  # Show only once in legend
                        hoverinfo='text',
                        hovertext=f"{train['name']}<br>From: {from_station} ({sorted_schedule[i]['departure']})<br>To: {to_station} ({sorted_schedule[i+1]['arrival']})"
                    ))
                    plotted_data = True  # Valid data was plotted
                except Exception as e:
                    continue  # Skip problematic segments
            
            # Add station points for arrivals/departures
            try:
                if st.session_state.time_on_x_axis:
                    # Time on X-axis, Station on Y-axis
                    if i == 0:  # First station
                        x = time_to_minutes(parse_time(sorted_schedule[i]['departure']))
                        y = sorted_schedule[i]['station']
                        label = f"Departure: {sorted_schedule[i]['departure']}"
                    else:  # All other stations
                        x = time_to_minutes(parse_time(sorted_schedule[i]['arrival']))
                        y = sorted_schedule[i]['station']
                        label = f"Arrival: {sorted_schedule[i]['arrival']}"
                        
                        # Add departure point if different from arrival
                        if sorted_schedule[i]['arrival'] != sorted_schedule[i]['departure']:
                            x_dep = time_to_minutes(parse_time(sorted_schedule[i]['departure']))
                            y_dep = sorted_schedule[i]['station']
                            
                            if x_dep is not None:
                                fig.add_trace(go.Scatter(
                                    x=[x_dep],
                                    y=[y_dep],
                                    mode='markers',
                                    marker=dict(size=8, color=train['color'], symbol='diamond'),
                                    name=train['name'] + ' dep',
                                    showlegend=False,
                                    hoverinfo='text',
                                    hovertext=f"{train['name']}<br>Station: {y_dep}<br>Departure: {sorted_schedule[i]['departure']}"
                                ))
                else:
                    # Station on X-axis, Time on Y-axis
                    if i == 0:  # First station
                        x = sorted_schedule[i]['station']
                        y = time_to_minutes(parse_time(sorted_schedule[i]['departure']))
                        label = f"Departure: {sorted_schedule[i]['departure']}"
                    else:  # All other stations
                        x = sorted_schedule[i]['station']
                        y = time_to_minutes(parse_time(sorted_schedule[i]['arrival']))
                        label = f"Arrival: {sorted_schedule[i]['arrival']}"
                        
                        # Add departure point if different from arrival
                        if sorted_schedule[i]['arrival'] != sorted_schedule[i]['departure']:
                            x_dep = sorted_schedule[i]['station']
                            y_dep = time_to_minutes(parse_time(sorted_schedule[i]['departure']))
                            
                            if y_dep is not None:
                                fig.add_trace(go.Scatter(
                                    x=[x_dep],
                                    y=[y_dep],
                                    mode='markers',
                                    marker=dict(size=8, color=train['color'], symbol='diamond'),
                                    name=train['name'] + ' dep',
                                    showlegend=False,
                                    hoverinfo='text',
                                    hovertext=f"{train['name']}<br>Station: {x_dep}<br>Departure: {sorted_schedule[i]['departure']}"
                                ))
                
                # Add the station point
                if None not in [x, y]:
                    fig.add_trace(go.Scatter(
                        x=[x] if st.session_state.time_on_x_axis else [x],
                        y=[y] if st.session_state.time_on_x_axis else [y],
                        mode='markers',
                        marker=dict(size=8, color=train['color']),
                        name=train['name'] + ' arr',
                        showlegend=False,
                        hoverinfo='text',
                        hovertext=f"{train['name']}<br>Station: {sorted_schedule[i]['station']}<br>{label}"
                    ))
                    plotted_data = True  # Valid data was plotted
            except Exception as e:
                continue  # Skip problematic points
    
    if plotted_data:
        # Configure axes
        if st.session_state.time_on_x_axis:
            # Time on X-axis
            fig.update_layout(
                xaxis=dict(
                    title=xaxis_title,
                    range=range_minutes,
                    tickmode='array',
                    tickvals=list(range(0, 24*60, 60)),  # Every hour
                    ticktext=[f"{h:02d}:00" for h in range(24)],
                    gridcolor='lightgray'
                ),
                yaxis=dict(
                    title=yaxis_title,
                    categoryorder='array',
                    categoryarray=y_categories,
                    gridcolor='lightgray'
                )
            )
        else:
            # Station on X-axis
            fig.update_layout(
                xaxis=dict(
                    title=xaxis_title,
                    categoryorder='array',
                    categoryarray=x_categories,
                    gridcolor='lightgray'
                ),
                yaxis=dict(
                    title=yaxis_title,
                    range=range_minutes,
                    tickmode='array',
                    tickvals=list(range(0, 24*60, 60)),  # Every hour
                    ticktext=[f"{h:02d}:00" for h in range(24)],
                    gridcolor='lightgray'
                )
            )
        
        # Add grid and improve layout
        fig.update_layout(
            plot_bgcolor='white',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            margin=dict(l=20, r=20, t=40, b=20),
            height=600
        )
        
        # Change time labels format on hover
        fig.update_traces(
            hovertemplate='%{hovertext}<extra></extra>'
        )
        
        # Display the figure
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No valid train segments to display. Please check your train schedules.")

# Train schedules table
st.markdown("## 📋 Train Schedules")

if not st.session_state.trains:
    st.info("No train schedules added yet")
else:
    # Create tabs for each train
    train_tabs = st.tabs([f"{train['name']}" for train in st.session_state.trains])
    
    for i, tab in enumerate(train_tabs):
        with tab:
            train = st.session_state.trains[i]
            
            # Train info and actions
            st.markdown(f"""
            <div style="background-color:{train['color']}25; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                <span style="display:flex; align-items:center;">
                    <span style="background-color:{train['color']}; width:16px; height:16px; border-radius:50%; display:inline-block; margin-right:8px;"></span>
                    <strong style="font-size:1.2rem;">{train['name']}</strong>
                </span>
            </div>
            """, unsafe_allow_html=True)
            
            # Action buttons without columns
            edit_btn = st.button("✏️ Edit Train", key=f"edit_train_{i}")
            delete_btn = st.button("🗑️ Delete Train", key=f"del_train_{i}")
            
            if edit_btn:
                st.session_state.selected_train_idx = i
                # Prepare form with existing train data
                st.session_state.template_schedule = train['schedule']
                st.session_state.train_form_key = str(uuid.uuid4())
                st.info(f"Selected {train['name']} for editing. Use the train schedule form to make changes.")
                st.rerun()
            
            if delete_btn:
                st.session_state.trains.pop(i)
                if st.session_state.selected_train_idx == i:
                    st.session_state.selected_train_idx = None
                elif st.session_state.selected_train_idx is not None and st.session_state.selected_train_idx > i:
                    st.session_state.selected_train_idx -= 1
                st.success(f"Removed train: {train['name']}")
                st.rerun()
            
            # Display schedule
            if train['schedule']:
                # Add visual timeline
                st.markdown("#### Schedule Timeline")
                timeline_data = []
                
                for item in train['schedule']:
                    if 'station' in item and 'arrival' in item and 'departure' in item:
                        if item['arrival'] and item['departure']:
                            timeline_data.append({
                                'Station': item['station'],
                                'Arrival': item['arrival'],
                                'Departure': item['departure']
                            })
                
                if timeline_data:
                    timeline_df = pd.DataFrame(timeline_data)
                    st.dataframe(timeline_df, use_container_width=True)
                else:
                    st.info("No valid schedule data for this train")
            else:
                st.info("No schedule data for this train")

# Data import/export section
st.markdown("## 💾 Data Management")

# Export functionality
st.subheader("Export Data")
if st.session_state.stations and st.session_state.trains:
    export_data = {
        "stations": st.session_state.stations,
        "trains": st.session_state.trains
    }
    json_str = json.dumps(export_data, indent=2)
    st.download_button(
        label="Download Data as JSON",
        data=json_str,
        file_name="train_diagram_data.json",
        mime="application/json",
        use_container_width=True
    )
else:
    st.info("Add stations and trains to enable export")

# Import functionality
st.subheader("Import Data")
uploaded_file = st.file_uploader("Upload JSON data", type=['json'])

if uploaded_file is not None:
    try:
        import_data = json.loads(uploaded_file.getvalue().decode())
        
        if 'stations' in import_data and 'trains' in import_data:
            if st.button("Load Data", use_container_width=True):
                st.session_state.stations = import_data['stations']
                st.session_state.trains = import_data['trains']
                st.success("Data loaded successfully")
                st.rerun()
        else:
            st.error("Invalid data format")
    except Exception as e:
        st.error(f"Error loading data: {e}")

# Instructions at the bottom
with st.expander("ℹ️ Instructions", expanded=False):
    st.markdown("""
    ## How to Use This Tool

    1. **Add Stations**:
       - Enter station names individually or use the bulk entry method
       - Use the sample stations button for a quick start
       - Stations represent points along your railway line

    2. **Create Train Schedules**:
       - Enter a name and pick a color for your train
       - Use one of the templates (Express, Local, Uptown, Downtown) for quick setup
       - Or manually add arrival/departure times for each station
       - Click "Add Train Schedule" when done

    3. **Visualize and Interact**:
       - The time-space diagram shows train movements between stations
       - Lines represent train journeys between stations
       - Points mark arrivals and departures at stations
       - Hover over elements to see details

    4. **Customize View**:
       - Adjust time range to focus on specific periods
       - Swap axes to change perspective (time on X or Y axis)
       - Reset view to return to default settings

    5. **Manage Data**:
       - Edit existing trains by selecting them in the Train Schedules section
       - Delete trains or stations when needed
       - Export your data to save your work
       - Import previously saved data to continue working

    **Tips**:
       - For each station, you only need to enter either arrival or departure time - the other will be copied
       - Times should be in 24-hour format (HH:MM)
       - If a train doesn't stop at a station, leave both fields empty
    """)

# Footer
st.markdown("""
<div style="text-align:center; margin-top:2rem; padding:1rem; background-color:#f8f9fa; border-radius:0.5rem;">
    <p>Train Time-Space Diagram Visualizer | Made with Streamlit</p>
</div>
""", unsafe_allow_html=True)
