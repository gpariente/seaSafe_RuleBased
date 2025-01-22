import math
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# =====================================================
# 1. Ship Class
# =====================================================
class Ship:
    def __init__(self, name, x, y, heading, speed, dest_x, dest_y):
        self.name = name
        self.x = x
        self.y = y
        self.heading = heading  # degrees
        self.speed = speed      # knots
        self.dest_x = dest_x
        self.dest_y = dest_y
        
        # Optionally store physical dimensions (not used directly yet)
        self.length_m = 100.0
        self.width_m = 20.0

    def update_position(self, dt_hours):
        distance = self.speed * dt_hours  # NM traveled
        heading_rad = math.radians(self.heading)
        self.x += distance * math.cos(heading_rad)
        self.y += distance * math.sin(heading_rad)

    def compute_heading_to_destination(self):
        dx = self.dest_x - self.x
        dy = self.dest_y - self.y
        angle_deg = math.degrees(math.atan2(dy, dx))
        return angle_deg

    def distance_to_destination(self):
        dx = self.dest_x - self.x
        dy = self.dest_y - self.y
        return math.sqrt(dx*dx + dy*dy)

    def get_position_vector(self):
        return np.array([self.x, self.y])

    def get_velocity_vector(self):
        """Velocity in NM/hour (knots are NM/hr)."""
        vx = self.speed * math.cos(math.radians(self.heading))
        vy = self.speed * math.sin(math.radians(self.heading))
        return np.array([vx, vy])


# =====================================================
# 2. Collision / CPA Utilities
# =====================================================
def compute_cpa_distance(shipA, shipB):
    """Returns the distance at the closest point of approach."""
    pA = shipA.get_position_vector()
    pB = shipB.get_position_vector()
    r0 = pB - pA  # relative position
    vA = shipA.get_velocity_vector()
    vB = shipB.get_velocity_vector()
    v = vB - vA   # relative velocity

    if np.allclose(v, 0):
        # Same velocity => distance is constant
        return np.linalg.norm(r0)

    t_cpa = -np.dot(r0, v) / np.dot(v, v)
    if t_cpa < 0:
        t_cpa = 0.0
    r_cpa = r0 + v * t_cpa
    dist_cpa = np.linalg.norm(r_cpa)
    return dist_cpa


def compute_cpa_with_assumed_heading(give_ship, other_ship, heading):
    """
    Computes the CPA if 'give_ship' uses 'heading' (degrees) 
    and 'other_ship' keeps its current heading.
    Speed is unchanged.
    """
    # Temporarily store old heading
    old_heading = give_ship.heading
    
    try:
        # Set new heading
        give_ship.heading = heading
        dist_cpa = compute_cpa_distance(give_ship, other_ship)
    finally:
        # Revert heading to old
        give_ship.heading = old_heading
    
    return dist_cpa


def relative_bearing_degs(from_ship, to_ship):
    """
    Returns relative bearing from 'from_ship' to 'to_ship' in (-180, 180).
    0 deg = dead ahead, > 0 = to port side, < 0 = to starboard side.
    """
    dx = to_ship.x - from_ship.x
    dy = to_ship.y - from_ship.y
    angle_abs = math.degrees(math.atan2(dy, dx))
    rel = angle_abs - from_ship.heading
    # Normalize to (-180, 180)
    while rel > 180:
        rel -= 360
    while rel <= -180:
        rel += 360
    return rel


# =====================================================
# 3. COLREG Classification
# =====================================================
def classify_encounter(shipA, shipB):
    """Returns 'head-on', 'crossing', 'overtaking', or 'unknown'."""
    bearingAB = relative_bearing_degs(shipA, shipB)
    bearingBA = relative_bearing_degs(shipB, shipA)

    # HEAD-ON if both bearings are near 0 deg
    if abs(bearingAB) < 10 and abs(bearingBA) < 10:
        return 'head-on'

    # OVERTAKING if one sees the other near ±180 deg (110 < abs(bearing) < 250).
    if 110 < abs(bearingAB) < 250:
        return 'overtaking'
    if 110 < abs(bearingBA) < 250:
        return 'overtaking'

    # Otherwise CROSSING
    return 'crossing'


def is_on_starboard_side(shipA, shipB):
    """True if B is on the starboard side of A."""
    bearingAB = relative_bearing_degs(shipA, shipB)
    # Starboard side => negative bearing in (-112.5, 0)
    if -112.5 < bearingAB < 0:
        return True
    return False


