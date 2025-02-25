# profile_generation_page.py
import streamlit as st
from profile_generator import ProfileGenerator
import pandas as pd
import matplotlib.pyplot as plt
import openpyxl
import io

def profile_generation_page():
    st.title("Profile Generation")

    profile_generator = ProfileGenerator()

    # --- Sidebar for Input ---  (Removed input parameters section)
    # --- Generate Profile Button --- (Removed Generate Profile button)

    # --- Save Data --- (No Changes)
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

    # --- Advanced Parameter Adjustment (Sliders) --- (Now the main profile generator)
    st.sidebar.header("Profile Generating Method")
    # if st.sidebar.checkbox("Enable Advanced Adjustment", value=True):  # Always enabled

    # Depth Selection
    depth_choice = st.sidebar.selectbox("Choose a depth:",
                                        options=[("50-100", 1), ("100-200", 2), ("200-300", 3),
                                                 ("300-400", 4), ("500-600", 5), ("600-700", 6)],
                                        format_func=lambda x: x[0])  # Display text, return value

    # Base Type Selection
    base_type = st.sidebar.selectbox("Choose a base type:",
                                      options=["Rock", "Sand", "Paleosol", "Lake sediment"])

    # Environment Type Selection
    env_type = st.sidebar.selectbox("Choose an environment type:",
                                     options=["Lake", "Peatland", "Wetland"])

    selected_zone = st.sidebar.selectbox("Select Zone:", options=profile_generator.zones)
    # selected_base_type = st.sidebar.selectbox("Select Base Type (for Zone 5):", options=["Rock", "Sand", "Paleosol", "Lake sediment"], key="base_type_select")
    # selected_env_type = st.sidebar.selectbox("Select Env. Type (for Zones 1-4):", options=["Lake", "Peatland", "Wetland"], key = "env_type_select")
    ranges = profile_generator.get_parameter_ranges(base_type, env_type, selected_zone)

    updated_ranges = {}
    for param, (min_val, max_val, trend) in ranges.items():
        # Create a label based on the parameter
        if param == "OM":
            label = "Organic Matter Content Range"
        elif param == "CC":
            label = "Carbonate Content Range"
        elif param == "IM":
            label = "Inorganic Matter Content Range"
        elif param == "MS":
            label = "Magnetic Susceptibility Range"
        elif param == "WL":
            label = "Warm-loving mollusc species Range"
        elif param == "CR":
            label = "Cold-resistant mollusc species Range"
        elif param == "AP":
            label = "Arboreal Pollen Range"
        elif param == "NAP":
            label = "Non-arboreal Pollen Range"
        else:
            label = f"{param} Range"


        trend_options = ["UP", "DN", "LF", "HF", "SP", "SL", "SH", "UD", "DU", "RM"]  # All trend options
        selected_trend = st.sidebar.selectbox(f"Trend for {label} (Zone {selected_zone})", options=trend_options, index=trend_options.index(trend))


        if param in ["OM", "IM", "CC", "Clay", "Silt", "Sand"]:
            new_min, new_max = st.sidebar.slider(
                f"{label} (Zone {selected_zone})",
                0, 100, (int(min_val), int(max_val)), step=1
            )
        elif param == "MS":
            new_min, new_max = st.sidebar.slider(
                f"{label} (Zone {selected_zone})",
                0, 1000, (int(min_val), int(max_val)), step=1
            )
        elif param in ["AP", "NAP", "WL", "CR"]:
             new_min, new_max = st.sidebar.slider(
                f"{label} (Zone {selected_zone})",
                0, 3000, (int(min_val), int(max_val)), step=1
            )
        elif param in ["Ca", "Mg", "Na", "K"]:
            new_min, new_max = st.sidebar.slider(
                f"{label} (Zone {selected_zone})",
                0, 4000, (int(min_val), int(max_val)), step=1
            )
        else: # Fallback (shouldn't be needed, but good practice)
            new_min, new_max = st.sidebar.slider(
                f"{label} (Zone {selected_zone})",
                0, 100, (int(min_val), int(max_val)), step=1
            )


        updated_ranges[param] = (new_min, new_max, selected_trend)

        # Add separators
        if param in ["IM", "Sand", "NAP", "CR"]:
            st.sidebar.markdown("---")

    if st.sidebar.button("Generate Profile"): # Changed label
        profile_generator.custom_ranges[(selected_zone, base_type, env_type)] = updated_ranges
        with st.spinner("Generating profile..."):
            data = profile_generator.generate_profile(depth_choice[1], base_type, env_type) # Use the numeric value.  VERY IMPORTANT!
            if data:
                st.session_state.data = data  # Store data in session state
                df = pd.DataFrame(data)
                st.dataframe(df.style.format("{:.2f}"))  # Format to 2 decimal places


                # --- Display Diagram ---
                fig = profile_generator.generate_diagram(data)
                st.pyplot(fig)
            else:
                st.warning("No data generated. Please check your input parameters.")

if __name__ == "__main__":
    profile_generation_page()