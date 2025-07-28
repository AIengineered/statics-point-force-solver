# concurrent_force_solver/renderer/diagram_renderer.py
import streamlit as st
from PIL import Image, ImageDraw # ADD Image here
import math
from typing import List, Dict, Any, Optional, Tuple

from core.config import BASE_MAGNITUDE_TO_PIXEL_SCALE, POLYGON_PADDING, CLOSURE_TOLERANCE_PIXELS, NUMERIC_ZERO_TOLERANCE
from core.drawing_primitives import draw_origin_dot, draw_arrow
from core.geometry_utils import normalize_angle_radians, normalize_angle_degrees
from core.data_models import Vector
import sympy as sp

def _get_effective_vector_drawing_properties(vec_obj: Vector, solution_dict: Optional[Dict[Any, Any]], F_sym: Optional[sp.Symbol], theta_sym_rad: Optional[sp.Symbol]) -> Tuple[float, float]:
    """
    Helper to determine the effective magnitude and angle (in radians) for drawing a vector,
    considering input values, solved values, and negative magnitudes.
    """
    mag_val = vec_obj.magnitude
    ang_val = vec_obj.angle

    if solution_dict and F_sym and theta_sym_rad:
        if F_sym in solution_dict:
            mag_val = float(solution_dict[F_sym])
        if theta_sym_rad in solution_dict:
            ang_val = float(solution_dict[theta_sym_rad])

    mag_val = float(mag_val) if isinstance(mag_val, (float, int)) else 0.0
    ang_val = float(ang_val) if isinstance(ang_val, (float, int)) else 0.0

    effective_mag = abs(mag_val)

    if solution_dict and theta_sym_rad and theta_sym_rad in solution_dict:
        ang_rad_initial = ang_val
    else:
        ang_rad_initial = math.radians(ang_val)

    effective_ang_rad = ang_rad_initial
    if mag_val < 0:
        effective_ang_rad += math.pi

    effective_ang_rad = normalize_angle_radians(effective_ang_rad)

    return effective_mag, effective_ang_rad


def _calculate_fbd_render_bounds(
    vectors_data: List[Vector],
    origin_point: Tuple[float, float],
    active_pixel_to_unit_scale: float,
    solution_dict: Optional[Dict[Any, Any]] = None,
    F_syms: Optional[List[sp.Symbol]] = None,
    theta_syms_rad: Optional[List[sp.Symbol]] = None
) -> Tuple[float, float, float, float]:
    """
    Calculates the min/max X and Y coordinates for an FBD drawing to determine its overall bounds.
    Uses the active_pixel_to_unit_scale to determine raw pixel lengths.
    """
    all_x_coords = [origin_point[0]]
    all_y_coords = [origin_point[1]]

    for i, vec_obj in enumerate(vectors_data):
        effective_mag, effective_ang_rad = _get_effective_vector_drawing_properties(
            vec_obj, solution_dict, F_syms[i] if F_syms else None, theta_syms_rad[i] if theta_syms_rad else None
        )

        scaled_length = effective_mag * active_pixel_to_unit_scale
        if scaled_length < 1.0: scaled_length = 1.0

        fx_pixel = scaled_length * math.cos(effective_ang_rad)
        fy_pixel = scaled_length * math.sin(effective_ang_rad)

        end_x = origin_point[0] + fx_pixel
        end_y = origin_point[1] - fy_pixel

        all_x_coords.append(end_x)
        all_y_coords.append(end_y)
    
    min_x = min(all_x_coords)
    max_x = max(all_x_coords)
    min_y = min(all_y_coords)
    max_y = max(all_y_coords)

    return min_x, max_x, min_y, max_y

