import json
import csv
import io
import base64
from datetime import datetime

from models.schedule import Schedule

def export_schedule_to_json(schedule):
    """
    Export a schedule to JSON format.
    
    Args:
        schedule (Schedule): Schedule object to export.
        
    Returns:
        str: JSON string representation of the schedule.
    """
    if not isinstance(schedule, Schedule):
        raise TypeError("Expected Schedule object")
    
    return json.dumps(schedule.to_dict(), indent=2)

def import_schedule_from_json(json_data):
    """
    Import a schedule from JSON format.
    
    Args:
        json_data (str): JSON string representation of a schedule.
        
    Returns:
        Schedule or None: Schedule object, or None if invalid.
    """
    try:
        data = json.loads(json_data)
        return Schedule.from_dict(data)
    except Exception as e:
        print(f"Error importing schedule: {e}")
        return None

def export_schedule_to_csv(schedule):
    """
    Export a schedule to CSV format (train timetables).
    
    Args:
        schedule (Schedule): Schedule object to export.
        
    Returns:
        str: CSV string representation of the schedule.
    """
    if not isinstance(schedule, Schedule):
        raise TypeError("Expected Schedule object")
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header with schedule name and timestamp
    writer.writerow([f"Schedule: {schedule.name}", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
    writer.writerow([])  # Empty row
    
    # For each train, write a timetable
    for train in schedule.trains:
        writer.writerow([f"Train: {train.name}"])
        writer.writerow(["Station", "Arrival", "Departure", "Dwell time"])
        
        for stop in train.schedule:
            station = stop.get('station', '')
            arrival = stop.get('arrival', '')
            departure = stop.get('departure', '')
            
            # Calculate dwell time
            from utils.time_utils import parse_time, format_duration
            dwell = ''
            if arrival is not None and departure is not None:
                arrival_mins = parse_time(arrival)
                departure_mins = parse_time(departure)
                if arrival_mins is not None and departure_mins is not None:
                    dwell = format_duration(departure_mins - arrival_mins)
            
            writer.writerow([station, arrival, departure, dwell])
        
        writer.writerow([])  # Empty row
    
    # Return CSV data
    return output.getvalue()

def export_stations_to_text(stations):
    """
    Export a list of stations to plain text (one per line).
    
    Args:
        stations (list): List of Station objects.
        
    Returns:
        str: Text representation of stations.
    """
    return "\n".join(station.name for station in stations)

def import_stations_from_text(text):
    """
    Import stations from plain text (one per line).
    
    Args:
        text (str): Text with station names (one per line).
        
    Returns:
        list: List of station names.
    """
    from models.station import Station
    
    # Split by lines and filter out empty lines
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    
    # Create Station objects
    stations = []
    for i, line in enumerate(lines):
        # Position stations evenly
        position = i / (len(lines) - 1) if len(lines) > 1 else 0
        stations.append(Station(name=line, position=position))
    
    return stations

def get_download_link(content, filename, mime_type="text/plain"):
    """
    Generate a download link for some content.
    
    Args:
        content (str): Content to download.
        filename (str): Name of the download file.
        mime_type (str, optional): MIME type. Default is "text/plain".
        
    Returns:
        str: HTML link for downloading.
    """
    b64 = base64.b64encode(content.encode()).decode()
    return f'<a href="data:{mime_type};base64,{b64}" download="{filename}">Download {filename}</a>'