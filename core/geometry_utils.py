# geometry_utils.py
import math

def calculate_vector_properties_from_line(x1: float, y1: float, x2: float, y2: float) -> tuple:
    """
    Calculates the dx, dy, drawn length, and angle (in degrees, 0-360°)
    from a line defined by two pixel coordinates.

    Args:
        x1 (float): X-coordinate of the line's start point.
        y1 (float): Y-coordinate of the line's start point.
        x2 (float): X-coordinate of the line's end point.
        y2 (float): Y-coordinate of the line's end point.

    Returns:
        tuple: (dx, dy, drawn_length, angle_degrees_normalized)
    """
    dx = x2 - x1
    dy = y2 - y1 # This dy is positive for downwards movement in pixel coordinates

    drawn_length = math.hypot(dx, dy)

    # Calculate angle. math.atan2(y, x) correctly handles all four quadrants.
    # CRITICAL: We use -dy because the canvas Y-axis is inverted (positive is down).
    # We want a standard mathematical angle where positive Y is up.
    if dx == 0 and dy == 0: # Handle zero-length vectors
        angle_radians = 0.0
    else:
        angle_radians = math.atan2(-dy, dx) # -dy to convert from screen Y-down to math Y-up

    angle_degrees = math.degrees(angle_radians)
    angle_degrees_normalized = normalize_angle_degrees(angle_degrees)

    return dx, dy, drawn_length, angle_degrees_normalized

def convert_polar_to_cartesian(magnitude: float, angle_degrees: float) -> tuple:
    """
    Converts a vector from polar coordinates (magnitude, angle in degrees)
    to Cartesian components (Fx, Fy).

    Args:
        magnitude (float): The magnitude of the vector.
        angle_degrees (float): The angle of the vector in degrees (0-360°).

    Returns:
        tuple: (Fx, Fy)
    """
    angle_radians = math.radians(angle_degrees)
    fx = magnitude * math.cos(angle_radians)
    fy = magnitude * math.sin(angle_radians)
    return fx, fy

def normalize_angle_degrees(angle_degrees: float) -> float:
    """
    Normalizes an angle to the 0-360 degree range.

    Args:
        angle_degrees (float): The angle in degrees.

    Returns:
        float: The normalized angle in degrees (0 <= angle < 360).
    """
    normalized_angle = angle_degrees % 360
    if normalized_angle < 0:
        normalized_angle += 360
    return normalized_angle

def normalize_angle_radians(angle_radians: float) -> float:
    """
    Normalizes an angle to the 0 to 2*pi radian range.

    Args:
        angle_radians (float): The angle in radians.

    Returns:
        float: The normalized angle in radians (0 <= angle < 2*pi).
    """
    normalized_angle = angle_radians % (2 * math.pi)
    if normalized_angle < 0:
        normalized_angle += (2 * math.pi)
    return normalized_angle