# =====================================================
# 4. Simulator with "Realistic" Heading Changes + Danger Prioritization
# =====================================================
class Simulator:
    def __init__(self, ships, time_step=30.0):
        self.ships = ships
        self.time_step = time_step  # seconds
        self.current_time = 0.0

        # Distances in NM
        self.destination_threshold = 0.05
        self.safe_distance = 0.3     # Desired min CPA
        self.heading_search_range = 40  # max starboard turn in degrees we search
        self.heading_search_step = 1.0  # 1-degree increments

    def step(self):
        dt_hours = self.time_step / 3600.0

        # 1) Assign each ship's heading to point to destination
        for ship in self.ships:
            if ship.distance_to_destination() > self.destination_threshold:
                ship.heading = ship.compute_heading_to_destination()

        # 2) Detect collisions + sort by ascending CPA => "prioritize danger"
        collision_pairs = self.detect_collision_risk()
        # Each item is (dist_cpa, i, j); sort by dist_cpa
        collision_pairs.sort(key=lambda x: x[0])

        # 3) For each pair in ascending CPA order, apply COLREG
        for (dist_cpa, i, j) in collision_pairs:
            shipA = self.ships[i]
            shipB = self.ships[j]
            encounter_type = classify_encounter(shipA, shipB)

            if encounter_type == 'head-on':
                # Both are give-way. Let's do starboard turns.
                self.apply_starboard_cpa_maneuver(shipA, shipB)

            elif encounter_type == 'crossing':
                # Determine which is give-way: the one who sees the other on starboard side
                # If B is on starboard of A => A yields
                if is_on_starboard_side(shipA, shipB):
                    # A yields
                    self.apply_single_ship_cpa_maneuver(shipA, shipB)
                elif is_on_starboard_side(shipB, shipA):
                    # B yields
                    self.apply_single_ship_cpa_maneuver(shipB, shipA)
                else:
                    # If uncertain, pick one to yield (A):
                    self.apply_single_ship_cpa_maneuver(shipA, shipB)

            elif encounter_type == 'overtaking':
                # The one behind is give-way
                bearingAB = relative_bearing_degs(shipA, shipB)
                # If B is behind A => B yields
                if 110 < abs(bearingAB) < 250:
                    self.apply_single_ship_cpa_maneuver(shipB, shipA)
                else:
                    self.apply_single_ship_cpa_maneuver(shipA, shipB)
            
            # else 'unknown': do nothing

        # 4) Update positions
        for ship in self.ships:
            if ship.distance_to_destination() > self.destination_threshold:
                ship.update_position(dt_hours)

        self.current_time += self.time_step

    def detect_collision_risk(self):
        """
        Returns a list of tuples (dist_cpa, i, j)
        for all pairs that have cpa < safe_distance.
        """
        n = len(self.ships)
        risk_pairs = []
        for i in range(n):
            for j in range(i+1, n):
                dist_cpa = compute_cpa_distance(self.ships[i], self.ships[j])
                if dist_cpa < self.safe_distance:
                    risk_pairs.append((dist_cpa, i, j))
        return risk_pairs

    def apply_starboard_cpa_maneuver(self, shipA, shipB):
        """
        In a head-on scenario, both are give-way. 
        We'll do a starboard maneuver on both.
        For each, do a 'CPA-based search' for starboard headings 
        that achieve min CPA with the other ship.
        """
        self.apply_single_ship_cpa_maneuver(shipA, shipB)
        self.apply_single_ship_cpa_maneuver(shipB, shipA)

    def apply_single_ship_cpa_maneuver(self, give_ship, other_ship):
        """
        For the 'give_ship', we search headings from 'current heading' 
        *starboard* up to heading_search_range degrees, 
        picking the minimal turn that yields a CPA >= safe_distance with 'other_ship'.
        """
        current_heading = give_ship.heading
        # Start from 0° of starboard turn, up to heading_search_range
        best_heading = current_heading
        best_cpa = compute_cpa_with_assumed_heading(give_ship, other_ship, current_heading)

        if best_cpa >= self.safe_distance:
            # Already safe; no turn needed
            return

        # We'll search starboard headings from (current_heading to current_heading - heading_search_range)
        # in increments of heading_search_step
        heading_found = False
        for angle_offset in np.arange(self.heading_search_step, self.heading_search_range + 0.1, self.heading_search_step):
            test_heading = current_heading - angle_offset
            cpa_test = compute_cpa_with_assumed_heading(give_ship, other_ship, test_heading)
            if cpa_test > best_cpa:
                best_cpa = cpa_test
                best_heading = test_heading

            if cpa_test >= self.safe_distance:
                heading_found = True
                break
        
        # Set the final heading
        give_ship.heading = best_heading

    def all_ships_arrived(self):
        return all(ship.distance_to_destination() < self.destination_threshold
                   for ship in self.ships)


# =====================================================
# 5. Demo
# =====================================================
def run_simulation():
    # Example: 2 ships meeting head-on
    # If no changes, they will pass dangerously close.
    # shipA = Ship("Ship A", 2.5, 0.0, 45.0, 30.0, 2.5, 5.0)
    # shipB = Ship("Ship B", 2.5, 0.5, 225.0, 20.0, 2.5, 5.0)
    shipA = Ship("Ship A", 0.0, 0.0, 45.0, 20.0, 5.0, 5.0)
    shipB = Ship("Ship B", 5.0, 5.0, 225.0, 20.0, 0.0, 0.0)
    ships = [shipA, shipB]

    sim = Simulator(ships, time_step=30.0)

    fig, ax = plt.subplots()
    ax.set_aspect('equal')
    ax.set_xlim(-1, 6)
    ax.set_ylim(-1, 6)

    scatters = []
    for ship in ships:
        scatter, = ax.plot([], [], 'o', label=ship.name)
        scatters.append(scatter)

    # plot destinations
    for ship in ships:
        ax.plot(ship.dest_x, ship.dest_y, 'r*')

    # ax.legend()

    def init():
        for scatter in scatters:
            scatter.set_data([], [])
        return scatters

    def update(frame):
        sim.step()

        # Update scatter positions
        for i, ship in enumerate(sim.ships):
            scatters[i].set_data([ship.x], [ship.y])

        # Stop if all arrived
        if sim.all_ships_arrived():
            anim.event_source.stop()

        return scatters

    anim = FuncAnimation(fig, update, init_func=init,
                         frames=200, interval=500, blit=True)
    plt.title("seaSafe")
    plt.show()


if __name__ == "__main__":
    run_simulation()