def calculate_polygon_render_params(
    vectors_data: List[Vector],
    origin_point: Tuple[float, float],
    canvas_width: int,
    canvas_height: int,
    active_pixel_to_unit_scale: Optional[float] = None,
    solution_dict: Optional[Dict[Any, Any]] = None,
    F_syms: Optional[List[sp.Symbol]] = None,
    theta_syms_rad: Optional[List[sp.Symbol]] = None
) -> Tuple[float, float, float, Tuple[float, float]]:
    """
    Calculates the fit_scale, offset_x, offset_y, and scaled_start_point for polygon rendering.
    Ensures that the polygon fits within the canvas and is centered.
    If active_pixel_to_unit_scale is provided, it uses that for length calculations
    instead of dynamic scaling, maintaining a consistent drawing scale.
    NOTE: The 'fit_scale' ensures all vectors fit the canvas, but can make
    smaller vectors very tiny if there's a large difference in magnitudes (e.g., >3x).
    """
    if not vectors_data:
        return 1.0, 0.0, 0.0, origin_point

    raw_polygon_points_unconstrained = [origin_point]
    current_temp_point = origin_point

    base_render_scale = active_pixel_to_unit_scale if active_pixel_to_unit_scale is not None else BASE_MAGNITUDE_TO_PIXEL_SCALE


    for i, vec_obj in enumerate(vectors_data):
        effective_mag, effective_ang_rad = _get_effective_vector_drawing_properties(
            vec_obj, solution_dict, F_syms[i] if F_syms else None, theta_syms_rad[i] if theta_syms_rad else None
        )

        scaled_length_for_bounds = effective_mag * base_render_scale
        if scaled_length_for_bounds < 1.0:
            scaled_length_for_bounds = 1.0

        fx_pixel_bounds = scaled_length_for_bounds * math.cos(effective_ang_rad)
        fy_pixel_bounds = scaled_length_for_bounds * math.sin(effective_ang_rad)

        next_temp_point = (current_temp_point[0] + fx_pixel_bounds, current_temp_point[1] - fy_pixel_bounds)
        raw_polygon_points_unconstrained.append(next_temp_point)
        current_temp_point = next_temp_point

    min_x_unconstrained = min(p[0] for p in raw_polygon_points_unconstrained)
    max_x_unconstrained = max(p[0] for p in raw_polygon_points_unconstrained)
    min_y_unconstrained = min(p[1] for p in raw_polygon_points_unconstrained)
    max_y_unconstrained = max(p[1] for p in raw_polygon_points_unconstrained)

    effective_range_x = max(1.0, max_x_unconstrained - min_x_unconstrained)
    effective_range_y = max(1.0, max_y_unconstrained - min_y_unconstrained)

    if active_pixel_to_unit_scale is not None:
        fit_scale = 1.0
        center_x_unconstrained = (min_x_unconstrained + max_x_unconstrained) / 2
        center_y_unconstrained = (min_y_unconstrained + max_y_unconstrained) / 2
        offset_x = canvas_width / 2 - center_x_unconstrained
        offset_y = canvas_height / 2 - center_y_unconstrained
    else:
        scale_x_needed = (canvas_width - 2 * POLYGON_PADDING) / effective_range_x
        scale_y_needed = (canvas_height - 2 * POLYGON_PADDING) / effective_range_y
        fit_scale = min(scale_x_needed, scale_y_needed, 1.0)

        offset_x = canvas_width / 2 - (min_x_unconstrained + max_x_unconstrained) / 2 * fit_scale
        offset_y = canvas_height / 2 - (min_y_unconstrained + max_y_unconstrained) / 2 * fit_scale
    
    scaled_start_point = (origin_point[0] * fit_scale + offset_x, origin_point[1] * fit_scale + offset_y)
    
    return fit_scale, offset_x, offset_y, scaled_start_point

