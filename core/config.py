# app_config.py

# --- Debugging ---
DEBUG_MODE = True # Set to True to enable debug messages (st.info)

# --- Application Titles ---
# Titles for the two separate Streamlit applications.
PAGE_TITLE_EQUILIBRIUM = "Equilibrium of Concurrent Forces Calculator"
PAGE_TITLE_RESULTANT = "Resultant of Concurrent Forces Calculator"

# --- Canvas Dimensions ---
# Maximum width for the drawing canvas to ensure it fits well on most screens.
MAX_CANVAS_WIDTH = 725
# Default height for the drawing canvas when no background image is uploaded.
DEFAULT_CANVAS_HEIGHT = 500

# --- Drawing & Scaling Constants ---
# Base factor to convert force magnitude units into pixels for drawing diagrams.
# E.g., if 100 units = 50 pixels, then this is 0.5 pixels/unit.
# NOTE: This scale is used when no user-defined scale is active.
# With MAX_CANVAS_WIDTH=725 and DEFAULT_CANVAS_HEIGHT=500,
# using this scale directly can lead to very large forces extending off-canvas.
# The auto-fitting logic (fit_scale in diagram_renderer) will heavily scale down
# diagrams with a wide range of magnitudes, potentially making smaller vectors tiny.
BASE_MAGNITUDE_TO_PIXEL_SCALE = 50.0

# Ideal pixel length for the first manually added force when it defines the scale.
# If you enter a magnitude for F1 (added via button), its drawn length will conceptually
# be this value, and the 'pixels/unit' scale will be derived as (this value / F1 magnitude).
# This helps ensure manually defined scales are visually sensible.
IDEAL_MANUAL_FORCE_PIXEL_LENGTH = 100.0

# Padding (in pixels) around the force polygon when auto-fitting it within the canvas.
POLYGON_PADDING = 20
# Visual tolerance (in pixels) for checking if a force polygon "closes" perfectly.
# If the closing gap is smaller than this, it's considered closed.
CLOSURE_TOLERANCE_PIXELS = 0.5

# --- Solver Constants ---
# Numerical tolerance for treating a calculated floating-point value as effectively zero.
# Used to check for equilibrium conditions.
NUMERIC_ZERO_TOLERANCE = 1e-6