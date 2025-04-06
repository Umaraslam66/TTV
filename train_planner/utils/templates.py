from utils.time_utils import parse_time, minutes_to_hhmm

def create_express_template(stations, start_time, speed=2):
    """
    Create an express train schedule template that stops at first, middle, and last stations.
    
    Args:
        stations (list): List of station names.
        start_time (str or int): Departure time from first station (HH:MM or minutes).
        speed (int, optional): Minutes between stations. Default is 2.
    
    Returns:
        list: Schedule template with stops.
    """
    if not stations:
        return []
    
    template = []
    # Ensure start_time is parsed to an integer
    start_minutes = parse_time(start_time)
    
    if start_minutes is None:
        start_minutes = 8 * 60  # Default to 8:00 AM
    
    # Convert to integer to be safe
    speed = int(speed) if not isinstance(speed, int) else speed
    
    # First station
    template.append({
        'station': stations[0],
        'arrival': start_minutes,  # Set arrival time equal to departure for first station
        'departure': start_minutes
    })
    
    # Middle station (if there are at least 3 stations)
    if len(stations) >= 3:
        middle_idx = len(stations) // 2
        middle_time = start_minutes + middle_idx * speed
        
        template.append({
            'station': stations[middle_idx],
            'arrival': middle_time,
            'departure': middle_time + 1  # 1 minute dwell time
        })
    
    # Last station
    last_idx = len(stations) - 1
    last_time = start_minutes + last_idx * speed
    
    template.append({
        'station': stations[last_idx],
        'arrival': last_time,
        'departure': None  # Terminal station may not have a departure
    })
    
    return template

def create_local_template(stations, start_time, speed=3, dwell_time=1):
    """
    Create a local train schedule template that stops at all stations.
    
    Args:
        stations (list): List of station names.
        start_time (str or int): Departure time from first station (HH:MM or minutes).
        speed (int, optional): Minutes between stations. Default is 3.
        dwell_time (int, optional): Minutes spent at each station. Default is 1.
    
    Returns:
        list: Schedule template with stops.
    """
    if not stations:
        return []
    
    template = []
    start_minutes = parse_time(start_time)
    
    if start_minutes is None:
        start_minutes = 8 * 60  # Default to 8:00 AM
    
    # Convert to integers to be safe
    speed = int(speed) if not isinstance(speed, int) else speed
    dwell_time = int(dwell_time) if not isinstance(dwell_time, int) else dwell_time
    
    current_time = start_minutes
    
    # First station
    template.append({
        'station': stations[0],
        'arrival': current_time,  # Set arrival equal to departure for first station
        'departure': current_time
    })
    
    # Rest of the stations
    for i in range(1, len(stations)):
        current_time += speed  # Travel time to next station
        
        arrival_time = current_time
        departure_time = None if i == len(stations) - 1 else current_time + dwell_time
        
        template.append({
            'station': stations[i],
            'arrival': arrival_time,
            'departure': departure_time
        })
        
        if departure_time is not None:
            current_time = departure_time
    
    return template

def create_uptown_template(stations, start_time, speed=3, dwell_time=1):
    """
    Create an uptown train schedule template (ascending station order).
    
    Args:
        stations (list): List of station names.
        start_time (str or int): Departure time from first station (HH:MM or minutes).
        speed (int, optional): Minutes between stations. Default is 3.
        dwell_time (int, optional): Minutes spent at each station. Default is 1.
    
    Returns:
        list: Schedule template with stops.
    """
    # Uptown is essentially the same as local for this implementation
    return create_local_template(stations, start_time, speed, dwell_time)

def create_downtown_template(stations, start_time, speed=3, dwell_time=1):
    """
    Create a downtown train schedule template (descending station order).
    
    Args:
        stations (list): List of station names.
        start_time (str or int): Departure time from first station (HH:MM or minutes).
        speed (int, optional): Minutes between stations. Default is 3.
        dwell_time (int, optional): Minutes spent at each station. Default is 1.
    
    Returns:
        list: Schedule template with stops.
    """
    # Reverse the station order
    reversed_stations = list(reversed(stations))
    return create_local_template(reversed_stations, start_time, speed, dwell_time)

