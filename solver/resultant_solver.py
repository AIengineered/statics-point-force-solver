# concurrent_force_solver/solver/resultant_solver.py
import streamlit as st
import sympy as sp
import math
from typing import List, Dict, Any

# Import our custom modules
from core.data_models import Vector # Imports the Vector dataclass for type hinting and object creation
from core.geometry_utils import normalize_angle_radians # Utility for normalizing angles to 0-2pi radians, useful for internal calculations
from solver.common import format_latex_sum_with_constants # Helper to format LaTeX expressions for display
from core.config import NUMERIC_ZERO_TOLERANCE # Constant for numerical comparison to zero, e.g., checking for equilibrium

def solve_for_resultant(vectors: List[Vector], user_R_value_str: str, user_alpha_value_str: str) -> Dict[str, Any]:
    """
    Solves for the resultant of a system of concurrent forces, including unknowns.

    Args:
        vectors (List[Vector]): A list of Vector dataclass objects representing the forces.
        user_R_value_str (str): User input string for known resultant magnitude R (blank if unknown).
        user_alpha_value_str (str): User input string for known resultant angle alpha (blank if unknown).

    Returns:
        Dict[str, Any]: A dictionary containing:
                        - 'all_sols': List of solution dictionaries from SymPy.
                        - 'F_syms': List of SymPy force magnitude symbols.
                        - 'theta_syms_rad': List of SymPy angle symbols (in radians).
                        - 'R_sym': SymPy symbol for resultant magnitude.
                        - 'alpha_sym_rad': SymPy symbol for resultant angle (radians).
                        - 'sum_fx_latex_raw_trig_terms': For LaTeX display.
                        - 'sum_fy_latex_raw_trig_terms': For LaTeX display.
                        - 'constant_fx_sum': Numeric sum of known Fx components.
                        - 'constant_fy_sum': Numeric sum of known Fy components.
                        - 'symbolic_fx_latex_terms': LaTeX terms for symbolic Fx parts.
                        - 'symbolic_fy_latex_terms': LaTeX terms for symbolic Fy parts.
                        - 'current_R_expr': The expression used for R in equations.
                        - 'current_alpha_rad_expr': The expression used for alpha in equations.
                        - 'unknown_symbols': List of SymPy symbols solved for.
                        - 'error': Boolean indicating if an error occurred.
    """
    ##st.info("DEBUG: Entering solve_for_resultant function.") # Debug message
    st.info(f"DEBUG: Input vectors: {vectors}") # Debug message
    st.info(f"DEBUG: user_R_value_str: '{user_R_value_str}', user_alpha_value_str: '{user_alpha_value_str}'") # Debug message

    # 1) Build SymPy symbols and expressions for sum of components.
    n = len(vectors) # Get the number of force vectors
    F_syms = [sp.Symbol(f"F{i+1}", real=True) for i in range(n)] # Create SymPy symbols for force magnitudes (e.g., F1, F2)
    theta_syms_rad = [sp.Symbol(f"theta_F{i+1}_rad", real=True) for i in range(n)] # Create SymPy symbols for angles in radians (e.g., theta_F1_rad)

    # --- INITIALIZE SUMMATION VARIABLES AND LISTS *BEFORE* THE LOOP ---
    # These must be initialized once before iterating through vectors to accumulate sums.
    sum_fx_expr = sp.Float(0.0) # Accumulates the symbolic sum of all force x-components
    sum_fy_expr = sp.Float(0.0) # Accumulates the symbolic sum of all force y-components

    sum_fx_latex_raw_trig_terms = [] # For LaTeX display of raw trigonometric terms
    sum_fy_latex_raw_trig_terms = [] # For LaTeX display of raw trigonometric terms
    
    constant_fx_sum = sp.Float(0.0) # Numeric sum of known Fx components
    constant_fy_sum = sp.Float(0.0) # Numeric sum of known Fy components
    
    symbolic_fx_latex_terms = [] # LaTeX terms for symbolic Fx parts
    symbolic_fy_latex_terms = [] # LaTeX terms for symbolic Fy parts

    unknown_symbols = [] # List to collect all symbols that are currently unknown and need to be solved for

    # Iterate through each force vector to build the summation expressions
    for i, vec_obj in enumerate(vectors):
        current_mag_input = vec_obj.magnitude # Get the magnitude from the Vector object
        current_angle_input = vec_obj.angle # Get the angle (in degrees or None) from the Vector object

        # Determine force magnitude expression (numeric or symbolic) and its LaTeX representation
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
            return {"error": True} # Indicate error

        # Determine angle expression (radians, numeric or symbolic) and its LaTeX representation
        if isinstance(current_angle_input, (float, int)): # If angle is a known number (degrees)
            ang_rad_for_expr = sp.Float(math.radians(current_angle_input)) # Convert to radians for SymPy expr
            angle_latex_deg = f"{current_angle_input:.0f}^\\circ" # Format for LaTeX display (e.g., 90^\circ)
        elif current_angle_input is None or (isinstance(current_angle_input, str) and current_angle_input.strip() == ""):
            ang_rad_for_expr = theta_syms_rad[i] # If blank or None, use the corresponding symbolic theta_F_rad
            angle_latex_deg = sp.latex(theta_syms_rad[i]).replace('_rad', '') # Get LaTeX, remove '_rad' for cleaner display
            unknown_symbols.append(theta_syms_rad[i]) # Add this angle to the list of unknowns
        else:
            # Handle invalid non-numeric input for angle
            st.error(f"Invalid angle input for θ{i+1}: '{current_angle_input}'. Please enter a number or leave blank.")
            return {"error": True} # Indicate error

        # Add the x and y components of the current force to the total sums
        sum_fx_expr += mag_expr * sp.cos(ang_rad_for_expr) # F_x = F * cos(theta)
        sum_fy_expr += mag_expr * sp.sin(ang_rad_for_expr) # F_y = F * sin(theta)

        # Populate lists for raw LaTeX display of trigonometric terms
        sum_fx_latex_raw_trig_terms.append(f"{mag_latex} \\cos({angle_latex_deg})") #
        sum_fy_latex_raw_trig_terms.append(f"{mag_latex} \\sin({angle_latex_deg})") #

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
            symbolic_fx_latex_terms.append(fx_term_eval) #
            symbolic_fy_latex_terms.append(fy_term_eval) #
        else:
            # If both magnitude and angle are symbolic
            symbolic_fx_latex_terms.append(f"{mag_latex} \\cos({angle_latex_deg})") #
            symbolic_fy_latex_terms.append(f"{mag_latex} \\sin({angle_latex_deg})") #

    # Define R and alpha as symbols for the resultant
    R_sym = sp.Symbol("R", real=True) # SymPy symbol for resultant magnitude
    alpha_sym_rad = sp.Symbol("alpha_rad", real=True) # SymPy symbol for resultant angle (in radians)

    current_R_expr = None # Placeholder for R's expression (numeric or symbolic)
    current_alpha_rad_expr = None # Placeholder for alpha's expression (numeric or symbolic)

    # Handle R (magnitude of resultant) input from user
    if user_R_value_str == "": # If user input is blank, R is an unknown
        current_R_expr = R_sym # Use the symbolic R_sym
        unknown_symbols.append(R_sym) # Add R to the list of unknowns to solve for
    else: # If user provided a value for R
        try:
            current_R_expr = sp.Float(user_R_value_str) # Convert to SymPy Float
        except ValueError:
            st.error(f"Invalid numeric input for Resultant Magnitude R: '{user_R_value_str}'. Please enter a number or leave blank.")
            return {"error": True} # Indicate error

    # Handle Alpha (angle of resultant) input from user
    if user_alpha_value_str == "": # If user input is blank, alpha is an unknown
        current_alpha_rad_expr = alpha_sym_rad # Use the symbolic alpha_sym_rad
        unknown_symbols.append(alpha_sym_rad) # Add alpha to the list of unknowns to solve for
    else: # If user provided a value for alpha
        try:
            current_alpha_rad_expr = sp.Float(math.radians(float(user_alpha_value_str))) # Convert degrees to radians and then to SymPy Float
        except ValueError:
            st.error(f"Invalid numeric input for Resultant Angle α: '{user_alpha_value_str}'. Please enter a number or leave blank.")
            return {"error": True} # Indicate error

    # Define the two fundamental equations for resultant: sum of forces in X/Y equals resultant's X/Y components.
    eq1 = sp.Eq(sum_fx_expr, current_R_expr * sp.cos(current_alpha_rad_expr)) # ΣFx = R * cos(α)
    eq2 = sp.Eq(sum_fy_expr, current_R_expr * sp.sin(current_alpha_rad_expr)) # ΣFy = R * sin(α)

    equations = [eq1, eq2] # Collect equations into a list for SymPy's solver
    st.info(f"DEBUG: Equations: Eq1={eq1}, Eq2={eq2}") # Debug: show the formulated equations
    st.info(f"DEBUG: Unknown symbols to solve for: {unknown_symbols}") # Debug: show identified unknowns

    all_sols = [] # List to store all solutions found by SymPy

    # Logic for when there are NO unknowns to solve for (all inputs are numeric).
    # In this case, the program calculates the resultant numerically and checks consistency with user input.
    if not unknown_symbols:
        ##st.info("DEBUG: All variables are known. Calculating numeric resultant.") # Debug message
        # Calculate the numerical sum of Fx and Fy components for all known vectors.
        sum_fx_n = float(sum_fx_expr) # Evaluate the symbolic expression numerically for Fx
        sum_fy_n = float(sum_fy_expr) # Evaluate the symbolic expression numerically for Fy

        res_mag_n_calculated = round(math.hypot(sum_fx_n, sum_fy_n), 3) # Calculate numerical resultant magnitude
        res_ang_n_calculated = round(math.degrees(math.atan2(sum_fy_n, sum_fx_n)), 2) # Calculate numerical resultant angle in degrees
        res_ang_n_calculated = res_ang_n_calculated % 360 # Normalize angle to 0-360 degrees
        if res_ang_n_calculated < 0: res_ang_n_calculated += 360 # Ensure positive angle if modulo result is negative

        # Compare with user-provided R and alpha
        # Use NUMERIC_ZERO_TOLERANCE from config for robust comparison
        is_consistent = (abs(res_mag_n_calculated - float(current_R_expr)) < NUMERIC_ZERO_TOLERANCE and #
                         abs(res_ang_n_calculated - math.degrees(float(current_alpha_rad_expr))) < NUMERIC_ZERO_TOLERANCE) #
        
        if is_consistent:
            st.success(f"**Calculated Resultant:** {res_mag_n_calculated} units @ {res_ang_n_calculated}° (Consistent with input R={float(current_R_expr)}, α={math.degrees(float(current_alpha_rad_expr)):.0f}°)")
        else:
            st.warning(f"**Calculated Resultant:** {res_mag_n_calculated} units @ {res_ang_n_calculated}° \n"
                        f"This is INCONSISTENT with your input Resultant R={float(current_R_expr)}, α={math.degrees(float(current_alpha_rad_expr)):.0f}°. Please check your inputs.")
        
        # Create a dummy solution for drawing purposes (contains calculated resultant and original vector data)
        # This allows the renderer to draw the polygon even when no symbolic solve occurred.
        all_sols_for_drawing = [{R_sym: sp.Float(res_mag_n_calculated), alpha_sym_rad: sp.Float(math.radians(res_ang_n_calculated))}]
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
        try: # <--- Start of the 'try' block
            # Direct numerical solution for the common R, alpha unknowns case.
            # This is more robust than general SymPy solve for this specific pattern.
            is_simple_R_alpha_case = (len(unknown_symbols) == 2 and R_sym in unknown_symbols and alpha_sym_rad in unknown_symbols)

            if is_simple_R_alpha_case:
                #st.info("DEBUG: Attempting direct numerical solution for R and alpha unknowns.") # Debug message
                
                # The resultant components are simply the sum of all known force components
                # Use .subs() to substitute known F and theta values into the sum_fx_expr and sum_fy_expr.
                # This correctly evaluates the numeric sums of components from known forces.
                required_Rx = float(sum_fx_expr.subs({s: v.magnitude if isinstance(v.magnitude, (float, int)) else s for s, v in zip(F_syms, vectors)}).subs({s: math.radians(v.angle) if isinstance(v.angle, (float, int)) else s for s, v in zip(theta_syms_rad, vectors)}))
                required_Ry = float(sum_fy_expr.subs({s: v.magnitude if isinstance(v.magnitude, (float, int)) else s for s, v in zip(F_syms, vectors)}).subs({s: math.radians(v.angle) if isinstance(v.angle, (float, int)) else s for s, v in zip(theta_syms_rad, vectors)}))
                
                R_solved = math.hypot(required_Rx, required_Ry) # Calculate magnitude of resultant
                alpha_solved = math.atan2(required_Ry, required_Rx) # Calculate angle of resultant in radians
                
                sol = {R_sym: sp.Float(R_solved), alpha_sym_rad: sp.Float(alpha_solved)} # Create a solution dictionary
                all_sols = [sol] # Store it as the only solution
                #st.info("DEBUG: Direct numerical solution found for R and alpha.") # Debug message
            else:
                # Fallback to general SymPy solve for other complex scenarios (e.g., solving for an F and theta, or more than 2 unknowns)
                #st.info("DEBUG: Falling back to general SymPy solve.") # Debug message
                solution_set = sp.solve(equations, unknown_symbols, dict=True) # Solve the system of equations for the unknowns
                st.info(f"DEBUG: SymPy solution set: {solution_set}") # Debug: show the SymPy solution set

                real_sols = [sol for sol in solution_set if all(s.is_real for s in sol.values())] # Filter for real number solutions (physical solutions)

                preferred_sols = [] # List to store preferred solutions (e.g., positive magnitudes)
                for sol in real_sols:
                    is_preferred = True # Assume solution is preferred until proven otherwise
                    for var, val in sol.items():
                        if isinstance(val, (sp.Float, float, int)):
                            # Prefer solutions where R magnitude and force magnitudes are positive
                            if (var == R_sym and float(val) < 0) or \
                                (var in F_syms and float(val) < 0):
                                is_preferred = False
                                break # If R or any force is negative, this is not a preferred solution
                    if is_preferred:
                        preferred_sols.append(sol) # Collect preferred solutions

                if preferred_sols:
                    all_sols = preferred_sols # Use preferred solutions if found
                    st.info(f"DEBUG: Preferred solutions (positive magnitudes): {len(all_sols)}")
                elif real_sols:
                    st.warning("No solutions with all positive magnitudes found. Displaying real solutions which may include negative magnitudes (indicating reversed direction).")
                    all_sols = real_sols # Otherwise, use any real solutions
                    st.info(f"DEBUG: Real solutions (may include negative magnitudes): {len(all_sols)}")
                elif solution_set:
                    st.warning("No real solutions found for the given conditions. Displaying potential complex solutions (not typically physical for forces).")
                    all_sols = solution_set # As a last resort, show complex solutions
                    st.info(f"DEBUG: Complex solutions: {len(all_sols)}")
                else:
                    st.info("No solutions found for the given system.")

        except Exception as e: # <--- End of the 'try' block, catch any exceptions during solving
            st.error(f"An error occurred during symbolic solving: {e}") # Display the error message
            st.info("Please check your inputs and ensure the system is solvable (e.g., number of equations matches number of unknowns).") #
            all_sols = [] # Clear solutions if an error occurs to prevent drawing issues

    # If all_sols is still empty after attempting to solve, it means no valid solutions were found
    if not all_sols:
        st.info("No solutions found for the given system.")

    # Return the results in a dictionary
    return {
        'all_sols': all_sols, # All computed solutions
        'F_syms': F_syms, # SymPy symbols for magnitudes
        'theta_syms_rad': theta_syms_rad, # SymPy symbols for angles
        'R_sym': R_sym, # SymPy symbol for resultant magnitude
        'alpha_sym_rad': alpha_sym_rad, # SymPy symbol for resultant angle
        'sum_fx_latex_raw_trig_terms': sum_fx_latex_raw_trig_terms, # Raw LaTeX terms for Fx equation
        'sum_fy_latex_raw_trig_terms': sum_fy_latex_raw_trig_terms, # Raw LaTeX terms for Fy equation
        'constant_fx_sum': constant_fx_sum, # Sum of known Fx components
        'constant_fy_sum': constant_fy_sum, # Sum of known Fy components
        'symbolic_fx_latex_terms': symbolic_fx_latex_terms, # LaTeX terms for symbolic Fx parts
        'symbolic_fy_latex_terms': symbolic_fy_latex_terms, # LaTeX terms for symbolic Fy parts
        'current_R_expr': current_R_expr, # The expression used for R in equations (numeric or symbolic)
        'current_alpha_rad_expr': current_alpha_rad_expr, # The expression used for alpha in equations (numeric or symbolic)
        'unknown_symbols': unknown_symbols, # List of all symbols that were solved for
        'error': False # Flag indicating no error occurred within this function
    }