import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import plotly.express as px

from utils.time_utils import minutes_to_hhmm, get_time_range

class Visualizer:
    """
    Class to handle visualization of train schedules in the Streamlit app.
    """
    
    @staticmethod
    def initialize_session_state():
        """Initialize visualization-related session state variables."""
        if 'time_on_x_axis' not in st.session_state:
            st.session_state.time_on_x_axis = True
        
        if 'min_time' not in st.session_state or 'max_time' not in st.session_state:
            # Default time range (6:00 AM to 10:00 PM)
            st.session_state.min_time = 6 * 60  # 6:00 AM in minutes
            st.session_state.max_time = 22 * 60  # 10:00 PM in minutes
    
    @staticmethod
    def visualize_schedule_ui():
        """UI for visualizing train schedules."""
        st.header("Schedule Visualization")
        
        if not st.session_state.stations or not st.session_state.trains:
            st.warning("Please add stations and trains to visualize the schedule.")
            return
        
        # Visualization controls
        st.subheader("Visualization Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.session_state.time_on_x_axis = st.checkbox(
                "Time on X-axis (horizontal)",
                value=st.session_state.time_on_x_axis
            )
        
        with col2:
            # Auto-calculate time range using the trains from session state
            if st.session_state.trains:
                # Make sure to pass the actual train data
                min_time, max_time = get_time_range(st.session_state.trains)
                
                # Convert to HH:MM for display
                min_time_str = minutes_to_hhmm(min_time)
                max_time_str = minutes_to_hhmm(max_time)
            
            st.write(f"Detected time range: {min_time_str} - {max_time_str}")
        
        # Manual time range adjustment
        col1, col2 = st.columns(2)
        
        with col1:
            min_hour = st.number_input("Start Hour", 0, 23, min_time // 60)
            min_minute = st.number_input("Start Minute", 0, 59, min_time % 60)
            st.session_state.min_time = min_hour * 60 + min_minute
        
        with col2:
            max_hour = st.number_input("End Hour", 0, 23, max_time // 60)
            max_minute = st.number_input("End Minute", 0, 59, max_time % 60)
            st.session_state.max_time = max_hour * 60 + max_minute
        
        # Time-space diagram
        st.subheader("Time-Space Diagram")
        fig = Visualizer.create_time_space_diagram(
            stations=st.session_state.stations,
            trains=st.session_state.trains,
            time_on_x=st.session_state.time_on_x_axis,
            min_time=st.session_state.min_time,
            max_time=st.session_state.max_time
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Train schedule table
        st.subheader("Train Schedules")
        Visualizer.display_train_schedules()
    
    @staticmethod
    def create_time_space_diagram(stations, trains, time_on_x=True, min_time=None, max_time=None, settings=None):
        """
        Create a time-space diagram for train schedules.
        
        Args:
            stations (list): List of Station objects.
            trains (list): List of Train dictionaries.
            time_on_x (bool, optional): If True, time is on X-axis. Default is True.
            min_time (int, optional): Minimum time in minutes. Default is None.
            max_time (int, optional): Maximum time in minutes. Default is None.
            settings (dict, optional): Visualization settings. Default is None.
            
        Returns:
            plotly.graph_objects.Figure: Plotly figure object.
        """
        # Set default settings if not provided
        if settings is None:
            settings = {
                'height': 600,
                'station_font_size': 12,
                'time_font_size': 10,
                'line_width': 2,
                'marker_size': 8,
                'time_interval': 60,
                'color_theme': 'plotly',
                'bg_color': 'white',
                'show_grid': True,
                'show_legend': True,
                'show_markers': True,
                'title': 'Train Time-Space Diagram'
            }
        
        # Determine axis ranges
        if min_time is None or max_time is None:
            if trains:
                min_time, max_time = get_time_range(trains)
            else:
                # Default range if no trains
                min_time = 6 * 60  # 6:00 AM
                max_time = 22 * 60  # 10:00 PM
        
        # Create figure
        fig = go.Figure()
        
        # Get station names and positions
        station_names = [s.name for s in stations]
        station_positions = [s.position for s in stations]
        
        # Choose color scheme based on theme
        color_schemes = {
            'plotly': None,  # Default Plotly colors
            'pastel': px.colors.qualitative.Pastel,
            'dark': px.colors.qualitative.Dark24,
            'vibrant': px.colors.qualitative.Vivid,
            'grayscale': [f'rgb({i},{i},{i})' for i in range(50, 200, 15)]
        }
        
        # Get color sequence based on theme
        color_sequence = color_schemes.get(settings['color_theme'])
        
        # Add each train to the plot
        for train_idx, train in enumerate(trains):
            # Skip trains with no valid schedule
            if not train.get('schedule', []) and not hasattr(train, 'schedule'):
                continue
                
            # Get the schedule from either dict or object
            schedule = train.schedule if hasattr(train, 'schedule') else train.get('schedule', [])
            
            # Extract schedule data
            x_data = []
            y_data = []
            hover_texts = []
            marker_symbols = []
            
            # Get train info
            train_name = train.name if hasattr(train, 'name') else train.get('name', 'Unknown')
            train_color = train.color if hasattr(train, 'color') else train.get('color', '#1f77b4')
            
            # Override color if using a color sequence
            if color_sequence and train_idx < len(color_sequence):
                train_color = color_sequence[train_idx]
            
            for stop in schedule:
                station = stop.get('station')
                arrival = stop.get('arrival')
                departure = stop.get('departure')
                
                # Skip if station is not in stations list
                if station not in station_names:
                    continue
                
                # Get station position
                station_idx = station_names.index(station)
                station_pos = station_positions[station_idx]
                
                # Add arrival point if it exists
                if arrival is not None:
                    # Skip if outside time range
                    if arrival < min_time or arrival > max_time:
                        continue
                    
                    time_val = arrival
                    pos_val = station_pos
                    
                    if time_on_x:
                        x_data.append(time_val)
                        y_data.append(pos_val)
                    else:
                        x_data.append(pos_val)
                        y_data.append(time_val)
                    
                    # Add hover text
                    hover_text = f"{train_name}<br>{station}<br>Arrival: {minutes_to_hhmm(arrival)}"
                    hover_texts.append(hover_text)
                    marker_symbols.append("circle")
                
                # Add departure point if it exists
                if departure is not None:
                    # Skip if outside time range
                    if departure < min_time or departure > max_time:
                        continue
                    
                    time_val = departure
                    pos_val = station_pos
                    
                    if time_on_x:
                        x_data.append(time_val)
                        y_data.append(pos_val)
                    else:
                        x_data.append(pos_val)
                        y_data.append(time_val)
                    
                    # Add hover text
                    hover_text = f"{train_name}<br>{station}<br>Departure: {minutes_to_hhmm(departure)}"
                    hover_texts.append(hover_text)
                    marker_symbols.append("square")
                    
            # Skip if no valid data points
            if not x_data or not y_data:
                continue
            
            # Determine line and marker mode based on settings
            mode = 'lines'
            if settings.get('show_markers', True):
                mode += '+markers'
            
            # Add lines and markers
            fig.add_trace(go.Scatter(
                x=x_data,
                y=y_data,
                mode=mode,
                name=train_name,
                line=dict(
                    color=train_color, 
                    width=settings.get('line_width', 2)
                ),
                marker=dict(
                    size=settings.get('marker_size', 8),
                    color=train_color,
                    symbol=marker_symbols
                ),
                text=hover_texts,
                hoverinfo='text'
            ))
        
        # Set background color
        bg_colors = {
            'white': 'white',
            'light gray': '#f0f2f6',
            'dark': '#262730',
            'transparent': 'rgba(0,0,0,0)'
        }
        bg_color = bg_colors.get(settings.get('bg_color', 'white'), 'white')
        
        # Generate time ticks based on interval
        time_interval = settings.get('time_interval', 60)
        time_ticks = list(range(
            (min_time // time_interval) * time_interval,
            max_time + time_interval,
            time_interval
        ))
        
        # Set axis titles and ranges
        if time_on_x:
            # Time on X-axis, stations on Y-axis
            fig.update_layout(
                xaxis=dict(
                    title='Time',
                    tickmode='array',
                    tickvals=time_ticks,
                    ticktext=[minutes_to_hhmm(t) for t in time_ticks],
                    tickfont=dict(size=settings.get('time_font_size', 10)),
                    range=[min_time, max_time]
                ),
                yaxis=dict(
                    title='Station',
                    tickmode='array',
                    tickvals=station_positions,
                    ticktext=station_names,
                    tickfont=dict(size=settings.get('station_font_size', 12))
                )
            )
        else:
            # Stations on X-axis, time on Y-axis
            fig.update_layout(
                xaxis=dict(
                    title='Station',
                    tickmode='array',
                    tickvals=station_positions,
                    ticktext=station_names,
                    tickfont=dict(size=settings.get('station_font_size', 12))
                ),
                yaxis=dict(
                    title='Time',
                    tickmode='array',
                    tickvals=time_ticks,
                    ticktext=[minutes_to_hhmm(t) for t in time_ticks],
                    tickfont=dict(size=settings.get('time_font_size', 10)),
                    range=[min_time, max_time]
                )
            )
        
        # Add grid lines
        fig.update_layout(
            grid=dict(rows=1, columns=1),
            plot_bgcolor=bg_color,
            paper_bgcolor=bg_color,
            title=settings.get('title', 'Train Time-Space Diagram'),
            height=settings.get('height', 600),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                font=dict(size=settings.get('station_font_size', 12))
            ),
            margin=dict(l=50, r=20, t=50, b=50),
            showlegend=settings.get('show_legend', True)
        )
        
        # Set grid visibility
        fig.update_xaxes(showgrid=settings.get('show_grid', True))
        fig.update_yaxes(showgrid=settings.get('show_grid', True))
        
        # Reverse Y-axis for time if not time_on_x
        if not time_on_x:
            fig.update_layout(yaxis_autorange="reversed")
        
        return fig
    
    @staticmethod
    def display_train_schedules(trains=None):
        """
        Display train schedules in tabular format.
        
        Args:
            trains (list, optional): List of trains to display. If None, uses all trains from session state.
        """
        # Use provided trains or get from session state
        if trains is None:
            if not st.session_state.trains:
                st.info("No trains to display")
                return
            trains = st.session_state.trains
            
        if not trains:
            st.info("No trains to display")
            return
        
        train_names = [train.get('name', f"Train {i+1}") for i, train in enumerate(trains)]
        
        # Create a train selector
        selected_train = st.selectbox(
            "Select train to view schedule",
            options=train_names
        )
        
        # Find the selected train
        selected_train_data = None
        for train in trains:
            if train.get('name') == selected_train:
                selected_train_data = train
                break
        
        if not selected_train_data:
            st.error("Train data not available")
            return
            
        # Check if train has schedule
        if not selected_train_data.get('schedule'):
            st.info(f"No schedule data for {selected_train_data.get('name', 'this train')}")
            return
        
        # Create a more attractive train info card
        col1, col2 = st.columns([3, 1])
        with col1:
            st.subheader(f"🚆 {selected_train}")
            
            # Get train statistics
            stops_count = len(selected_train_data['schedule'])
            
            # Find first and last stations
            first_station = selected_train_data['schedule'][0].get('station', 'N/A') if stops_count > 0 else 'N/A'
            last_station = selected_train_data['schedule'][-1].get('station', 'N/A') if stops_count > 0 else 'N/A'
            
            # Find start and end times
            start_time = None
            if stops_count > 0:
                first_stop = selected_train_data['schedule'][0]
                start_time = first_stop.get('departure', first_stop.get('arrival'))
            
            end_time = None
            if stops_count > 0:
                last_stop = selected_train_data['schedule'][-1]
                end_time = last_stop.get('arrival', last_stop.get('departure'))
            
            # Calculate journey time
            journey_time = None
            if start_time is not None and end_time is not None:
                journey_time = end_time - start_time
                
            # Display info
            st.write(f"**From:** {first_station} **To:** {last_station}")
            st.write(f"**Stops:** {stops_count}")
            if start_time is not None:
                st.write(f"**Departure:** {minutes_to_hhmm(start_time)}")
            if end_time is not None:
                st.write(f"**Arrival:** {minutes_to_hhmm(end_time)}")
            if journey_time is not None:
                hours = journey_time // 60
                mins = journey_time % 60
                st.write(f"**Journey Time:** {hours}h {mins:02d}m")
        
        with col2:
            # Display color sample
            st.markdown(
                f"<div style='background-color:{selected_train_data.get('color', '#1f77b4')}; "
                f"width:50px; height:50px; border-radius:5px; margin-top:20px;'></div>",
                unsafe_allow_html=True
            )
        
        # Convert schedule to dataframe
        schedule_data = []
        for i, stop in enumerate(selected_train_data['schedule']):
            # Safely get values, handling potential None values
            station = stop.get('station', '')
            arrival = stop.get('arrival')
            departure = stop.get('departure')
            
            # Calculate dwell time
            dwell_time = "-"
            if arrival is not None and departure is not None:
                dwell_minutes = departure - arrival
                if dwell_minutes > 0:
                    dwell_time = f"{dwell_minutes} min"
            
            # Calculate travel time from previous stop
            travel_time = "-"
            if i > 0 and arrival is not None:
                prev_stop = selected_train_data['schedule'][i-1]
                prev_departure = prev_stop.get('departure')
                if prev_departure is not None:
                    travel_minutes = arrival - prev_departure
                    if travel_minutes > 0:
                        travel_time = f"{travel_minutes} min"
            
            schedule_data.append({
                'Stop': i+1,
                'Station': station,
                'Arrival': minutes_to_hhmm(arrival) if arrival is not None else "-",
                'Departure': minutes_to_hhmm(departure) if departure is not None else "-",
                'Dwell Time': dwell_time,
                'Travel Time': travel_time
            })
        
        if not schedule_data:
            st.info("No stops in this train's schedule")
            return
            
        # Display the schedule in a styled dataframe
        st.markdown("### Schedule")
        df = pd.DataFrame(schedule_data)
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                'Stop': st.column_config.NumberColumn(
                    "Stop",
                    format="%d",
                    width="small"
                ),
                'Station': st.column_config.TextColumn(
                    "Station",
                    width="medium"
                ),
                'Arrival': st.column_config.TextColumn(
                    "Arrival",
                    width="medium"
                ),
                'Departure': st.column_config.TextColumn(
                    "Departure",
                    width="medium"
                ),
                'Dwell Time': st.column_config.TextColumn(
                    "Dwell Time",
                    width="medium"
                ),
                'Travel Time': st.column_config.TextColumn(
                    "Travel Time",
                    width="medium",
                    help="Time from previous station"
                )
            }
        )
        
        # Display visual timeline
        st.markdown("### Timeline")
        Visualizer.display_train_timeline(selected_train_data)
    
    @staticmethod
    def display_train_timeline(train):
        """
        Display a simplified visual timeline for a single train.
        
        Args:
            train (dict): Train dictionary with schedule.
        """
        # Get schedule from train dict
        if hasattr(train, 'schedule'):
            schedule = train.schedule
        else:
            schedule = train.get('schedule', [])
            
        if not schedule:
            st.info("No timeline available - schedule is empty")
            return
        
        # Calculate total time range
        min_time = float('inf')
        max_time = 0
        has_valid_times = False
        
        for stop in schedule:
            arrival = stop.get('arrival')
            departure = stop.get('departure')
            
            if arrival is not None and isinstance(arrival, (int, float)):
                min_time = min(min_time, arrival)
                max_time = max(max_time, arrival)
                has_valid_times = True
                
            if departure is not None and isinstance(departure, (int, float)):
                min_time = min(min_time, departure)
                max_time = max(max_time, departure)
                has_valid_times = True
        
        if not has_valid_times or min_time == float('inf') or max_time == 0:
            st.info("Cannot create timeline - no valid time values")
            return
            
        # Ensure there's a reasonable time range
        if max_time - min_time < 10:  # Less than 10 minutes
            min_time -= 5
            max_time += 5
        
        # Create a timeline figure
        fig = go.Figure()
        
        # Add each stop as a point
        for stop in train['schedule']:
            station = stop['station']
            arrival = stop['arrival']
            departure = stop['departure']
            
            if arrival is not None:
                # Position as percentage of timeline
                pos = (arrival - min_time) / (max_time - min_time) * 100
                
                fig.add_trace(go.Scatter(
                    x=[pos],
                    y=[0.5],
                    mode='markers+text',
                    marker=dict(size=12, color=train['color'], symbol='circle'),
                    text=[station],
                    textposition='top center',
                    showlegend=False,
                    hovertext=f"{station}<br>Arrival: {minutes_to_hhmm(arrival)}"
                ))
            
            if departure is not None and departure != arrival:
                # Position as percentage of timeline
                pos = (departure - min_time) / (max_time - min_time) * 100
                
                fig.add_trace(go.Scatter(
                    x=[pos],
                    y=[0.5],
                    mode='markers',
                    marker=dict(size=10, color=train['color'], symbol='square'),
                    showlegend=False,
                    hovertext=f"{station}<br>Departure: {minutes_to_hhmm(departure)}"
                ))
        
        # Add timeline bar
        fig.add_shape(
            type='line',
            x0=0, y0=0.5,
            x1=100, y1=0.5,
            line=dict(color='gray', width=2)
        )
        
        # Add tick marks for hours
        hour = (min_time // 60) * 60
        while hour <= max_time:
            # Position as percentage of timeline
            pos = (hour - min_time) / (max_time - min_time) * 100
            
            if 0 <= pos <= 100:
                # Add tick mark
                fig.add_shape(
                    type='line',
                    x0=pos, y0=0.4,
                    x1=pos, y1=0.6,
                    line=dict(color='gray', width=1)
                )
                
                # Add hour label
                fig.add_annotation(
                    x=pos,
                    y=0.3,
                    text=minutes_to_hhmm(hour),
                    showarrow=False,
                    font=dict(size=10)
                )
            
            hour += 60
        
        # Update layout
        fig.update_layout(
            height=150,
            margin=dict(l=20, r=20, t=50, b=20),
            xaxis=dict(
                range=[-5, 105],
                showticklabels=False,
                showgrid=False,
                zeroline=False
            ),
            yaxis=dict(
                range=[0, 1],
                showticklabels=False,
                showgrid=False,
                zeroline=False
            ),
            title="Timeline",
            plot_bgcolor='white',
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)