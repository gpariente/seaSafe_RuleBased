import math
import numpy as np

class Ship:
    def __init__(self, name, x, y, heading, speed, dest_x, dest_y, length_m=100, width_m=20):
        """
        Initializes a new Ship object with the given parameters.

        Args:
            name (str): Ship name or identifier.
            x, y (float): Initial position in Nautical Miles (NM).
            heading (float): Initial heading in degrees (0 = East, 90 = North).
            speed (float): Speed in knots (NM/h).
            dest_x, dest_y (float): Destination coordinates in NM.
            length_m (float): Physical length of the ship in meters (default is 100).
            width_m (float): Physical width of the ship in meters (default is 20).

        Note:
            The ship's heading is initialized by computing the heading towards its destination.
            The attribute `heading_adjusted` tracks how many degrees the ship has turned starboard
            during the current time step.
        """
        self.name = name
        self.x = x
        self.y = y
        self.speed = speed
        self.dest_x = dest_x
        self.dest_y = dest_y
        self.length_m = length_m
        self.width_m = width_m
        self.arrival_time = None
        
        # Initialize heading toward the destination.
        self.heading = self.compute_heading_to_destination()
        
        # Degrees turned starboard in the current time step.
        self.heading_adjusted = 0.0

    def reset_heading_adjusted(self):
        """
        Resets the heading adjustment counter for the current time step.
        This should be called at the beginning of each simulation step.
        """
        self.heading_adjusted = 0.0

    def update_position(self, dt_hours):
        """
        Moves the ship forward based on its current heading and speed.

        Parameters:
            dt_hours (float): The time step in hours.
        
        Calculation:
            distance_nm = speed (in NM/h) * dt_hours.
            The new position is updated using the cosine and sine of the current heading (converted to radians).
        """
        distance_nm = self.speed * dt_hours
        rad = math.radians(self.heading)
        self.x += distance_nm * math.cos(rad)
        self.y += distance_nm * math.sin(rad)

    def distance_to_destination(self):
        """
        Computes the Euclidean distance from the ship's current position to its destination.

        Returns:
            float: The distance in Nautical Miles (NM).
        """
        dx = self.dest_x - self.x
        dy = self.dest_y - self.y
        return math.sqrt(dx*dx + dy*dy)

    def compute_heading_to_destination(self):
        """
        Calculates the heading (in degrees) from the ship's current position to its destination.
        
        Returns:
            float: The heading in degrees.
            
        Note:
            If the ship is already at its destination (or nearly so), the current heading is returned.
        """
        dx = self.dest_x - self.x
        dy = self.dest_y - self.y
        if abs(dx) < 1e-9 and abs(dy) < 1e-9:
            return self.heading  # Already at destination; retain current heading.
        angle_deg = math.degrees(math.atan2(dy, dx))
        return angle_deg

    def get_position_vector(self):
        """
        Returns the current position of the ship as a NumPy array.

        Returns:
            numpy.ndarray: Array containing [x, y] coordinates.
        """
        return np.array([self.x, self.y])

    def get_velocity_vector(self):
        """
        Computes the velocity vector of the ship based on its speed and current heading.
        
        Note:
            Speed is given in knots (NM/h), so the resulting velocity vector is in NM/h.
        
        Returns:
            numpy.ndarray: Array containing the velocity components [vx, vy].
        """
        vx = self.speed * math.cos(math.radians(self.heading))
        vy = self.speed * math.sin(math.radians(self.heading))
        return np.array([vx, vy])
