class Train:
    """
    Represents a train in the scheduling system.
    
    Attributes:
        name (str): The name/identifier of the train.
        color (str): The color to represent this train in visualizations.
        schedule (list): List of stops (each with station, arrival, departure).
    """
    
    def __init__(self, name, color="#1f77b4", schedule=None):
        """
        Initialize a new Train object.
        
        Args:
            name (str): The name/identifier of the train.
            color (str, optional): Color for visualization (hex or name). Default is Plotly blue.
            schedule (list, optional): List of schedule items. Default is empty list.
        """
        self.name = name
        self.color = color
        self.schedule = schedule if schedule is not None else []
    
    def add_stop(self, station, arrival=None, departure=None):
        """
        Add a stop to the train's schedule.
        
        Args:
            station (str): Station name.
            arrival (str or int, optional): Arrival time (HH:MM or minutes).
            departure (str or int, optional): Departure time (HH:MM or minutes).
        """
        self.schedule.append({
            'station': station,
            'arrival': arrival,
            'departure': departure
        })
    
    def update_stop(self, index, station=None, arrival=None, departure=None):
        """
        Update an existing stop in the train's schedule.
        
        Args:
            index (int): Index of the stop to update.
            station (str, optional): New station name.
            arrival (str or int, optional): New arrival time.
            departure (str or int, optional): New departure time.
        
        Returns:
            bool: True if updated successfully, False otherwise.
        """
        if 0 <= index < len(self.schedule):
            if station:
                self.schedule[index]['station'] = station
            if arrival is not None:
                self.schedule[index]['arrival'] = arrival
            if departure is not None:
                self.schedule[index]['departure'] = departure
            return True
        return False
    
    def remove_stop(self, index):
        """
        Remove a stop from the train's schedule.
        
        Args:
            index (int): Index of the stop to remove.
        
        Returns:
            bool: True if removed successfully, False otherwise.
        """
        if 0 <= index < len(self.schedule):
            self.schedule.pop(index)
            return True
        return False
    
    def get_statistics(self):
        """
        Calculate statistics about this train's schedule.
        
        Returns:
            dict: Dictionary with statistics.
        """
        if not self.schedule:
            return {
                'stops': 0,
                'total_time': 0,
                'total_distance': 0,
                'avg_speed': 0
            }
        
        # This is a simplified version - in a real system we would use
        # actual distances and more complex calculations
        first_stop = self.schedule[0]
        last_stop = self.schedule[-1]
        
        # For simplicity, assuming arrival at first stop and departure from last stop
        first_time = first_stop.get('arrival', first_stop.get('departure', 0))
        last_time = last_stop.get('departure', last_stop.get('arrival', 0))
        
        return {
            'stops': len(self.schedule),
            'total_time': last_time - first_time if isinstance(last_time, (int, float)) and isinstance(first_time, (int, float)) else 0,
            'total_distance': len(self.schedule) - 1,  # simplified
            'avg_speed': (len(self.schedule) - 1) / ((last_time - first_time) if last_time != first_time else 1) if isinstance(last_time, (int, float)) and isinstance(first_time, (int, float)) else 0
        }
    
    def validate(self):
        """
        Validate the train data.
        
        Returns:
            tuple: (is_valid, error_message)
        """
        if not self.name:
            return False, "Train must have a name"
        
        if not self.schedule:
            return False, "Train must have at least one stop"
        
        # More validation could be added here
        
        return True, ""
    
    def to_dict(self):
        """
        Convert train to dictionary for serialization.
        
        Returns:
            dict: Train data as dictionary.
        """
        return {
            'name': self.name,
            'color': self.color,
            'schedule': self.schedule
        }
    
    @classmethod
    def from_dict(cls, data):
        """
        Create a Train instance from dictionary data.
        
        Args:
            data (dict): Dictionary containing train data.
            
        Returns:
            Train: A new Train instance.
        """
        return cls(
            name=data.get('name', ''),
            color=data.get('color', '#1f77b4'),
            schedule=data.get('schedule', [])
        )
    
    def __str__(self):
        """Return string representation of the train."""
        return f"{self.name} ({len(self.schedule)} stops)"
    
    def __repr__(self):
        """Return detailed string representation of the train."""
        return f"Train(name='{self.name}', stops={len(self.schedule)})"