def render_force_polygon_diagram(
    vectors: List[Vector],
    origin: Tuple[float, float],
    W: int, H: int,
    bg_image: Image.Image,
    is_equilibrium_app: bool,
    solution_context: Optional[Dict[Any, Any]] = None,
    F_syms: Optional[List[sp.Symbol]] = None,
    theta_syms_rad: Optional[List[sp.Symbol]] = None,
    R_sym: Optional[sp.Symbol] = None,
    alpha_sym_rad: Optional[sp.Symbol] = None
):
    """
    Renders the force polygon diagram, either dynamically for numeric inputs
    or based on solved symbolic results.
    """
    imgp = bg_image.copy()
    d = ImageDraw.Draw(imgp)

    active_pixel_to_unit_scale_for_drawing = st.session_state.get("calculated_pixel_to_unit_scale", BASE_MAGNITUDE_TO_PIXEL_SCALE)
    if not st.session_state.user_defined_scale_active or st.session_state.calculated_pixel_to_unit_scale is None:
        active_pixel_to_unit_scale_for_drawing = BASE_MAGNITUDE_TO_PIXEL_SCALE

    fit_scale, offset_x, offset_y, scaled_start_point_for_drawing = \
        calculate_polygon_render_params(
            vectors, origin, W, H,
            active_pixel_to_unit_scale=active_pixel_to_unit_scale_for_drawing if st.session_state.user_defined_scale_active else None,
            solution_dict=solution_context, F_syms=F_syms, theta_syms_rad=theta_syms_rad
        )

    if st.session_state.debug_mode:
        st.info(f"DEBUG: Polygon Fit Scale: {fit_scale:.3f}")
        st.info(f"DEBUG: Polygon Offset: ({offset_x:.0f}, {offset_y:.0f})")

    imgp = draw_origin_dot(imgp, scaled_start_point_for_drawing)

    current_poly_point_for_drawing = scaled_start_point_for_drawing

    for i, vec_obj in enumerate(vectors):
        effective_mag, effective_ang_rad = _get_effective_vector_drawing_properties(
            vec_obj, solution_context, F_syms[i] if F_syms else None, theta_syms_rad[i] if theta_syms_rad else None
        )
        if st.session_state.debug_mode:
            original_mag_display = f"{vec_obj.magnitude:.3f}" if isinstance(vec_obj.magnitude, (float, int)) else "N/A"
            original_angle_display = f"{vec_obj.angle:.2f}°" if isinstance(vec_obj.angle, (float, int)) else "N/A"
            st.info(f"DEBUG DRAW SOLVED: F{i+1}: Original Mag={original_mag_display}, Original Ang={original_angle_display}, Effective Mag={effective_mag:.3f}, Effective Ang={math.degrees(effective_ang_rad):.2f}°")


        final_scaled_length = effective_mag * active_pixel_to_unit_scale_for_drawing * fit_scale
        if final_scaled_length < 1.0:
            final_scaled_length = 1.0

        fx_pixel = final_scaled_length * math.cos(effective_ang_rad)
        fy_pixel = final_scaled_length * math.sin(effective_ang_rad)

        next_poly_point_for_drawing = (current_poly_point_for_drawing[0] + fx_pixel, current_poly_point_for_drawing[1] - fy_pixel)

        draw_arrow(d, current_poly_point_for_drawing, next_poly_point_for_drawing, fill="orange", width=4, outline_color="black", outline_width_increase=2)
        text_pos = (next_poly_point_for_drawing[0] + 10, next_poly_point_for_drawing[1] - 10)
        d.text(text_pos, f"F{i+1}", fill="orange")

        current_poly_point_for_drawing = next_poly_point_for_drawing

    # --- Handle Resultant / Closure Line ---
    closing_vector_dx = scaled_start_point_for_drawing[0] - current_poly_point_for_drawing[0]
    closing_vector_dy = scaled_start_point_for_drawing[1] - current_poly_point_for_drawing[1]
    closing_vector_magnitude = math.hypot(closing_vector_dx, closing_vector_dy)

    if is_equilibrium_app:
        if closing_vector_magnitude > CLOSURE_TOLERANCE_PIXELS:
            draw_arrow(d, current_poly_point_for_drawing, scaled_start_point_for_drawing, fill="purple", width=6, outline_color="black", outline_width_increase=3)
            st.warning(f"Polygon does not perfectly close (Closing line magnitude: {closing_vector_magnitude:.3f} pixels).")
        else:
            st.success("Polygon closes perfectly, indicating equilibrium!")
        
        st.image(imgp, caption="Force Polygon (head-to-tail, closing line in purple if not zero)", use_column_width=False, width=W)

        if solution_context and '_calculated_R_mag' in solution_context:
            res_mag = solution_context['_calculated_R_mag']
            res_ang = math.degrees(solution_context['_calculated_R_alpha'])
            res_ang = normalize_angle_degrees(res_ang)

            if abs(res_mag) < NUMERIC_ZERO_TOLERANCE:
                st.success(f"**System is in Equilibrium!** (Resultant is approximately 0)")
            else:
                st.warning(f"**System is NOT in Equilibrium.** Resultant: {res_mag} units @ {res_ang}°")

    else:
        draw_arrow(d, scaled_start_point_for_drawing, current_poly_point_for_drawing, fill="purple", width=6, outline_color="black", outline_width_increase=3)
        R_val = None
        alpha_val_deg = None
        if solution_context and R_sym and R_sym in solution_context and solution_context[R_sym] is not None:
            R_val = float(solution_context[R_sym])
        if solution_context and alpha_sym_rad and alpha_sym_rad in solution_context and solution_context[alpha_sym_rad] is not None:
            alpha_val_deg = normalize_angle_degrees(math.degrees(float(solution_context[alpha_sym_rad])))

        if R_val is not None and alpha_val_deg is not None:
            text_pos_r = (current_poly_point_for_drawing[0] + 10, current_poly_point_for_drawing[1] - 10)
            d.text(text_pos_r, f"R={R_val:.1f}@{alpha_val_deg:.0f}°", fill="purple")
            st.success(f"**Resultant:** {R_val:.3f} units @ {alpha_val_deg:.2f}°")
        else:
            text_pos_r = (current_poly_point_for_drawing[0] + 10, current_poly_point_for_drawing[1] - 10)
            d.text(text_pos_r, "R", fill="purple")
            st.warning("Resultant magnitude/angle unknown or not fully resolved.")
        
        st.image(imgp, caption="Force Polygon (head-to-tail, resultant in purple)", use_column_width=False, width=W)

