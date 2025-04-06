from .train import Train
from .station import Station

class Schedule:
    """
    Represents a complete railway schedule, containing trains and stations.
    
    Attributes:
        stations (list): List of Station objects.
        trains (list): List of Train objects.
        name (str): Name of the schedule.
    """
    
    def __init__(self, name="New Schedule", stations=None, trains=None):
        """
        Initialize a new Schedule object.
        
        Args:
            name (str, optional): Name of the schedule. Default is "New Schedule".
            stations (list, optional): List of Station objects. Default is empty list.
            trains (list, optional): List of Train objects. Default is empty list.
        """
        self.name = name
        self.stations = stations if stations is not None else []
        self.trains = trains if trains is not None else []
    
    def add_station(self, station):
        """
        Add a station to the schedule.
        
        Args:
            station (Station): Station object to add.
            
        Returns:
            bool: True if added successfully, False if already exists.
        """
        if not any(s.name == station.name for s in self.stations):
            self.stations.append(station)
            # Calculate positions if not set
            self._recalculate_station_positions()
            return True
        return False
    
    def add_stations(self, stations):
        """
        Add multiple stations to the schedule.
        
        Args:
            stations (list): List of Station objects.
            
        Returns:
            int: Number of stations successfully added.
        """
        added = 0
        for station in stations:
            if self.add_station(station):
                added += 1
        return added
    
    def remove_station(self, station_name):
        """
        Remove a station from the schedule.
        
        Args:
            station_name (str): Name of the station to remove.
            
        Returns:
            bool: True if removed, False if not found.
        """
        for i, station in enumerate(self.stations):
            if station.name == station_name:
                self.stations.pop(i)
                # Update station positions
                self._recalculate_station_positions()
                return True
        return False
    
    def _recalculate_station_positions(self):
        """Recalculate station positions to be evenly distributed."""
        if self.stations:
            for i, station in enumerate(self.stations):
                station.position = i / (len(self.stations) - 1 if len(self.stations) > 1 else 1)
    
    def add_train(self, train):
        """
        Add a train to the schedule.
        
        Args:
            train (Train): Train object to add.
            
        Returns:
            bool: True if added successfully, False if already exists.
        """
        if not any(t.name == train.name for t in self.trains):
            self.trains.append(train)
            return True
        return False
    
    def remove_train(self, train_name):
        """
        Remove a train from the schedule.
        
        Args:
            train_name (str): Name of the train to remove.
            
        Returns:
            bool: True if removed, False if not found.
        """
        for i, train in enumerate(self.trains):
            if train.name == train_name:
                self.trains.pop(i)
                return True
        return False
    
    def get_station_by_name(self, name):
        """
        Get a station by its name.
        
        Args:
            name (str): Station name to find.
            
        Returns:
            Station or None: The matching station or None if not found.
        """
        for station in self.stations:
            if station.name == name:
                return station
        return None
    
    def get_train_by_name(self, name):
        """
        Get a train by its name.
        
        Args:
            name (str): Train name to find.
            
        Returns:
            Train or None: The matching train or None if not found.
        """
        for train in self.trains:
            if train.name == name:
                return train
        return None
    
    def validate(self):
        """
        Validate the entire schedule.
        
        Returns:
            tuple: (is_valid, error_message)
        """
        # Check stations
        if not self.stations:
            return False, "Schedule must have at least one station"
        
        # Check trains
        if not self.trains:
            return False, "Schedule must have at least one train"
        
        # Check for duplicate station names
        station_names = [s.name for s in self.stations]
        if len(station_names) != len(set(station_names)):
            return False, "Duplicate station names found"
        
        # Check for duplicate train names
        train_names = [t.name for t in self.trains]
        if len(train_names) != len(set(train_names)):
            return False, "Duplicate train names found"
        
        # Check that train stops reference valid stations
        for train in self.trains:
            for stop in train.schedule:
                if stop['station'] not in station_names:
                    return False, f"Train {train.name} references unknown station: {stop['station']}"
        
        return True, ""
    
    def to_dict(self):
        """
        Convert schedule to dictionary for serialization.
        
        Returns:
            dict: Schedule data as dictionary.
        """
        return {
            'name': self.name,
            'stations': [s.to_dict() for s in self.stations],
            'trains': [t.to_dict() for t in self.trains]
        }
    
    @classmethod
    def from_dict(cls, data):
        """
        Create a Schedule instance from dictionary data.
        
        Args:
            data (dict): Dictionary containing schedule data.
            
        Returns:
            Schedule: A new Schedule instance.
        """
        stations = [Station.from_dict(s) for s in data.get('stations', [])]
        trains = [Train.from_dict(t) for t in data.get('trains', [])]
        
        return cls(
            name=data.get('name', 'Imported Schedule'),
            stations=stations,
            trains=trains
        )
    
    def __str__(self):
        """Return string representation of the schedule."""
        return f"Schedule: {self.name} ({len(self.stations)} stations, {len(self.trains)} trains)"