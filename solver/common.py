# solver_common.py
import sympy as sp

def format_latex_sum_with_constants(constant_sum_val: sp.Float, symbolic_terms_list: list[str]) -> str:
    """
    Helper function to format a sum of terms into a clean LaTeX string,
    combining numerical constants and symbolic expressions.

    Args:
        constant_sum_val (sp.Float): The numerical sum of all constant terms.
        symbolic_terms_list (list[str]): A list of LaTeX strings for symbolic terms.

    Returns:
        str: The formatted LaTeX string representing the sum.
    """
    formatted_parts = []
    # Use a small tolerance for displaying constants as zero to avoid "0.000"
    if abs(constant_sum_val) > 1e-6:
        formatted_parts.append(f"{constant_sum_val:.3f}")
    
    for term in symbolic_terms_list:
        term_stripped = term.strip()
        if term_stripped.startswith('-'): # If term starts with a minus, just append it.
            formatted_parts.append(term_stripped)
        elif formatted_parts: # If there are already terms, add a '+'
            formatted_parts.append(f"+ {term_stripped}")
        else: # If it's the very first term (and constant_sum_val was zero), just add it
            formatted_parts.append(term_stripped)
    
    if not formatted_parts: # If everything sums to zero or is empty
        return "0"
    
    # Clean up any " + -" sequences to just " - "
    return ' '.join(formatted_parts).replace("+ -", "- ")
