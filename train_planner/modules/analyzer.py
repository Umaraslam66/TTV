import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from utils.time_utils import minutes_to_hhmm, parse_time, time_diff

class Analyzer:
    """
    Class to analyze train schedules in the Streamlit app.
    """
    
    @staticmethod
    def analyze_schedule_ui():
        """UI for analyzing train schedules."""
        st.header("Schedule Analysis")
        
        if not st.session_state.stations or not st.session_state.trains:
            st.warning("Please add stations and trains to analyze the schedule.")
            return
        
        tabs = st.tabs(["Conflict Detection", "Track Utilization", "Performance Metrics"])
        
        with tabs[0]:
            Analyzer.conflict_detection_ui()
        
        with tabs[1]:
            Analyzer.track_utilization_ui()
        
        with tabs[2]:
            Analyzer.performance_metrics_ui()
    
    @staticmethod
    def conflict_detection_ui():
        """UI for detecting schedule conflicts."""
        st.subheader("Schedule Conflict Detection")
        
        # Check for conflicts
        conflicts = Analyzer.detect_conflicts(st.session_state.trains)
        
        if conflicts:
            st.error(f"Found {len(conflicts)} potential conflicts in the schedule")
            
            # Create a dataframe to display conflicts
            conflict_data = []
            for conflict in conflicts:
                conflict_data.append({
                    "Train 1": conflict['train1_name'],
                    "Train 2": conflict['train2_name'],
                    "Station": conflict['station'],
                    "Time": minutes_to_hhmm(conflict['time']),
                    "Conflict Type": conflict['type']
                })
            
            df = pd.DataFrame(conflict_data)
            st.dataframe(df, use_container_width=True)
            
            # Visualization of conflicts
            st.subheader("Conflict Visualization")
            Analyzer.visualize_conflicts(conflicts)
        else:
            st.success("No schedule conflicts detected")
    
    @staticmethod
    def detect_conflicts(trains, min_separation=2):
        """
        Detect schedule conflicts between trains.
        
        Args:
            trains (list): List of Train dictionaries or Train objects.
            min_separation (int, optional): Minimum separation in minutes. Default is 2.
            
        Returns:
            list: List of conflict dictionaries.
        """
        conflicts = []
        
        # Compare each pair of trains
        for i in range(len(trains)):
            for j in range(i + 1, len(trains)):
                train1 = trains[i]
                train2 = trains[j]
                
                # Handle both Train objects and dictionaries for train1
                if hasattr(train1, 'schedule'):
                    train1_schedule = train1.schedule
                    train1_name = train1.name
                elif isinstance(train1, dict):
                    train1_schedule = train1.get('schedule', [])
                    train1_name = train1.get('name', f"Train {i+1}")
                else:
                    continue  # Skip if neither format is valid
                
                # Handle both Train objects and dictionaries for train2
                if hasattr(train2, 'schedule'):
                    train2_schedule = train2.schedule
                    train2_name = train2.name
                elif isinstance(train2, dict):
                    train2_schedule = train2.get('schedule', [])
                    train2_name = train2.get('name', f"Train {j+1}")
                else:
                    continue  # Skip if neither format is valid
                
                # Check for conflicts at each station
                train1_stations = {stop['station']: stop for stop in train1_schedule}
                train2_stations = {stop['station']: stop for stop in train2_schedule}
                
                # Find common stations
                common_stations = set(train1_stations.keys()) & set(train2_stations.keys())
                
                for station in common_stations:
                    train1_stop = train1_stations[station]
                    train2_stop = train2_stations[station]
                    
                    # Check arrival-arrival conflicts
                    if train1_stop.get('arrival') is not None and train2_stop.get('arrival') is not None:
                        time_difference = abs(train1_stop['arrival'] - train2_stop['arrival'])
                        
                        if time_difference < min_separation:
                            conflicts.append({
                                'train1_name': train1_name,
                                'train2_name': train2_name,
                                'station': station,
                                'time': min(train1_stop['arrival'], train2_stop['arrival']),
                                'type': 'Arrival-Arrival',
                                'difference': time_difference
                            })
                    
                    # Check departure-departure conflicts
                    if train1_stop.get('departure') is not None and train2_stop.get('departure') is not None:
                        time_difference = abs(train1_stop['departure'] - train2_stop['departure'])
                        
                        if time_difference < min_separation:
                            conflicts.append({
                                'train1_name': train1_name,
                                'train2_name': train2_name,
                                'station': station,
                                'time': min(train1_stop['departure'], train2_stop['departure']),
                                'type': 'Departure-Departure',
                                'difference': time_difference
                            })
                    
                    # Check arrival-departure conflicts
                    if train1_stop.get('arrival') is not None and train2_stop.get('departure') is not None:
                        time_difference = abs(train1_stop['arrival'] - train2_stop['departure'])
                        
                        if time_difference < min_separation:
                            conflicts.append({
                                'train1_name': train1_name,
                                'train2_name': train2_name,
                                'station': station,
                                'time': min(train1_stop['arrival'], train2_stop['departure']),
                                'type': 'Arrival-Departure',
                                'difference': time_difference
                            })
                    
                    # Check departure-arrival conflicts
                    if train1_stop.get('departure') is not None and train2_stop.get('arrival') is not None:
                        time_difference = abs(train1_stop['departure'] - train2_stop['arrival'])
                        
                        if time_difference < min_separation:
                            conflicts.append({
                                'train1_name': train1_name,
                                'train2_name': train2_name,
                                'station': station,
                                'time': min(train1_stop['departure'], train2_stop['arrival']),
                                'type': 'Departure-Arrival',
                                'difference': time_difference
                            })
        
        return conflicts
    
    @staticmethod
    def visualize_conflicts(conflicts):
        """
        Visualize schedule conflicts.
        
        Args:
            conflicts (list): List of conflict dictionaries.
        """
        if not conflicts:
            return
        
        # Create a scatter plot of conflicts
        fig = go.Figure()
        
        # Extract unique trains and stations
        trains = set()
        stations = set()
        
        for conflict in conflicts:
            trains.add(conflict['train1_name'])
            trains.add(conflict['train2_name'])
            stations.add(conflict['station'])
        
        trains = sorted(list(trains))
        stations = sorted(list(stations))
        
        # Create a color map for conflict types
        conflict_types = {
            'Arrival-Arrival': 'red',
            'Departure-Departure': 'orange',
            'Arrival-Departure': 'blue',
            'Departure-Arrival': 'green'
        }
        
        # Add a trace for each conflict type
        for conflict_type, color in conflict_types.items():
            filtered_conflicts = [c for c in conflicts if c['type'] == conflict_type]
            
            if not filtered_conflicts:
                continue
            
            # Create scatter plot
            fig.add_trace(go.Scatter(
                x=[c['time'] for c in filtered_conflicts],
                y=[c['station'] for c in filtered_conflicts],
                mode='markers',
                marker=dict(
                    size=10,
                    color=color
                ),
                name=conflict_type,
                text=[f"{c['train1_name']} vs {c['train2_name']}<br>Diff: {c['difference']} min" for c in filtered_conflicts],
                hoverinfo='text'
            ))
        
        # Update layout
        fig.update_layout(
            title="Schedule Conflicts",
            xaxis=dict(
                title="Time",
                tickmode='array',
                tickvals=list(range(0, 24 * 60, 60)),
                ticktext=[minutes_to_hhmm(t) for t in range(0, 24 * 60, 60)]
            ),
            yaxis=dict(
                title="Station",
                categoryorder='array',
                categoryarray=stations
            ),
            height=400,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    @staticmethod
    def track_utilization_ui():
        """UI for analyzing track utilization."""
        st.subheader("Track Utilization Analysis")
        
        # Calculate utilization data
        utilization_data = Analyzer.calculate_track_utilization(
            st.session_state.stations,
            st.session_state.trains
        )
        
        # Display utilization by time
        st.write("**Utilization by Time**")
        Analyzer.visualize_time_utilization(utilization_data['time_data'])
        
        # Display utilization by station
        st.write("**Utilization by Station**")
        Analyzer.visualize_station_utilization(utilization_data['station_data'])
    
    @staticmethod
    def calculate_track_utilization(stations, trains):
        """
        Calculate track utilization data.
        
        Args:
            stations (list): List of Station objects.
            trains (list): List of Train dictionaries.
            
        Returns:
            dict: Dictionary with utilization data.
        """
        # Initialize data structures
        station_names = [s.name for s in stations]
        
        # Count trains per hour at each station
        time_data = {}
        for hour in range(24):
            time_data[hour] = {station: 0 for station in station_names}
        
        # Count total trains at each station
        station_data = {station: 0 for station in station_names}
        
        # Process each train schedule
        for train in trains:
            for stop in train['schedule']:
                station = stop['station']
                
                # Skip if station not in stations list
                if station not in station_names:
                    continue
                
                # Increment station counter
                station_data[station] += 1
                
                # Increment hourly counter
                arrival = stop.get('arrival')
                if arrival is not None:
                    try:
                        # Make sure arrival is an integer
                        if isinstance(arrival, str):
                            arrival = parse_time(arrival)
                            
                        if arrival is not None:
                            hour = int(arrival) // 60
                            if 0 <= hour < 24:
                                time_data[hour][station] += 1
                    except (TypeError, ValueError):
                        # Skip if we can't process the arrival time
                        pass
        
        return {
            'time_data': time_data,
            'station_data': station_data
        }
    
    @staticmethod
    def visualize_time_utilization(time_data):
        """
        Visualize track utilization by time.
        
        Args:
            time_data (dict): Dictionary of hourly utilization data.
        """
        # Create a heatmap
        hours = sorted(time_data.keys())
        stations = sorted(time_data[hours[0]].keys())
        
        z_data = []
        for station in stations:
            row = []
            for hour in hours:
                row.append(time_data[hour][station])
            z_data.append(row)
        
        fig = go.Figure(data=go.Heatmap(
            z=z_data,
            x=[f"{hour}:00" for hour in hours],
            y=stations,
            colorscale='Viridis',
            hoverongaps=False
        ))
        
        fig.update_layout(
            title="Trains per Hour at Each Station",
            xaxis_title="Hour of Day",
            yaxis_title="Station",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    @staticmethod
    def visualize_station_utilization(station_data):
        """
        Visualize track utilization by station.
        
        Args:
            station_data (dict): Dictionary of station utilization data.
        """
        # Create a bar chart
        stations = list(station_data.keys())
        values = list(station_data.values())
        
        fig = px.bar(
            x=stations,
            y=values,
            labels={'x': 'Station', 'y': 'Number of Trains'},
            title="Total Trains per Station"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    @staticmethod
    def performance_metrics_ui():
        """UI for analyzing performance metrics."""
        st.subheader("Performance Metrics")
        
        if not st.session_state.trains:
            st.info("No trains to analyze")
            return
        
        # Calculate metrics
        metrics = Analyzer.calculate_performance_metrics(st.session_state.trains)
        
        # Display overall metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Trains", metrics['total_trains'])
        
        with col2:
            st.metric("Average Stops", round(metrics['avg_stops'], 1))
        
        with col3:
            st.metric("Average Dwell Time", f"{round(metrics['avg_dwell_time'], 1)} min")
        
        # Display detailed metrics table
        st.write("**Train Metrics**")
        st.dataframe(metrics['train_metrics'], use_container_width=True)
        
        # Visualize train speeds
        st.write("**Average Train Speeds**")
        fig = px.bar(
            metrics['train_metrics'],
            x='Train',
            y='Avg Speed',
            color='Train',
            labels={'Train': 'Train', 'Avg Speed': 'Average Speed (stations/minute)'},
            title="Average Train Speeds"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    @staticmethod
    def calculate_performance_metrics(trains):
        """
        Calculate performance metrics for train schedules.
        
        Args:
            trains (list): List of Train dictionaries.
            
        Returns:
            dict: Dictionary with performance metrics.
        """
        total_trains = len(trains)
        total_stops = 0
        total_dwell_time = 0
        dwell_count = 0
        
        train_metrics = []
        
        for train in trains:
            train_name = train['name']
            stops = train['schedule']
            
            # Skip if no stops
            if not stops:
                continue
            
            stops_count = len(stops)
            total_stops += stops_count
            
            # Calculate dwell times
            train_dwell_time = 0
            train_dwell_count = 0
            
            for stop in stops:
                arrival = stop.get('arrival')
                departure = stop.get('departure')
                
                if arrival is not None and departure is not None:
                    dwell = departure - arrival
                    train_dwell_time += dwell
                    train_dwell_count += 1
                    
                    total_dwell_time += dwell
                    dwell_count += 1
            
            # Calculate average speed
            if stops_count >= 2:
                first_stop = stops[0]
                last_stop = stops[-1]
                
                first_time = first_stop.get('departure', first_stop.get('arrival'))
                last_time = last_stop.get('arrival', last_stop.get('departure'))
                
                if first_time is not None and last_time is not None:
                    total_time = last_time - first_time
                    total_stations = stops_count - 1
                    
                    avg_speed = total_stations / total_time if total_time > 0 else 0
                else:
                    avg_speed = 0
            else:
                avg_speed = 0
            
            # Add to train metrics
            train_metrics.append({
                'Train': train_name,
                'Stops': stops_count,
                'Total Time (min)': total_time if 'total_time' in locals() else 0,
                'Avg Dwell (min)': train_dwell_time / train_dwell_count if train_dwell_count > 0 else 0,
                'Avg Speed': avg_speed
            })
        
        # Calculate overall averages
        avg_stops = total_stops / total_trains if total_trains > 0 else 0
        avg_dwell_time = total_dwell_time / dwell_count if dwell_count > 0 else 0
        
        return {
            'total_trains': total_trains,
            'total_stops': total_stops,
            'avg_stops': avg_stops,
            'avg_dwell_time': avg_dwell_time,
            'train_metrics': pd.DataFrame(train_metrics)
        }