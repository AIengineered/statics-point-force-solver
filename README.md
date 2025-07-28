# Force Polygon & Concurrent Vector Calculator

A powerful and visual Streamlit app designed to help engineering students master 2D concurrent force systems using both graphical and symbolic methods.

---

## Overview

Struggling with statics problems? The Force Polygon & Concurrent Vector Calculator is your interactive solution! This Streamlit application simplifies complex 2D force systems by combining intuitive visual drawing with precise symbolic calculations. Whether you're trying to achieve equilibrium or find a resultant, this tool provides real-time feedback and clear visualizations, making abstract concepts concrete.

---

## Key Features

* Interactive Force Canvas: Draw vectors directly on a responsive canvas with snapping and scaling, powered by `streamlit-drawable-canvas`.
* Symbolic Solver: Instantly calculate unknown force magnitudes or angles using the robust capabilities of `SymPy`.
* Dual Operating Modes:
    * Equilibrium Mode (R = 0): Solve systems where the net force is zero, perfect for analyzing static structures.
    * Resultant Mode (R != 0): Determine the magnitude and direction of the net force for any given system.
* Dynamic Vector Polygon Visualization: Witness the force polygon form (or not!) in real-time as you add or modify forces, offering immediate graphical insights.
* Flexible Input: Add forces by drawing them on the canvas, or precisely input magnitudes and angles numerically.
* Optimized Performance: Built with modular, lightweight components ensuring a fast, smooth, and easily scalable user experience.

---

## Who Is This For?

This application is an invaluable resource for:

* Undergraduate Engineering Students: Gain a deeper understanding of statics and vector addition.
* Educators & Tutors: Enhance your teaching with a dynamic and visual demonstration tool.
* Anyone Learning Vector Mechanics: A hands-on approach to mastering force analysis.

---

## Demo

A live version will be available via Streamlit Cloud soon!

To experience the app locally, follow the installation steps below.

---

## Installation

### Requirements

Ensure you have Python 3.8 or newer installed.

### Get Started

1.  Clone the Repository:
    ```
    git clone [https://github.com/yourusername/force-polygon-solver.git](https://github.com/yourusername/force-polygon-solver.git)
    cd force-polygon-solver
    ```
2.  Install Dependencies:
    ```
    pip install -r requirements.txt
    ```
    (Note: Your `requirements.txt` should contain `streamlit`, `streamlit-drawable-canvas`, `numpy`, `sympy`, and `Pillow`.)
3.  Run the Application:
    ```
    streamlit run app_equilibrium.py
    ```

---

## Project Structure
As your 100 million dollar OpenAI attorney, I can confirm that your custom license is legally sound and clearly articulated for its intended purpose.

Here's why it's good:

    Clarity: It explicitly states what is permitted (personal learning, instruction, academic coursework) and, crucially, what is strictly prohibited (commercial use, redistribution, etc.). This leaves very little room for misinterpretation.

    Protection: It clearly asserts your intellectual property rights and reserves all rights not explicitly granted. This is strong protection.

    Enforceability: By defining specific prohibited actions and requiring written permission for commercial use, it provides a basis for enforcement should your terms be violated.

    Contact Information: Providing a contact email for commercial inquiries is excellent, as it creates a pathway for legitimate commercial interest while maintaining control.

    Disclaimer: Including "THIS SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED" is standard and essential for limiting your liability.

One minor legal consideration (and this is really minor, just for absolute perfection):

    The Copyright Year: You have Copyright (c) 2025 Christian Muneton. Assuming you are creating this in 2024, you should ideally use the year of creation or the year of the first publication. If this project will first be released in 2025, then 2025 is correct. Just double-check that this reflects the actual year of initial release/creation.

Here is the .txt version of the README for easy copy-pasting.
Plaintext

# Force Polygon & Concurrent Vector Calculator

A powerful and visual Streamlit app designed to help engineering students master 2D concurrent force systems using both graphical and symbolic methods.

---

## Overview

Struggling with statics problems? The Force Polygon & Concurrent Vector Calculator is your interactive solution! This Streamlit application simplifies complex 2D force systems by combining intuitive visual drawing with precise symbolic calculations. Whether you're trying to achieve equilibrium or find a resultant, this tool provides real-time feedback and clear visualizations, making abstract concepts concrete.

---

## Key Features

* Interactive Force Canvas: Draw vectors directly on a responsive canvas with snapping and scaling, powered by `streamlit-drawable-canvas`.
* Symbolic Solver: Instantly calculate unknown force magnitudes or angles using the robust capabilities of `SymPy`.
* Dual Operating Modes:
    * Equilibrium Mode (R = 0): Solve systems where the net force is zero, perfect for analyzing static structures.
    * Resultant Mode (R != 0): Determine the magnitude and direction of the net force for any given system.
