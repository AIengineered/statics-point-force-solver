# concurrent_force_solver/solver/equilibrium_solver.py
import streamlit as st
import sympy as sp
import math
from typing import List, Dict, Any

# Import our custom modules
from core.data_models import Vector # Imports the Vector dataclass for type hinting and object creation
from core.geometry_utils import normalize_angle_radians # Utility for normalizing angles to 0-2pi radians, useful for internal calculations
from solver.common import format_latex_sum_with_constants # Helper to format LaTeX expressions for display
from core.config import NUMERIC_ZERO_TOLERANCE # Constant for numerical comparison to zero, e.g., checking for equilibrium

def solve_for_equilibrium(vectors: List[Vector]) -> Dict[str, Any]:
    """
    Solves for unknown forces and angles required to achieve equilibrium (Resultant = 0).

    Args:
        vectors (List[Vector]): A list of Vector dataclass objects representing the forces.

    Returns:
        Dict[str, Any]: A dictionary containing various results and debug information.
    """
    if st.session_state.debug_mode: st.info("DEBUG: Entering solve_for_equilibrium function.") # Debug message indicating function entry
    if st.session_state.debug_mode: st.info(f"Debug: Input vectors: {vectors}") # Debug message showing the input force vectors

    # 1) Build SymPy symbols and expressions for sum of components.
    n = len(vectors) # Get the number of force vectors
    # Create SymPy symbols for force magnitudes (e.g., F1, F2, F3)
    F_syms = [sp.Symbol(f"F{i+1}", real=True) for i in range(n)] # 'real=True' ensures SymPy treats them as real numbers
    # Create SymPy symbols for angles in radians (e.g., theta_F1_rad, theta_F2_rad)
    theta_syms_rad = [sp.Symbol(f"theta_F{i+1}_rad", real=True) for i in range(n)] # Angles are handled in radians for SymPy's trigonometric functions

    # --- INITIALIZE SUMMATION VARIABLES AND LISTS *BEFORE* THE LOOP ---
    # Initialize symbolic expressions for the sum of x and y components.
    # Using sp.Float(0.0) ensures SymPy handles these as precise floating-point numbers.
    sum_fx_expr = sp.Float(0.0) # Accumulates the symbolic sum of all force x-components
    sum_fy_expr = sp.Float(0.0) # Accumulates the symbolic sum of all force y-components

    # Lists to hold LaTeX terms for display, preserving original trig functions
    sum_fx_latex_raw_trig_terms = []
    sum_fy_latex_raw_trig_terms = []
    
    # Numeric sums of known force components (for evaluating the constant part of the equation)
    constant_fx_sum = sp.Float(0.0)
    constant_fy_sum = sp.Float(0.0)
    
    # Lists to hold LaTeX terms for symbolic parts of the evaluated equations
    symbolic_fx_latex_terms = []
    symbolic_fy_latex_terms = []

    # List to keep track of all symbols that are currently unknown and need to be solved for
    unknown_symbols = []

    # Iterate through each force vector to build the summation expressions
    for i, vec_obj in enumerate(vectors):
        current_mag_input = vec_obj.magnitude # Get the magnitude from the Vector object
        current_angle_input = vec_obj.angle   # Get the angle (in degrees or None) from the Vector object

        # Determine the expression for force magnitude (numeric or symbolic) and its LaTeX string
        if isinstance(current_mag_input, (float, int)): # If magnitude is a known number
            mag_expr = sp.Float(current_mag_input) # Use its numeric value as a SymPy Float
            mag_latex = f"{current_mag_input:.1f}" # Format for LaTeX display
        elif current_mag_input is None or (isinstance(current_mag_input, str) and current_mag_input.strip() == ""):
            mag_expr = F_syms[i] # If blank or None, use the corresponding symbolic F_sym
            mag_latex = sp.latex(F_syms[i]) # Get its LaTeX representation (e.g., F_{1})
            unknown_symbols.append(F_syms[i]) # Add this force magnitude to the list of unknowns
        else:
            # Handle invalid non-numeric input for magnitude
            st.error(f"Invalid magnitude input for F{i+1}: '{current_mag_input}'. Please enter a number or leave blank.")
            return {"error": True} # Return an error flag

        # Determine the expression for angle (radians, numeric or symbolic) and its LaTeX string
        if isinstance(current_angle_input, (float, int)): # If angle is a known number (degrees)
            ang_rad_for_expr = sp.Float(math.radians(current_angle_input)) # Convert to radians for SymPy's trig functions
            angle_latex_deg = f"{current_angle_input:.0f}^\\circ" # Format for LaTeX display (e.g., 90^\circ)
        elif current_angle_input is None or (isinstance(current_angle_input, str) and current_angle_input.strip() == ""):
            ang_rad_for_expr = theta_syms_rad[i] # If blank or None, use the corresponding symbolic theta_F_rad
            angle_latex_deg = sp.latex(theta_syms_rad[i]).replace('_rad', '') # Get LaTeX, remove '_rad' for cleaner display
            unknown_symbols.append(theta_syms_rad[i]) # Add this angle to the list of unknowns
        else:
            # Handle invalid non-numeric input for angle
            st.error(f"Invalid angle input for θ{i+1}: '{current_angle_input}'. Please enter a number or leave blank.")
            return {"error": True} # Return an error flag

        # Add the x and y components of the current force to the total sums
        sum_fx_expr += mag_expr * sp.cos(ang_rad_for_expr) # F_x = F * cos(theta)
        sum_fy_expr += mag_expr * sp.sin(ang_rad_for_expr) # F_y = F * sin(theta)

        # Populate lists for raw LaTeX display of trigonometric terms
        sum_fx_latex_raw_trig_terms.append(f"{mag_latex} \\cos({angle_latex_deg})")
        sum_fy_latex_raw_trig_terms.append(f"{mag_latex} \\sin({angle_latex_deg})")

        # Populate constant and symbolic terms for the evaluated LaTeX display
        if isinstance(current_mag_input, (float, int)) and isinstance(current_angle_input, (float, int)):
            # If both are numeric, add to constant sums
            constant_fx_sum += sp.Float(current_mag_input) * sp.cos(sp.Float(math.radians(current_angle_input)))
            constant_fy_sum += sp.Float(current_mag_input) * sp.sin(sp.Float(math.radians(current_angle_input)))
        elif isinstance(current_mag_input, (float, int)):
            # If only magnitude is numeric, angle is symbolic
            symbolic_fx_latex_terms.append(f"{current_mag_input:.3f} \\cos({angle_latex_deg})")
            symbolic_fy_latex_terms.append(f"{current_mag_input:.3f} \\sin({angle_latex_deg})")
        elif isinstance(current_angle_input, (float, int)):
            # If only angle is numeric, magnitude is symbolic
            cos_val = math.cos(math.radians(current_angle_input))
            sin_val = math.sin(math.radians(current_angle_input))
            # Format coefficients for symbolic terms to avoid "1.000 F" or "0.000 F"
            fx_term_eval = f"{cos_val:.3f} {mag_latex}" if abs(cos_val) not in [0.0, 1.0] else (f"{mag_latex}" if cos_val == 1.0 else (f"-{mag_latex}" if cos_val == -1.0 else "0"))
            fy_term_eval = f"{sin_val:.3f} {mag_latex}" if abs(sin_val) not in [0.0, 1.0] else (f"{mag_latex}" if sin_val == 1.0 else (f"-{mag_latex}" if sin_val == -1.0 else "0"))
            symbolic_fx_latex_terms.append(fx_term_eval)
            symbolic_fy_latex_terms.append(fy_term_eval)
        else:
            # If both magnitude and angle are symbolic
            symbolic_fx_latex_terms.append(f"{mag_latex} \\cos({angle_latex_deg})")
            symbolic_fy_latex_terms.append(f"{mag_latex} \\sin({angle_latex_deg})")

    # Define the two fundamental equilibrium equations: sum of forces in X and Y equals zero.
    # sp.Eq creates an equality expression for SymPy to solve.
    eq1 = sp.Eq(sum_fx_expr, sp.Float(0)) # Sum of forces in X direction equals zero
    eq2 = sp.Eq(sum_fy_expr, sp.Float(0)) # Sum of forces in Y direction equals zero

    equations = [eq1, eq2] # Collect equations into a list for SymPy's solver
    if st.session_state.debug_mode: st.info(f"Debug: Equations: Eq1={eq1}, Eq2={eq2}") # Debug: show the formulated equations
    if st.session_state.debug_mode: st.info(f"Debug: Unknown symbols to solve for: {unknown_symbols}") # Debug: show identified unknowns

    all_sols = [] # List to store all solutions found by SymPy
    _calculated_R_mag = 0.0 # Internal placeholder for resultant magnitude if all forces are known
    _calculated_R_alpha = 0.0 # Internal placeholder for resultant angle if all forces are known

    # Logic for when there are NO unknowns to solve for (all inputs are numeric).
    # In this case, the program checks if the system is actually in equilibrium.
    if not unknown_symbols:
        #if st.session_state.debug_mode: st.info("DEBUG: All variables are known. Checking for equilibrium.") # Debug: All inputs are numbers
        # Calculate the numerical sum of Fx and Fy components for all known vectors.
        sum_fx_n = float(sum_fx_expr) # Evaluate the symbolic expression numerically for Fx
        sum_fy_n = float(sum_fy_expr) # Evaluate the symbolic expression numerically for Fy

        res_mag_n = round(math.hypot(sum_fx_n, sum_fy_n), 3) # Calculate numerical resultant magnitude
        res_ang_n = round(math.degrees(math.atan2(sum_fy_n, sum_fx_n)), 2) # Calculate numerical resultant angle in degrees
        res_ang_n = res_ang_n % 360 # Normalize angle to 0-360 degrees
        if res_ang_n < 0: res_ang_n += 360 # Ensure positive angle if modulo result is negative

        _calculated_R_mag = res_mag_n # Store for internal use/display
        _calculated_R_alpha = math.radians(res_ang_n) # Store angle in radians for consistency

        if abs(res_mag_n) < NUMERIC_ZERO_TOLERANCE: # Check if resultant magnitude is close to zero (equilibrium)
            st.success(f"**System is in Equilibrium!** (Resultant is approximately 0)") # Display success message
        else:
            st.warning(f"**System is NOT in Equilibrium.** Resultant: {res_mag_n} units @ {res_ang_n}°. To achieve equilibrium, the resultant should be 0.") # Display warning

        # Create a dummy solution for drawing purposes (contains original vector data)
        # This allows the renderer to draw the polygon even when no symbolic solve occurred.
        all_sols_for_drawing = [{"_calculated_R_mag": res_mag_n, "_calculated_R_alpha": math.radians(res_ang_n)}]
        for i, vec_obj in enumerate(vectors):
            if isinstance(vec_obj.magnitude, (float, int)):
                all_sols_for_drawing[0][F_syms[i]] = sp.Float(vec_obj.magnitude) # Add known magnitudes to the "solution" dict
            if isinstance(vec_obj.angle, (float, int)):
                all_sols_for_drawing[0][theta_syms_rad[i]] = sp.Float(math.radians(vec_obj.angle)) # Add known angles (converted to radians)
        all_sols = all_sols_for_drawing # Set the main solution list to this dummy solution
        
    else: # There are unknowns, attempt to solve symbolically
        # Check for solvability (number of equations vs. number of unknowns)
        if len(unknown_symbols) > len(equations): # More unknowns than equations (underdetermined)
            st.warning(f"Underdetermined system: {len(unknown_symbols)} unknowns but only {len(equations)} equations. Solutions may not be unique or may contain free parameters.")
        elif len(unknown_symbols) < len(equations): # Fewer unknowns than equations (overdetermined)
            st.warning(f"Overdetermined system: {len(unknown_symbols)} unknowns but {len(equations)} equations. Solutions might not exist.")
        
        # Use a try-except block to gracefully handle potential errors during the symbolic solving process
        try:
            # Identify if this is the simple case of solving for one unknown Force and one unknown Angle
            unknown_F_syms = [s for s in unknown_symbols if s in F_syms]
            unknown_theta_syms_rad = [s for s in unknown_symbols if s in theta_syms_rad]

            is_simple_F_theta_case = False
            # Check if there's exactly one unknown magnitude and one unknown angle, and they correspond to the same force
            if len(unknown_F_syms) == 1 and len(unknown_theta_syms_rad) == 1:
                f_idx = F_syms.index(unknown_F_syms[0])
                theta_idx = theta_syms_rad.index(unknown_theta_syms_rad[0])
                if f_idx == theta_idx:
                    is_simple_F_theta_case = True
                    if st.session_state.debug_mode: st.info(f"Debug: Identified simple F/theta case for F{f_idx+1}.")

            if is_simple_F_theta_case:
                if st.session_state.debug_mode: st.info("DEBUG: Attempting direct numerical solution for F and theta unknowns (Equilibrium).")

                # The required components of the unknown force to balance the system for equilibrium
                # These are the negative of the sum of the known (constant) components.
                required_fx = -float(constant_fx_sum)
                required_fy = -float(constant_fy_sum)
                
                F_solved = math.hypot(required_fx, required_fy) # Magnitude is hypotenuse of required components
                theta_solved = math.atan2(required_fy, required_fx) # Angle is atan2 of required components (in radians)
                
                # Create a solution dictionary for this simple case
                sol = {unknown_F_syms[0]: sp.Float(F_solved), unknown_theta_syms_rad[0]: sp.Float(theta_solved)}
                all_sols = [sol] # Store it as the only solution
                if st.session_state.debug_mode: st.info("DEBUG: Direct numerical solution found for F and theta.")
            else:
                # Fallback to general SymPy's solve function for more complex scenarios (e.g., multiple unknowns, only angles, etc.)
                if st.session_state.debug_mode: st.info("DEBUG: Falling back to general SymPy solve.")
                solution_set = sp.solve(equations, unknown_symbols, dict=True) # Solve the system of equations for the unknowns
                if st.session_state.debug_mode: st.info(f"Debug: SymPy solution set: {solution_set}")

                # Filter for real number solutions (physical solutions)
                real_sols = [sol for sol in solution_set if all(s.is_real for s in sol.values())]

                preferred_sols = []
                for sol in real_sols:
                    is_preferred = True
                    for var, val in sol.items():
                        if isinstance(val, (sp.Float, float, int)):
                            # Prefer solutions where force magnitudes are positive
                            if (var in F_syms and float(val) < 0):
                                is_preferred = False
                                break # If any force is negative, this is not a preferred solution
                    if is_preferred:
                        preferred_sols.append(sol) # Collect preferred solutions

                if preferred_sols:
                    all_sols = preferred_sols # Use preferred solutions if found
                    if st.session_state.debug_mode: st.info(f"Debug: Preferred solutions (positive magnitudes): {len(all_sols)}")
                elif real_sols:
                    st.warning("No solutions with all positive magnitudes found. Displaying real solutions which may include negative magnitudes (indicating reversed direction).")
                    all_sols = real_sols # Otherwise, use any real solutions
                    if st.session_state.debug_mode: st.info(f"Debug: Real solutions (may include negative magnitudes): {len(all_sols)}")
                elif solution_set:
                    st.warning("No real solutions found for the given conditions. Displaying potential complex solutions (not typically physical for forces).")
                    all_sols = solution_set # As a last resort, show complex solutions
                    if st.session_state.debug_mode: st.info(f"Debug: Complex solutions: {len(all_sols)}")
                else:
                    st.info("No solutions found for the given system.")

        except Exception as e: # Catch any other exceptions that occur during solving
            st.error(f"An error occurred during symbolic solving: {e}") # Display the error message
            st.info("Please check your inputs and ensure the system is solvable (e.g., number of equations matches number of unknowns).")
            all_sols = [] # Clear solutions if an error occurs to prevent drawing issues

    # If all_sols is still empty after attempting to solve, it means no valid solutions were found
    if not all_sols:
        st.info("No solutions found for the given system.")

    # Return the results in a dictionary
    return {
        'all_sols': all_sols, # All computed solutions
        'F_syms': F_syms, # SymPy symbols for magnitudes
        'theta_syms_rad': theta_syms_rad, # SymPy symbols for angles
        'sum_fx_latex_raw_trig_terms': sum_fx_latex_raw_trig_terms, # Raw LaTeX terms for Fx equation
        'sum_fy_latex_raw_trig_terms': sum_fy_latex_raw_trig_terms, # Raw LaTeX terms for Fy equation
        'constant_fx_sum': constant_fx_sum, # Sum of known Fx components
        'constant_fy_sum': constant_fy_sum, # Sum of known Fy components
        'symbolic_fx_latex_terms': symbolic_fx_latex_terms, # LaTeX terms for symbolic Fx parts
        'symbolic_fy_latex_terms': symbolic_fy_latex_terms, # LaTeX terms for symbolic Fy parts
        'unknown_symbols': unknown_symbols, # List of all symbols that were solved for
        'error': False, # Flag indicating no error occurred within this function
        '_calculated_R_mag': _calculated_R_mag, # Calculated Resultant magnitude (if all inputs known)
        '_calculated_R_alpha': _calculated_R_alpha # Calculated Resultant angle (if all inputs known)
    }