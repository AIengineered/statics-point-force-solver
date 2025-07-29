import streamlit as st
import sys
import os
import sympy as sp
import math
from PIL import Image # For image handling (e.g., background image)
from io import BytesIO # For handling image data in bytes (e.g., BytesIO)
# No need for 'import base64' here, as the direct PIL Image handling for st_canvas is preferred for 0.9.3


# ==============================================================================
# 1. ESSENTIAL IMPORTS & PATH SETUP (NO STREAMLIT COMMANDS YET!)
#    These lines must come first to correctly configure Python's module search path
#    and allow subsequent imports from your project structure.
# ==============================================================================

# Calculate the project root directory.
# This ensures that absolute imports (like 'from core.config') work correctly,
# regardless of where you run the Streamlit command from.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Add the project root to Python's system path.
# This makes 'core', 'ui', 'solver', 'renderer' discoverable as top-level packages.
# Check if it's already there to prevent adding duplicates.
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# ==============================================================================
# 2. IMPORT VARIABLES NEEDED FOR st.set_page_config()
#    These must be imported *before* set_page_config if they are used by it.
# ==============================================================================
from core.config import PAGE_TITLE_EQUILIBRIUM, MAX_CANVAS_WIDTH, DEFAULT_CANVAS_HEIGHT # Imports constants from config

# ==============================================================================
# 3. STREAMLIT PAGE CONFIGURATION (MUST BE THE FIRST 'st.' COMMAND!)
#    This sets the title and layout of your Streamlit app page.
# ==============================================================================
st.set_page_config(page_title=PAGE_TITLE_EQUILIBRIUM, layout="centered") # Sets the page title and layout

# ==============================================================================
# 4. SESSION STATE INITIALIZATION (CRITICAL: MUST BE CALLED IMMEDIATELY AFTER set_page_config)
#    This ensures all st.session_state variables are defined before being used.
# ==============================================================================
# Import session_manager functions.
from core.session_manager import initialize_common_session_state, reset_all_app_state, increment_canvas_reset_key # Imports session state management functions
initialize_common_session_state() # Initialize common Streamlit session state variables here

# Initialize a flag to control explicit reruns. This flag acts as a single point
# to request a rerun from various parts of the application logic.
if 'trigger_rerun_after_logic' not in st.session_state:
    st.session_state.trigger_rerun_after_logic = False


# ==============================================================================
# 5. REMAINING IMPORTS AND APPLICATION LOGIC
#    Now that set_page_config and session_state are done, we can import other modules
# ==============================================================================
# The 'from ui.canvas_interaction import ...' import should NOT contain 'render_origin_pick_canvas' here
# as it's defined within the local scope below.
from ui.canvas_interaction import handle_force_drawing_input, handle_origin_selection_ui
# NOTE: render_origin_pick_canvas will be imported directly within the conditional block that uses it
from ui.force_properties_ui import render_force_properties_sidebar_content, render_drawing_scale_settings
from solver.equilibrium_solver import solve_for_equilibrium
from renderer.diagram_renderer import render_force_polygon_diagram, render_free_body_diagram
from core.data_models import Vector
from solver.common import format_latex_sum_with_constants


# --- DEBUG MESSAGES AT START OF SCRIPT RUN ---
# These messages help trace the execution flow and session state values at the beginning of each rerun.
if st.session_state.debug_mode:
    st.info(f"--- SCRIPT START (RERUN) ---")
    st.info(f"Current canvas_reset at script start: {st.session_state.canvas_reset}")
    st.info(f"Current last_uploaded_filename at script start: {st.session_state.last_uploaded_filename}")
    st.info(f"Current trigger_rerun_after_logic at script start: {st.session_state.trigger_rerun_after_logic}")
# --- END DEBUG MESSAGES ---


# --- Main Application Title ---
st.title(PAGE_TITLE_EQUILIBRIUM)


# --- Upload Background Image (Optional) ---
# This section handles file uploads for a background image on the canvas.
uploaded_file = st.file_uploader("Upload background image (optional, e.g. structure or diagram)", type=["png", "jpg", "jpeg"])

needs_file_update_and_rerun = False

# This will hold the final PIL Image object for both canvas background and FBD/Polygon rendering.
# It will always be a PIL Image (either processed uploaded image or a new white one).
bg_image_for_display_and_drawing = None 