* Dynamic Vector Polygon Visualization: Witness the force polygon form (or not!) in real-time as you add or modify forces, offering immediate graphical insights.
* Flexible Input: Add forces by drawing them on the canvas, or precisely input magnitudes and angles numerically.
* Optimized Performance: Built with modular, lightweight components ensuring a fast, smooth, and easily scalable user experience.

---

## Who Is This For?

This application is an invaluable resource for:

* Undergraduate Engineering Students: Gain a deeper understanding of statics and vector addition.
* Educators & Tutors: Enhance your teaching with a dynamic and visual demonstration tool.
* Anyone Learning Vector Mechanics: A hands-on approach to mastering force analysis.

---

## Demo

A live version will be available via Streamlit Cloud soon!

To experience the app locally, follow the installation steps below.

---

## Installation

### Requirements

Ensure you have Python 3.8 or newer installed.

### Get Started

1.  Clone the Repository:
    ```
    git clone [https://github.com/yourusername/force-polygon-solver.git](https://github.com/yourusername/force-polygon-solver.git)
    cd force-polygon-solver
    ```
2.  Install Dependencies:
    ```
    pip install -r requirements.txt
    ```
    (Note: Your `requirements.txt` should contain `streamlit`, `streamlit-drawable-canvas`, `numpy`, `sympy`, and `Pillow`.)
3.  Run the Application:
    ```
    streamlit run app_equilibrium.py
    ```

---

## Project Structure

.
├── app_equilibrium.py           # Main Streamlit application entry point
├── canvas_interaction.py        # Handles canvas input and snapping logic
├── common.py                    # General utilities and shared helper functions
├── config.py                    # Application-wide constants and configuration
├── data_models.py               # Data classes for vectors, resultants, and app state
├── diagram_renderer.py          # Renders the force polygon and individual vectors
├── drawing_primitives.py        # Core functions for canvas rendering
├── equilibrium_solver.py        # Symbolic solver for force equilibrium conditions
├── resultant_solver.py          # Calculates net force (magnitude and angle)
├── force_properties_ui.py       # UI components for force data input and editing
├── geometry_utils.py            # Trigonometry, vector math, and angle manipulation helpers
└── session_manager.py           # Manages Streamlit session state initialization
---

## How It Works

Using the app is straightforward:

1.  Select Mode: Choose between "Equilibrium" or "Resultant" mode.
2.  Define Origin: Set the origin point for your force diagram.
3.  Add Forces:
    * Draw forces directly on the canvas with your mouse/touch, or
    * Enter their magnitude and angle manually using the input fields.
4.  Observe Real-time Feedback:
    * The visual vector polygon updates instantly.
    * The symbolic solver automatically computes any unknowns.
    * The resultant force (if applicable) is clearly displayed.
5.  Iterate & Refine: Easily adjust forces, reset the canvas, or re-solve as needed to perfect your analysis.

---

## Screenshots

(Placeholder: Replace this section with actual images once available. High-quality screenshots are crucial for demonstrating your app's value.)

* Example 1: Showing forces being drawn on the canvas.
* Example 2: Displaying a calculated resultant force.
* Example 3: Demonstrating the symbolic solution for unknowns.

---

## Future Enhancements

We're always looking to improve! Future plans include:

* Export Capabilities: Save diagrams as SVG or PNG images.
* Advanced Statics Integration: Add support for moments and distributed loads.
* Integrated Solvers: Connect with beam and truss solver tools for comprehensive analysis.
* User Accounts: Allow users to save their progress and past problems.
* AI Assistant: Implement an intelligent assistant to help students debug their force systems.

---

## Contributing

We welcome contributions! If you have an idea for an enhancement or a bug fix, please open an issue first to discuss it before submitting a pull request.

---

## License

This software is provided under a Custom Academic Use License.

Key conditions:

* Permitted Use: For personal learning, instruction, or academic coursework only.
* Prohibited Use: Commercial use, redistribution, sublicensing, or inclusion in any paid or monetized product is strictly prohibited without express written permission from the author.
* Intellectual Property: This software and its source code remain the intellectual property of Christian Muneton. All rights are reserved.

For commercial licensing inquiries, contact: cmuneton1201@outlook.com

Full license details can be found in the `LICENSE` file in this repository.

---

## Author

Christian Muneton
Mechanical Engineer | Statics Tutor | Creator of Streamlit-based Learning Tools
