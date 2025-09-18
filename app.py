import streamlit as st
from data_loader import load_reference_data
from plotter import plot_graphs
from io import BytesIO
import base64
import numpy as np

st.set_page_config(layout="wide")
st.title("General Curve Plotter")

# Axis Ranges (first)
st.header("Axis Ranges")
col_range1, col_range2 = st.columns(2)
with col_range1:
    x_min = st.number_input("X Min", value=0.0, help="Can be negative")
    x_max = st.number_input("X Max", value=4000.0)
with col_range2:
    y_min = st.number_input("Y Min", value=0.0, help="Can be negative")
    y_max = st.number_input("Y Max", value=31000.0)

# Suggest intervals
suggest_major_x = round((x_max - x_min) / 10, -int(np.log10((x_max - x_min)/10)) + 1) if x_max > x_min else 1000
suggest_minor_x = suggest_major_x / 5
suggest_major_y = round((y_max - y_min) / 10, -int(np.log10((y_max - y_min)/10)) + 1) if y_max > y_min else 1000
suggest_minor_y = suggest_major_y / 5

# Data Upload
st.header("Upload Excel Data")
st.markdown("Excel format: col0 = curve name, col1+ = polynomial coefficients (high to low degree).")
uploaded_file = st.file_uploader("Upload Excel", type=['xlsx'])

# Plot Style
st.header("Plot Style")
col_style1, col_style2 = st.columns(2)
with col_style1:
    color_mode = st.radio("Color Mode", ["Colorful", "Black and White"])
    use_colorful = color_mode == "Colorful"
    if use_colorful:
        num_colors = st.number_input("Number of Distinct Colors", min_value=5, max_value=30, value=10)
    bg_color = st.color_picker("Background Color", value='#F5F5F5' if use_colorful else '#FFFFFF')
with col_style2:
    legend_loc = st.selectbox("Legend Placement", ["Upper Right", "Upper Left", "Lower Right", "Lower Left", "Center Left", "Center Top", "Center Bottom"])
    custom_legends = st.text_area("Custom Legends (name: #hex_color or name, one per line)", help="Overrides Excel names. E.g., Curve1: #ff0000")

# Plot Grouping
st.header("Plot Grouping")
plot_grouping = st.radio("Plot all curves on one graph or one graph per curve?", ["All in One", "One per Curve"])

# Grid and Ticks
st.header("Grid and Ticks")
show_grid = st.checkbox("Show Grid?", value=True)
col_grid1, col_grid2 = st.columns(2)
with col_grid1:
    grid_major_x = st.number_input("Major Grid X", value=suggest_major_x)
    grid_minor_x = st.number_input("Minor Grid X", value=suggest_minor_x)
    x_major_int = st.number_input("X Major Tick Interval", value=suggest_major_x)
    x_minor_int = st.number_input("X Minor Tick Interval", value=suggest_minor_x)
with col_grid2:
    grid_major_y = st.number_input("Major Grid Y", value=suggest_major_y)
    grid_minor_y = st.number_input("Minor Grid Y", value=suggest_minor_y)
    y_major_int = st.number_input("Y Major Tick Interval", value=suggest_major_y)
    y_minor_int = st.number_input("Y Minor Tick Interval", value=suggest_minor_y)

# Axis Details
st.header("Axis Positions and Frame")
col_axis1, col_axis2 = st.columns(2)
with col_axis1:
    x_pos = st.radio("X Axis Position", ["Top", "Bottom"])
    y_pos = st.radio("Y Axis Position", ["Left", "Right"])
with col_axis2:
    plot_frame = st.radio("Plot Frame", ["Only Axes", "Square/Box"])
    scale_type = st.radio("Scale Type", ["Normal (Linear)", "Log-Log"])

# Curve Options
st.header("Curve Fit and Behavior")
col_curve1, col_curve2 = st.columns(2)
with col_curve1:
    func_type = st.selectbox("Curve Fit Type", ["Polynomial"])
    st.info("Degree auto-detected per curve from non-zero coeffs.")
with col_curve2:
    allow_reentry_x = st.checkbox("Allow Re-entry After Exiting X Bounds?", value=False)
    allow_reentry_y = st.checkbox("Allow Re-entry After Exiting Y Bounds?", value=False)

# Titles and Labels
st.header("Chart Labels")
title = st.text_input("Chart Title", value="Curve Plot")
x_label = st.text_input("X Label", value="X Axis")
y_label = st.text_input("Y Label", value="Y Axis")

# Generate
if st.button("Generate Plot(s)"):
    with st.spinner("Loading data and generating plot(s)..."):
        data_ref = load_reference_data(uploaded_file)
        if plot_grouping == "All in One" and len(data_ref) > 15:
            st.warning("More than 15 curves in one plot may be cluttered. Consider 'One per Curve'.")
        
        figs = plot_graphs(data_ref, use_colorful, num_colors if use_colorful else 1, bg_color, legend_loc, custom_legends, 
                          scale_type, show_grid, grid_major_x if show_grid else suggest_major_x, grid_minor_x if show_grid else suggest_minor_x,
                          grid_major_y if show_grid else suggest_major_y, grid_minor_y if show_grid else suggest_minor_y,
                          func_type, x_min, x_max, y_min, y_max, x_pos, y_pos, plot_frame,
                          x_major_int, x_minor_int, y_major_int, y_minor_int, allow_reentry_x, allow_reentry_y,
                          title, x_label, y_label, plot_grouping)

        for i, (fig, curve_name) in enumerate(figs):
            st.subheader(f"Plot {i+1}" + (f": {curve_name}" if plot_grouping == "One per Curve" else ""))
            st.pyplot(fig)
            buf = BytesIO()
            fig.savefig(buf, format="png", bbox_inches='tight')
            buf.seek(0)
            b64 = base64.b64encode(buf.read()).decode()
            href = f'<a href="data:image/png;base64,{b64}" download="curve_plot_{curve_name if plot_grouping == "One per Curve" else "all"}.png">Download Plot</a>'
            st.markdown(href, unsafe_allow_html=True)
