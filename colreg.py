import math
import numpy as np
from ship import *

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