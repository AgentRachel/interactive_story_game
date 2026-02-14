class Room:
    def __init__(self, name):
        self.name = name
        self.connections = []
        self.occupants = []
        self.noise_level = 0
        self.description = f"A {name.lower()}"
        self.items = []

class MapGenerator:
    def generate_default_map(self):
        """Generate default house map"""
        rooms = {
            "Library": Room("Library"),
            "Kitchen": Room("Kitchen"),
            "Hallway": Room("Hallway"),
            "Basement": Room("Basement"),
            "Attic": Room("Attic")
        }
        
        # Set descriptions
        rooms["Library"].description = "A dusty library with old books and a fireplace"
        rooms["Kitchen"].description = "A modern kitchen with various appliances"
        rooms["Hallway"].description = "A central hallway connecting all rooms"
        rooms["Basement"].description = "A dark, damp basement with storage boxes"
        rooms["Attic"].description = "A cramped attic filled with old furniture"
        
        # Create connections (undirected graph)
        rooms["Library"].connections = [rooms["Hallway"]]
        rooms["Hallway"].connections = [rooms["Library"], rooms["Kitchen"], rooms["Basement"], rooms["Attic"]]
        rooms["Kitchen"].connections = [rooms["Hallway"]]
        rooms["Basement"].connections = [rooms["Hallway"]]
        rooms["Attic"].connections = [rooms["Hallway"]]
        
        # Create map object
        map_obj = type("MapObj", (), {})()
        map_obj.rooms = rooms
        return map_obj
    
    def generate_ai_map(self, size="medium"):
        """Generate AI-created map"""
        # For now, return default map
        # Can be enhanced to create procedural maps
        return self.generate_default_map()