# If a file has been uploaded via the uploader.
if uploaded_file is not None:
    if st.session_state.debug_mode: st.info(f"DEBUG: File uploader has a file: {uploaded_file.name}.")

    if "last_uploaded_filename" not in st.session_state or st.session_state.last_uploaded_filename != uploaded_file.name:
        if st.session_state.debug_mode: st.info(f"DEBUG: New file detected (or re-selected): {uploaded_file.name}. Processing...")
        
        img0 = Image.open(BytesIO(uploaded_file.getvalue()))
        
        # --- START OF CRITICAL NEW CODE: Ensure RGB mode and handle alpha for compatibility ---
        # This converts any image to RGB and composites transparent images onto a white background.
        # This is VITAL for streamlit-drawable-canvas 0.9.3 to render images correctly.
        if img0.mode in ('RGBA', 'LA') or (img0.mode == 'P' and 'transparency' in img0.info):
            # Create a white background image the same size as img0
            background = Image.new("RGB", img0.size, "white")
            # Paste img0 onto the background. If RGBA, use the alpha channel as a mask.
            background.paste(img0, mask=img0.split()[3] if img0.mode == 'RGBA' else None)
            img0 = background
        elif img0.mode != 'RGB':
            # Convert other non-alpha modes (e.g., 'L' for grayscale, 'CMYK') to RGB
            img0 = img0.convert("RGB")
        # --- END OF CRITICAL NEW CODE ---

        w, h = img0.size
        if w > MAX_CANVAS_WIDTH: # Resize if image is too wide
            img0 = img0.resize((MAX_CANVAS_WIDTH, int(h * MAX_CANVAS_WIDTH / w)), Image.LANCZOS)
        
        buf = BytesIO()
        img0.save(buf, format="PNG") # Save as PNG after processing
        
        st.session_state.bg_image_bytes = buf.getvalue()
        st.session_state.last_uploaded_filename = uploaded_file.name
        if st.session_state.debug_mode: st.info(f"DEBUG: app_equilibrium: Called reset_all_app_state() after new file upload.")
        needs_file_update_and_rerun = True
    else:
        if st.session_state.debug_mode: st.info("DEBUG: File uploader has same file as last processed. No reprocessing initiated by this block.")

# Condition 2: No file is currently in the uploader (uploaded_file is None).
elif ("bg_image_bytes" in st.session_state and st.session_state.bg_image_bytes is not None) or \
     ("last_uploaded_filename" in st.session_state and st.session_state.last_uploaded_filename is not None):
    
    if st.session_state.debug_mode: st.info("DEBUG: File uploader is empty. Clearing any previously loaded background image from session state.")
    st.session_state.bg_image_bytes = None
    st.session_state.last_uploaded_filename = None
    
    reset_all_app_state()
    if st.session_state.debug_mode: st.info(f"DEBUG: app_equilibrium: Called reset_all_app_state() after clearing file.")
    needs_file_update_and_rerun = True
else:
    if st.session_state.debug_mode: st.info("DEBUG: No file uploaded, and no previous file found in session state.")

if needs_file_update_and_rerun:
    st.session_state.trigger_rerun_after_logic = True
    if st.session_state.debug_mode: st.info(f"DEBUG: app_equilibrium: Setting trigger_rerun_after_logic to True due to file change.")


# --- Canvas & Origin Setup ---
# Determine canvas dimensions and the PIL Image to be used as background.
# This 'bg_image_for_display_and_drawing' variable will always be a clean, RGB PIL Image.
if st.session_state.bg_image_bytes:
    bg_image_for_display_and_drawing = Image.open(BytesIO(st.session_state.bg_image_bytes))
    W, H = bg_image_for_display_and_drawing.size
else: # Default white canvas if no image uploaded
    W, H = MAX_CANVAS_WIDTH, DEFAULT_CANVAS_HEIGHT
    bg_image_for_display_and_drawing = Image.new("RGB", (W, H), "white") # Always ensure a white PIL Image

