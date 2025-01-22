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
        self.heading = heading  # in degrees
        self.speed = speed      # in knots
        self.dest_x = dest_x
        self.dest_y = dest_y

        # Optionally store length/width if needed
        self.length_m = 100.0
        self.width_m = 20.0

    def update_position(self, dt_hours):
        distance = self.speed * dt_hours  # NM traveled = knots * hours
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
        vx = self.speed * math.cos(math.radians(self.heading))
        vy = self.speed * math.sin(math.radians(self.heading))
        return np.array([vx, vy])

# =====================================================
# 2. Collision Risk / CPA
# =====================================================
def compute_cpa_distance(shipA, shipB):
    pA = shipA.get_position_vector()
    pB = shipB.get_position_vector()
    r0 = pB - pA  # relative position (B w.r.t A)
    vA = shipA.get_velocity_vector()
    vB = shipB.get_velocity_vector()
    v = vB - vA   # relative velocity

    if np.allclose(v, 0):
        # same velocity => distance is constant
        return np.linalg.norm(r0)

    t_cpa = -np.dot(r0, v) / np.dot(v, v)
    if t_cpa < 0:
        t_cpa = 0.0
    r_cpa = r0 + v * t_cpa
    dist_cpa = np.linalg.norm(r_cpa)
    return dist_cpa

def relative_bearing_degs(from_ship, to_ship):
    """
    Returns the relative bearing from `from_ship` to `to_ship` in degrees.
    0 deg = dead ahead, +90 deg = on from_ship's port beam, -90 deg = starboard beam, etc.
    We'll normalize to (-180, 180).
    """
    # Vector from A->B
    dx = to_ship.x - from_ship.x
    dy = to_ship.y - from_ship.y
    # Absolute angle of that vector (relative to East)
    angle_abs = math.degrees(math.atan2(dy, dx))
    # Relative angle to from_ship's heading
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
    """
    Classify the encounter type: 'head-on', 'crossing', 'overtaking', or 'unknown'
    We'll do a simple approach using relative bearings in each direction.
    """
    # Relative bearings A->B, B->A
    bearingAB = relative_bearing_degs(shipA, shipB)
    bearingBA = relative_bearing_degs(shipB, shipA)

    # HEAD-ON: each sees the other roughly ahead
    # For simplicity, we'll call it head-on if bearingAB ~ 0 deg, bearingBA ~ 0 deg (±10 deg).
    if abs(bearingAB) < 10 and abs(bearingBA) < 10:
        return 'head-on'

    # OVERTAKING: B is behind A if bearingAB ~ 180 deg. 
    # We'll consider an overtaking if bearingAB is in ±70 deg of 180
    # i.e. if bearingAB in (110, 250) => B is behind A.
    # But we also check from B's perspective just to confirm.
    if 110 < abs(bearingAB) < 250:
        return 'overtaking'  # B behind A => from A's perspective
    if 110 < abs(bearingBA) < 250:
        return 'overtaking'  # A behind B => from B's perspective

    # Otherwise, assume CROSSING if bearings are not near 180 or 0.
    return 'crossing'

def is_on_starboard_side(shipA, shipB):
    """
    Returns True if shipB is on the starboard side of shipA.
    We can say starboard side is relative bearing in (-112.5, 0).
    """
    bearingAB = relative_bearing_degs(shipA, shipB)
    # Starboard side if bearingAB is negative (and within some range)
    if -112.5 < bearingAB < 0:
        return True
    return False

def is_on_port_side(shipA, shipB):
    """
    Returns True if shipB is on the port side of shipA (bearingAB in (0, 112.5)).
    """
    bearingAB = relative_bearing_degs(shipA, shipB)
    if 0 < bearingAB < 112.5:
        return True
    return False

