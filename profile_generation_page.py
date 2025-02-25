# profile_generation_page.py
import streamlit as st
from profile_generator import ProfileGenerator  # Assuming you have this file
import pandas as pd
import matplotlib.pyplot as plt
import openpyxl
import random
import io


def profile_generation_page():
    st.title("Profile Generation")

    profile_generator = ProfileGenerator()

    # --- Layout ---
    col1, col2 = st.columns([1, 2])  # Adjust column widths as needed

    with col1:
        st.markdown("### Home")  # Use markdown for headers
        st.markdown("Home menu point")
        st.markdown("Profile Generation menu point")

        st.markdown("---")
        st.markdown("### Generate dataset")  # Section header
        # --- Generate Profile Button ---  Moved inside col1
        if st.button("Generate Profile"):
            with st.spinner("Generating profile..."):
                if depth_choice is not None: # Check if depth choice valid
                    data = profile_generator.generate_profile(depth_choice, selected_base_type, selected_env_type)  # Use selected types
                    if data:
                        st.session_state.data = data  # Store data in session state
                        df = pd.DataFrame(data)
                        st.dataframe(df.style.format("{:.2f}"))  # Format to 2 decimal places

                        # --- Display Diagram --- (also within col1)
                        fig = profile_generator.generate_diagram(data)
                        st.pyplot(fig)
                    else:
                        st.warning("No data generated. Please check your input parameters.")
                else:
                    st.error("Please fix depth settings first")

        st.markdown("---")
        st.markdown("### Save Data")
        st.markdown("Save Data as .CSV")
        st.markdown("Save Data as Excel")

        st.markdown("---")
        st.markdown("### Save Diagram")
        st.markdown("Save Diagram as .PNG")
        st.markdown("Save Diagram as .SVG")
        st.markdown("---")



        # --- Save Data --- (Moved inside col1, only displays if data exists)
        if 'data' in st.session_state and st.session_state.data:
            df_download = pd.DataFrame(st.session_state.data)

            # CSV download
            csv = df_download.to_csv(index=False).encode('utf-8')
            st.download_button(
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
            st.download_button(
                label="Download data as Excel",
                data=excel_buffer,
                file_name='paleo_profile.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            )

            # Save Diagram (Moved inside col1, only if data exists)
            fig = profile_generator.generate_diagram(st.session_state.data)

            # Save diagram as PNG
            buf_png = io.BytesIO()
            fig.savefig(buf_png, format="png")
            buf_png.seek(0)
            st.download_button(
                label="Download Diagram as PNG",
                data=buf_png,
                file_name="paleo_profile_diagram.png",
                mime="image/png",
            )

            # Save diagram as SVG
            buf_svg = io.BytesIO()
            fig.savefig(buf_svg, format="svg")
            buf_svg.seek(0)
            st.download_button(
                label="Download Diagram as SVG",
                data=buf_svg,
                file_name="paleo_profile_diagram.svg",
                mime="image/svg+xml",
            )

    with col2:
        st.markdown("### Parameter Adjustment")  # Section header

        # --- Input Parameters ---  (Now in col2)
        st.markdown("**Depth Selection**") # More descriptive title
        min_depth = st.number_input("Minimum Depth", min_value=0, max_value=1000, value=0, step=1)
        max_depth = st.number_input("Maximum Depth", min_value=0, max_value=1000, value=1000, step=1)

        if max_depth <= min_depth:
              st.error("Maximum depth must be greater than minimum depth.")
              depth_choice = None
        else:
            depth_choice = random.randint(min_depth, max_depth)

        # --- Advanced Parameter Adjustment (Sliders) --- (Now in col2)
        st.markdown("**Advanced Parameter Adjustment**")
        selected_zone = st.selectbox("Select Zone:", options=profile_generator.zones)  # Using all zones for simplicity
        selected_base_type = st.selectbox("Select Base Type (for Zone 5):",
                                          options=["Rock", "Sand", "Paleosol", "Lake sediment"], key="base_type_select")  # Added key
        selected_env_type = st.selectbox("Select Env. Type (for Zones 1-4):",
                                         options=["Lake", "Peatland", "Wetland"], key="env_type_select")  # Added key
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
            updated_ranges[param] = (new_min, new_max, trend)  # Keep trend

        if st.button("Apply Custom Ranges"):
            profile_generator.custom_ranges[(selected_zone, selected_base_type, selected_env_type)] = updated_ranges  # Pass base/env
            st.success("Custom ranges applied!")
        # --- Input Parameters ---

if __name__ == "__main__":
    profile_generation_page()