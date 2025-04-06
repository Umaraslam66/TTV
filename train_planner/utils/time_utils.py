import re
from datetime import datetime, timedelta

def parse_time(time_str):
    """
    Parse a time string in HH:MM format to minutes since midnight.
    
    Args:
        time_str (str or int or float): Time string in HH:MM format or minutes.
        
    Returns:
        int or None: Minutes since midnight, or None if invalid.
    """
    # Handle None case
    if time_str is None:
        return None
    
    # If already a number, just return it as an int
    if isinstance(time_str, (int, float)):
        return int(time_str)
    
    # Handle non-string inputs
    if not isinstance(time_str, str):
        return None
    
    # Strip whitespace and handle empty string
    time_str = time_str.strip()
    if not time_str:
        return None
    
    # Try to parse as HH:MM
    try:
        # Standard HH:MM format
        time_pattern = re.compile(r'^(\d{1,2}):(\d{2})$')
        match = time_pattern.match(time_str)
        
        if match:
            hours = int(match.group(1))
            minutes = int(match.group(2))
            
            if 0 <= hours < 24 and 0 <= minutes < 60:
                return hours * 60 + minutes
        
        # Alternative format - just hours (e.g., "9")
        if time_str.isdigit():
            hours = int(time_str)
            if 0 <= hours < 24:
                return hours * 60
            # Or just interpret as minutes directly
            if 0 <= hours < 24 * 60:
                return hours
        
        # Handle formats like "9:00am" or "9:00 am"
        am_pm_pattern = re.compile(r'^(\d{1,2}):(\d{2})\s*(am|pm)$', re.IGNORECASE)
        match = am_pm_pattern.match(time_str.replace(' ', ''))
        
        if match:
            hours = int(match.group(1))
            minutes = int(match.group(2))
            am_pm = match.group(3).lower()
            
            if 1 <= hours <= 12 and 0 <= minutes < 60:
                if am_pm == 'pm' and hours < 12:
                    hours += 12
                elif am_pm == 'am' and hours == 12:
                    hours = 0
                
                return hours * 60 + minutes
                
    except (ValueError, TypeError, AttributeError) as e:
        # Log the error if desired
        # print(f"Error parsing time: {e}")
        pass
    
    return None

