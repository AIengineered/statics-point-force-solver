import streamlit as st
import sys
import os
import sympy as sp
import math
from PIL import Image # For image handling (e.g., background image)
from io import BytesIO # For handling image data in bytes (e.g., BytesIO)

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
from ui.canvas_interaction import handle_force_drawing_input, handle_origin_selection_ui, render_origin_pick_canvas # Imports canvas interaction functions
from ui.force_properties_ui import render_force_properties_sidebar_content, render_drawing_scale_settings # Import both functions
from solver.equilibrium_solver import solve_for_equilibrium # Imports the equilibrium solver function
from renderer.diagram_renderer import render_force_polygon_diagram, render_free_body_diagram # Imports the diagram renderer
from core.data_models import Vector # Imports the Vector dataclass
from solver.common import format_latex_sum_with_constants # Imports helper for LaTeX formatting


# --- DEBUG MESSAGES AT START OF SCRIPT RUN ---
# These messages help trace the execution flow and session state values at the beginning of each rerun.
if st.session_state.debug_mode:
    st.info(f"--- SCRIPT START (RERUN) ---")
    st.info(f"Current canvas_reset at script start: {st.session_state.canvas_reset}")
    st.info(f"Current last_uploaded_filename at script start: {st.session_state.last_uploaded_filename}")
    st.info(f"Current trigger_rerun_after_logic at script start: {st.session_state.trigger_rerun_after_logic}")
# --- END DEBUG MESSAGES ---


# --- Main Application Title ---
st.title(PAGE_TITLE_EQUILIBRIUM) # Main app title


# --- Upload Background Image (Optional) ---
# This section handles file uploads for a background image on the canvas.
# It checks if a new file is uploaded or if an existing one is cleared,
# and triggers a state reset and rerun if necessary.
uploaded_file = st.file_uploader("Upload background image (optional, e.g. structure or diagram)", type=["png", "jpg", "jpeg"])

# Flag to determine if a reset/rerun is needed due to file upload/clear.
# This helps consolidate the rerun request at the end of the script.
needs_file_update_and_rerun = False

# Condition 1: A file has been uploaded via the uploader.
if uploaded_file is not None:
    if st.session_state.debug_mode: st.info(f"DEBUG: File uploader has a file: {uploaded_file.name}.") # Debug: confirm file is seen by widget

    # Check if this is a genuinely NEW file (different filename) or if it's the SAME file
    # being re-uploaded/persisted by Streamlit.
    # CRITICAL FIX: Add explicit check for 'last_uploaded_filename' in session_state
    if "last_uploaded_filename" not in st.session_state or st.session_state.last_uploaded_filename != uploaded_file.name:
        if st.session_state.debug_mode: st.info(f"DEBUG: New file detected (or re-selected): {uploaded_file.name}. Processing...")
        
        img0 = Image.open(BytesIO(uploaded_file.getvalue()))
        w, h = img0.size
        if w > MAX_CANVAS_WIDTH: # Resize if image is too wide
            img0 = img0.resize((MAX_CANVAS_WIDTH, int(h * MAX_CANVAS_WIDTH / w)), Image.LANCZOS) # Resize image
        buf = BytesIO()
        img0.save(buf, format="PNG")
        
        st.session_state.bg_image_bytes = buf.getvalue() # Store image bytes
        st.session_state.last_uploaded_filename = uploaded_file.name # Store filename
        if st.session_state.debug_mode: st.info(f"DEBUG: app_equilibrium: Called reset_all_app_state() after new file upload.")
        needs_file_update_and_rerun = True # Indicate that a rerun is needed
    else:
        if st.session_state.debug_mode: st.info("DEBUG: File uploader has same file as last processed. No reprocessing initiated by this block.")

# Condition 2: No file is currently in the uploader (uploaded_file is None).
# This branch executes if the user has cleared the file or no file was ever selected.
# CRITICAL FIX: Add explicit checks for 'bg_image_bytes' and 'last_uploaded_filename' in session_state
elif ("bg_image_bytes" in st.session_state and st.session_state.bg_image_bytes is not None) or \
     ("last_uploaded_filename" in st.session_state and st.session_state.last_uploaded_filename is not None):
    
    if st.session_state.debug_mode: st.info("DEBUG: File uploader is empty. Clearing any previously loaded background image from session state.")
    st.session_state.bg_image_bytes = None # Clear image bytes
    st.session_state.last_uploaded_filename = None # Clear filename
    
    reset_all_app_state() # Reset other app-related state.
    if st.session_state.debug_mode: st.info(f"DEBUG: app_equilibrium: Called reset_all_app_state() after clearing file.")
    needs_file_update_and_rerun = True # Indicate that a rerun is needed
else:
    if st.session_state.debug_mode: st.info("DEBUG: No file uploaded, and no previous file found in session state.")

# If a rerun has been requested by the file handling logic, set the main trigger flag.
if needs_file_update_and_rerun:
    st.session_state.trigger_rerun_after_logic = True
    if st.session_state.debug_mode: st.info(f"DEBUG: app_equilibrium: Setting trigger_rerun_after_logic to True due to file change.")


# --- Canvas & Origin Setup ---
# Determine canvas dimensions and background image based on upload status.
if st.session_state.bg_image_bytes:
    bg_image = Image.open(BytesIO(st.session_state.bg_image_bytes)) # Load uploaded image
    W, H = bg_image.size # Use image dimensions
else: # Default white canvas if no image uploaded
    W, H = MAX_CANVAS_WIDTH, DEFAULT_CANVAS_HEIGHT # Use default dimensions
    bg_image = Image.new("RGB", (W, H), "white") # Create a white background image

