# ui/canvas_interaction.py
import streamlit as st
from PIL import Image
from io import BytesIO
from streamlit_drawable_canvas import st_canvas
# Import custom modules
from core.drawing_primitives import draw_origin_dot, get_object_id
from core.geometry_utils import calculate_vector_properties_from_line, convert_polar_to_cartesian
from core.data_models import Vector
from core.config import MAX_CANVAS_WIDTH, DEFAULT_CANVAS_HEIGHT, BASE_MAGNITUDE_TO_PIXEL_SCALE # Keep BASE_MAGNITUDE_TO_PIXEL_SCALE for now as a fallback/default
from core.session_manager import increment_canvas_reset_key # Still needed for increments triggered by app_equilibrium/resultant


def handle_force_drawing_input(W: int, H: int, origin: tuple, bg_image: Image.Image):
    """
    Manages the main force drawing canvas for users to draw force vectors.
    It captures drawn lines, converts them to Vector objects, and updates the session state
    to reflect the new force, triggering a rerun if a new line is drawn.
    If it's the first vector drawn and a user-defined scale is not active, it will prompt
    the user to define a scale.

    Args:
        W (int): Width of the canvas in pixels.
        H (int): Height of the canvas in pixels.
        origin (tuple): (x, y) coordinates of the current origin point on the canvas.
        bg_image (PIL.Image.Image): The background image for the canvas.
    """
    if st.session_state.debug_mode: st.info(f"DEBUG: handle_force_drawing_input() - START. canvas_reset: {st.session_state.canvas_reset}, trigger_rerun: {st.session_state.trigger_rerun_after_logic}") # Debug message
    st.subheader("1️⃣ Draw Force Vectors (from origin)")

    current_canvas_image = bg_image.copy()
    current_canvas_image = draw_origin_dot(current_canvas_image, origin)

    # Display the main drawable canvas.
    res = st_canvas(
        fill_color="",                # No fill for lines
        stroke_width=4,               # Thickness of the drawn line
        stroke_color="orange",        # Color of the drawn line
        background_image=current_canvas_image, # The image drawn with origin
        height=H, width=W,            # Dimensions of the canvas
        drawing_mode="line",          # Only allow drawing lines
        key=f"vector-canvas-{st.session_state.canvas_reset}" # Unique key to force canvas refresh
    )

    if res.json_data: # Check if json_data (containing drawn objects) is not None
        if st.session_state.debug_mode: st.info(f"DEBUG: Raw json_data from main canvas: {res.json_data}") # Debug: Show raw data from canvas

        all_lines_on_canvas = [o for o in res.json_data.get("objects", []) if o.get("type")=="line"]

        if all_lines_on_canvas:
            latest_canvas_line = all_lines_on_canvas[-1]
            current_line_id = get_object_id(latest_canvas_line)

            # Check if this specific line has already been processed in a previous rerun.
            if current_line_id != st.session_state.last_processed_drawable_object_id:
                st.session_state.last_processed_drawable_object_id = current_line_id
                if st.session_state.debug_mode: st.info(f"DEBUG: New line detected in handle_force_drawing_input. ID: {current_line_id}") # Debug message

                o = latest_canvas_line
                raw_x0, raw_y0, raw_x1, raw_y1 = o["x1"], o["y1"], o["x2"], o["y2"]

                dx, dy, drawn_length, angle_degrees_normalized = \
                    calculate_vector_properties_from_line(raw_x0, raw_y0, raw_x1, raw_y1)

                new_vector = Vector(
                    angle=angle_degrees_normalized,
                    magnitude=None, # Revert to None to allow for unknown magnitudes
                    drawn_length=drawn_length,
                )
                st.session_state.vectors.append(new_vector)

                # --- START OF ADDITION FOR USER-DEFINED SCALE ---
                # If this is the first vector drawn AND no user-defined scale is active,
                # set it as the reference vector for scale definition.
                if len(st.session_state.vectors) == 1 and not st.session_state.user_defined_scale_active:
                    st.session_state.reference_drawn_length = drawn_length
                    # We will prompt the user to enter reference_magnitude in force_properties_ui.py
                    # For now, reference_magnitude remains None until user input.
                # --- END OF ADDITION ---

                # Request a script rerun via the centralized flag.
                st.session_state.trigger_rerun_after_logic = True
                if st.session_state.debug_mode: st.info(f"DEBUG: handle_force_drawing_input: Set trigger_rerun_after_logic to True after new line.") # Debug message
    if st.session_state.debug_mode: st.info(f"DEBUG: handle_force_drawing_input() - END. canvas_reset: {st.session_state.canvas_reset}, trigger_rerun: {st.session_state.trigger_rerun_after_logic}") # Debug message


def render_origin_pick_canvas(W: int, H: int, bg_image):
    """
    Renders a temporary canvas for picking origin. Should be called in the main area, not sidebar.
    """
    st.subheader("Click on the canvas to select new origin:")
    
    # If a background image exists, use it
    temp_img = bg_image.copy()
    if st.session_state.origin:
        temp_img = draw_origin_dot(temp_img, st.session_state.origin)

    result = st_canvas(
        fill_color="deepskyblue",
        stroke_width=16,
        stroke_color="deepskyblue",
        background_image=temp_img,
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