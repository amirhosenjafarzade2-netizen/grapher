import streamlit as st
import matplotlib.pyplot as plt
from data_loader import load_reference_data
from plotter import plot_graphs
from io import BytesIO
import base64
import numpy as np
import pandas as pd

st.set_page_config(layout="wide")
st.title("Curve Plotter")

# Debug Toggle
debug = st.checkbox("Enable Debug Mode (Show Data and Logs)", value=False)

# Axis Ranges
st.header("Axis Ranges")
auto_scale_y = st.checkbox(
    "Auto-Scale Y-Axis (Depth)", 
    value=False,
    help="Automatically adjusts Y Min and Y Max to fit all curves based on computed values. If unchecked, uses fixed ranges (default: 0 to 31,000 ft)."
)
col_range1, col_range2, col_range3, col_range4 = st.columns(4)
with col_range1:
    x_min = st.number_input("X Min (Pressure, psi)", value=0.0, help="Can be negative")
with col_range2:
    x_max = st.number_input("X Max (Pressure, psi)", value=4000.0)
with col_range3:
    y_min = st.number_input("Y Min (Depth, ft)", value=0.0, help="Can be negative", disabled=auto_scale_y)
with col_range4:
    y_max = st.number_input("Y Max (Depth, ft)", value=31000.0, disabled=auto_scale_y)

# Validate ranges
if x_min >= x_max:
    st.error("X Max must be greater than X Min")
    st.stop()
if not auto_scale_y and y_min >= y_max:
    st.error("Y Max must be greater than Y Min")
    st.stop()

# Data Upload
st.header("Upload Excel Data")
st.markdown("Excel format: col0 = name (e.g., 'Curve1'), col1+ = coefficients (highest to lowest degree, e.g., a, b, c, d, e, f for 5th-degree).")
uploaded_file = st.file_uploader("Upload Excel", type=['xlsx'])
if not uploaded_file and not debug:
    st.warning("Please upload an Excel file to generate plots.")
    st.stop()

# Plot Style
st.header("Plot Style")
col_style1, col_style2 = st.columns(2)
with col_style1:
    color_mode = st.radio("Color Mode", ["Colorful", "Black and White"])
    use_colorful = color_mode == "Colorful"
    if use_colorful:
        num_colors = st.number_input("Number of Distinct Colors", min_value=5, max_value=50, value=30)
    bg_color = st.color_picker("Background Color", value='#F5F5F5' if use_colorful else '#FFFFFF')
with col_style2:
    legend_loc = st.selectbox("Legend Placement", ["Upper Right", "Upper Left", "Lower Right", "Lower Left", "Center Left"], index=4)
    custom_legends = st.text_area("Custom Legends (name: #hex_color or name, one per line)", help="Overrides Excel names. E.g., Curve1: #ff0000")

# Plot Grouping
st.header("Plot Grouping")
plot_grouping = st.radio("Plot all curves on one graph or one graph per curve?", ["All in One", "One per Curve"])

# Grid and Ticks
st.header("Grid and Ticks")
show_grid = st.checkbox("Show Grid?", value=True)
col_grid1, col_grid2 = st.columns(2)
with col_grid1:
    grid_major_x = st.number_input("Major Grid X (psi)", value=1000.0, min_value=1e-10)
    grid_minor_x = st.number_input("Minor Grid X (psi)", value=200.0, min_value=1e-10)
    x_major_int = st.number_input("X Major Tick Interval (psi)", value=1000.0, min_value=1e-10)
    x_minor_int = st.number_input("X Minor Tick Interval (psi)", value=200.0, min_value=1e-10)
with col_grid2:
    grid_major_y = st.number_input("Major Grid Y (ft)", value=1000.0, min_value=1e-10)
    grid_minor_y = st.number_input("Minor Grid Y (ft)", value=200.0, min_value=1e-10)
    y_major_int = st.number_input("Y Major Tick Interval (ft)", value=1000.0, min_value=1e-10)
    y_minor_int = st.number_input("Y Minor Tick Interval (ft)", value=200.0, min_value=1e-10)

# Axis Details
st.header("Axis Positions")
col_axis1, col_axis2 = st.columns(2)
with col_axis1:
    x_pos = st.radio("X Axis Position", ["Top", "Bottom"], index=0)
    y_pos = st.radio("Y Axis Position", ["Left", "Right"], index=0)

# Titles and Labels
st.header("Chart Labels")
title = st.text_input("Chart Title", value="Curve Plot")
x_label = st.text_input("X Label", value="Gradient Pressure, psi")
y_label = st.text_input("Y Label", value="Depth, ft")