def minutes_to_hhmm(minutes):
    """
    Convert minutes since midnight to HH:MM format.
    
    Args:
        minutes (int or str): Minutes since midnight or a time string.
        
    Returns:
        str: Time in HH:MM format, or empty string if invalid.
    """
    if minutes is None:
        return ""
    
    # If it's a string, try to parse it first
    if isinstance(minutes, str):
        minutes = parse_time(minutes)
        if minutes is None:
            return ""
    
    # Ensure we have an integer
    try:
        minutes = int(minutes)
        
        # Handle negative times by wrapping to previous day
        if minutes < 0:
            minutes = (24 * 60) + (minutes % (24 * 60))
        
        # Calculate hours and minutes
        hours = (minutes // 60) % 24
        mins = minutes % 60
        
        return f"{hours:02d}:{mins:02d}"
    except (TypeError, ValueError):
        return ""

def hhmm_to_timeobj(time_str):
    """
    Convert a time string in HH:MM format to a datetime object.
    
    Args:
        time_str (str or int): Time string in HH:MM format or minutes.
        
    Returns:
        datetime or None: Datetime object, or None if invalid.
    """
    # Convert to minutes first
    minutes = parse_time(time_str)
    
    if minutes is not None:
        try:
            hours = minutes // 60
            mins = minutes % 60
            
            # Use today's date as a base
            base_date = datetime.now().replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            
            return base_date + timedelta(hours=hours, minutes=mins)
        except (TypeError, ValueError, OverflowError):
            return None
    
    return None

def timeobj_to_minutes(time_obj):
    """
    Convert a datetime object to minutes since midnight.
    
    Args:
        time_obj (datetime): Datetime object.
        
    Returns:
        int or None: Minutes since midnight, or None if invalid.
    """
    if time_obj is None:
        return None
    
    try:
        return time_obj.hour * 60 + time_obj.minute
    except (AttributeError, TypeError):
        return None

def time_diff(time1, time2):
    """
    Calculate the difference between two times in minutes.
    
    Args:
        time1 (str or int): First time (HH:MM or minutes).
        time2 (str or int): Second time (HH:MM or minutes).
        
    Returns:
        int or None: Difference in minutes (time2 - time1), or None if invalid.
    """
    minutes1 = parse_time(time1)
    minutes2 = parse_time(time2)
    
    if minutes1 is not None and minutes2 is not None:
        return minutes2 - minutes1
    
    return None

def format_duration(minutes):
    """
    Format a duration in minutes to a human-readable string.
    
    Args:
        minutes (int or str): Duration in minutes or a time string.
        
    Returns:
        str: Formatted duration (e.g., "1h 30m").
    """
    if minutes is None:
        return ""
    
    # Try to parse if it's a string
    if isinstance(minutes, str):
        try:
            minutes = int(minutes)
        except ValueError:
            return ""
    
    # Handle non-numeric types
    if not isinstance(minutes, (int, float)):
        return ""
    
    # Handle negative durations
    if minutes < 0:
        return f"-{format_duration(-minutes)}"
    
    hours = int(minutes) // 60
    mins = int(minutes) % 60
    
    if hours > 0:
        return f"{hours}h {mins}m" if mins > 0 else f"{hours}h"
    else:
        return f"{mins}m"

def is_valid_time(time_str):
    """
    Check if a time string is valid.
    
    Args:
        time_str (str or int): Time string or minutes to check.
        
    Returns:
        bool: True if valid, False otherwise.
    """
    return parse_time(time_str) is not None

def get_time_range(trains):
    """
    Calculate the min and max times from a list of trains.
    
    Args:
        trains (list): List of Train objects or train dictionaries.
        
    Returns:
        tuple: (min_time, max_time) in minutes.
    """
    if not trains:
        # Default range if no trains
        return 6 * 60, 22 * 60  # 6:00 AM to 10:00 PM
    
    min_time = float('inf')
    max_time = 0
    found_valid_times = False
    
    for train in trains:
        # Handle both Train objects and dictionaries
        if hasattr(train, 'schedule'):
            schedule = train.schedule
        elif isinstance(train, dict) and 'schedule' in train:
            schedule = train['schedule']
        else:
            continue  # Skip if neither format is valid
        
        for stop in schedule:
            # Handle different access patterns
            if isinstance(stop, dict):
                arrival = stop.get('arrival')
                departure = stop.get('departure')
            else:
                # Try attribute access
                try:
                    arrival = getattr(stop, 'arrival', None)
                    departure = getattr(stop, 'departure', None)
                except Exception:
                    continue  # Skip if can't access attributes
            
            # Parse times if they're strings
            arrival_mins = parse_time(arrival)
            departure_mins = parse_time(departure)
            
            if arrival_mins is not None:
                min_time = min(min_time, arrival_mins)
                max_time = max(max_time, arrival_mins)
                found_valid_times = True
            
            if departure_mins is not None:
                min_time = min(min_time, departure_mins)
                max_time = max(max_time, departure_mins)
                found_valid_times = True
    
    # If no valid times found, use defaults
    if not found_valid_times or min_time == float('inf') or max_time == 0:
        min_time = 6 * 60  # 6:00 AM
        max_time = 22 * 60  # 10:00 PM
    
    # Add some padding
    min_time = max(0, min_time - 30)
    max_time = min(24 * 60, max_time + 30)
    
    return min_time, max_time

def create_time_range(start, end, step=60):
    """
    Create a range of times from start to end with a given step.
    
    Args:
        start (int): Start time in minutes.
        end (int): End time in minutes.
        step (int, optional): Step in minutes. Default is 60 (hourly).
        
    Returns:
        list: List of times in minutes.
    """
    if start is None or end is None:
        return []
    
    if isinstance(start, str):
        start = parse_time(start)
    if isinstance(end, str):
        end = parse_time(end)
    
    if start is None or end is None:
        return []
    
    try:
        return list(range(int(start), int(end) + 1, int(step)))
    except (TypeError, ValueError):
        return []