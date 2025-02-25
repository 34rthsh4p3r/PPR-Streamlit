# app.py
import streamlit as st
from profile_generator import ProfileGenerator
import pandas as pd
import matplotlib.pyplot as plt
import openpyxl
import random
import io
import os

# Set Streamlit page configuration
st.set_page_config(
    page_title="PPR - Paleo Profile Randomizer",
    page_icon="PPR.ico",
    initial_sidebar_state="expanded"
    )

def home_page():
    """
    Displays the Home page for the PPR application, including project
    description, usage instructions, and other relevant information.
    """

    # Display banner image (replace 'banner.png' or 'screenshot.png' with your image)
    # st.image("screenshot.png", use_container_width=True) # Uncomment if you have an image

    st.title("PPR - Paleo Profile Randomizer")
    st.markdown(
        """
        **Welcome to the Paleo Profile Randomizer (PPR) application!**

        This tool generates synthetic paleoecological profile data, simulating information from sediment cores. It's designed for educational purposes, data analysis testing, and exploring paleoenvironmental concepts.
        """
    )

    st.markdown("---")
    st.subheader("Project Description")
    st.markdown("""
[![Python](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

PPR (Paleo Profile Randomizer) is a Python application designed to generate synthetic paleoecological profile data, simulating the information obtained from sediment cores. This tool allows users to explore how different environmental and geological factors influence the composition of sediment records. PPR is valuable for educational purposes, data analysis testing, hypothesis generation, and model development in paleoecology.

The application generates data based on user-selected parameters:

*   **Depth:** User-defined depth range (e.g., 50-700 cm) with 2 cm intervals.
*   **Zones:** Five distinct zones with randomly assigned percentages (each zone representing 10-60% of the total depth).
*   **Base Type:** Geological base type (Rock, Sand, Paleosol, or Lake Sediment).
*   **Environment Type:** Paleoenvironment (Lake, Peatland, or Wetland).
*   **Parameters:** A comprehensive set of parameters, including:
    *   Loss on Ignition: Organic Matter (OM), Carbonate Content (CC), Inorganic Matter (IM)
    *   Magnetic Susceptibility (MS)
    *   Grain size: Clay, Silt, Sand percentages
    *   Water-soluble geochemical concentrations: Ca, Mg, Na, K
    *   Charcoal abundances
    *   Arboreal pollen (AP) abundances
    *   Non arboreal pollen (NAP) abundances
    *   Mollusc abundances: Warm-loving, Cold-resistant

Data generation is not purely random. Values follow trends (increasing, decreasing, stagnant, sporadic, etc.) that are typical of real-world paleoecological datasets, providing a more realistic simulation. The generated data is displayed in a scrollable table within the application and can be exported as a CSV file.
""")


    st.markdown("---")
    st.subheader("Why PPR is Useful")  # Added this section back
    st.markdown("""
*   **Educational Tool:** Ideal for teaching students about paleoecology.
*   **Data Simulation:** Generate datasets for testing analysis methods.
*   **Hypothesis Generation:** Explore parameter combinations.
*   **Data Interpretation Practice:** Develop interpretation skills.
*   **Model Development:** Adapt algorithms for complex models.
*   **Demonstration and Presentation:** Create visualizations of data.
""")
    st.markdown("---")
    st.subheader("Contributing")
    st.markdown("""
Contributions are welcome! Fork the repository, create a branch, make changes, and submit a pull request.
""")

    st.markdown("---")
    st.subheader("Maintainer")
    st.markdown("""
*   [34rthsh4p3r](https://github.com/34rthsh4p3r)
""")

    st.markdown("---")
    st.subheader("Acknowledgments")
    st.markdown("Developed with assistance from Google AI Studio.")

    st.markdown("---")
    st.subheader("License")
    st.markdown("Licensed under the GNU General Public License v3.0.")


    # Footer (remains the same)
    st.markdown("---")

# profile_generation_page() function in app.py

