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
    Displays the Home page for the PPR application.
    """

    st.title("PPR - Paleo Profile Randomizer")
    st.markdown("""
        [![Python](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/)
        [![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
            """)
    st.markdown("---")
    st.markdown("""

PPR, a Python application, generates synthetic paleoecological profile data.
It allows users to investigate various environmental and geological factors.
Its utility spans education, data analysis, hypothesis generation, data interpretation, model development, and presentation.
The application generates data based on user-selected parameters:

*   **Depth:** User-defined depth range with 2 cm intervals.
*   **Zones:** Multiple distinct zones with user assigned percentages.
*   **Parameters:** A comprehensive set of parameters, including:
    *   Loss on Ignition: Organic Matter (OM), Carbonate Content (CC), Inorganic Matter (IM)
    *   Grain size: Clay, Silt, Sand percentages
    *   Water-soluble geochemical concentrations: Ca, Mg, Na, K
    *   Charcoal abundances
    *   Arboreal pollen (AP) and Non arboreal pollen (NAP) abundances
    *   Mollusc abundances: Warm-loving, Cold-resistant

Values follow trends (increasing, decreasing, stagnant, sporadic, etc.).
The generated data can be exported as CSV, Excel, PNG or SVG.
""")

    st.markdown("---")

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
          return

    depth_choice = list(range(min_depth, max_depth + 1, 2))

    # Number of Zones
    num_zones = st.sidebar.number_input("Number of Zones", min_value=1, max_value=10, value=5, step=1)

    # Zone Percentages
    zone_percentages = []
    remaining_percentage = 100
    for i in range(num_zones - 1):
        percentage = st.sidebar.number_input(f"Zone {i+1} Percentage (0-{remaining_percentage}%)", min_value=0, max_value=remaining_percentage, value=random.randint(5,min(20,remaining_percentage)), step=1)
        zone_percentages.append(percentage)
        remaining_percentage -= percentage
    zone_percentages.append(remaining_percentage)

    st.sidebar.write(f"Zone {num_zones}: {remaining_percentage}%")
    if sum(zone_percentages) != 100:
        st.sidebar.error("Zone percentages must sum to 100%.")
        return
    # --- Generate Profile Button ---
    if st.sidebar.button("Generate Profile"):
        with st.spinner("Generating profile..."):
            data = profile_generator.generate_profile(depth_choice, zone_percentages)
            if data:
                st.session_state.data = data
                df = pd.DataFrame(data)
                st.dataframe(df.style.format("{:.0f}"))

                # --- Display Diagram ---
                fig = profile_generator.generate_diagram(data)
                st.pyplot(fig)
            else:
                st.warning("No data generated. Please check your input parameters.")


    # --- Advanced Parameter Adjustment (Sliders and Dropdowns) ---
    st.sidebar.header("Advanced Parameter Adjustment")

    if 'data' in st.session_state:  # Only show if data has been generated
        selected_zone_index = st.sidebar.selectbox("Select Zone:", options=list(range(1, num_zones + 1)))
        selected_zone = selected_zone_index  # Corrected zone selection


        ranges = profile_generator.get_parameter_ranges(selected_zone)

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
            profile_generator.custom_ranges[selected_zone] = updated_ranges
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
