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

        # Tracking heading adjustments within a time step
        self.heading_adjusted = 0.0

    def reset_heading_adjusted(self):
        self.heading_adjusted = 0.0

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
    def __init__(self, ships, time_step=30.0, safe_distance=0.2,
                 heading_search_range=40, heading_search_step=1.0):
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
        We'll do multiple iterations of collision resolution before
        finally moving the ships.
        """
        dt_hours = self.time_step / 3600.0

        # Reset heading adjustments for all ships at the start of the step
        for sh in self.ships:
            sh.reset_heading_adjusted()

        # 1) Baseline heading: each ship aims at destination
        for sh in self.ships:
            if sh.distance_to_destination() > self.destination_threshold:
                sh.heading = sh.compute_heading_to_destination()

        # 2) Multi-step collision resolution
        max_iterations = 5  # or more if you prefer
        for _ in range(max_iterations):
            collisions = self.detect_collisions()
            if not collisions:
                # No collisions -> done
                break
            collisions.sort(key=lambda x: x[0])  # sort by ascending cpa

            improved_any = False
            for (dist_cpa, i, j) in collisions:
                if dist_cpa >= self.safe_distance:
                    continue  # this collision is no longer relevant
                shipA = self.ships[i]
                shipB = self.ships[j]
                encounter = classify_encounter(shipA, shipB)

                # determine who is give-way
                # in head-on, both yield
                if encounter == 'head-on':
                    # both do multi-ship starboard
                    improvedA = self.apply_multi_ship_starboard(shipA)
                    improvedB = self.apply_multi_ship_starboard(shipB)
                    if improvedA or improvedB:
                        improved_any = True
                elif encounter == 'crossing':
                    if is_on_starboard_side(shipA, shipB):
                        # A is give-way
                        if self.apply_multi_ship_starboard(shipA):
                            improved_any = True
                    elif is_on_starboard_side(shipB, shipA):
                        # B is give-way
                        if self.apply_multi_ship_starboard(shipB):
                            improved_any = True
                    else:
                        # default to letting A yield
                        if self.apply_multi_ship_starboard(shipA):
                            improved_any = True
                else:  # overtaking
                    bearingAB = abs(relative_bearing_degs(shipA, shipB))
                    if 110 < bearingAB < 250:
                        # B behind A => B yields
                        if self.apply_multi_ship_starboard(shipB):
                            improved_any = True
                    else:
                        # default to A yields
                        if self.apply_multi_ship_starboard(shipA):
                            improved_any = True

            if not improved_any:
                # No improvements in this iteration, avoid infinite loop
                break

        # 3) Now update positions
        for sh in self.ships:
            if sh.distance_to_destination() > self.destination_threshold:
                sh.update_position(dt_hours)

        self.current_time += self.time_step

    def apply_multi_ship_starboard(self, give_ship):
        """
        Attempt a multi-ship starboard turn for 'give_ship' up to self.heading_search_range,
        searching in self.heading_search_step increments.
        We pick the heading that yields the largest minimum CPA to all other ships,
        but do not exceed the total heading_range.
        
        Returns True if a heading change was made, False if not.
        """
        current_heading = give_ship.heading
        max_total_adjust = self.heading_search_range - give_ship.heading_adjusted
        if max_total_adjust <= 0:
            return False  # No adjustment left

        # We can only adjust up to the remaining allowed heading range
        # So the max offset we can apply in this call is min(heading_search_range, max_total_adjust)
        # Considering heading_step increments
        max_offset = min(self.heading_search_range, max_total_adjust)
        # Adjust in heading_search_step increments
        possible_offsets = np.arange(self.heading_search_step, max_offset + 1, self.heading_search_step)

        best_heading = current_heading
        best_min_cpa = self.compute_min_cpa_over_others(give_ship, current_heading)

        for offset in possible_offsets:
            test_heading = current_heading - offset
            cpa_test = self.compute_min_cpa_over_others(give_ship, test_heading)
            if cpa_test > best_min_cpa:
                best_min_cpa = cpa_test
                best_heading = test_heading
                # Record the heading adjustment
                give_ship.heading_adjusted += offset
                improved = True
                if best_min_cpa >= self.safe_distance:
                    # Good enough => we can stop searching
                    break

        if best_heading != current_heading:
            give_ship.heading = best_heading
            return True
        return False

    def compute_min_cpa_over_others(self, give_ship, test_heading):
        """
        Temporarily set 'give_ship.heading' to 'test_heading' and compute
        the minimum CPA to *all* other ships. Then revert.
        """
        old_heading = give_ship.heading
        give_ship.heading = test_heading
        min_cpa = float('inf')
        for s in self.ships:
            if s is not give_ship:
                cpa = compute_cpa_distance(give_ship, s)
                if cpa < min_cpa:
                    min_cpa = cpa
        give_ship.heading = old_heading
        return min_cpa

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

    def all_ships_arrived(self):
        return all(s.distance_to_destination() < self.destination_threshold
                   for s in self.ships)

    def get_collisions_with_roles(self):
        """
        Returns a list of (dist_cpa, i, j, encounter, role_i, role_j)
        for all pairs that have CPA < safe_distance, sorted by dist_cpa ascending.

        'role_i' and 'role_j' will be "Give-Way", "Stand-On", or "" (if no collision).
        In a head-on scenario, both might be "Give-Way".
        """
        results = []
        collisions = self.detect_collisions()
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
                return ("Give-Way", "Stand-On")
        else:  # overtaking
            bearingAB = abs(relative_bearing_degs(shipA, shipB))
            if 110 < bearingAB < 250:
                return ("Stand-On", "Give-Way")
            else:
                return ("Give-Way", "Stand-On")
