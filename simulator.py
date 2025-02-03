import math
import numpy as np

from ship import Ship
from colreg import (
    compute_cpa_and_tcpa,
    relative_bearing_degs,
    classify_encounter,
    is_on_starboard_side
)

# Mapping from RGB tuples to color names.
COLOR_NAMES = {
    (0, 255, 0): "Green",
    (255, 255, 0): "Yellow",
    (128, 128, 128): "Gray",
    (0, 0, 0): "Black",
    (128, 0, 128): "Purple"
}

def get_color_name(color):
    return COLOR_NAMES.get(tuple(color), "Unknown")

class Simulator:
    def __init__(self, ships, time_step, safe_distance,
                 heading_search_range, heading_search_step):
        """
        ships: list of Ship objects
        time_step: simulation step in seconds
        safe_distance: in NM
        heading_search_range, heading_search_step: starboard turn constraints
        """
        self.ships = ships
        self.time_step = time_step
        self.safe_distance = safe_distance
        self.heading_search_range = heading_search_range
        self.heading_search_step = heading_search_step

        self.ui_log = []
        self.collisions_avoided = []  # List of detailed collision-avoidance messages.
        self.current_time = 0.0
        self.destination_threshold = 0.1  # NM threshold to consider a ship as "arrived"
        self.no_collision_count = 0  # consecutive simulation steps without collisions

        # Counters for encounter types.
        self.count_headon = 0
        self.count_crossing = 0
        self.count_overtaking = 0

    def step(self, debug=False):
        dt_hours = self.time_step / 3600.0

        # 1) Reset heading_adjusted for each ship.
        for sh in self.ships:
            sh.reset_heading_adjusted()

        # 2) Detect collisions.
        collisions = self.detect_collisions()
        if not collisions:
            self.no_collision_count += 1
        else:
            self.no_collision_count = 0

        # 3) If collision‑free for multiple steps, revert heading.
        if self.no_collision_count > 10:
            for sh in self.ships:
                if sh.distance_to_destination() > self.destination_threshold:
                    self.revert_heading_with_clamp(sh)

        # 4) Multi-iteration collision resolution.
        max_iters = 100
        for iteration in range(max_iters):
            collisions = self.detect_collisions()
            if not collisions:
                if debug:
                    print(f"[Iteration {iteration}] No collisions => done.")
                break

            improved_any = False
            for dist_cpa, t_cpa, i, j in collisions:
                if dist_cpa >= 3 * self.safe_distance:
                    continue
                shipA = self.ships[i]
                shipB = self.ships[j]
                encounter = classify_encounter(shipA, shipB)
                roles = self.assign_roles(shipA, shipB, encounter)  # (roleA, roleB)
                if debug:
                    print(f"Resolving {get_color_name(shipA.color)} vs {get_color_name(shipB.color)}, {encounter}, dist_cpa={dist_cpa:.3f}")

                # Process encounter types.
                if encounter == 'head-on':
                    impA = self.apply_multi_ship_starboard(shipA, debug=debug)
                    impB = self.apply_multi_ship_starboard(shipB, debug=debug)
                    if impA:
                        msg = (f"{get_color_name(shipA.color)} avoided collision in a head-on encounter with "
                               f"{get_color_name(shipB.color)}, role: {roles[0]}, Timestep: {self.current_time}.")
                        self.collisions_avoided.append(msg)
                        self.count_headon += 1
                    if impB:
                        msg = (f"{get_color_name(shipB.color)} avoided collision in a head-on encounter with "
                               f"{get_color_name(shipA.color)}, role: {roles[1]}, Timestep: {self.current_time}.")
                        self.collisions_avoided.append(msg)
                        self.count_headon += 1
                    if impA or impB:
                        improved_any = True

                elif encounter == 'crossing':
                    if is_on_starboard_side(shipA, shipB):
                        impA = self.apply_multi_ship_starboard(shipA, debug=debug)
                        if impA:
                            msg = (f"{get_color_name(shipA.color)} avoided collision in a crossing encounter with "
                                   f"{get_color_name(shipB.color)}, role: {roles[0]}, Timestep: {self.current_time}.")
                            self.collisions_avoided.append(msg)
                            self.count_crossing += 1
                            improved_any = True
                        else:
                            impB = self.apply_multi_ship_starboard(shipB, stand_on=True, debug=debug)
                            if impB:
                                msg = (f"{get_color_name(shipB.color)} avoided collision in a crossing encounter with "
                                       f"{get_color_name(shipA.color)}, role: {roles[1]}, Timestep: {self.current_time}.")
                                self.collisions_avoided.append(msg)
                                self.count_crossing += 1
                                improved_any = True
                    else:
                        impB = self.apply_multi_ship_starboard(shipB, debug=debug)
                        if impB:
                            msg = (f"{get_color_name(shipB.color)} avoided collision in a crossing encounter with "
                                   f"{get_color_name(shipA.color)}, role: {roles[1]}, Timestep: {self.current_time}.")
                            self.collisions_avoided.append(msg)
                            self.count_crossing += 1
                            improved_any = True
                        else:
                            impA = self.apply_multi_ship_starboard(shipA, stand_on=True, debug=debug)
                            if impA:
                                msg = (f"{get_color_name(shipA.color)} avoided collision in a crossing encounter with "
                                       f"{get_color_name(shipB.color)}, role: {roles[0]}, Timestep: {self.current_time}.")
                                self.collisions_avoided.append(msg)
                                self.count_crossing += 1
                                improved_any = True

                else:  # overtaking
                    bearingAB = abs(relative_bearing_degs(shipA, shipB))
                    if 112.5 < bearingAB < 250:
                        impB = self.apply_multi_ship_starboard(shipB, debug=debug)
                        if impB:
                            msg = (f"{get_color_name(shipB.color)} avoided collision in an overtaking encounter with "
                                   f"{get_color_name(shipA.color)}, role: {roles[1]}, Timestep: {self.current_time}.")
                            self.collisions_avoided.append(msg)
                            self.count_overtaking += 1
                            improved_any = True
                        else:
                            impA = self.apply_multi_ship_starboard(shipA, stand_on=True, debug=debug)
                            if impA:
                                msg = (f"{get_color_name(shipA.color)} avoided collision in an overtaking encounter with "
                                       f"{get_color_name(shipB.color)}, role: {roles[0]}, Timestep: {self.current_time}.")
                                self.collisions_avoided.append(msg)
                                self.count_overtaking += 1
                                improved_any = True
                    else:
                        impA = self.apply_multi_ship_starboard(shipA, debug=debug)
                        if impA:
                            msg = (f"{get_color_name(shipA.color)} avoided collision in an overtaking encounter with "
                                   f"{get_color_name(shipB.color)}, role: {roles[0]}, Timestep: {self.current_time}.")
                            self.collisions_avoided.append(msg)
                            self.count_overtaking += 1
                            improved_any = True
                        else:
                            impB = self.apply_multi_ship_starboard(shipB, stand_on=True, debug=debug)
                            if impB:
                                msg = (f"{get_color_name(shipB.color)} avoided collision in an overtaking encounter with "
                                       f"{get_color_name(shipA.color)}, role: {roles[1]}, Timestep: {self.current_time}.")
                                self.collisions_avoided.append(msg)
                                self.count_overtaking += 1
                                improved_any = True

            if not improved_any:
                if debug:
                    print(f"No improvements iteration {iteration}, stopping.")
                break

        # 5) Move ships.
        for sh in self.ships:
            # If the ship has arrived (distance below threshold) and arrival_time not recorded, record it.
            if sh.distance_to_destination() < self.destination_threshold:
                if sh.arrival_time is None:
                    sh.arrival_time = self.current_time
            else:
                sh.update_position(dt_hours)

        # Increment simulation time.
        self.current_time += self.time_step
        if debug:
            print(f"Completed step. time={self.current_time} s.\n")

    def detect_collisions(self):
        """
        Detects collisions between ships based on the CPA (Closest Point of Approach).

        Returns:
            list of tuples: Each tuple contains (dist_cpa, t_cpa, i, j) where i and j are ship indices.
        """
        pairs = []
        n = len(self.ships)
        for i in range(n):
            for j in range(i+1, n):
                dist_cpa, t_cpa = compute_cpa_and_tcpa(self.ships[i], self.ships[j])
                if dist_cpa < 3 * self.safe_distance:
                    pairs.append((dist_cpa, t_cpa, i, j))
        pairs.sort(key=lambda x: (x[1], x[0]))
        return pairs

    def apply_multi_ship_starboard(self, ship, stand_on=False, debug=False):
        """
        Attempts to adjust a ship's heading to improve its CPA relative to other ships.

        Parameters:
            ship (Ship): The ship to adjust.
            stand_on (bool): If True, restricts the adjustment (for the stand-on vessel).
            debug (bool): If True, prints debug information.

        Returns:
            bool: True if an adjustment was made; False otherwise.
        """
        base_heading = ship.heading
        if stand_on:
            max_range = min(self.heading_search_range, 10.0)
        else:
            max_range = self.heading_search_range
        remaining_turn = max_range - ship.heading_adjusted
        if remaining_turn <= 0:
            if debug:
                print(f"{get_color_name(ship.color)} has no remaining turn allowed (stand_on={stand_on}).")
            return False
        current_cpa = self.compute_min_cpa_over_others(ship, base_heading)
        best_cpa = current_cpa
        best_offset = 0.0
        step = self.heading_search_step
        increments = np.arange(step, remaining_turn + 0.0001, step)
        for offset in increments:
            test_heading = base_heading - offset
            test_cpa = self.compute_min_cpa_over_others(ship, test_heading)
            if test_cpa > best_cpa:
                best_cpa = test_cpa
                best_offset = offset
        if best_offset > 0:
            new_heading = base_heading - best_offset
            ship.heading = new_heading
            ship.heading_adjusted += best_offset
            if debug:
                print(f"{get_color_name(ship.color)} improved CPA: {current_cpa:.3f} -> {best_cpa:.3f} by turning {best_offset:.1f} deg")
            return True
        if debug:
            print(f"{get_color_name(ship.color)} no offset improves CPA (stand_on={stand_on}).")
        return False

    def compute_min_cpa_over_others(self, give_ship, test_heading):
        """
        Computes the minimum CPA for a given ship against all other ships, if the ship used a specified test heading.

        Parameters:
            give_ship (Ship): The ship for which to compute the CPA.
            test_heading (float): The heading to test.

        Returns:
            float: The minimum CPA (in NM).
        """
        old_heading = give_ship.heading
        give_ship.heading = test_heading
        min_cpa = float('inf')
        for s in self.ships:
            if s is not give_ship:
                dist_cpa, _ = compute_cpa_and_tcpa(give_ship, s)
                if dist_cpa < min_cpa:
                    min_cpa = dist_cpa
        give_ship.heading = old_heading
        return min_cpa

    def revert_heading_with_clamp(self, ship):
        """
        Reverts a ship's heading toward its destination, limited by the maximum allowed turn.

        Parameters:
            ship (Ship): The ship whose heading is to be reverted.
        """
        curr_hd = ship.heading
        dest_hd = ship.compute_heading_to_destination()
        diff = dest_hd - curr_hd
        while diff > 180:
            diff -= 360
        while diff <= -180:
            diff += 360
        max_turn = self.heading_search_range
        if diff > max_turn:
            diff = max_turn
        elif diff < -max_turn:
            diff = -max_turn
        ship.heading = curr_hd + diff

    def all_ships_arrived(self):
        """
        Checks if all ships have reached their destination.

        Returns:
            bool: True if every ship's distance to destination is below the threshold; otherwise, False.
        """
        return all(s.distance_to_destination() < self.destination_threshold for s in self.ships)

    def get_collisions_with_roles(self):
        """
        Retrieves a list of collisions along with assigned roles for each encounter.

        Returns:
            list of tuples: Each tuple contains (dist_cpa, i, j, encounter, roleA, roleB).
        """
        results = []
        collisions = self.detect_collisions()
        for dist_cpa, t_cpa, i, j in collisions:
            if dist_cpa >= 3 * self.safe_distance:
                continue
            shipA = self.ships[i]
            shipB = self.ships[j]
            encounter = classify_encounter(shipA, shipB)
            roleA, roleB = self.assign_roles(shipA, shipB, encounter)
            results.append((dist_cpa, i, j, encounter, roleA, roleB))
        return results

    def assign_roles(self, shipA, shipB, encounter_type):
        """
        Determines the roles (Give-Way or Stand-On) for two ships based on the encounter type.

        Parameters:
            shipA (Ship): The first ship.
            shipB (Ship): The second ship.
            encounter_type (str): The type of encounter ('head-on', 'crossing', or 'overtaking').

        Returns:
            tuple: (roleA, roleB) where each role is a string ("Give-Way" or "Stand-On").
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
        else:
            bearingAB = abs(relative_bearing_degs(shipA, shipB))
            if 112.5 < bearingAB < 250:
                return ("Stand-On", "Give-Way")
            else:
                return ("Give-Way", "Stand-On")
