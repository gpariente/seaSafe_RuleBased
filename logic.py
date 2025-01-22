# logic.py
import math
import numpy as np

#############################################################################
# 1. Ship Class
#############################################################################
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
        self.heading = heading
        self.speed = speed
        self.dest_x = dest_x
        self.dest_y = dest_y

        self.length_m = length_m
        self.width_m = width_m

    def update_position(self, dt_hours):
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
        angle_deg = math.degrees(math.atan2(dy, dx))
        return angle_deg

    def get_position_vector(self):
        return np.array([self.x, self.y])

    def get_velocity_vector(self):
        vx = self.speed * math.cos(math.radians(self.heading))
        vy = self.speed * math.sin(math.radians(self.heading))
        return np.array([vx, vy])


#############################################################################
# 2. Collision & COLREG Utilities
#############################################################################
def compute_cpa_distance(shipA, shipB):
    """
    Compute the distance at the closest point of approach (CPA).
    Returns the min distance, assuming constant velocity.
    """
    pA = shipA.get_position_vector()
    pB = shipB.get_position_vector()
    vA = shipA.get_velocity_vector()
    vB = shipB.get_velocity_vector()
    r0 = pB - pA
    v_rel = vB - vA

    if np.allclose(v_rel, 0):
        return np.linalg.norm(r0)

    t_cpa = -np.dot(r0, v_rel) / np.dot(v_rel, v_rel)
    if t_cpa < 0:
        t_cpa = 0.0
    r_cpa = r0 + v_rel * t_cpa
    return np.linalg.norm(r_cpa)


def relative_bearing_degs(from_ship, to_ship):
    """
    Returns the relative bearing from 'from_ship' to 'to_ship' in (-180,180].
    0 deg => dead ahead, + => port side, - => starboard side.
    """
    dx = to_ship.x - from_ship.x
    dy = to_ship.y - from_ship.y
    angle_abs = math.degrees(math.atan2(dy, dx))
    rel = angle_abs - from_ship.heading
    # Normalize
    while rel > 180:
        rel -= 360
    while rel <= -180:
        rel += 360
    return rel


def classify_encounter(shipA, shipB):
    """
    Basic classification:
      - 'head-on' if each sees the other near 0 deg
      - 'overtaking' if near 180 deg
      - else 'crossing'
    """
    bearingAB = abs(relative_bearing_degs(shipA, shipB))
    bearingBA = abs(relative_bearing_degs(shipB, shipA))

    if bearingAB < 10 and bearingBA < 10:
        return 'head-on'
    if (110 < bearingAB < 250) or (110 < bearingBA < 250):
        return 'overtaking'
    return 'crossing'


def is_on_starboard_side(shipA, shipB):
    bearingAB = relative_bearing_degs(shipA, shipB)
    return -112.5 < bearingAB < 0


