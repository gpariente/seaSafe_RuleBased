# simulator.py
import math
import numpy as np

from ship import Ship
from colreg import (
    compute_cpa_and_tcpa,
    relative_bearing_degs,
    classify_encounter,
    is_on_starboard_side
)

class Simulator:
    def __init__(self, ships, time_step, safe_distance,
                 heading_search_range, heading_search_step):
        """
        ships: list of Ship objects
        time_step: step in seconds
        safe_distance: NM
        heading_search_range, heading_search_step: starboard turn constraints
        """
        self.ships = ships
        self.time_step = time_step
        self.safe_distance = safe_distance
        self.heading_search_range = heading_search_range
        self.heading_search_step = heading_search_step

        self.ui_log = []
        self.current_time = 0.0
        self.destination_threshold = 0.1  # NM
        self.no_collision_count = 0  # consecutive steps collision-free

    def step(self, debug=False):
        dt_hours = self.time_step / 3600.0

        # 1) reset heading_adjusted
        for sh in self.ships:
            sh.reset_heading_adjusted()

        # 2) detect collisions
        collisions = self.detect_collisions()
        if not collisions:
            self.no_collision_count += 1
        else:
            self.no_collision_count = 0

        # 3) if collision-free multiple steps => revert heading
        if self.no_collision_count > 5:
            for sh in self.ships:
                if sh.distance_to_destination() > self.destination_threshold:
                    self.revert_heading_with_clamp(sh)

        # 4) multi-iteration collision resolution
        max_iters = 100
        for iteration in range(max_iters):
            collisions = self.detect_collisions()
            if not collisions:
                if debug:
                    print(f"[Iteration {iteration}] No collisions => done.")
                break

            improved_any = False
            for dist_cpa, t_cpa, i, j in collisions:
                if dist_cpa >= 2.1 * self.safe_distance:
                    continue
                shipA = self.ships[i]
                shipB = self.ships[j]
                encounter = classify_encounter(shipA, shipB)
                if debug:
                    print(f"Resolving {shipA.name} vs {shipB.name}, {encounter}, dist_cpa={dist_cpa:.3f}")

                if encounter == 'head-on':
                    impA = self.apply_multi_ship_starboard(shipA, debug=debug)
                    impB = self.apply_multi_ship_starboard(shipB, debug=debug)
                    if impA or impB:
                        improved_any = True
                elif encounter == 'crossing':
                    # figure out who is give-way
                    if is_on_starboard_side(shipA, shipB):
                        # A is give-way
                        impA = self.apply_multi_ship_starboard(shipA, debug=debug)
                        if not impA:
                            impB = self.apply_multi_ship_starboard(shipB, stand_on=True, debug=debug)
                            if impB:
                                improved_any = True
                        else:
                            improved_any = True
                    else:
                        # B is give-way
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
                        impA = self.apply_multi_ship_starboard(shipA, debug=debug)
                        if not impA:
                            impB = self.apply_multi_ship_starboard(shipB, stand_on=True, debug=debug)
                            if impB:
                                improved_any = True
                        else:
                            improved_any = True

            if not improved_any:
                if debug:
                    print(f"No improvements iteration {iteration}, stopping.")
                break

        # 5) move ships
        for sh in self.ships:
            if sh.distance_to_destination() > self.destination_threshold:
                sh.update_position(dt_hours)

        self.current_time += self.time_step
        if debug:
            print(f"Completed step. time={self.current_time} s.\n")

    def detect_collisions(self):
        """
        Return list of (dist_cpa, t_cpa, i, j) for pairs with dist_cpa < 2.1 * safe_distance.
        """
        pairs = []
        n = len(self.ships)
        for i in range(n):
            for j in range(i+1, n):
                dist_cpa, t_cpa = compute_cpa_and_tcpa(self.ships[i], self.ships[j])
                if dist_cpa < 2.1 * self.safe_distance:
                    pairs.append((dist_cpa, t_cpa, i, j))
        pairs.sort(key=lambda x: (x[1], x[0]))  # sort by t_cpa, then dist_cpa
        return pairs

    def apply_multi_ship_starboard(self, ship, stand_on=False, debug=False):
        base_heading = ship.heading
        if stand_on:
            max_range = min(self.heading_search_range, 10.0)
        else:
            max_range = self.heading_search_range

        # how many degrees remain for starboard in this step
        remaining_turn = max_range - ship.heading_adjusted
        if remaining_turn <= 0:
            if debug:
                print(f"   {ship.name} has no remaining turn allowed (stand_on={stand_on}).")
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
            msg = f"{ship.name} turned starboard {best_offset:.1f} deg => new heading={new_heading:.1f}"
            self.ui_log.append(msg)
            if debug:
                print("   " + msg + f", CPA {current_cpa:.3f} -> {best_cpa:.3f}")
            return True

        if debug:
            print(f"   {ship.name} no offset improves CPA (stand_on={stand_on}).")
        return False

    def compute_min_cpa_over_others(self, give_ship, test_heading):
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
        Gradually revert 'ship.heading' toward ship.compute_heading_to_destination(),
        but do not exceed heading_search_range in one step.
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
        return all(s.distance_to_destination() < self.destination_threshold
                   for s in self.ships)

    def get_collisions_with_roles(self):
        results = []
        collisions = self.detect_collisions()
        for dist_cpa, t_cpa, i, j in collisions:
            if dist_cpa >= 2.1 * self.safe_distance:
                continue
            shipA = self.ships[i]
            shipB = self.ships[j]
            encounter = classify_encounter(shipA, shipB)
            roleA, roleB = self.assign_roles(shipA, shipB, encounter)
            results.append((dist_cpa, i, j, encounter, roleA, roleB))
        return results

    def assign_roles(self, shipA, shipB, encounter_type):
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