# Set default origin to center of canvas if not already defined.
if st.session_state.origin is None:
    st.session_state.origin = (W // 2, H // 2)
origin = st.session_state.origin


# ==============================================================================
# --- SIDEBAR CONTENT (ALL INPUTS & MAIN ACTIONS) ---
# ==============================================================================
with st.sidebar:
    
    st.title("🎛 Controls")

    with st.expander("🖼 Background & Canvas Setup", expanded=True):
        handle_origin_selection_ui(W, H)

    # --- Section 2: Force Inputs ---
    with st.expander("➕ Force Vectors", expanded=True):
        st.write("Angles: 0° is rightward, +CCW.")

        if st.button("➕ Add Force Manually"):
            st.session_state.vectors.append(Vector(angle=None, magnitude=None, drawn_length=0.0))
            st.session_state.trigger_rerun_after_logic = True
            if st.session_state.debug_mode: st.info("DEBUG: Added new empty vector.")

        render_force_properties_sidebar_content()

        st.markdown("---")
        st.subheader("Drawing Scale Settings")
        render_drawing_scale_settings()

    # --- Section 3: Solver ---
    with st.expander("🎯 Solve for Equilibrium", expanded=True):
        st.write("Set unknown magnitudes and/or angles blank to solve.")
        st.markdown("**Resultant Magnitude R:** `0`  \n**Resultant Angle α:** `Indeterminate`")
        solve_click = st.button("🔍 Solve for Unknowns")
        if solve_click:
            st.session_state.last_solve_click = True
            if st.session_state.debug_mode: st.info("DEBUG: Solve button clicked.")

    # --- Section 4: History (Undo/Redo) ---
    with st.expander("↩️ Undo / Redo (Coming Soon)", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            if st.button("↩️ Undo"):
                st.session_state.undo_requested = True
        with col2:
            if st.button("↪️ Redo"):
                st.session_state.redo_requested = True
        st.caption("Reverses the last canvas or input change.")

    # --- Section 5: App Reset ---
    with st.expander("🧹 Reset & Clear", expanded=False):
        if st.button("Clear All Forces & Canvas"):
            if st.session_state.debug_mode: st.info("DEBUG: Clear All clicked.")
            reset_all_app_state()
            st.session_state.trigger_rerun_after_logic = True
            if st.session_state.debug_mode: st.info("DEBUG: trigger_rerun_after_logic set True from clear.")

st.sidebar.caption("All angles: 0° is right, +CCW. Blank for symbolic solve.")


# --- Main Canvas Area ---
# This handles both the origin picking mode and the normal drawing mode.

if st.session_state.get("pick_origin_mode", False):
    # Origin pick mode: Show a canvas with a background image and let user click
    # Import render_origin_pick_canvas here as it's only used conditionally.
    from ui.canvas_interaction import render_origin_pick_canvas
    render_origin_pick_canvas(W, H, bg_image_for_display_and_drawing) # Pass the processed PIL Image
else:
    # Normal drawing mode: draw forces on the main canvas
    if st.session_state.debug_mode: st.info("DEBUG: Calling handle_force_drawing_input.")
    handle_force_drawing_input(W, H, origin, bg_image_for_display_and_drawing) # Pass the processed PIL Image
    if st.session_state.debug_mode: st.info(f"DEBUG: Returned from handle_force_drawing_input. canvas_reset: {st.session_state.canvas_reset}")


# --- Display Force Polygon & Solver Results ---
# This section orchestrates the display of either the dynamic numeric polygon
# or the symbolic solver results based on user interaction.

# Dynamic numeric polygon display:
# Shown if no explicit solve button click AND all vectors have numeric magnitude/angle.
# if not st.session_state.last_solve_click and \
# all(isinstance(v.magnitude, (float, int)) and isinstance(v.angle, (float, int)) for v in st.session_state.vectors):
#     st.subheader("3️⃣ Force Polygon & Equilibrium Check") # Section header
#     if st.session_state.debug_mode: st.info("DEBUG: Displaying dynamic numeric force polygon for equilibrium check.")

#     # Call the renderer function for dynamic display
#     render_force_polygon_diagram(
#         vectors=st.session_state.vectors, # List of Vector objects
#         origin=origin, # Origin point
#         W=W, H=H, # Canvas dimensions
#         bg_image=bg_image, # Background image
#         is_equilibrium_app=True, # Flag indicating this is the Equilibrium app
#         solution_context=None, # No solved context for dynamic display
#         F_syms=None, theta_syms_rad=None, R_sym=None, alpha_sym_rad=None # No SymPy symbols needed here
#     ) #

# # Symbolic solver results display:
# # Shown only if the solve button was clicked.
# elif st.session_state.last_solve_click: # If solve button was clicked
#     st.subheader("2️⃣ Solve Results") # Section header
#     if st.session_state.debug_mode: st.info("DEBUG: Entering symbolic solve logic block.")

#     # Call the solver function from equilibrium_solver module
#     solver_output = solve_for_equilibrium(
#         vectors=st.session_state.vectors # List of Vector objects
#     ) # Calls the solver to get results

#     if solver_output.get("error"): # Check if an error occurred during solving
#         st.session_state.last_solve_click = False # Turn off solve display on error
#         if st.session_state.debug_mode: st.info("DEBUG: Solver reported an error. Resetting last_solve_click.")
#         # No st.stop() here. Let the script finish and rerun if flag is set by solver error handling.
#     else:
#         all_sols = solver_output['all_sols'] # List of solutions from solver
#         F_syms = solver_output['F_syms'] # SymPy symbols for magnitudes
#         theta_syms_rad = solver_output['theta_syms_rad'] # SymPy symbols for angles

#         # --- DETAILED LATEX OUTPUT BLOCK ---
#         st.subheader("Symbolic Equations") # Subheader for equations section

#         # Retrieve LaTeX terms and sums from the solver_output dictionary
#         sum_fx_latex_raw_trig_terms = solver_output['sum_fx_latex_raw_trig_terms'] # Raw trigonometric terms for Fx
#         sum_fy_latex_raw_trig_terms = solver_output['sum_fy_latex_raw_trig_terms'] # Raw trigonometric terms for Fy
#         constant_fx_sum = solver_output['constant_fx_sum'] # Numeric sum of known Fx components
#         constant_fy_sum = solver_output['constant_fy_sum'] # Numeric sum of known Fy components
#         symbolic_fx_latex_terms = solver_output['symbolic_fx_latex_terms'] # LaTeX terms for symbolic Fx parts
#         symbolic_fy_latex_terms = solver_output['symbolic_fy_latex_terms'] # LaTeX terms for symbolic Fy parts
#         unknown_symbols = solver_output['unknown_symbols'] # List of symbols that were identified as unknowns

#         # Display raw trigonometric terms for Sum Fx and Sum Fy
#         # This joins individual terms with " + " and adds parentheses if a term contains "+" or "-"
#         sum_fx_raw_joined = " + ".join(f"({term})" if "+" in term or "-" in term else term for term in sum_fx_latex_raw_trig_terms)
#         sum_fy_raw_joined = " + ".join(f"({term})" if "+" in term or "-" in term else term for term in sum_fy_latex_raw_trig_terms)

#         st.latex(f"\\sum F_x = {sum_fx_raw_joined}") # Display Sum Fx equation
#         st.latex(f"\\sum F_y = {sum_fy_raw_joined}") # Display Sum Fy equation

#         # Display Rx and Ry expressions (always 0 for equilibrium)
#         st.latex(f"R_x = 0") # Resultant X component is 0 for equilibrium
#         st.latex(f"R_y = 0") # Resultant Y component is 0 for equilibrium

#         # Get the final LaTeX representation for the left-hand side (LHS) of the solved equations.
#         # This uses the `format_latex_sum_with_constants` helper to combine numeric and symbolic terms.
#         lhs_eq1_final_latex = format_latex_sum_with_constants(constant_fx_sum, symbolic_fx_latex_terms) # Formats the LHS of Fx equation
#         lhs_eq2_final_latex = format_latex_sum_with_constants(constant_fy_sum, symbolic_fy_latex_terms) # Formats the LHS of Fy equation

#         # Display the final system of equations that SymPy solved for (LHS = RHS)
#         # For equilibrium, the RHS is always 0.
#         st.latex(f"\\therefore \\quad {lhs_eq1_final_latex} = 0") # Final Fx equation set to zero
#         st.latex(f"\\therefore \\quad {lhs_eq2_final_latex} = 0") # Final Fy equation set to zero
        
#         # Inform the user what symbols SymPy attempted to solve for.
#         st.markdown(f"Solving for: `{', '.join(str(s).replace('_rad', '') for s in unknown_symbols)}`") # Displays the unknown symbols

#         # Display solver warnings (underdetermined/overdetermined) if any.
#         # This uses information about the number of unknowns vs. available equations (2 for 2D equilibrium).
#         if len(unknown_symbols) > 2: # If more than 2 unknowns, system is underdetermined.
#             st.warning(f"Underdetermined system: {len(unknown_symbols)} unknowns but only 2 equations. Solutions may not be unique or may contain free parameters.")
#         elif len(unknown_symbols) < 2: # If less than 2 unknowns, system is overdetermined.
#             st.warning(f"Overdetermined system: {len(unknown_symbols)} unknowns but 2 equations. Solutions might not exist.")

#         # --- END OF DETAILED LATEX OUTPUT BLOCK ---

#         # Display solutions and draw polygons
#         if all_sols: # If solutions were found
#             for idx, sol in enumerate(all_sols, start=1): # Iterate through each solution
#                 st.markdown(f"### Solution #{idx}") # Solution header
#                 #st.info(f"Debug: Displaying Solution #{idx}: {sol}") # (Commented out debug)

#                 # Print out the numeric values of the solved unknowns.
#                 for var, val in sol.items(): # Iterate through variables and values in the solution
#                     if isinstance(val, (sp.Float, float, int)): # If the solved value is a number
#                         v = float(val) # Convert to standard float
#                         if var in F_syms: # If it's a solved magnitude for a force
#                             if v < 0: # If magnitude is negative, indicate direction reversal.
#                                 st.warning(f"{var} = {abs(v):.3f} (direction reversed)")
#                             else:
#                                 st.success(f"{var} = {v:.3f}")
#                         elif var in theta_syms_rad: # If it's a solved angle for a force
#                             deg = math.degrees(v) % 360 # Convert radians to degrees and normalize
#                             st.success(f"θ{theta_syms_rad.index(var)+1} = {deg:.2f}°")
#                     else: # Handle cases where SymPy might return symbolic or complex expressions.
#                         st.info(f"{var} = {val} (Symbolic or Complex)")

#                 st.subheader(f"Force Polygon (Solution {idx})") # Subheader for force polygon
#                 render_force_polygon_diagram(
#                     vectors=st.session_state.vectors, # Pass original vectors for iteration
#                     origin=origin, # Origin point
#                     W=W, H=H, # Canvas dimensions
#                     bg_image=bg_image, # Background image
#                     is_equilibrium_app=True, # Flag indicating Equilibrium app
#                     solution_context=sol, # Pass the specific solution to draw the polygon accurately
#                     F_syms=F_syms, theta_syms_rad=theta_syms_rad, # SymPy symbols for drawing
#                     R_sym=None, alpha_sym_rad=None # No R/alpha symbols for equilibrium app
#                 ) #
#         else:
#             st.info("No solutions found or no vectors defined with solvable unknowns.") # Message if no solutions


# --- Display Free Body Diagram (FBD) and Solver Results ---
# FBD is always displayed if there are vectors, acting as the primary visualization.

st.subheader("2️⃣ Free Body Diagram (FBD) - Problem Setup") # Added "Problem Setup" for clarity
if st.session_state.debug_mode: st.info("DEBUG: Displaying FBD for problem setup.")

# Call the FBD renderer function to show current input forces (before solve or if solve not clicked)
render_free_body_diagram(
    vectors=st.session_state.vectors,
    origin=origin,
    W=W, H=H,
    bg_image=bg_image,
    is_equilibrium_app=True,
    solution_context=None, # This FBD shows current user inputs, no solved context yet
    F_syms=None, theta_syms_rad=None, R_sym=None, alpha_sym_rad=None
)

# --- Force Polygon & Solver Results (Conditional Display) ---
if st.session_state.last_solve_click: # If solve button was clicked
    st.subheader("3️⃣ Solve Results & Diagrams") # Changed subheader for more general solve results
    if st.session_state.debug_mode: st.info("DEBUG: Entering symbolic solve logic block.")

    solver_output = solve_for_equilibrium(
        vectors=st.session_state.vectors
    )

    if solver_output.get("error"):
        st.session_state.last_solve_click = False
        if st.session_state.debug_mode: st.info("DEBUG: Solver reported an error. Resetting last_solve_click.")
    else:
        all_sols = solver_output['all_sols']
        F_syms = solver_output['F_syms']
        theta_syms_rad = solver_output['theta_syms_rad']

        st.subheader("Symbolic Equations")
        sum_fx_latex_raw_trig_terms = solver_output['sum_fx_latex_raw_trig_terms']
        sum_fy_latex_raw_trig_terms = solver_output['sum_fy_latex_raw_trig_terms']
        constant_fx_sum = solver_output['constant_fx_sum']
        constant_fy_sum = solver_output['constant_fy_sum']
        symbolic_fx_latex_terms = solver_output['symbolic_fx_latex_terms']
        symbolic_fy_latex_terms = solver_output['symbolic_fy_latex_terms']
        unknown_symbols = solver_output['unknown_symbols']

        sum_fx_raw_joined = " + ".join(f"({term})" if "+" in term or "-" in term else term for term in sum_fx_latex_raw_trig_terms)
        sum_fy_raw_joined = " + ".join(f"({term})" if "+" in term or "-" in term else term for term in sum_fy_latex_raw_trig_terms)

        st.latex(f"\\sum F_x = {sum_fx_raw_joined}")
        st.latex(f"\\sum F_y = {sum_fy_raw_joined}")

        st.latex(f"R_x = 0")
        st.latex(f"R_y = 0")

        lhs_eq1_final_latex = format_latex_sum_with_constants(constant_fx_sum, symbolic_fx_latex_terms)
        lhs_eq2_final_latex = format_latex_sum_with_constants(constant_fy_sum, symbolic_fy_latex_terms)

        st.latex(f"\\therefore \\quad {lhs_eq1_final_latex} = 0")
        st.latex(f"\\therefore \\quad {lhs_eq2_final_latex} = 0")

        st.markdown(f"Solving for: `{', '.join(str(s).replace('_rad', '') for s in unknown_symbols)}`")

        if len(unknown_symbols) > 2:
            st.warning(f"Underdetermined system: {len(unknown_symbols)} unknowns but only 2 equations. Solutions may not be unique or may contain free parameters.")
        elif len(unknown_symbols) < 2:
            st.warning(f"Overdetermined system: {len(unknown_symbols)} unknowns but 2 equations. Solutions might not exist.")

        # Display solutions and draw diagrams for each solution
        if all_sols:
            for idx, sol in enumerate(all_sols, start=1):
                st.markdown(f"### Solution #{idx}")
                for var, val in sol.items():
                    if isinstance(val, (sp.Float, float, int)):
                        v = float(val)
                        if var in F_syms:
                            if v < 0:
                                st.warning(f"{var} = {abs(v):.3f} (direction reversed)")
                            else:
                                st.success(f"{var} = {v:.3f}")
                        elif var in theta_syms_rad:
                            deg = math.degrees(v) % 360
                            st.success(f"θ{theta_syms_rad.index(var)+1} = {deg:.2f}°")
                    else:
                        st.info(f"{var} = {val} (Symbolic or Complex)")

                st.subheader(f"Free Body Diagram (Solution {idx})")
                render_free_body_diagram(
                    vectors=st.session_state.vectors, # Pass original vectors for iteration
                    origin=origin,
                    W=W, H=H,
                    bg_image=bg_image,
                    is_equilibrium_app=True,
                    solution_context=sol,
                    F_syms=F_syms, theta_syms_rad=theta_syms_rad,
                    R_sym=None, alpha_sym_rad=None
                )

                st.subheader(f"Force Polygon (Solution {idx})")
                render_force_polygon_diagram(
                    vectors=st.session_state.vectors,
                    origin=origin,
                    W=W, H=H,
                    bg_image=bg_image,
                    is_equilibrium_app=True,
                    solution_context=sol,
                    F_syms=F_syms, theta_syms_rad=theta_syms_rad,
                    R_sym=None, alpha_sym_rad=None
                )
        else:
            st.info("No solutions found or no vectors defined with solvable unknowns.")
elif all(isinstance(v.magnitude, (float, int)) and isinstance(v.angle, (float, int)) for v in st.session_state.vectors):
    st.subheader("3️⃣ Force Polygon & Equilibrium Check (Numeric Inputs)")
    if st.session_state.debug_mode: st.info("DEBUG: Displaying dynamic numeric force polygon for equilibrium check.")

    render_force_polygon_diagram(
        vectors=st.session_state.vectors,
        origin=origin,
        W=W, H=H,
        bg_image=bg_image,
        is_equilibrium_app=True,
        solution_context=None,
        F_syms=None, theta_syms_rad=None, R_sym=None, alpha_sym_rad=None
    )
else:
    st.info("Draw forces or click 'Solve for Unknowns' to see results.")

# --- Pick Origin Mode (TEMPORARY CANVAS) ---
if st.session_state.get("pick_origin_mode", False):
    st.subheader("Click anywhere on the canvas to set the new origin")
    pass


# --- Final Rerun Logic ---
if st.session_state.debug_mode: 
    st.info(f"--- SCRIPT END --- Checking trigger_rerun_after_logic: {st.session_state.trigger_rerun_after_logic}")
    st.info(f"--- SCRIPT END --- Current canvas_reset before final check: {st.session_state.canvas_reset}")

if st.session_state.trigger_rerun_after_logic:
    if st.session_state.debug_mode: st.info("DEBUG: Triggering st.experimental_rerun()!")

    st.session_state.update({
        "trigger_rerun_after_logic": False,
        "canvas_reset": st.session_state.canvas_reset + 1
    })

    if st.session_state.debug_mode: st.info(f"DEBUG: canvas_reset incremented to {st.session_state.canvas_reset} before rerun.")
    st.experimental_rerun()