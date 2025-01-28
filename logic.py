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


#############################################################################
# 2. Collision & COLREG Utilities
#############################################################################
def compute_cpa_and_tcpa(shipA, shipB):
    """
    Compute the closest point of approach (CPA) distance and the time of that CPA.
    Returns (dist_cpa, t_cpa).
    If t_cpa < 0, the CPA is in the past, so we clamp it to 0.0.
    """
    pA = shipA.get_position_vector()
    vA = shipA.get_velocity_vector()
    pB = shipB.get_position_vector()
    vB = shipB.get_velocity_vector()

    r0 = pB - pA
    v_rel = vB - vA
    denom = np.dot(v_rel, v_rel)

    # If relative velocity ~ 0, ships move parallel => CPA is current distance
    if abs(denom) < 1e-9:
        dist_cpa = np.linalg.norm(r0)
        return dist_cpa, 0.0

    t_cpa = -np.dot(r0, v_rel) / denom
    if t_cpa < 0:
        t_cpa = 0.0

    r_cpa = r0 + v_rel * t_cpa
    dist_cpa = np.linalg.norm(r_cpa)
    return dist_cpa, t_cpa


def relative_bearing_degs(from_ship, to_ship):
    """
    Returns the relative bearing from 'from_ship' to 'to_ship' in (-180,180].
     - 0 deg => dead ahead
     - positive => port side
     - negative => starboard side
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

    # Head-on if both bearings near 0
    if bearingAB < 10 and bearingBA < 10:
        return 'head-on'

    # Overtaking if at least one sees the other near 180
    if (110 < bearingAB < 250) or (110 < bearingBA < 250):
        return 'overtaking'

    return 'crossing'


def is_on_starboard_side(shipA, shipB):
    """
    True if shipB is on the starboard side of shipA.
    i.e. from A's perspective, bearing to B is in (-112.5, 0).
    """
    bearingAB = relative_bearing_degs(shipA, shipB)
    return -112.5 < bearingAB < 0


#############################################################################
# 3. Simulator
#############################################################################
class Simulator:
    def __init__(self, ships, time_step, safe_distance,
                 heading_search_range, heading_search_step):
        """
        Args:
            ships (list of Ship)
            time_step (float): step in seconds
            safe_distance (float): NM
            heading_search_range (float): up to N deg starboard in one step
            heading_search_step (float): starboard increments (deg)
        """
        self.ships = ships
        self.time_step = time_step
        self.safe_distance = safe_distance
        self.heading_search_range = heading_search_range
        self.heading_search_step = heading_search_step
        self.ui_log = []
        self.current_time = 0.0
        self.destination_threshold = 0.1  # NM
        self.no_collision_count = 0  # how many consecutive steps collision-free


    def step(self, debug=False):
        dt_hours = self.time_step / 3600.0

        # 1) Reset heading adjustments
        for sh in self.ships:
            sh.reset_heading_adjusted()
            
        # 1) DETECT collisions
        collisions = self.detect_collisions()

        if not collisions:
            self.no_collision_count += 1
        else:
            self.no_collision_count = 0

        # 2) If collisions are gone for multiple steps, revert heading gradually
        if self.no_collision_count > 5:
            for sh in self.ships:
                if sh.distance_to_destination() > self.destination_threshold:
                    self.revert_heading_with_clamp(sh)

            
        # else if collisions remain or we haven't had enough collision-free steps,
        # keep the heading from last step.

        max_iterations = 100
        for iteration in range(max_iterations):
            collisions = self.detect_collisions()
            if not collisions:
                if debug:
                    print(f"[Iteration {iteration}] No collisions detected. Done.")
                break

            if debug:
                print(f"[Iteration {iteration}] Detected {len(collisions)} collisions:")
                for dist_cpa, t_cpa, i, j in collisions:
                    shipA = self.ships[i]
                    shipB = self.ships[j]
                    print(f"  - {shipA.name} vs {shipB.name}: distCPA={dist_cpa:.3f}, tCPA={t_cpa:.2f}")

            improved_any = False

            for (dist_cpa, t_cpa, i, j) in collisions:
                if dist_cpa >= 2.1 * self.safe_distance:
                    continue
                shipA = self.ships[i]
                shipB = self.ships[j]
                encounter = classify_encounter(shipA, shipB)
                if debug:
                    print(f"   Resolving {shipA.name} vs {shipB.name}: encounter={encounter}")

                if encounter == 'head-on':
                    impA = self.apply_multi_ship_starboard(shipA, debug=debug)
                    impB = self.apply_multi_ship_starboard(shipB, debug=debug)
                    if impA or impB:
                        improved_any = True
                elif encounter == 'crossing':
                    if is_on_starboard_side(shipA, shipB):
                        impA = self.apply_multi_ship_starboard(shipA, debug=debug)
                        if not impA:
                            impB = self.apply_multi_ship_starboard(shipB, stand_on=True, debug=debug)
                            if impB:
                                improved_any = True
                        else:
                            improved_any = True
                    else:
                        impB = self.apply_multi_ship_starboard(shipB, debug=debug)
                        if not impB:
                            impA = self.apply_multi_ship_starboard(shipA, stand_on=True, debug=debug)
                            if impA:
                                improved_any = True
                        else:
                            improved_any = True
                else:  # overtaking
                    bearingAB = abs(relative_bearing_degs(shipA, shipB))
                    if 110 < bearingAB < 250:
                        # B behind A
                        impB = self.apply_multi_ship_starboard(shipB, debug=debug)
                        if not impB:
                            impA = self.apply_multi_ship_starboard(shipA, stand_on=True, debug=debug)
                            if impA:
                                improved_any = True
                        else:
                            improved_any = True
                    else:
                        # A behind B
                        impA = self.apply_multi_ship_starboard(shipA, debug=debug)
                        if not impA:
                            impB = self.apply_multi_ship_starboard(shipB, stand_on=True, debug=debug)
                            if impB:
                                improved_any = True
                        else:
                            improved_any = True

            if not improved_any:
                if debug:
                    print(f"   No improvements in iteration {iteration}, stopping.")
                break

        # 4) Move ships
        for sh in self.ships:
            if sh.distance_to_destination() > self.destination_threshold:
                sh.update_position(dt_hours)
        self.current_time += self.time_step
        if debug:
            print(f"Completed step. Advanced time to {self.current_time} s.\n")


    def detect_collisions(self):
        """
        Return a list of (dist_cpa, t_cpa, i, j) for pairs with dist_cpa < safe_distance.
        Sort by earliest t_cpa, then by dist_cpa ascending.
        """
        n = len(self.ships)
        pairs = []
        for i in range(n):
            for j in range(i+1, n):
                dist_cpa, t_cpa = compute_cpa_and_tcpa(self.ships[i], self.ships[j])
                if dist_cpa < 2.1 * self.safe_distance:
                    pairs.append((dist_cpa, t_cpa, i, j))
        # sort by t_cpa, then dist_cpa
        pairs.sort(key=lambda x: (x[1], x[0]))
        return pairs

    def apply_multi_ship_starboard(self, ship, stand_on=False, debug=False):
        base_heading = ship.heading
        if stand_on:
            max_range = min(self.heading_search_range, 10.0)
        else:
            max_range = self.heading_search_range

        remaining_turn = max_range - ship.heading_adjusted
        if remaining_turn <= 0:
            if debug:
                print(f"      {ship.name} has no remaining turn allowed (stand_on={stand_on}).")
            return False

        step = self.heading_search_step
        current_cpa = self.compute_min_cpa_over_others(ship, base_heading)
        best_cpa = current_cpa
        best_offset = 0.0

        increments = np.arange(step, remaining_turn + 0.0001, step)

        for offset in increments:
            test_heading = base_heading - offset
            test_cpa = self.compute_min_cpa_over_others(ship, test_heading)
            if test_cpa > best_cpa:
                best_cpa = test_cpa
                best_offset = offset

        if best_offset > 0:
            # We found an improvement
            new_heading = base_heading - best_offset
            ship.heading = new_heading
            ship.heading_adjusted += best_offset
            self.ui_log.append(f"{ship.name} turned starboard {best_offset:.1f} deg => new heading={new_heading:.1f}")
            if debug:
                print(f"      {ship.name} turning starboard by {best_offset} deg => new heading={new_heading:.1f}, improved CPA from {current_cpa:.3f} to {best_cpa:.3f}")
            return True

        if debug:
            print(f"      {ship.name} found NO offset that improves CPA (stand_on={stand_on}).")
        return False

    def compute_min_cpa_over_others(self, give_ship, test_heading):
        """
        Temporarily set give_ship.heading to test_heading,
        compute min CPA with all other ships,
        revert heading. 
        """
        old_heading = give_ship.heading
        give_ship.heading = test_heading

        min_cpa = float('inf')
        for s in self.ships:
            if s is not give_ship:
                dist_cpa, _ = compute_cpa_and_tcpa(give_ship, s)
                if dist_cpa < min_cpa:
                    min_cpa = dist_cpa

        # revert
        give_ship.heading = old_heading
        return min_cpa
    
    def revert_heading_with_clamp(self, ship):
        """
        Gradually revert 'ship.heading' toward 'compute_heading_to_destination()',
        but do not exceed heading_search_range in one step.
        """
        current_hd = ship.heading
        dest_hd = ship.compute_heading_to_destination()

        # 1) Find minimal difference in [-180,180]
        diff = dest_hd - current_hd
        while diff > 180:
            diff -= 360
        while diff <= -180:
            diff += 360

        # 2) clamp difference to ± heading_search_range
        max_turn = self.heading_search_range
        if diff > max_turn:
            diff = max_turn
        elif diff < -max_turn:
            diff = -max_turn

        # 3) apply
        new_hd = current_hd + diff
        ship.heading = new_hd
    def all_ships_arrived(self):
        """
        True if all ships have reached (or are within threshold of) their destinations.
        """
        return all(s.distance_to_destination() < self.destination_threshold for s in self.ships)

    def get_collisions_with_roles(self):
        """
        Returns a list of (dist_cpa, i, j, encounter, role_i, role_j) for
        all pairs that have dist_cpa < safe_distance. Primarily for UI labeling.
        """
        results = []
        collisions = self.detect_collisions()
        for (dist_cpa, t_cpa, i, j) in collisions:
            if dist_cpa >= 2.1 * self.safe_distance:
                continue
            shipA = self.ships[i]
            shipB = self.ships[j]
            encounter = classify_encounter(shipA, shipB)
            roleA, roleB = self.assign_roles(shipA, shipB, encounter)
            results.append((dist_cpa, i, j, encounter, roleA, roleB))
        return results

    def assign_roles(self, shipA, shipB, encounter_type):
        """
        Return (roleA, roleB) as strings: "Give-Way", "Stand-On", or "".
        Used mainly for UI labels.
        """
        if encounter_type == 'head-on':
            return ("Give-Way", "Give-Way")
        elif encounter_type == 'crossing':
            if is_on_starboard_side(shipA, shipB):
                return ("Give-Way", "Stand-On")
            elif is_on_starboard_side(shipB, shipA):
                return ("Stand-On", "Give-Way")
            else:
                return ("Give-Way", "Stand-On")  # fallback
        else:  # overtaking
            bearingAB = abs(relative_bearing_degs(shipA, shipB))
            if 110 < bearingAB < 250:
                return ("Stand-On", "Give-Way")
            else:
                return ("Give-Way", "Stand-On")
