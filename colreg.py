# colreg.py
"""
COLREG Helper Functions

This module provides helper functions for the SeaSafe Simulator to calculate collision-related parameters
and to classify ship encounters in compliance with the International Regulations for Preventing Collisions at Sea (COLREG).
Functions include computation of the Closest Point of Approach (CPA) and Time to CPA (TCPA), calculation of relative bearings,
classification of encounters (head-on, overtaking, crossing), and determining if one ship is on the starboard side of another.
"""

import math
import numpy as np
from ship import *  # Import all from ship module (Ship class and related functions)

def compute_cpa_and_tcpa(shipA, shipB):
    """
    Compute the Closest Point of Approach (CPA) distance and the time to CPA (TCPA) between two ships.

    Parameters:
        shipA (Ship): The first ship.
        shipB (Ship): The second ship.

    Returns:
        tuple: (dist_cpa, t_cpa)
            - dist_cpa (float): The distance at CPA (in Nautical Miles).
            - t_cpa (float): The time until CPA (in hours). If t_cpa < 0 (i.e., the CPA is in the past),
              it is clamped to 0.0.
    """
    pA = shipA.get_position_vector()
    vA = shipA.get_velocity_vector()
    pB = shipB.get_position_vector()
    vB = shipB.get_velocity_vector()

    r0 = pB - pA      # Relative position vector from shipA to shipB
    v_rel = vB - vA   # Relative velocity vector between the two ships
    denom = np.dot(v_rel, v_rel)

    # If relative velocity is nearly zero, the ships are moving parallelly.
    # In this case, the CPA is simply the current distance.
    if abs(denom) < 1e-9:
        dist_cpa = np.linalg.norm(r0)
        return dist_cpa, 0.0

    t_cpa = -np.dot(r0, v_rel) / denom
    if t_cpa < 0:
        t_cpa = 0.0

    r_cpa = r0 + v_rel * t_cpa  # Relative position at CPA
    dist_cpa = np.linalg.norm(r_cpa)
    return dist_cpa, t_cpa

def relative_bearing_degs(from_ship, to_ship):
    """
    Calculates the relative bearing from one ship to another.

    The relative bearing is defined in the range (-180, 180]:
      - 0° indicates that the target is directly ahead.
      - Positive angles indicate the target is to the port side.
      - Negative angles indicate the target is to the starboard side.

    Parameters:
        from_ship (Ship): The ship from whose perspective the bearing is calculated.
        to_ship (Ship): The target ship.

    Returns:
        float: The relative bearing in degrees.
    """
    dx = to_ship.x - from_ship.x
    dy = to_ship.y - from_ship.y
    angle_abs = math.degrees(math.atan2(dy, dx))  # Absolute angle from from_ship to to_ship.
    rel = angle_abs - from_ship.heading         # Relative angle considering from_ship's heading.
    # Normalize the relative angle to the interval (-180, 180].
    while rel > 180:
        rel -= 360
    while rel <= -180:
        rel += 360
    return rel

def classify_encounter(shipA, shipB):
    """
    Classifies the encounter between two ships based on their relative bearings.

    Classification rules:
      - 'head-on': Both ships see each other near 0° (i.e., almost directly ahead).
      - 'overtaking': At least one ship sees the other near 180°.
      - 'crossing': All other cases.

    Parameters:
        shipA (Ship): The first ship.
        shipB (Ship): The second ship.

    Returns:
        str: The encounter type ('head-on', 'overtaking', or 'crossing').
    """
    bearingAB = abs(relative_bearing_degs(shipA, shipB))
    bearingBA = abs(relative_bearing_degs(shipB, shipA))

    # Both ships see each other nearly directly ahead.
    if bearingAB < 12.5 and bearingBA < 12.5:
        return 'head-on'

    # At least one ship sees the other nearly 180° away.
    if (112.5 < bearingAB < 250) or (112.5 < bearingBA < 250):
        return 'overtaking'

    # All other cases are considered crossing encounters.
    return 'crossing'

def is_on_starboard_side(shipA, shipB):
    """
    Determines whether shipB is on the starboard side of shipA.

    In maritime navigation, for shipA, a negative relative bearing (between -112.5° and 0°)
    indicates that shipB is on the starboard side.

    Parameters:
        shipA (Ship): The reference ship.
        shipB (Ship): The target ship.

    Returns:
        bool: True if shipB is on the starboard side of shipA, False otherwise.
    """
    bearingAB = relative_bearing_degs(shipA, shipB)
    return -112.5 < bearingAB < 0