# Set default origin to center of canvas if not already defined.
if st.session_state.origin is None:
    st.session_state.origin = (W // 2, H // 2) # Set origin to center of canvas
origin = st.session_state.origin # Use a local variable for clarity

# ==============================================================================
# --- SIDEBAR CONTENT (ALL INPUTS & MAIN ACTIONS) ---
# This section is organized to place global controls, then solve button,
# then individual force properties, and finally reset options.
# ==============================================================================
with st.sidebar:
    
    st.title("🎛 Controls")

    with st.expander("🖼 Background & Canvas Setup", expanded=True):
        handle_origin_selection_ui(W, H)

    # --- Section 2: Force Inputs ---
    with st.expander("➕ Force Vectors", expanded=True):
        # SIMPLIFIED TEXT HERE: Keep only the general angle convention
        st.write("Angles: 0° is rightward, +CCW.")

        # Add the "Add Force" button as requested
        if st.button("➕ Add Force Manually"):
            # Create a new, empty vector. Magnitude and angle will be None.
            # drawn_length is 0.0 because it's not drawn.
            st.session_state.vectors.append(Vector(angle=None, magnitude=None, drawn_length=0.0))
            # Trigger a rerun to display the new empty force inputs immediately
            st.session_state.trigger_rerun_after_logic = True
            if st.session_state.debug_mode: st.info("DEBUG: Added new empty vector.")

        # This function will now handle the conditional instructions and force inputs
        render_force_properties_sidebar_content()

        # --- NEW POSITION FOR DRAWING SCALE SETTINGS ---
        st.markdown("---") # Separator between force inputs and scale settings
        st.subheader("Drawing Scale Settings") # Subheader for this section
        render_drawing_scale_settings() # Call the function here
        # --- END NEW POSITION ---

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

    # The old "Drawing Scale Settings" expander from the end is now removed.

st.sidebar.caption("All angles: 0° is right, +CCW. Blank for symbolic solve.")


# --- Main Canvas Area ---
# This handles both the origin picking mode and the normal drawing mode.

if st.session_state.get("pick_origin_mode", False):
    # Origin pick mode: Show a canvas with a background image and let user click
    from ui.canvas_interaction import render_origin_pick_canvas # Ensure this import is correct
    render_origin_pick_canvas(W, H, bg_image)
else:
    # Normal drawing mode: draw forces on the main canvas
    if st.session_state.debug_mode: st.info("DEBUG: Calling handle_force_drawing_input.")
    handle_force_drawing_input(W, H, origin, bg_image)
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

                # --- NEW: Render FBD with solved values for each solution ---
                st.subheader(f"Free Body Diagram (Solution {idx})") # Subheader for solved FBD
                render_free_body_diagram(
                    vectors=st.session_state.vectors, # Pass original vectors for iteration
                    origin=origin,
                    W=W, H=H,
                    bg_image=bg_image,
                    is_equilibrium_app=True,
                    solution_context=sol, # Pass the current solution to FBD
                    F_syms=F_syms, theta_syms_rad=theta_syms_rad,
                    R_sym=None, alpha_sym_rad=None
                )
                # --- END NEW FBD ---

                st.subheader(f"Force Polygon (Solution {idx})") # Subheader for force polygon
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
    # This block now handles the scenario where all inputs are numeric AND solve button was NOT clicked.
    # It still runs the equilibrium check and polygon, but it's now an 'elif' to the solve block.
    st.subheader("3️⃣ Force Polygon & Equilibrium Check (Numeric Inputs)")
    if st.session_state.debug_mode: st.info("DEBUG: Displaying dynamic numeric force polygon for equilibrium check.")

    # Call the renderer function for dynamic display
    render_force_polygon_diagram(
        vectors=st.session_state.vectors,
        origin=origin,
        W=W, H=H,
        bg_image=bg_image,
        is_equilibrium_app=True,
        solution_context=None, # No solved context for dynamic display
        F_syms=None, theta_syms_rad=None, R_sym=None, alpha_sym_rad=None
    )
else:
    st.info("Draw forces or click 'Solve for Unknowns' to see results.")

# --- Pick Origin Mode (TEMPORARY CANVAS) ---
# This block activates when the user clicks "Pick Origin on Canvas".
# It displays a special canvas for picking a single point.
# This is placed at the end as it temporarily takes over the main content area.
if st.session_state.pick_origin_mode: # If in origin picking mode
    st.subheader("Click anywhere on the canvas to set the new origin") # User instruction
    # The actual canvas and processing for picking the origin is now fully handled
    # within the handle_origin_selection_ui function (called in the sidebar section).
    # This 'pass' ensures no redundant canvas rendering occurs here.
    pass


# --- Final Rerun Logic ---
# This is the single, centralized point where Streamlit reruns are triggered.
# It checks the 'trigger_rerun_after_logic' flag which is set by various user interactions
# (file upload/clear, drawing forces, changing force properties, picking origin, clearing all).
if st.session_state.debug_mode: 
    st.info(f"--- SCRIPT END --- Checking trigger_rerun_after_logic: {st.session_state.trigger_rerun_after_logic}")
    st.info(f"--- SCRIPT END --- Current canvas_reset before final check: {st.session_state.canvas_reset}")

if st.session_state.trigger_rerun_after_logic:
    if st.session_state.debug_mode: st.info("DEBUG: Triggering st.experimental_rerun()!")

    # Atomically update state variables relevant to the rerun.
    # This sets the rerun flag to False and increments canvas_reset for the next rendering.
    st.session_state.update({
        "trigger_rerun_after_logic": False,
        "canvas_reset": st.session_state.canvas_reset + 1
    })

    if st.session_state.debug_mode: st.info(f"DEBUG: canvas_reset incremented to {st.session_state.canvas_reset} before rerun.")
    st.experimental_rerun()