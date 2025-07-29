# ui/canvas_interaction.py
import streamlit as st
from PIL import Image
from io import BytesIO # Keep for consistency, though not used in st_canvas arg here
from streamlit_drawable_canvas import st_canvas
from typing import Optional, Union # <--- ADDED: Import Union for type hinting


# Import custom modules
from core.drawing_primitives import draw_origin_dot, get_object_id
from core.geometry_utils import calculate_vector_properties_from_line, convert_polar_to_cartesian
from core.data_models import Vector
from core.config import MAX_CANVAS_WIDTH, DEFAULT_CANVAS_HEIGHT, BASE_MAGNITUDE_TO_PIXEL_SCALE
from core.session_manager import increment_canvas_reset_key


# Modified function signature to accept `bg_image_for_st_canvas` as the processed PIL Image
def handle_force_drawing_input(W: int, H: int, origin: tuple, bg_image_for_st_canvas: Image.Image):
    """
    Manages the main force drawing canvas for users to draw force vectors.
    Args:
        W (int): Width of the canvas in pixels.
        H (int): Height of the canvas in pixels.
        origin (tuple): (x, y) coordinates of the current origin point on the canvas.
        bg_image_for_st_canvas (PIL.Image.Image): The pre-processed PIL Image to use as background.
    """
    # No debug messages are enabled unless st.session_state.debug_mode is True, set in config.py
    if st.session_state.debug_mode: st.info(f"DEBUG: handle_force_drawing_input() - START. canvas_reset: {st.session_state.canvas_reset}, trigger_rerun: {st.session_state.trigger_rerun_after_logic}")
    st.subheader("1️⃣ Draw Force Vectors (from origin)")

    # Use the passed bg_image_for_st_canvas, which is already a clean PIL Image
    current_canvas_image_with_origin = draw_origin_dot(bg_image_for_st_canvas.copy(), origin)

    # Display the main drawable canvas.
    res = st_canvas(
        fill_color="",                # No fill for lines
        stroke_width=4,               # Thickness of the drawn line
        stroke_color="orange",        # Color of the drawn line
        background_image=current_canvas_image_with_origin, # <--- Pass the PIL Image directly
        # DO NOT provide 'background_color' if using 'background_image' for this component version (0.9.3)
        height=H, width=W,            # Dimensions of the canvas
        drawing_mode="line",          # Only allow drawing lines
        key=f"vector-canvas-{st.session_state.canvas_reset}" # Unique key to force canvas refresh
    )

    if res.json_data:
        if st.session_state.debug_mode: st.info(f"DEBUG: Raw json_data from main canvas: {res.json_data}")

        all_lines_on_canvas = [o for o in res.json_data.get("objects", []) if o.get("type")=="line"]

        if all_lines_on_canvas:
            latest_canvas_line = all_lines_on_canvas[-1]
            current_line_id = get_object_id(latest_canvas_line)

            if current_line_id != st.session_state.last_processed_drawable_object_id:
                st.session_state.last_processed_drawable_object_id = current_line_id
                if st.session_state.debug_mode: st.info(f"DEBUG: New line detected in handle_force_drawing_input. ID: {current_line_id}")

                o = latest_canvas_line
                raw_x0, raw_y0, raw_x1, raw_y1 = o["x1"], o["y1"], o["x2"], o["y2"]

                dx, dy, drawn_length, angle_degrees_normalized = \
                    calculate_vector_properties_from_line(raw_x0, raw_y0, raw_x1, raw_y1)

                new_vector = Vector(
                    angle=angle_degrees_normalized,
                    magnitude=None,
                    drawn_length=drawn_length,
                )
                st.session_state.vectors.append(new_vector)

                if len(st.session_state.vectors) == 1 and not st.session_state.user_defined_scale_active:
                    st.session_state.reference_drawn_length = drawn_length
                
                st.session_state.trigger_rerun_after_logic = True
                if st.session_state.debug_mode: st.info(f"DEBUG: handle_force_drawing_input: Set trigger_rerun_after_logic to True after new line.")
    if st.session_state.debug_mode: st.info(f"DEBUG: handle_force_drawing_input() - END. canvas_reset: {st.session_state.canvas_reset}, trigger_rerun: {st.session_state.trigger_rerun_after_logic}")


# Modified function signature to accept `bg_image_for_st_canvas`
def render_origin_pick_canvas(W: int, H: int, bg_image_for_st_canvas: Image.Image):
    """
    Renders a temporary canvas for picking origin. Should be called in the main area, not sidebar.
    Args:
        W (int): Width of the canvas in pixels.
        H (int): Height of the canvas in pixels.
        bg_image_for_st_canvas (PIL.Image.Image): The pre-processed PIL Image to use as background.
    """
    st.subheader("Click on the canvas to select new origin:")
    
    # Use the passed bg_image_for_st_canvas, which is already a clean PIL Image
    temp_img_with_origin = draw_origin_dot(bg_image_for_st_canvas.copy(), st.session_state.origin)

    result = st_canvas(
        fill_color="deepskyblue",
        stroke_width=16,
        stroke_color="deepskyblue",
        background_image=temp_img_with_origin, # <--- Pass the PIL Image directly
        # DO NOT provide 'background_color' if using 'background_image' for this component version (0.9.3)
        update_streamlit=True,
        height=H,
        width=W,
        drawing_mode="point",
        key=f"pick-origin-canvas-{st.session_state.canvas_reset}"
    )

    if result.json_data and result.json_data.get("objects"):
        new_obj = result.json_data["objects"][-1]
        current_id = get_object_id(new_obj)
        if current_id != st.session_state.last_processed_drawable_object_id:
            st.session_state.last_processed_drawable_object_id = current_id

            if new_obj.get("type") == "point":
                st.session_state.origin = (new_obj["x"], new_obj["y"])
            elif new_obj.get("type") == "circle":
                st.session_state.origin = (new_obj["left"] + new_obj["radius"], new_obj["top"] + new_obj["radius"])

            st.session_state.pick_origin_mode = False
            st.session_state.trigger_rerun_after_logic = True

def handle_origin_selection_ui(W: int, H: int):
    """
    Places sidebar buttons for origin control without rendering the canvas in the sidebar.
    Origin selection canvas is instead handled in the main area.
    """
    if st.sidebar.button("📍 Pick Origin on Canvas"):
        st.session_state.pick_origin_mode = True
        st.session_state.last_processed_drawable_object_id = None
        st.session_state.trigger_rerun_after_logic = True

    if st.sidebar.button("🎯 Reset Origin to Center"):
        st.session_state.origin = (W // 2, H // 2)
        st.session_state.pick_origin_mode = False
        st.session_state.trigger_rerun_after_logic = True