#############################################################################
# 3. Simulator
#############################################################################
class Simulator:
    def __init__(self, ships, time_step=30.0, safe_distance=0.2, heading_search_range=40, heading_search_step=1.0):
        """
        Args:
            ships (list of Ship)
            time_step (float): step in seconds
            safe_distance (float): NM
            heading_search_range (float): up to N deg starboard
            heading_search_step (float): step in deg
        """
        self.ships = ships
        self.time_step = time_step
        self.safe_distance = safe_distance
        self.heading_search_range = heading_search_range
        self.heading_search_step = heading_search_step

        self.current_time = 0.0
        self.destination_threshold = 0.05  # NM

    def step(self):
        """
        Advance the simulation by self.time_step seconds.
        - Compute baseline heading to destination.
        - Detect collisions, sort by ascending CPA.
        - Apply starboard maneuvers for collisions.
        - Update positions.
        """
        dt_hours = self.time_step / 3600.0

        # 1) Set heading to dest by default
        for sh in self.ships:
            if sh.distance_to_destination() > self.destination_threshold:
                sh.heading = sh.compute_heading_to_destination()

        # 2) Collisions
        collisions = self.detect_collisions()
        collisions.sort(key=lambda x: x[0])  # sort by dist_cpa ascending

        # 3) Resolve collisions
        for (dist_cpa, i, j) in collisions:
            shipA = self.ships[i]
            shipB = self.ships[j]
            encounter = classify_encounter(shipA, shipB)

            if encounter == 'head-on':
                # both yield
                self.starboard_cpa_search(shipA, shipB)
                self.starboard_cpa_search(shipB, shipA)
            elif encounter == 'crossing':
                # who yields?
                if is_on_starboard_side(shipA, shipB):
                    self.starboard_cpa_search(shipA, shipB)
                elif is_on_starboard_side(shipB, shipA):
                    self.starboard_cpa_search(shipB, shipA)
            else:  # overtaking
                bearingAB = relative_bearing_degs(shipA, shipB)
                if 110 < abs(bearingAB) < 250:
                    self.starboard_cpa_search(shipB, shipA)
                else:
                    self.starboard_cpa_search(shipA, shipB)

        # 4) Update positions
        for sh in self.ships:
            if sh.distance_to_destination() > self.destination_threshold:
                sh.update_position(dt_hours)

        self.current_time += self.time_step

    def detect_collisions(self):
        """
        Return [(dist_cpa, i, j), ...] for pairs with cpa < safe_distance
        """
        n = len(self.ships)
        pairs = []
        for i in range(n):
            for j in range(i+1, n):
                cpa = compute_cpa_distance(self.ships[i], self.ships[j])
                if cpa < self.safe_distance:
                    pairs.append((cpa, i, j))
        return pairs

    def starboard_cpa_search(self, give_ship, other_ship):
        """
        Minimal starboard turn up to heading_search_range in heading_search_step increments
        to maintain safe_distance.
        """
        current = give_ship.heading
        best_heading = current
        best_cpa = compute_cpa_distance(give_ship, other_ship)
        if best_cpa >= self.safe_distance:
            return

        import numpy as np
        for offset in np.arange(1, self.heading_search_range+1, self.heading_search_step):
            test = current - offset
            old = give_ship.heading
            give_ship.heading = test
            cpa_test = compute_cpa_distance(give_ship, other_ship)
            give_ship.heading = old

            if cpa_test > best_cpa:
                best_cpa = cpa_test
                best_heading = test
            if best_cpa >= self.safe_distance:
                break

        give_ship.heading = best_heading

    def all_ships_arrived(self):
        return all(s.distance_to_destination() < self.destination_threshold for s in self.ships)

    def get_collisions_with_roles(self):
        """
        Returns a list of (dist_cpa, i, j, encounter, role_i, role_j)
        for all pairs that have CPA < safe_distance, sorted by dist_cpa ascending.

        'role_i' and 'role_j' will be "Give-Way", "Stand-On", or "" (if no collision).
        In a head-on scenario, both might be "Give-Way".
        """
        results = []
        collisions = self.detect_collisions()
        # sort by ascending cpa
        collisions.sort(key=lambda x: x[0])

        for (cpa, i, j) in collisions:
            shipA = self.ships[i]
            shipB = self.ships[j]
            encounter = classify_encounter(shipA, shipB)
            roleA, roleB = self.assign_roles(shipA, shipB, encounter)
            results.append((cpa, i, j, encounter, roleA, roleB))

        return results

    def assign_roles(self, shipA, shipB, encounter_type):
        """
        Return (roleA, roleB) as strings: 'Give-Way', 'Stand-On', or ''
        """
        if encounter_type == 'head-on':
            return ("Give-Way", "Give-Way")
        elif encounter_type == 'crossing':
            if is_on_starboard_side(shipA, shipB):
                return ("Give-Way", "Stand-On")
            elif is_on_starboard_side(shipB, shipA):
                return ("Stand-On", "Give-Way")
            else:
                # ambiguous => default to (A=Give-Way, B=Stand-On)
                return ("Give-Way", "Stand-On")
        else:  # overtaking
            bearingAB = abs(relative_bearing_degs(shipA, shipB))
            if 110 < bearingAB < 250:
                # B behind A => B is give-way
                return ("Stand-On", "Give-Way")
            else:
                return ("Give-Way", "Stand-On")