def create_custom_template(stations, stops, start_time, speed=3, dwell_time=1):
    """
    Create a custom train schedule template that stops at specified stations.
    
    Args:
        stations (list): List of all station names.
        stops (list): List of station names to stop at.
        start_time (str or int): Departure time from first station (HH:MM or minutes).
        speed (int, optional): Minutes between stations. Default is 3.
        dwell_time (int, optional): Minutes spent at each station. Default is 1.
    
    Returns:
        list: Schedule template with stops.
    """
    if not stations or not stops:
        return []
    
    # Validate stops - all must be in stations list
    valid_stops = [stop for stop in stops if stop in stations]
    
    if not valid_stops:
        return []
    
    # Sort stops by their position in the stations list
    station_indices = {station: idx for idx, station in enumerate(stations)}
    sorted_stops = sorted(valid_stops, key=lambda s: station_indices[s])
    
    # Now create a schedule using these sorted stops
    template = []
    start_minutes = parse_time(start_time)
    
    if start_minutes is None:
        start_minutes = 8 * 60  # Default to 8:00 AM
    
    current_time = start_minutes
    
    # First stop (no arrival)
    template.append({
        'station': sorted_stops[0],
        'arrival': current_time,
        'departure': current_time
    })
    
    # Calculate travel time based on station indices
    for i in range(1, len(sorted_stops)):
        prev_idx = station_indices[sorted_stops[i-1]]
        curr_idx = station_indices[sorted_stops[i]]
        stations_passed = curr_idx - prev_idx
        
        # Time to next stop depends on number of stations passed
        travel_time = stations_passed * speed
        current_time += travel_time
        
        arrival_time = current_time
        departure_time = current_time + dwell_time if i < len(sorted_stops) - 1 else None
        
        template.append({
            'station': sorted_stops[i],
            'arrival': arrival_time,
            'departure': departure_time
        })
        
        if departure_time is not None:
            current_time = departure_time
    
    return template

def get_sample_templates(stations):
    """
    Get a set of sample templates for the given stations.
    
    Args:
        stations (list): List of station names.
    
    Returns:
        dict: Dictionary of sample templates.
    """
    if not stations:
        return {}
    
    return {
        "Morning Express": create_express_template(stations, "07:30", 2),
        "Afternoon Express": create_express_template(stations, "16:30", 2),
        "Morning Local": create_local_template(stations, "08:00", 3, 1),
        "Afternoon Local": create_local_template(stations, "17:00", 3, 1),
        "Morning Uptown": create_uptown_template(stations, "08:30", 3, 1),
        "Afternoon Downtown": create_downtown_template(stations, "17:30", 3, 1)
    }

def create_hourly_pattern(base_schedule, hours_range=(6, 22)):
    """
    Create an hourly service pattern based on a base schedule.
    
    Args:
        base_schedule (list): Base schedule with one service.
        hours_range (tuple): Range of hours to create services for (start, end).
        
    Returns:
        list: List of train schedules.
    """
    if not base_schedule:
        return []
    
    # Get first departure time in minutes since midnight
    first_stop = base_schedule[0]
    if 'departure' not in first_stop or first_stop['departure'] is None:
        return []
    
    base_departure = first_stop['departure']
    base_hour = base_departure // 60
    base_minute = base_departure % 60
    
    # Calculate time shift for each hour
    trains = []
    for hour in range(hours_range[0], hours_range[1] + 1):
        # Skip the base hour as we already have that schedule
        if hour == base_hour:
            continue
        
        # Create a copy of the base schedule with adjusted times
        hour_diff = hour - base_hour
        hour_shift = hour_diff * 60  # in minutes
        
        new_schedule = []
        for stop in base_schedule:
            new_stop = stop.copy()
            
            if new_stop.get('arrival') is not None:
                new_stop['arrival'] = new_stop['arrival'] + hour_shift
            
            if new_stop.get('departure') is not None:
                new_stop['departure'] = new_stop['departure'] + hour_shift
                
            new_schedule.append(new_stop)
        
        # Create train for this hour
        train_name = f"{hour:02d}:{base_minute:02d} Service"
        trains.append({
            'schedule': new_schedule,
            'name': train_name,
            'color': '#1f77b4'  # Blue
        })
    
    return trains

