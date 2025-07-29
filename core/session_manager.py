# concurrent_force_solver/core/session_manager.py
import streamlit as st
from core.data_models import Vector # Assuming core.data_models exists and is correctly imported

def initialize_common_session_state():
    """
    Initializes common Streamlit session state variables if they don't already exist.
    This function should be called once at the beginning of each main application script
    to ensure all necessary state variables are defined.
    """
    # --- Initialize debug_mode FIRST within initialize_common_session_state ---
    if "debug_mode" not in st.session_state:
        st.session_state.debug_mode = False # Default to False for production
    # --- End of debug_mode initialization ---

    if st.session_state.debug_mode: st.info("DEBUG: initialize_common_session_state() - START") # Debug message
    if "vectors" not in st.session_state:
        # Stores list of Vector objects representing forces drawn by the user.
        st.session_state.vectors = []
    if "bg_image_bytes" not in st.session_state:
        # Stores uploaded background image as bytes for display on canvas.
        st.session_state.bg_image_bytes = None
    if "canvas_reset" not in st.session_state:
        # Counter used as a key for st_canvas. Incrementing this forces st_canvas to re-initialize,
        # effectively clearing its drawn content.
        st.session_state.canvas_reset = 0 # Starting value for the key
    if "origin" not in st.session_state:
        # Stores the (x, y) pixel coordinates of the user-defined origin on the canvas.
        st.session_state.origin = None
    if "pick_origin_mode" not in st.session_state:
        # Boolean flag to indicate if the user is currently in origin selection mode.
        st.session_state.pick_origin_mode = False
    if "last_uploaded_filename" not in st.session_state:
        # Stores the name of the last successfully processed uploaded file.
        # Used to prevent reprocessing the same file on subsequent reruns.
        st.session_state.last_uploaded_filename = None
    if "last_solve_click" not in st.session_state:
        # Boolean flag to indicate if the "Solve" button was clicked, controlling solve results display.
        st.session_state.last_solve_click = False
    if "debug_last_vector_info" not in st.session_state:
        # String to store and display debug information about the most recently drawn vector.
        st.session_state.debug_last_vector_info = ""
    if "last_processed_drawable_object_id" not in st.session_state:
        # Stores a unique ID of the last drawn/picked object from st_canvas to prevent duplicate processing.
        st.session_state.last_processed_drawable_object_id = None
    if "raw_uploaded_file" not in st.session_state:
        # Stores the actual st.UploadedFile object returned by st.file_uploader.
        # This helps manage the file's state across reruns, especially with Streamlit 1.25.0 quirks.
        st.session_state.raw_uploaded_file = None
    # --- START OF ADDITIONS FOR USER-DEFINED SCALE ---
    if "user_defined_scale_active" not in st.session_state:
        st.session_state.user_defined_scale_active = False # Flag if user-defined scale is active
    if "reference_drawn_length" not in st.session_state:
        st.session_state.reference_drawn_length = None # Drawn length (pixels) of the reference vector
    if "reference_magnitude" not in st.session_state:
        st.session_state.reference_magnitude = None # User-input magnitude of the reference vector
    if "calculated_pixel_to_unit_scale" not in st.session_state:
        st.session_state.calculated_pixel_to_unit_scale = None # The derived scale (pixels/unit)
    # --- END OF ADDITIONS ---
    if st.session_state.debug_mode: st.info(f"DEBUG: initialize_common_session_state() - END. canvas_reset: {st.session_state.canvas_reset}") # Debug message

def reset_all_app_state(preserve_keys=None):
    """
    Reset all Streamlit session state variables, preserving specified keys,
    then re-initializes all common state variables to ensure consistency.

    Args:
        preserve_keys (list of str): Keys to keep in session_state.
            Defaults to commonly used keys like uploaded image and debug mode.
    """
    # Always ensure debug_mode is available for logging within this function
    # This prevents AttributeError if reset_all_app_state is called very early
    # or after a full st.session_state.clear() by external factors.
    if "debug_mode" not in st.session_state:
        st.session_state.debug_mode = False

    if st.session_state.debug_mode: st.info("DEBUG: reset_all_app_state() - START")

    # Define the truly essential keys to preserve across a full reset.
    # Other variables will be re-initialized to their defaults by initialize_common_session_state().
    keys_to_actually_preserve = [
        "bg_image_bytes",
        "last_uploaded_filename",
        "debug_mode", # Always preserve debug_mode
        # --- ADDITIONS FOR USER-DEFINED SCALE ---
        "user_defined_scale_active",
        "reference_drawn_length",
        "reference_magnitude",
        "calculated_pixel_to_unit_scale",
        # --- END OF ADDITIONS ---
    ]

    # Combine user-specified preserve_keys with our essential ones, avoiding duplicates
    if preserve_keys:
        keys_to_actually_preserve.extend([k for k in preserve_keys if k not in keys_to_actually_preserve])

    # Save the values of the keys we intend to preserve
    preserved_values = {k: st.session_state[k] for k in keys_to_actually_preserve if k in st.session_state}

    # Clear ALL session state variables
    st.session_state.clear()

    # Re-initialize all common session state variables to their default values
    # This ensures that all expected keys (like 'vectors', 'canvas_reset', etc.) are present
    initialize_common_session_state()

    # Restore only the explicitly preserved values
    for k, v in preserved_values.items():
        st.session_state[k] = v

    if st.session_state.debug_mode: st.info("DEBUG: reset_all_app_state() - END. Preserved keys restored and all state re-initialized.")

def increment_canvas_reset_key():
    """
    Increments the `canvas_reset` session state variable.
    This function should be called when a state change (like new image, clearing canvas)
    requires the `st_canvas` widget to be re-initialized and clear its internal state.
    """
    st.session_state.canvas_reset += 1
    if st.session_state.debug_mode: st.info(f"DEBUG: increment_canvas_reset_key() called. New canvas_reset: {st.session_state.canvas_reset}")

def push_to_history():
    import copy
    if 'vector_history' not in st.session_state:
        st.session_state.vector_history = []
    st.session_state.vector_history.append(copy.deepcopy(st.session_state.vectors))

def undo_last_action():
    if st.session_state.vector_history:
        st.session_state.vectors = st.session_state.vector_history.pop()