# =====================================================
# 4. Simulator with COLREG Avoidance
# =====================================================
class Simulator:
    def __init__(self, ships, time_step=30.0):
        self.ships = ships
        self.time_step = time_step
        self.current_time = 0.0
        self.destination_threshold = 0.05
        self.safe_distance = 0.2  # NM

        # A fixed "starboard turn" angle we apply if we must yield
        self.starboard_turn_angle = 15.0

    def step(self):
        """
        1) Detect pairs with collision risk
        2) Classify encounter type
        3) Apply appropriate COLREG rule
        4) Update positions
        """
        dt_hours = self.time_step / 3600.0

        # First, set headings to destination if no conflict
        # We'll apply potential avoidance overrides below
        for ship in self.ships:
            if ship.distance_to_destination() > self.destination_threshold:
                # direct heading to waypoint (baseline)
                desired_heading = ship.compute_heading_to_destination()
                ship.heading = desired_heading

        # Detect collisions, group them for resolution
        collision_pairs = self.detect_collision_risk()

        # For each pair, apply COLREG
        for (i, j) in collision_pairs:
            shipA = self.ships[i]
            shipB = self.ships[j]
            encounter_type = classify_encounter(shipA, shipB)

            if encounter_type == 'head-on':
                # Both turn starboard
                shipA.heading -= self.starboard_turn_angle
                shipB.heading -= self.starboard_turn_angle

            elif encounter_type == 'crossing':
                # If B is on starboard of A => A is give-way (and must turn starboard).
                if is_on_starboard_side(shipA, shipB):
                    # A yields
                    shipA.heading -= self.starboard_turn_angle
                elif is_on_starboard_side(shipB, shipA):
                    # B yields
                    shipB.heading -= self.starboard_turn_angle
                else:
                    # If we can't decide clearly, A might yield
                    shipA.heading -= self.starboard_turn_angle

            elif encounter_type == 'overtaking':
                # The overtaking ship yields.
                # We'll guess who is behind by checking relative bearings.
                bearingAB = relative_bearing_degs(shipA, shipB)
                if 110 < abs(bearingAB) < 250:
                    # B is behind A => B is overtaking A => B yields
                    shipB.heading += self.starboard_turn_angle
                else:
                    # A is overtaking B => A yields
                    shipA.heading += self.starboard_turn_angle
            else:
                # unknown or no classification => do nothing
                pass

        # Now update positions with final headings
        for ship in self.ships:
            if ship.distance_to_destination() > self.destination_threshold:
                ship.update_position(dt_hours)

        self.current_time += self.time_step

    def detect_collision_risk(self):
        """
        Returns list of index pairs (i, j) where i < j
        if cpa distance < safe_distance
        """
        n = len(self.ships)
        risk_pairs = []
        for i in range(n):
            for j in range(i+1, n):
                dist_cpa = compute_cpa_distance(self.ships[i], self.ships[j])
                if dist_cpa < self.safe_distance:
                    risk_pairs.append((i, j))
        return risk_pairs

    def all_ships_arrived(self):
        return all(ship.distance_to_destination() < self.destination_threshold
                   for ship in self.ships)


# =====================================================
# 5. Demo
# =====================================================
def run_simulation():
    # Example: 2 ships meeting head-on
    shipA = Ship("Ship A", 2.5, 0.0, 45.0, 20.0, 2.5, 5.0)
    shipB = Ship("Ship B", 0, 2.5, 225.0, 20.0, 5, 2.5)
    ships = [shipA, shipB]

    sim = Simulator(ships, time_step=30.0)

    # Matplotlib stuff
    fig, ax = plt.subplots()
    ax.set_aspect('equal')
    ax.set_xlim(-1, 6)
    ax.set_ylim(-1, 6)

    scatters = []
    for ship in ships:
        scatter, = ax.plot([], [], 'o', label=ship.name)
        scatters.append(scatter)

    for ship in ships:
        ax.plot(ship.dest_x, ship.dest_y, 'r*')  # mark destinations

    ax.legend()

    def init():
        for scatter in scatters:
            scatter.set_data([], [])
        return scatters

    def update(frame):
        # Step simulation
        sim.step()

        # Move scatter
        for i, ship in enumerate(sim.ships):
            scatters[i].set_data([ship.x], [ship.y])

        # Stop if all arrived
        if sim.all_ships_arrived():
            anim.event_source.stop()

        return scatters

    anim = FuncAnimation(fig, update, init_func=init,
                         frames=200, interval=500, blit=True)
    plt.title("Step 3: Simple COLREG Collision Avoidance")
    plt.show()


if __name__ == "__main__":
    run_simulation()