def profile_generation_page():
    st.title("Profile Generation")

    profile_generator = ProfileGenerator()

    # --- Sidebar for Input ---
    st.sidebar.header("Input Parameters")

    # Depth Selection
    min_depth = st.sidebar.number_input("Minimum Depth", min_value=0, max_value=1000, value=0, step=1)
    max_depth = st.sidebar.number_input("Maximum Depth", min_value=0, max_value=1000, value=1000, step=1)

    if max_depth <= min_depth:
          st.sidebar.error("Maximum depth must be greater than minimum depth.")
          depth_choice = None
    else:
        depth_choice = random.randint(min_depth, max_depth)

    # --- Generate Profile Button ---
    if st.sidebar.button("Generate Profile"):
        with st.spinner("Generating profile..."):
            data = profile_generator.generate_profile(depth_choice, base_type, env_type)  # Use the numeric value.
            if data:
                st.session_state.data = data  # Store data in session state
                df = pd.DataFrame(data)
                st.dataframe(df.style.format("{:.0f}"))  # Format to 0 decimal places

                # --- Display Diagram ---
                fig = profile_generator.generate_diagram(data)
                st.pyplot(fig)
            else:
                st.warning("No data generated. Please check your input parameters.")

    # --- Advanced Parameter Adjustment (Sliders) ---
    st.header("Advanced Parameter Adjustment")  # Moved back to main area
    selected_zone = st.selectbox("Select Zone:", options=profile_generator.zones)
    selected_base_type = st.selectbox("Select Base Type (for Zone 5):", options=["Rock", "Sand", "Paleosol", "Lake sediment"], key="base_type_select")
    selected_env_type = st.selectbox("Select Env. Type (for Zones 1-4):", options=["Lake", "Peatland", "Wetland"], key="env_type_select")
    ranges = profile_generator.get_parameter_ranges(selected_base_type, selected_env_type, selected_zone)

    updated_ranges = {}
    for param, (min_val, max_val, trend) in ranges.items():
        if param in ["OM", "IM", "CC", "Clay", "Silt", "Sand"]:
            new_min, new_max = st.slider(
                f"{param} Range (Zone {selected_zone}, Trend: {trend})",
                0.0, 100.0, (float(min_val), float(max_val)), step=0.1
            )
        else:
             new_min, new_max = st.slider(
                f"{param} Range (Zone {selected_zone}, Trend: {trend})",
                0.0, 2000.0, (float(min_val), float(max_val)), step=0.1
            )
        updated_ranges[param] = (new_min, new_max, trend)

    if st.button("Apply Custom Ranges"):  # Moved back to main area
        profile_generator.custom_ranges[(selected_zone, selected_base_type, selected_env_type)] = updated_ranges
        st.success("Custom ranges applied!")

       # --- Save Data ---
    if 'data' in st.session_state and st.session_state.data:
        st.sidebar.header("Save Data")
        df_download = pd.DataFrame(st.session_state.data)

        # CSV download
        csv = df_download.to_csv(index=False).encode('utf-8')
        st.sidebar.download_button(
            label="Download data as CSV",
            data=csv,
            file_name='paleo_profile.csv',
            mime='text/csv',
        )

        # Excel (xlsx) download.  Requires openpyxl.
        excel_buffer = io.BytesIO()  # Use BytesIO
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df_download.to_excel(writer, index=False, sheet_name='Profile Data')
        excel_buffer.seek(0)  # Rewind the buffer to the beginning
        st.sidebar.download_button(
            label="Download data as Excel",
            data=excel_buffer,
            file_name='paleo_profile.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        # Save Diagram
        if 'data' in st.session_state and st.session_state.data:
                st.sidebar.header("Save Diagram")
                # Generate the diagram
                fig = profile_generator.generate_diagram(st.session_state.data)

                # Save diagram as PNG
                buf_png = io.BytesIO()
                fig.savefig(buf_png, format="png")
                buf_png.seek(0)
                st.sidebar.download_button(
                    label="Download Diagram as PNG",
                    data=buf_png,
                    file_name="paleo_profile_diagram.png",
                    mime="image/png",
                )

                # Save diagram as SVG
                buf_svg = io.BytesIO()
                fig.savefig(buf_svg, format="svg")
                buf_svg.seek(0)
                st.sidebar.download_button(
                    label="Download Diagram as SVG",
                    data=buf_svg,
                    file_name="paleo_profile_diagram.svg",
                    mime="image/svg+xml",
                )
            
def main():
    """Main function to handle page navigation."""

    # Initialize session state for tracking current page
    if "current_page" not in st.session_state:
        st.session_state["current_page"] = "Home"

    # Sidebar navigation buttons
    if st.sidebar.button("Home"):
        st.session_state["current_page"] = "Home"
    if st.sidebar.button("Profile Generation"):
        st.session_state["current_page"] = "Profile Generation"

    # Route to the selected page
    current_page = st.session_state["current_page"]

    if current_page == "Home":
        home_page()  # Correctly call the home_page function
    elif current_page == "Profile Generation":
        profile_generation_page()  # Call the main() function *within* the module

if __name__ == "__main__":
    main()
