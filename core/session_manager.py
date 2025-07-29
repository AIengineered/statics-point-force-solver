# concurrent_force_solver/core/session_manager.py
import streamlit as st
import copy # Added for push_to_history
from core.data_models import Vector # Assuming core.data_models exists and is correctly imported

def initialize_common_session_state():
    """
    Initializes common Streamlit session state variables if they don't already exist.
    This function should be called once at the beginning of each main application script
    to ensure all necessary state variables are defined.
    """
    # --- Initialize debug_mode FIRST within initialize_common_session_state ---
    # Ensure all keys are checked individually for "not in st.session_state"
    # This prevents an AttributeError when a key is accessed before it's set.
    
    if "debug_mode" not in st.session_state:
        st.session_state.debug_mode = False # Default to False for production (You confirmed this change)
    
    # Only run debug info if debug_mode is now set and True
    if st.session_state.debug_mode: st.info("DEBUG: initialize_common_session_state() - START")

    if "vectors" not in st.session_state:
        st.session_state.vectors = []
    if "bg_image_bytes" not in st.session_state:
        st.session_state.bg_image_bytes = None
    if "canvas_reset" not in st.session_state:
        st.session_state.canvas_reset = 0
    if "origin" not in st.session_state:
        st.session_state.origin = None
    if "pick_origin_mode" not in st.session_state:
        st.session_state.pick_origin_mode = False
    if "last_uploaded_filename" not in st.session_state:
        st.session_state.last_uploaded_filename = None
    if "last_solve_click" not in st.session_state:
        st.session_state.last_solve_click = False
    if "debug_last_vector_info" not in st.session_state:
        st.session_state.debug_last_vector_info = ""
    if "last_processed_drawable_object_id" not in st.session_state:
        st.session_state.last_processed_drawable_object_id = None
    if "raw_uploaded_file" not in st.session_state:
        st.session_state.raw_uploaded_file = None
    if "user_defined_scale_active" not in st.session_state:
        st.session_state.user_defined_scale_active = False
    if "reference_drawn_length" not in st.session_state:
        st.session_state.reference_drawn_length = None
    if "reference_magnitude" not in st.session_state:
        st.session_state.reference_magnitude = None
    if "calculated_pixel_to_unit_scale" not in st.session_state:
        st.session_state.calculated_pixel_to_unit_scale = None
    if "vector_history" not in st.session_state:
        st.session_state.vector_history = []
    if "undo_requested" not in st.session_state:
        st.session_state.undo_requested = False
    if "redo_requested" not in st.session_state:
        st.session_state.redo_requested = False
    # This key MUST be initialized here
    if "trigger_rerun_after_logic" not in st.session_state:
        st.session_state.trigger_rerun_after_logic = False


    if st.session_state.debug_mode: st.info(f"DEBUG: initialize_common_session_state() - END. canvas_reset: {st.session_state.canvas_reset}")

def reset_all_app_state(preserve_keys=None):
    """
    Reset all Streamlit session state variables, preserving specified keys,
    then re-initializes all common state variables to ensure consistency.
    """
    # Always ensure debug_mode is available for logging within this function
    if "debug_mode" not in st.session_state:
        st.session_state.debug_mode = False # Set temporary default if not initialized

    if st.session_state.debug_mode: st.info("DEBUG: reset_all_app_state() - START")

    keys_to_actually_preserve = [
        "bg_image_bytes",
        "last_uploaded_filename",
        "debug_mode",
        "user_defined_scale_active",
        "reference_drawn_length",
        "reference_magnitude",
        "calculated_pixel_to_unit_scale",
        "trigger_rerun_after_logic", # Ensure this is also preserved if needed during resets
        # We need to preserve 'origin' if user sets it manually, otherwise it defaults.
        # However, reset_all_app_state is usually for a full reset including origin,
        # unless specifically passed in `preserve_keys`. Let's ensure initialize
        # sets a default origin if it's cleared.
    ]

    if preserve_keys:
        keys_to_actually_preserve.extend([k for k in preserve_keys if k not in keys_to_actually_preserve])

    preserved_values = {k: st.session_state[k] for k in keys_to_actually_preserve if k in st.session_state}

    st.session_state.clear() # Clear ALL session state variables

    initialize_common_session_state() # Re-initialize all common session state variables

    for k, v in preserved_values.items():
        st.session_state[k] = v # Restore only the explicitly preserved values

    if st.session_state.debug_mode: st.info("DEBUG: reset_all_app_state() - END. Preserved keys restored and all state re-initialized.")

def increment_canvas_reset_key():
    st.session_state.canvas_reset += 1
    if st.session_state.debug_mode: st.info(f"DEBUG: increment_canvas_reset_key() called. New canvas_reset: {st.session_state.canvas_reset}")

def push_to_history():
    # import copy # Already imported at top level of module
    if 'vector_history' not in st.session_state:
        st.session_state.vector_history = []
    st.session_state.vector_history.append(copy.deepcopy(st.session_state.vectors))

def undo_last_action():
    if st.session_state.vector_history:
        st.session_state.vectors = st.session_state.vector_history.pop()