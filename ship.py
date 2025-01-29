import math
import numpy as np

class Ship:
    def __init__(self, name, x, y, heading, speed, dest_x, dest_y, length_m=100, width_m=20):
        """
        Args:
            name (str): Ship name/identifier
            x, y (float): Initial position in NM
            heading (float): Initial heading in degrees (0=East, 90=North)
            speed (float): Speed in knots (NM/h)
            dest_x, dest_y (float): Destination coords in NM
            length_m, width_m (float): Physical size in meters
        """
        self.name = name
        self.x = x
        self.y = y
        self.speed = speed
        self.dest_x = dest_x
        self.dest_y = dest_y
        self.length_m = length_m
        self.width_m = width_m
        self.heading = self.compute_heading_to_destination()

        # How many degrees we have turned starboard in the current time-step
        self.heading_adjusted = 0.0

    def reset_heading_adjusted(self):
        self.heading_adjusted = 0.0

    def update_position(self, dt_hours):
        """
        Move the ship forward according to its current heading and speed.
        dt_hours is time in hours.
        """
        distance_nm = self.speed * dt_hours
        rad = math.radians(self.heading)
        self.x += distance_nm * math.cos(rad)
        self.y += distance_nm * math.sin(rad)

    def distance_to_destination(self):
        dx = self.dest_x - self.x
        dy = self.dest_y - self.y
        return math.sqrt(dx*dx + dy*dy)

    def compute_heading_to_destination(self):
        dx = self.dest_x - self.x
        dy = self.dest_y - self.y
        if abs(dx) < 1e-9 and abs(dy) < 1e-9:
            return self.heading  # Already at destination
        angle_deg = math.degrees(math.atan2(dy, dx))
        return angle_deg

    def get_position_vector(self):
        return np.array([self.x, self.y])

    def get_velocity_vector(self):
        """
        Velocity in (x, y). Speed is in knots (NM/h),
        so 1 knot = 1 NM/h.
        """
        vx = self.speed * math.cos(math.radians(self.heading))
        vy = self.speed * math.sin(math.radians(self.heading))
        return np.array([vx, vy])