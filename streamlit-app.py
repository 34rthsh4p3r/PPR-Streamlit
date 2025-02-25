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
    layout="wide"
    )

def home_page():
    """
    Displays the Home page for the PPR application, including project
    description, usage instructions, and other relevant information.
    """

    # Display banner image (replace 'banner.png' or 'screenshot.png' with your image)
    # st.image("screenshot.png", use_container_width=True) # Uncomment if you have an image

    st.title("PPR - Paleo Profile Randomizer")
    st.markdown("""
        [![Python](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/)
        [![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
            """)
    st.markdown("---")
    st.markdown("""

PPR, a Python application, generates synthetic paleoecological profile data, simulating the information retrieved from sediment cores.  This tool enables users to investigate the influence of various environmental and geological factors on sediment record composition.  Its utility spans several areas, including education, where it can teach students about paleoecology; data analysis, by generating datasets for testing methods; hypothesis generation, through exploration of parameter combinations; data interpretation practice, allowing for the development of interpretation skills; model development, by facilitating the adaptation of algorithms for complex models; and demonstration and presentation, enabling the creation of data visualizations.
The application generates data based on user-selected parameters:

*   **Depth:** User-defined depth range with 2 cm intervals.
*   **Zones:** Multiple distinct zones with randomly assigned percentages (each zone representing a custom % of the total depth).
*   **Base Type:** Geological base type (Rock, Sand, Paleosol, or Lake Sediment).
*   **Environment Type:** Paleoenvironment (Lake, Peatland, or Wetland).
*   **Parameters:** A comprehensive set of parameters, including:
    *   Loss on Ignition: Organic Matter (OM), Carbonate Content (CC), Inorganic Matter (IM)
    *   Magnetic Susceptibility (MS)
    *   Grain size: Clay, Silt, Sand percentages
    *   Water-soluble geochemical concentrations: Ca, Mg, Na, K
    *   Charcoal abundances
    *   Arboreal pollen (AP) and Non arboreal pollen (NAP) abundances
    *   Mollusc abundances: Warm-loving, Cold-resistant

Data generation is not purely random. Values follow trends (increasing, decreasing, stagnant, sporadic, etc.) that are typical of real-world paleoecological datasets, providing a more realistic simulation. The generated data is displayed in a scrollable table and a diagram within the application and can be exported as a CSV, Excel, PNG or SVG file.
""")

    # Footer (remains the same)
    st.markdown("---")

# profile_generation_page() function in app.py

def profile_generation_page():
    st.title("Profile Generation")

    profile_generator = ProfileGenerator()

    # --- Sidebar for Input ---
    st.sidebar.header("Input Parameters")

    # --- Generate Profile Button ---
    if st.sidebar.button("Generate"):
        with st.spinner("Generating profile..."):
            data = profile_generator.generate_profile(depth_choice, base_type, env_type)  # Pass base_type and env_type
            if data:
                st.session_state.data = data  # Store data in session state
                df = pd.DataFrame(data)
                st.dataframe(df.style.format("{:.0f}"))  # Format to 0 decimal places

                # --- Display Diagram ---
                fig = profile_generator.generate_diagram(data)
                st.pyplot(fig)
            else:
                st.warning("No data generated. Please check your input parameters.")

   # Depth Selection
    min_depth = st.sidebar.number_input("Minimum Depth", min_value=0, max_value=1000, value=0, step=1)
    max_depth = st.sidebar.number_input("Maximum Depth", min_value=0, max_value=1000, value=1000, step=1)

    if max_depth <= min_depth:
          st.sidebar.error("Maximum depth must be greater than minimum depth.")
          return  # Exit the function if depth is invalid

    depth_choice = list(range(min_depth, max_depth + 1, 2)) # Define depth_choice

        # Base Type Selection
    base_type = st.sidebar.selectbox("Choose a base type:",
                                        options=["Rock", "Sand", "Paleosol", "Lake sediment"])

    # Environment Type Selection
    env_type = st.sidebar.selectbox("Choose an environment type:",
                                        options=["Lake", "Peatland", "Wetland"])

# --- Advanced Parameter Adjustment (Sliders and Dropdowns) ---
    st.sidebar.header("Advanced Parameter Adjustment")

    if 'data' in st.session_state:  # Only show if data has been generated
        selected_zone_index = st.sidebar.selectbox("Select Zone:", options=list(range(1, num_zones + 1)))
        selected_zone = selected_zone_index  # Corrected zone selection


        ranges = profile_generator.get_parameter_ranges(base_type, env_type, selected_zone)

        updated_ranges = {}

        for param, (min_val, max_val, _) in ranges.items():  # Unpack only min, max, ignore trend
            trend_options = ["SP", "UP", "DN", "LF", "HF", "SL", "SH", "UD", "DU", "RM"]  # Define trend options

            if param in ["OM", "IM", "CC", "Clay", "Silt", "Sand"]:
                new_min, new_max = st.sidebar.slider(
                    f"{param} Range (Zone {selected_zone})",
                    0.0, 100.0, (float(min_val), float(max_val)), step=0.1
                )
            else:
                new_min, new_max = st.sidebar.slider(
                    f"{param} Range (Zone {selected_zone})",
                    0.0, 2000.0, (float(min_val), float(max_val)), step=0.1
                )

            selected_trend = st.sidebar.selectbox(
                f"{param} Trend (Zone {selected_zone})",
                options=trend_options,
                index=trend_options.index(ranges[param][2]) if ranges[param][2] in trend_options else 0  # Set default selection
            )

            updated_ranges[param] = (new_min, new_max, selected_trend)

        if st.sidebar.button("Apply Custom Ranges"):
            profile_generator.custom_ranges[(selected_zone, base_type, env_type)] = updated_ranges
            st.sidebar.success("Custom ranges applied!")

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
