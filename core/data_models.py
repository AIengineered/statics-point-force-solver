# core/data_models.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class Vector:
    """
    Represents a force vector with its physical properties and drawing-related length.

    Attributes:
        angle (float | None): The angle of the vector in degrees (0-360° range).
                                None if the angle is unknown (e.g., for a symbolic solve).
        magnitude (float | None): The magnitude of the vector.
                                    None if the magnitude is unknown (e.g., for a symbolic solve).
        drawn_length (float): The pixel length of the vector as initially drawn on the canvas.
                                Used as a visual hint for the user to input magnitude.
        # Removed fx and fy, as they are derived and can lead to display inconsistencies for unknowns.
        # The solver calculates components directly from magnitude and angle.
    """
    angle: Optional[float]
    magnitude: Optional[float]
    drawn_length: float
    # fx: Optional[float] = None # REMOVED
    # fy: Optional[float] = None # REMOVED