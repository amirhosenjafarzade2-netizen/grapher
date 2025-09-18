import streamlit as st
import matplotlib.pyplot as plt
from data_loader import load_reference_data, preview_data
from plotter import plot_graphs
from io import BytesIO
import base64
import numpy as np
import pandas as pd
import time

# Page configuration
st.set_page_config(
    layout="wide", 
    page_title="Advanced Curve Plotter", 
    page_icon="📈"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {font-size: 2.5rem; font-weight: bold; color: #1f77b4;}
    .section-header {font-size: 1.5rem; color: #2e86ab; margin-top: 2rem;}
    .warning-box {background-color: #fff3cd; padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #ffc107;}
    .success-box {background-color: #d4edda; padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #28a745;}
    .error-box {background-color: #f8d7da; padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #dc3545;}
    .stNumberInput > div > div > div > div {width: 100%;}
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-header">Advanced Curve Plotter</h1>', unsafe_allow_html=True)
st.markdown("Plot polynomial curves with automatic range handling (from -10000 to 10000 and beyond)")

# Debug Toggle
debug = st.sidebar.checkbox("Enable Debug Mode", value=False, help="Show detailed data processing info")

# Axis Ranges Section
st.markdown('<h2 class="section-header">🎯 Axis Configuration</h2>', unsafe_allow_html=True)

col_axis_options = st.columns([1, 1, 1, 1])
with col_axis_options[0]:
    auto_scale_y = st.checkbox(
        "🔄 Auto-Scale Y-Axis", 
        value=True,
        key="auto_scale_y"
    )
with col_axis_options[1]:
    stop_y_exit = st.checkbox(
        "⏹️ Stop at Y-Exit", 
        value=False,
        key="stop_y_exit"
    )
with col_axis_options[2]:
    stop_x_exit = st.checkbox(
        "⏹️ Stop at X-Exit", 
        value=False,
        key="stop_x_exit"
    )
with col_axis_options[3]:
    invert_y_axis = st.checkbox(
        "🔄 Invert Y-Axis", 
        value=False,
        key="invert_y_axis"
    )

col_range1, col_range2, col_range3, col_range4 = st.columns(4)
with col_range1:
    x_min = st.number_input(
        "X Min", 
        value=-1000.0, 
        help="Minimum X value (Pressure, psi) - can be very large or small",
        key="x_min_range"
    )
with col_range2:
    x_max = st.number_input(
        "X Max", 
        value=4000.0, 
        help="Maximum X value (Pressure, psi) - can be very large or small",
        key="x_max_range"
    )

# Y-axis controls with conditional rendering
with col_range3:
    if auto_scale_y:
        st.info("📏 Y-axis will be auto-scaled based on data")
        y_min_input = -1000.0  # Default for auto-scale
    else:
        y_min_input = st.number_input(
            "Y Min", 
            value=-1000.0, 
            help="Minimum Y value (Depth, ft) - can be negative",
            key="y_min_range"
        )

with col_range4:
    if auto_scale_y:
        st.info("📏 Y-axis will be auto-scaled based on data")
        y_max_input = 1000.0  # Default for auto-scale
    else:
        y_max_input = st.number_input(
            "Y Max", 
            value=1000.0, 
            help="Maximum Y value (Depth, ft)",
            key="y_max_range"
        )

# Range validation
if x_min >= x_max:
    st.markdown("""
    <div class="error-box">
        <strong>❌ Invalid X Range:</strong> X Max must be greater than X Min
    </div>
    """, unsafe_allow_html=True)
    st.stop()

if not auto_scale_y and y_min_input >= y_max_input:
    st.markdown("""
    <div class="error-box">
        <strong>❌ Invalid Y Range:</strong> Y Max must be greater than Y Min
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# Data Upload Section
st.markdown('<h2 class="section-header">📁 Data Upload</h2>', unsafe_allow_html=True)

col_upload1, col_upload2 = st.columns([3, 1])
with col_upload1:
    st.markdown("""
    **Excel Format:**
    - Column A: Curve Name (e.g., 'Curve1')
    - Column B+: Coefficients (highest degree first)
    - Maximum polynomial degree: 10
    - Handles any range automatically (from -10000 to 10000 and beyond)
    """)
    uploaded_file = st.file_uploader(
        "Choose Excel file", 
        type=['xlsx', 'xls'], 
        help="Upload your polynomial data", 
        key="uploaded_file"
    )
with col_upload2:
    if uploaded_file is not None:
        if st.button("👁️ Preview Data", key="preview_button"):
            with st.spinner("Previewing data..."):
                preview_result = preview_data(uploaded_file, max_rows=3)
                if "error" not in preview_result:
                    with st.container():
                        st.markdown(""" 
                        ✅ Data Preview: 
                        """, unsafe_allow_html=True)
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Rows", preview_result["rows"])
                            st.metric("Columns", preview_result["columns"])
                        with col2:
                            sample_row = preview_result["first_row"][:6] if preview_result["first_row"] else []
                            st.write("**Sample Row:**", sample_row)
                else:
                    st.markdown(f""" 
                    ❌ Preview Error: {preview_result["error"]} 
                    """, unsafe_allow_html=True)

# Handle no file upload
if not uploaded_file and not debug:
    st.markdown(""" 
    ⚠️ No File Uploaded: Please upload an Excel file to generate plots 
    """, unsafe_allow_html=True)
    st.stop()

# Plot Configuration Section
st.markdown('<h2 class="section-header">🎨 Plot Configuration</h2>', unsafe_allow_html=True)
col_style1, col_style2 = st.columns(2)

with col_style1:
    st.subheader("Visual Style")
    color_mode = st.radio(
        "Color Mode", 
        ["Colorful", "Black and White"], 
        key="color_mode"
    )
    use_colorful = color_mode == "Colorful"
    if use_colorful:
        num_colors = st.slider(
            "Number of Colors", 
            min_value=5, 
            max_value=50, 
            value=35, 
            key="num_colors"
        )
    else:
        num_colors = 1
    bg_color = st.color_picker(
        "Background Color", 
        value='#F8F9FA' if use_colorful else '#FFFFFF', 
        key="bg_color"
    )

with col_style2:
    st.subheader("Layout")
    legend_loc = st.selectbox(
        "Legend Position", 
        ["Upper Right", "Upper Left", "Lower Right", "Lower Left", "Center Left", "Center Right", "Upper Center", "Lower Center", "Best"], 
        index=8, 
        key="legend_loc"
    )
    plot_grouping = st.radio(
        "Plot Grouping", 
        ["All in One", "One per Curve"], 
        horizontal=True, 
        key="plot_grouping"
    )
    custom_legends = st.text_area(
        "Custom Legends (Optional)", 
        placeholder="Curve1: #ff0000\nCurve2\nCurve3: #00ff00", 
        help="Format: 'name: #hex_color' or just 'name' (one per line)", 
        height=80, 
        key="custom_legends"
    )

# Grid and Ticks Section
st.markdown('<h2 class="section-header">📐 Grid & Ticks</h2>', unsafe_allow_html=True)
show_grid = st.checkbox("Show Grid", value=True, key="show_grid")
col_grid1, col_grid2 = st.columns(2)

with col_grid1:
    st.subheader("X-Axis (Pressure)")
    # Calculate reasonable defaults based on range
    x_range = abs(x_max - x_min)
    grid_major_x_default = max(1e-10, x_range / 10)
    grid_minor_x_default = max(1e-10, x_range / 50)
    x_major_int_default = max(1e-10, x_range / 8)
    x_minor_int_default = max(1e-10, x_range / 40)

    grid_major_x = st.number_input(
        "Major Grid Spacing", 
        value=grid_major_x_default, 
        min_value=1e-10, 
        step=max(1e-10, grid_major_x_default * 0.1), 
        key="grid_major_x"
    )
    grid_minor_x = st.number_input(
        "Minor Grid Spacing", 
        value=grid_minor_x_default, 
        min_value=1e-10, 
        step=max(1e-10, grid_minor_x_default * 0.1), 
        key="grid_minor_x"
    )
    x_major_int = st.number_input(
        "Major Tick Interval", 
        value=x_major_int_default, 
        min_value=1e-10, 
        step=max(1e-10, x_major_int_default * 0.1), 
        key="x_major_int"
    )
    x_minor_int = st.number_input(
        "Minor Tick Interval", 
        value=x_minor_int_default, 
        min_value=1e-10, 
        step=max(1e-10, x_minor_int_default * 0.1), 
        key="x_minor_int"
    )

with col_grid2:
    st.subheader("Y-Axis (Depth)")
    # Calculate reasonable defaults based on range
    if auto_scale_y:
        y_range = 2000  # Default range for auto-scaling
    else:
        y_range = abs(y_max_input - y_min_input)
    
    grid_major_y_default = max(1e-10, y_range / 10)
    grid_minor_y_default = max(1e-10, y_range / 50)
    y_major_int_default = max(1e-10, y_range / 8)
    y_minor_int_default = max(1e-10, y_range / 40)

    grid_major_y = st.number_input(
        "Major Grid Spacing", 
        value=grid_major_y_default, 
        min_value=1e-10, 
        step=max(1e-10, grid_major_y_default * 0.1), 
        key="grid_major_y"
    )
    grid_minor_y = st.number_input(
        "Minor Grid Spacing", 
        value=grid_minor_y_default, 
        min_value=1e-10, 
        step=max(1e-10, grid_minor_y_default * 0.1), 
        key="grid_minor_y"
    )
    y_major_int = st.number_input(
        "Major Tick Interval", 
        value=y_major_int_default, 
        min_value=1e-10, 
        step=max(1e-10, y_major_int_default * 0.1), 
        key="y_major_int"
    )
    y_minor_int = st.number_input(
        "Minor Tick Interval", 
        value=y_minor_int_default, 
        min_value=1e-10, 
        step=max(1e-10, y_minor_int_default * 0.1), 
        key="y_minor_int"
    )

# Generate Plot Button
if st.button("📊 Generate Plot", type="primary"):
    with st.spinner("Generating plots..."):
        try:
            # Load data
            data = load_reference_data(uploaded_file)
            
            if debug:
                st.markdown("### 🔍 Debug Information")
                st.write("Loaded Data:")
                st.write(data)
            
            # Determine Y-axis limits
            if auto_scale_y:
                y_min = None
                y_max = None
            else:
                y_min = y_min_input
                y_max = y_max_input
            
            # Generate plots
            plot_configs = {
                'x_min': x_min,
                'x_max': x_max,
                'y_min': y_min,
                'y_max': y_max,
                'stop_y_exit': stop_y_exit,
                'stop_x_exit': stop_x_exit,
                'invert_y_axis': invert_y_axis,
                'color_mode': color_mode,
                'num_colors': num_colors,
                'bg_color': bg_color,
                'legend_loc': legend_loc,
                'plot_grouping': plot_grouping,
                'custom_legends': custom_legends,
                'show_grid': show_grid,
                'grid_major_x': grid_major_x,
                'grid_minor_x': grid_minor_x,
                'x_major_int': x_major_int,
                'x_minor_int': x_minor_int,
                'grid_major_y': grid_major_y,
                'grid_minor_y': grid_minor_y,
                'y_major_int': y_major_int,
                'y_minor_int': y_minor_int
            }
            
            # Generate and display plots
            plots = plot_graphs(data, **plot_configs)
            
            for i, plot in enumerate(plots):
                st.pyplot(plot)
                
                # Download button for individual plots
                buf = BytesIO()
                plot.savefig(buf, format='png', bbox_inches='tight')
                buf.seek(0)
                img_str = base64.b64encode(buf.read()).decode()
                st.markdown(f"""
                <a href="data:image/png;base64,{img_str}" download="curve_plot_{i+1}.png">
                    💾 Download Plot {i+1}
                </a>
                """, unsafe_allow_html=True)
                
        except Exception as e:
            st.markdown(f"""
            <div class="error-box">
                <strong>❌ Plot Generation Error:</strong> {str(e)}
            </div>
            """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #6c757d;'>
    <p>Advanced Curve Plotter v1.0 | Built with ❤️ using Streamlit & Matplotlib</p>
</div>
""", unsafe_allow_html=True)