def create_express_local_pattern(stations, base_departure, interval=10):
    """
    Create express and local service pattern.
    
    Args:
        stations (list): List of station names.
        base_departure (int): Base departure time in minutes.
        interval (int): Interval between services in minutes.
        
    Returns:
        list: List of train schedules (express and local).
    """
    if not stations or len(stations) < 3:
        return []
    
    # Create express train (first, major stations, last)
    express_schedule = []
    express_stations = [stations[0]]  # First station
    
    # Add major stations (every third station)
    for i in range(1, len(stations) - 1):
        if i % 3 == 0:  # Adjust this logic for different express patterns
            express_stations.append(stations[i])
    
    express_stations.append(stations[-1])  # Last station
    
    # Build express schedule
    travel_time_per_station = 3  # minutes between stations for express
    current_time = base_departure
    
    # First station
    express_schedule.append({
        'station': express_stations[0],
        'arrival': current_time,
        'departure': current_time
    })
    
    # Remaining stations
    for i in range(1, len(express_stations)):
        # Find positions in the full station list
        current_idx = stations.index(express_stations[i-1])
        next_idx = stations.index(express_stations[i])
        stations_passed = next_idx - current_idx
        
        # Travel time depends on stations passed
        travel_time = stations_passed * travel_time_per_station
        current_time += travel_time
        
        arrival_time = current_time
        departure_time = current_time + 1 if i < len(express_stations) - 1 else None
        
        express_schedule.append({
            'station': express_stations[i],
            'arrival': arrival_time,
            'departure': departure_time
        })
        
        if departure_time is not None:
            current_time = departure_time
    
    # Create local train (all stations)
    local_schedule = []
    
    # Local train leaves after the express
    local_departure = base_departure + interval
    current_time = local_departure
    
    # First station
    local_schedule.append({
        'station': stations[0],
        'arrival': current_time,
        'departure': current_time
    })
    
    # Remaining stations
    for i in range(1, len(stations)):
        current_time += 2  # 2 minutes per station for local
        
        arrival_time = current_time
        departure_time = current_time + 1 if i < len(stations) - 1 else None
        
        local_schedule.append({
            'station': stations[i],
            'arrival': arrival_time,
            'departure': departure_time
        })
        
        if departure_time is not None:
            current_time = departure_time
    
    # Create the trains
    express_train = {
        'name': f"Express {minutes_to_hhmm(base_departure)}",
        'color': '#1f77b4',  # Blue
        'schedule': express_schedule
    }
    
    local_train = {
        'name': f"Local {minutes_to_hhmm(local_departure)}",
        'color': '#ff7f0e',  # Orange
        'schedule': local_schedule
    }
    
    return [express_train, local_train]

def create_shuttle_pattern(stations, base_departure, frequency=20, duration=(6, 22)):
    """
    Create a shuttle service pattern with frequent service.
    
    Args:
        stations (list): List of station names.
        base_departure (int): Base departure time in minutes.
        frequency (int): Frequency in minutes between services.
        duration (tuple): Hours range to operate (start, end).
        
    Returns:
        list: List of train schedules.
    """
    if not stations or len(stations) < 2:
        return []
    
    shuttle_trains = []
    
    # Convert duration hours to minutes
    start_time = duration[0] * 60
    end_time = duration[1] * 60
    
    # Adjust base departure to be within range
    current_departure = max(start_time, base_departure)
    
    # Generate trains until end time
    while current_departure < end_time:
        # Create a basic schedule for this departure
        schedule = []
        current_time = current_departure
        
        # First station
        schedule.append({
            'station': stations[0],
            'arrival': current_time,
            'departure': current_time
        })
        
        # Remaining stations
        for i in range(1, len(stations)):
            current_time += 3  # 3 minutes between stations
            
            arrival_time = current_time
            departure_time = current_time + 1 if i < len(stations) - 1 else None
            
            schedule.append({
                'station': stations[i],
                'arrival': arrival_time,
                'departure': departure_time
            })
            
            if departure_time is not None:
                current_time = departure_time
        
        # Create return journey (reverse direction)
        return_departure = current_time + 5  # 5 minute layover
        return_schedule = []
        current_time = return_departure
        
        # First station (was last station)
        return_schedule.append({
            'station': stations[-1],
            'arrival': current_time,
            'departure': current_time
        })
        
        # Remaining stations (reverse order)
        for i in range(len(stations) - 2, -1, -1):
            current_time += 3  # 3 minutes between stations
            
            arrival_time = current_time
            departure_time = current_time + 1 if i > 0 else None
            
            return_schedule.append({
                'station': stations[i],
                'arrival': arrival_time,
                'departure': departure_time
            })
            
            if departure_time is not None:
                current_time = departure_time
        
        # Create trains for this departure
        outbound_train = {
            'name': f"Outbound {minutes_to_hhmm(current_departure)}",
            'color': '#1f77b4',  # Blue
            'schedule': schedule
        }
        
        inbound_train = {
            'name': f"Inbound {minutes_to_hhmm(return_departure)}",
            'color': '#ff7f0e',  # Orange
            'schedule': return_schedule
        }
        
        shuttle_trains.extend([outbound_train, inbound_train])
        
        # Move to next departure
        current_departure += frequency
    
    return shuttle_trains

