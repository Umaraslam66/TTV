class Station:
    """
    Represents a railway station in the scheduling system.
    
    Attributes:
        name (str): The name of the station.
        position (float): The relative position of the station (for visualization).
        constraints (dict): Optional station constraints (e.g., minimum dwell time).
    """
    
    def __init__(self, name, position=None, constraints=None):
        """
        Initialize a new Station object.
        
        Args:
            name (str): The name of the station.
            position (float, optional): The relative position of the station. If None, will be assigned later.
            constraints (dict, optional): Station constraints.
        """
        self.name = name
        self.position = position if position is not None else 0
        self.constraints = constraints if constraints is not None else {}
        
    def validate(self):
        """
        Validate station data.
        
        Returns:
            bool: True if station is valid, otherwise False.
        """
        # Basic validation - station must have a name
        return self.name and isinstance(self.name, str) and len(self.name.strip()) > 0
    
    def to_dict(self):
        """
        Convert station to dictionary for serialization.
        
        Returns:
            dict: Station data as dictionary.
        """
        return {
            'name': self.name,
            'position': self.position,
            'constraints': self.constraints
        }
    
    @classmethod
    def from_dict(cls, data):
        """
        Create a Station instance from dictionary data.
        
        Args:
            data (dict): Dictionary containing station data.
            
        Returns:
            Station: A new Station instance.
        """
        return cls(
            name=data.get('name', ''),
            position=data.get('position', 0),
            constraints=data.get('constraints', {})
        )
    
    def __str__(self):
        """Return string representation of the station."""
        return self.name
    
    def __repr__(self):
        """Return detailed string representation of the station."""
        return f"Station(name='{self.name}', position={self.position})"
    
    def __eq__(self, other):
        """Check equality with another station based on name."""
        if isinstance(other, Station):
            return self.name == other.name
        elif isinstance(other, str):
            return self.name == other
        return False