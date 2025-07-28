# concurrent_force_solver/ui/force_properties_ui.py
import streamlit as st
import math
from typing import Optional

from core.data_models import Vector
from core.config import IDEAL_MANUAL_FORCE_PIXEL_LENGTH, BASE_MAGNITUDE_TO_PIXEL_SCALE


def render_force_properties_sidebar_content():
    """
    Renders the general instructions for forces and the individual force property inputs.
    The scale definition UI is now in render_drawing_scale_settings.
    """
    if st.session_state.debug_mode: st.info("DEBUG: render_force_properties_sidebar_content() - START")

    if not st.session_state.vectors:
        st.info("Draw a force vector on the canvas to get started.")
        if st.session_state.debug_mode: st.info("DEBUG: render_force_properties_sidebar_content() - END: No vectors to display.")
        return

    st.info("Enter known values for magnitude or angle. Leave blanks for unknowns to solve.")

    st.markdown("---") # Separator between general instruction and individual forces

    for i, vec_obj in enumerate(st.session_state.vectors):
        mag_display: Optional[str] = None
        angle_display: Optional[str] = None

        if isinstance(vec_obj.magnitude, (float, int)):
            mag_display = f"F{i+1}={vec_obj.magnitude:.1f}"
        else:
            mag_display = f"F{i+1}"

        if isinstance(vec_obj.angle, (float, int)):
            angle_display = f"θ{i+1}={vec_obj.angle:.0f}°"
        else:
            angle_display = f"θ{i+1}"

        col1, col2 = st.columns([0.8, 0.2])
        with col1:
             st.markdown(f"**{mag_display} @ {angle_display}**")
        with col2:
            if st.button("🗑️", key=f"delete_force_{i}"):
                st.session_state.vectors.pop(i)
                st.session_state.trigger_rerun_after_logic = True
                if st.session_state.debug_mode: st.info(f"DEBUG: Deleted force F{i+1}.")
                st.experimental_rerun()
        
        mag_value_str = "" if vec_obj.magnitude is None else str(vec_obj.magnitude)
        mag_input_str = st.text_input(
            f"Magnitude F{i+1}",
            value=mag_value_str,
            key=f"mag_str_{i}",
            label_visibility="collapsed",
        )
        
        angle_value_str = "" if vec_obj.angle is None else str(vec_obj.angle)
        angle_input_str = st.text_input(
            f"Angle θ{i+1} [deg]",
            value=angle_value_str,
            key=f"ang_str_{i}",
            label_visibility="collapsed",
        )
            
        trigger_rerun_for_input_change = False
        
        current_magnitude_obj = vec_obj.magnitude
        new_magnitude_val = None
        if mag_input_str.strip() != "":
            try:
                new_magnitude_val = float(mag_input_str)
            except ValueError:
                new_magnitude_val = mag_input_str.strip()

        if current_magnitude_obj != new_magnitude_val:
            vec_obj.magnitude = new_magnitude_val
            trigger_rerun_for_input_change = True

        current_angle_obj = vec_obj.angle
        new_angle_val = None
        if angle_input_str.strip() != "":
            try:
                new_angle_val = float(angle_input_str)
                new_angle_val = new_angle_val % 360
                if new_angle_val < 0:
                    new_angle_val += 360
            except ValueError:
                new_angle_val = angle_input_str.strip()

        if current_angle_obj != new_angle_val:
            vec_obj.angle = new_angle_val
            trigger_rerun_for_input_change = True

        if trigger_rerun_for_input_change:
            if st.session_state.debug_mode: st.info(f"DEBUG: F{i+1} input changed. Triggering rerun.")
            st.session_state.trigger_rerun_after_logic = True
        
        if i < len(st.session_state.vectors) - 1:
            st.markdown("---")

    if st.session_state.debug_mode: st.info("DEBUG: render_force_properties_sidebar_content() - END")