# Generate
if st.button("Generate Plot(s)"):
    plt.close('all')  # Clear figure cache
    with st.spinner("Loading data and generating plot(s)..."):
        if debug:
            data_ref, skipped_rows = load_reference_data(uploaded_file, debug=True)
            if auto_scale_y:
                y_vals_all = []
                for entry in data_ref:
                    coeffs = entry['coefficients']
                    x_vals = np.linspace(x_min, x_max, 1000)  # Increased resolution
                    y_vals = np.polyval(coeffs, x_vals)
                    y_vals = y_vals[np.isfinite(y_vals)]
                    if len(y_vals) > 0:
                        y_vals_all.extend(y_vals)
                if y_vals_all:
                    y_min = float(np.min(y_vals_all) * 1.2)
                    y_max = float(np.max(y_vals_all) * 1.2)
                    if y_max > 1e6:
                        y_max = min(y_max, 1e6)
                        st.warning("Y Max capped at 1,000,000 to prevent extreme scaling.")
                    if y_min == y_max:
                        y_min -= 1
                        y_max += 1
                else:
                    y_min, y_max = 0, 31000
                    st.warning("Auto-scale failed: No valid y-values. Using default range [0, 31,000].")
            figs, skipped_curves = plot_graphs(
                data_ref, use_colorful, num_colors if use_colorful else 1, bg_color, legend_loc, custom_legends,
                show_grid, grid_major_x, grid_minor_x, grid_major_y, grid_minor_y,
                x_min, x_max, y_min, y_max, x_pos, y_pos,
                x_major_int, x_minor_int, y_major_int, y_minor_int,
                title, x_label, y_label, plot_grouping, auto_scale_y, debug=True)
            
            # Debug info
            st.header("Debug Information")
            st.subheader("Loaded Data")
            debug_data = [
                {
                    "Name": entry['name'],
                    "Coefficients": entry['coefficients']
                } for entry in data_ref
            ]
            st.dataframe(pd.DataFrame(debug_data))
            if skipped_rows:
                st.subheader("Skipped Excel Rows")
                st.write("\n".join(skipped_rows))
            if skipped_curves:
                st.subheader("Skipped Curves")
                st.write("\n".join(skipped_curves))
            # Sample points
            st.subheader("Sample Curve Points")
            sample_points = []
            for entry in data_ref:
                coeffs = entry['coefficients']
                x_samples = np.linspace(x_min, x_max, 10)
                y_samples = np.polyval(coeffs, x_samples)
                y_finite = y_samples[np.isfinite(y_samples)]
                min_y = float(np.min(y_finite)) if len(y_finite) > 0 else None
                max_y = float(np.max(y_finite)) if len(y_finite) > 0 else None
                for x, y in zip(x_samples, y_samples):
                    sample_points.append({
                        "Curve": entry['name'],
                        "X (psi)": x,
                        "Y (ft)": y,
                        "Min Y (Curve)": min_y,
                        "Max Y (Curve)": max_y
                    })
            st.dataframe(pd.DataFrame(sample_points))
            # Debug plot
            if sample_points:
                fig_debug, ax_debug = plt.subplots(figsize=(8, 6))
                for curve_name in set(p['Curve'] for p in sample_points):
                    curve_points = [p for p in sample_points if p['Curve'] == curve_name]
                    x_vals = [p['X (psi)'] for p in curve_points]
                    y_vals = [p['Y (ft)'] for p in curve_points]
                    ax_debug.scatter(x_vals, y_vals, label=curve_name, s=50)
                ax_debug.set_xlabel(x_label)
                ax_debug.set_ylabel(y_label)
                ax_debug.set_xlim(x_min, x_max)
                ax_debug.set_ylim(y_min, y_max)
                ax_debug.invert_yaxis()
                ax_debug.legend()
                ax_debug.set_title("Debug: Sample Points")
                st.pyplot(fig_debug)
                plt.close(fig_debug)
        else:
            data_ref = load_reference_data(uploaded_file)
            if not data_ref:
                st.error("No valid data loaded from Excel. Please check file format.")
                st.stop()
            if auto_scale_y:
                y_vals_all = []
                for entry in data_ref:
                    coeffs = entry['coefficients']
                    x_vals = np.linspace(x_min, x_max, 1000)  # Increased resolution
                    y_vals = np.polyval(coeffs, x_vals)
                    y_vals = y_vals[np.isfinite(y_vals)]
                    if len(y_vals) > 0:
                        y_vals_all.extend(y_vals)
                if y_vals_all:
                    y_min = float(np.min(y_vals_all) * 1.2)
                    y_max = float(np.max(y_vals_all) * 1.2)
                    if y_max > 1e6:
                        y_max = min(y_max, 1e6)
                        st.warning("Y Max capped at 1,000,000 to prevent extreme scaling.")
                    if y_min == y_max:
                        y_min -= 1
                        y_max += 1
                else:
                    y_min, y_max = 0, 31000
                    st.warning("Auto-scale failed: No valid y-values. Using default range [0, 31,000].")
            figs = plot_graphs(
                data_ref, use_colorful, num_colors if use_colorful else 1, bg_color, legend_loc, custom_legends,
                show_grid, grid_major_x, grid_minor_x, grid_major_y, grid_minor_y,
                x_min, x_max, y_min, y_max, x_pos, y_pos,
                x_major_int, x_minor_int, y_major_int, y_minor_int,
                title, x_label, y_label, plot_grouping, auto_scale_y)

        if not figs:
            st.error("No plots generated. Enable debug mode to diagnose issues.")
            st.stop()

        if plot_grouping == "All in One" and len(data_ref) > 30:
            st.warning("More than 30 curves in one plot may be cluttered. Consider 'One per Curve'.")

        for i, (fig, curve_name) in enumerate(figs):
            st.subheader(f"Plot {i+1}" + (f": {curve_name}" if plot_grouping == "One per Curve" else ""))
            st.pyplot(fig)
            buf = BytesIO()
            fig.savefig(buf, format="png", bbox_inches='tight')
            buf.seek(0)
            b64 = base64.b64encode(buf.read()).decode()
            href = f'<a href="data:image/png;base64,{b64}" download="curve_plot_{curve_name if plot_grouping == "One per Curve" else "all"}.png">Download Plot</a>'
            st.markdown(href, unsafe_allow_html=True)