def create_peak_service_pattern(stations, am_peak=(7, 9), pm_peak=(16, 18), frequency=10):
    """
    Create peak-hour service pattern with increased frequency during peak times.
    
    Args:
        stations (list): List of station names.
        am_peak (tuple): AM peak hours range (start, end).
        pm_peak (tuple): PM peak hours range (start, end).
        frequency (int): Frequency in minutes between peak services.
        
    Returns:
        list: List of train schedules.
    """
    if not stations or len(stations) < 2:
        return []
    
    peak_trains = []
    
    # Create AM peak trains (typically inbound/toward city center)
    am_start = am_peak[0] * 60  # Convert hours to minutes
    am_end = am_peak[1] * 60
    
    # Generate AM peak trains
    current_departure = am_start
    while current_departure < am_end:
        # Create schedule for this departure
        schedule = []
        current_time = current_departure
        
        # First station
        schedule.append({
            'station': stations[0],
            'arrival': current_time,
            'departure': current_time
        })
        
        # Remaining stations
        for i in range(1, len(stations)):
            current_time += 2  # Faster service during peak
            
            arrival_time = current_time
            departure_time = current_time + 1 if i < len(stations) - 1 else None
            
            schedule.append({
                'station': stations[i],
                'arrival': arrival_time,
                'departure': departure_time
            })
            
            if departure_time is not None:
                current_time = departure_time
        
        # Create train for this departure
        train_name = f"AM Peak {minutes_to_hhmm(current_departure)}"
        peak_trains.append({
            'name': train_name,
            'color': '#2ca02c',  # Green
            'schedule': schedule
        })
        
        # Move to next departure
        current_departure += frequency
    
    # Create PM peak trains (typically outbound/away from city center)
    pm_start = pm_peak[0] * 60
    pm_end = pm_peak[1] * 60
    
    # Generate PM peak trains
    current_departure = pm_start
    while current_departure < pm_end:
        # Create schedule for this departure (reverse direction)
        schedule = []
        current_time = current_departure
        
        # First station (city center)
        schedule.append({
            'station': stations[-1],
            'arrival': current_time,
            'departure': current_time
        })
        
        # Remaining stations (reverse order)
        for i in range(len(stations) - 2, -1, -1):
            current_time += 2  # Faster service during peak
            
            arrival_time = current_time
            departure_time = current_time + 1 if i > 0 else None
            
            schedule.append({
                'station': stations[i],
                'arrival': arrival_time,
                'departure': departure_time
            })
            
            if departure_time is not None:
                current_time = departure_time
        
        # Create train for this departure
        train_name = f"PM Peak {minutes_to_hhmm(current_departure)}"
        peak_trains.append({
            'name': train_name,
            'color': '#d62728',  # Red
            'schedule': schedule
        })
        
        # Move to next departure
        current_departure += frequency
    
    return peak_trains