def render_free_body_diagram(
    vectors: List[Vector],
    origin: Tuple[float, float],
    W: int, H: int,
    bg_image: Image.Image,
    is_equilibrium_app: bool,
    solution_context: Optional[Dict[Any, Any]] = None,
    F_syms: Optional[List[sp.Symbol]] = None,
    theta_syms_rad: Optional[List[sp.Symbol]] = None,
    R_sym: Optional[sp.Symbol] = None,
    alpha_sym_rad: Optional[sp.Symbol] = None
):
    """
    Renders the Free Body Diagram (FBD) showing all forces originating from a single point.
    Applies user-defined scale if active, otherwise uses base scale.
    NOTE: The 'fit_scale' ensures all vectors fit the canvas, but can make
    smaller vectors very tiny if there's a large difference in magnitudes (e.g., >3x).
    """
    img_fbd = bg_image.copy()
    d_fbd = ImageDraw.Draw(img_fbd)

    active_pixel_to_unit_scale_for_drawing = st.session_state.get("calculated_pixel_to_unit_scale", BASE_MAGNITUDE_TO_PIXEL_SCALE)
    if not st.session_state.user_defined_scale_active or st.session_state.calculated_pixel_to_unit_scale is None:
        active_pixel_to_unit_scale_for_drawing = BASE_MAGNITUDE_TO_PIXEL_SCALE

    # Calculate FBD render parameters for *vector scaling*, not origin positioning.
    # The FBD should always originate from the given 'origin' pixel coordinate.
    min_x_unconstrained, max_x_unconstrained, min_y_unconstrained, max_y_unconstrained = \
        _calculate_fbd_render_bounds(vectors, origin, active_pixel_to_unit_scale_for_drawing, solution_context, F_syms, theta_syms_rad)

    effective_range_x = max(1.0, max_x_unconstrained - min_x_unconstrained)
    effective_range_y = max(1.0, max_y_unconstrained - min_y_unconstrained)

    scale_x_needed = (W - 2 * POLYGON_PADDING) / effective_range_x
    scale_y_needed = (H - 2 * POLYGON_PADDING) / effective_range_y

    fbd_fit_scale = min(scale_x_needed, scale_y_needed, 1.0)

    # ALWAYS fix the origin for FBD at its user-defined or default position
    scaled_origin_for_drawing = origin

    # Determine the scale to apply ONLY to vector lengths.
    # If user-defined scale is active, render_diagram_overall_scale is 1.0 (fixed scale).
    # Otherwise, use fbd_fit_scale to ensure vectors fit the canvas.
    render_diagram_overall_scale = 1.0
    if not st.session_state.user_defined_scale_active or st.session_state.calculated_pixel_to_unit_scale is None:
        render_diagram_overall_scale = fbd_fit_scale

    # Draw the origin dot first, using the fixed scaled_origin_for_drawing
    img_fbd = draw_origin_dot(img_fbd, scaled_origin_for_drawing)

    # Draw each force vector originating from the origin
    for i, vec_obj in enumerate(vectors):
        effective_mag, effective_ang_rad = _get_effective_vector_drawing_properties(
            vec_obj, solution_context, F_syms[i] if F_syms else None, theta_syms_rad[i] if theta_syms_rad else None
        )

        # Calculate end point of the vector
        # Apply both active_pixel_to_unit_scale_for_drawing AND render_diagram_overall_scale
        scaled_length = effective_mag * active_pixel_to_unit_scale_for_drawing * render_diagram_overall_scale
        if scaled_length < 1.0:
            scaled_length = 1.0

        fx_pixel = scaled_length * math.cos(effective_ang_rad)
        fy_pixel = scaled_length * math.sin(effective_ang_rad)
        
        # End point for drawing: origin_x + fx, origin_y - fy (due to inverted Y)
        end_point = (scaled_origin_for_drawing[0] + fx_pixel, scaled_origin_for_drawing[1] - fy_pixel)

        # Draw the arrow for the force
        draw_arrow(d_fbd, scaled_origin_for_drawing, end_point, fill="orange", width=4, outline_color="black", outline_width_increase=2)
        
        # Add force label (e.g., F1)
        text_pos = (end_point[0] + 10, end_point[1] - 10)
        d_fbd.text(text_pos, f"F{i+1}", fill="orange")

    # --- Draw Resultant (for Resultant App) or Equilibrant (for Equilibrium App if needed) ---
    R_val = None
    alpha_val_rad = None

    if not is_equilibrium_app and solution_context and R_sym and R_sym in solution_context and solution_context[R_sym] is not None:
        R_val = float(solution_context[R_sym])
        if alpha_sym_rad and alpha_sym_rad in solution_context and solution_context[alpha_sym_rad] is not None:
            alpha_val_rad = float(solution_context[alpha_sym_rad])
    
    elif is_equilibrium_app and solution_context and '_calculated_R_mag' in solution_context:
        R_val = solution_context['_calculated_R_mag']
        alpha_val_rad = solution_context['_calculated_R_alpha']

    if R_val is not None and alpha_val_rad is not None and abs(R_val) > NUMERIC_ZERO_TOLERANCE:
        res_scaled_length = abs(R_val) * active_pixel_to_unit_scale_for_drawing * render_diagram_overall_scale
        if res_scaled_length < 1.0: res_scaled_length = 1.0

        draw_alpha_rad = normalize_angle_radians(alpha_val_rad)
        line_color = "purple" # Changed from "red" to "purple" for consistency with polygon solution line
        label_text = f"R={abs(R_val):.1f}"

        res_fx_pixel = res_scaled_length * math.cos(draw_alpha_rad)
        res_fy_pixel = res_scaled_length * math.sin(draw_alpha_rad)
        res_end_point = (scaled_origin_for_drawing[0] + res_fx_pixel, scaled_origin_for_drawing[1] - res_fy_pixel)

        draw_arrow(d_fbd, scaled_origin_for_drawing, res_end_point, fill=line_color, width=6, outline_color="black", outline_width_increase=3)
        
        res_text_pos = (res_end_point[0] + 10, res_end_point[1] - 10)
        d_fbd.text(res_text_pos, label_text, fill=line_color)


    st.image(img_fbd, caption="Free Body Diagram", use_column_width=False, width=W)

    if is_equilibrium_app:
        if solution_context and '_calculated_R_mag' in solution_context:
            res_mag = solution_context['_calculated_R_mag']
            res_ang = math.degrees(solution_context['_calculated_R_alpha'])
            res_ang = normalize_angle_degrees(res_ang)

            if abs(res_mag) < NUMERIC_ZERO_TOLERANCE:
                st.success(f"**System is in Equilibrium!** (Resultant is approximately 0)")
            else:
                st.warning(f"**System is NOT in Equilibrium.** Resultant: {res_mag:.3f} units @ {res_ang:.2f}°")
    else:
        if R_val is not None and alpha_val_rad is not None:
            alpha_val_deg = normalize_angle_degrees(math.degrees(alpha_val_rad))
            st.success(f"**Resultant:** {R_val:.3f} units @ {alpha_val_deg:.2f}°")
        else:
            st.warning("Resultant magnitude/angle unknown or not fully resolved.")