# THIS FUNCTION IS AT THE TOP-LEVEL SCOPE
def render_drawing_scale_settings():
    """
    Renders the UI for defining and adjusting the drawing scale.
    This function is designed to be called within a larger section (e.g., an expander).
    It no longer provides its own subheaders, as the calling context will do so.
    """
    if st.session_state.debug_mode: st.info("DEBUG: render_drawing_scale_settings() - START")

    # If no user-defined scale is active, try to define one or give guidance.
    if not st.session_state.user_defined_scale_active:
        st.info("The drawing scale will be automatically defined by the first force (F1) you draw or add manually once its magnitude is entered.")
        
        # Only proceed to try and auto-set scale if there's at least one vector
        if st.session_state.vectors and len(st.session_state.vectors) >= 1:
            f1_vec_obj = st.session_state.vectors[0]
            
            # Check if F1 has a numeric, positive magnitude to set scale
            if isinstance(f1_vec_obj.magnitude, (float, int)) and f1_vec_obj.magnitude > 0: 
                
                # Case A: F1 was DRAWN (reference_drawn_length is set and positive)
                if st.session_state.reference_drawn_length is not None and st.session_state.reference_drawn_length > 0:
                    st.session_state.reference_magnitude = f1_vec_obj.magnitude
                    st.session_state.calculated_pixel_to_unit_scale = \
                        st.session_state.reference_drawn_length / st.session_state.reference_magnitude
                    st.session_state.user_defined_scale_active = True
                    st.session_state.trigger_rerun_after_logic = True
                    if st.session_state.debug_mode: st.info(f"DEBUG: Scale auto-set from DRAWN F1: {st.session_state.calculated_pixel_to_unit_scale:.3f} pixels/unit")
                
                # Case B: F1 was MANUALLY ADDED (drawn_length is 0.0)
                elif f1_vec_obj.drawn_length == 0.0:
                    st.session_state.reference_drawn_length = IDEAL_MANUAL_FORCE_PIXEL_LENGTH 
                    st.session_state.reference_magnitude = f1_vec_obj.magnitude
                    # Recalculate based on IDEAL_MANUAL_FORCE_PIXEL_LENGTH
                    st.session_state.calculated_pixel_to_unit_scale = \
                        IDEAL_MANUAL_FORCE_PIXEL_LENGTH / f1_vec_obj.magnitude
                    st.session_state.user_defined_scale_active = True
                    st.session_state.trigger_rerun_after_logic = True
                    if st.session_state.debug_mode: st.info(f"DEBUG: Scale auto-set from MANUAL F1 (using {IDEAL_MANUAL_FORCE_PIXEL_LENGTH}px): {st.session_state.calculated_pixel_to_unit_scale:.3f} pixels/unit")
            
            # This 'else' block provides guidance when F1 has no valid positive magnitude yet.
            else: # F1 magnitude is not positive number (None, 0, non-numeric)
                if f1_vec_obj.drawn_length == 0.0:
                    st.info(f"F1 was added manually. Enter a positive magnitude to set the drawing scale (e.g., if F1=100 units, it will be displayed at {IDEAL_MANUAL_FORCE_PIXEL_LENGTH} pixels).")
                elif st.session_state.reference_drawn_length is not None and st.session_state.reference_drawn_length > 0:
                     st.info(f"F1 was drawn with length: {st.session_state.reference_drawn_length:.1f} pixels. Enter its positive magnitude.")
        # else: No vectors yet, initial message above suffices
                
    else: # User-defined scale IS active, so render the number_input for adjustment
        current_scale_px_per_unit = st.session_state.get("calculated_pixel_to_unit_scale")
        
        # SAFEGARD: Ensure current_scale_px_per_unit is a valid positive number before using it as value in st.number_input
        if current_scale_px_per_unit is None or current_scale_px_per_unit <= 0:
            # Fallback if the scale somehow became invalid while user_defined_scale_active is True
            st.warning("Detected an invalid scale value. Resetting to default base scale for adjustment.")
            current_scale_px_per_unit = BASE_MAGNITUDE_TO_PIXEL_SCALE 
            st.session_state.calculated_pixel_to_unit_scale = BASE_MAGNITUDE_TO_PIXEL_SCALE # Correct the session state
            st.session_state.user_defined_scale_active = False # Revert to non-active state for better flow
            st.session_state.trigger_rerun_after_logic = True
            return # Rerun will fix the state, so exit this run
            
        new_scale_px_per_unit = st.number_input(
            "Pixels per Unit (Px/Unit)",
            value=float(current_scale_px_per_unit), # Ensure float value
            min_value=0.01, # Prevent division by zero and extremely tiny scales
            format="%.2f",
            key="manual_scale_input" # Consistent key
        )

        if new_scale_px_per_unit != current_scale_px_per_unit:
            st.session_state.calculated_pixel_to_unit_scale = new_scale_px_per_unit
            st.session_state.trigger_rerun_after_logic = True
            if st.session_state.debug_mode: st.info(f"DEBUG: User manually set scale to: {new_scale_px_per_unit:.2f} pixels/unit")

        # Display the scale's inverse for clarity
        if st.session_state.calculated_pixel_to_unit_scale is not None and st.session_state.calculated_pixel_to_unit_scale > 0:
             st.success(f"Current Scale: 1 unit = {1/st.session_state.calculated_pixel_to_unit_scale:.2f} pixels.")
        else:
             st.warning("Invalid scale value. Please set a positive 'Pixels per Unit'.")

        if st.button("Reset Scale", key="reset_scale_btn"): # Consistent key
            st.session_state.user_defined_scale_active = False
            st.session_state.reference_drawn_length = None
            st.session_state.reference_magnitude = None
            st.session_state.calculated_pixel_to_unit_scale = None
            st.session_state.trigger_rerun_after_logic = True
            if st.session_state.debug_mode: st.info("DEBUG: User-defined scale reset.")
    
    if st.session_state.debug_mode: st.info("DEBUG: render_drawing_scale_settings() - END")