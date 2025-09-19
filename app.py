import streamlit as st
import matplotlib.pyplot as plt
from data_loader import load_reference_data, preview_data
from plotter import plot_graphs
from io import BytesIO
import base64
import numpy as np
import pandas as pd
import time
import zipfile  # Added missing import for ZIP functionality

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

# FIXED: Y-axis controls with ORIGINAL conditional rendering and layout
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

with col_range3:
    if auto_scale_y:
        st.info("📏 Y-axis will be auto-scaled based on data")
        y_min_input = -1000.0  # Default for auto-scale (but won't be used)
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
        y_max_input = 1000.0  # Default for auto-scale (but won't be used)
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
        if st.button("👁️ Preview Data", key="preview_button", use_container_width=True):
            with st.spinner("Previewing data..."):
                # Create a copy for preview to avoid file handle conflicts
                preview_file = BytesIO(uploaded_file.read())
                preview_file.seek(0)
                preview_result = preview_data(preview_file, max_rows=3)
                
                if "error" not in preview_result:
                    with st.container():
                        st.markdown(""" 
                        <div class="success-box">
                            ✅ Data Preview Successful
                        </div>
                        """, unsafe_allow_html=True)
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Rows", preview_result["rows"])
                            st.metric("Columns", preview_result["columns"])
                        with col2:
                            sample_row = preview_result["first_row"][:6] if preview_result["first_row"] else []
                            st.write("**Sample Row:**", sample_row)
                            if "sample_data" in preview_result:
                                st.write("**Sample Data:**")
                                st.dataframe(pd.DataFrame(preview_result["sample_data"]))
                else:
                    st.markdown(f""" 
                    <div class="error-box">
                        ❌ Preview Error: {preview_result["error"]}
                    </div>
                    """, unsafe_allow_html=True)

# Handle no file upload - FIXED FOR DEBUG MODE
if not uploaded_file:
    if not debug:
        st.markdown(""" 
        <div class="warning-box">
            ⚠️ No File Uploaded: Please upload an Excel file to generate plots
        </div>
        """, unsafe_allow_html=True)
        st.stop()
    else:
        # Debug mode: generate sample data
        st.markdown("""
        <div class="success-box">
            🧪 Debug Mode: Using sample data
        </div>
        """, unsafe_allow_html=True)
        uploaded_file = None  # Will trigger debug data generation

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
if st.button("📊 Generate Plot", type="primary", use_container_width=True):
    with st.spinner("Generating plots..."):
        try:
            # Reset uploaded file position if needed
            if uploaded_file is not None:
                uploaded_file.seek(0)
            
            # Load data - FIXED FOR DEBUG MODE
            if debug and uploaded_file is None:
                data, debug_info = load_reference_data(None, debug=True)
                if debug_info:
                    st.markdown("### 🧪 Debug Data Info")
                    for info in debug_info:
                        st.write(info)
            else:
                data, _ = load_reference_data(uploaded_file, debug=debug)
            
            if debug:
                st.markdown("### 🔍 Debug Information")
                st.write("**Loaded Data:**")
                st.json(data)
            
            # Validate data loaded
            if not data:
                st.markdown("""
                <div class="error-box">
                    ❌ No valid data loaded. Please check your Excel file format.
                </div>
                """, unsafe_allow_html=True)
                st.stop()
            
            # FIXED: Determine Y-axis limits for auto-scaling
            if auto_scale_y:
                y_min_final = None
                y_max_final = None
            else:
                y_min_final = y_min_input
                y_max_final = y_max_input
            
            # Default values for missing parameters
            x_pos = "bottom"
            y_pos = "left"
            title = "Polynomial Curves"
            x_label = "Pressure (psi)"
            y_label = "Depth (ft)"
            figsize = (12, 8) if plot_grouping == "One per Curve" else (14, 10)
            dpi = 300
            
            # Call plot_graphs with correct parameter order
            figs, skipped_curves = plot_graphs(
                data_ref=data,
                use_colorful=use_colorful,
                num_colors=num_colors,
                bg_color=bg_color,
                legend_loc=legend_loc,
                custom_legends=custom_legends,
                show_grid=show_grid,
                grid_major_x=grid_major_x,
                grid_minor_x=grid_minor_x,
                grid_major_y=grid_major_y,
                grid_minor_y=grid_minor_y,
                x_min=x_min,
                x_max=x_max,
                y_min=y_min_final,  # FIXED: Use None for auto-scaling
                y_max=y_max_final,  # FIXED: Use None for auto-scaling
                x_pos=x_pos,
                y_pos=y_pos,
                x_major_int=x_major_int,
                x_minor_int=x_minor_int,
                y_major_int=y_major_int,
                y_minor_int=y_minor_int,
                title=title,
                x_label=x_label,
                y_label=y_label,
                plot_grouping=plot_grouping,
                auto_scale_y=auto_scale_y,
                stop_y_exit=stop_y_exit,
                stop_x_exit=stop_x_exit,
                debug=debug,
                invert_y_axis=invert_y_axis,
                figsize=figsize,
                dpi=dpi
            )
            
            # Display plots
            if not figs:
                st.markdown("""
                <div class="warning-box">
                    ⚠️ No plots generated. Check the skipped curves below.
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="success-box">
                    ✅ Generated {len(figs)} plot{'s' if len(figs) > 1 else ''}
                </div>
                """, unsafe_allow_html=True)
                
                for i, (fig, curve_name) in enumerate(figs):
                    st.subheader(f"Plot {i+1}" + (f": {curve_name}" if plot_grouping == "One per Curve" else ""))
                    
                    # Display plot
                    st.pyplot(fig)
                    
                    # Download button for individual plots
                    buf = BytesIO()
                    fig.savefig(buf, format='png', bbox_inches='tight', dpi=dpi)
                    buf.seek(0)
                    img_str = base64.b64encode(buf.read()).decode()
                    safe_name = curve_name.replace(' ', '_').replace('/', '_')[:50]  # Sanitize filename
                    st.markdown(f"""
                    <a href="data:image/png;base64,{img_str}" download="curve_plot_{i+1}_{safe_name}.png" style="text-decoration: none; padding: 0.5rem; background-color: #007bff; color: white; border-radius: 0.25rem; display: inline-block;">
                        💾 Download Plot {i+1}: {curve_name}
                    </a>
                    """, unsafe_allow_html=True)
                    
                    # Close the figure to free memory
                    plt.close(fig)
                
                # Bulk download option
                if len(figs) > 1:
                    st.markdown("### 📦 Bulk Download")
                    zip_buffer = BytesIO()
                    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                        for i, (fig, curve_name) in enumerate(figs):
                            buf = BytesIO()
                            fig.savefig(buf, format='png', bbox_inches='tight', dpi=dpi)
                            buf.seek(0)
                            safe_name = f"curve_plot_{i+1}_{curve_name.replace(' ', '_').replace('/', '_')[:50]}.png"
                            zip_file.writestr(safe_name, buf.getvalue())
                    
                    zip_buffer.seek(0)
                    zip_str = base64.b64encode(zip_buffer.read()).decode()
                    st.markdown(f"""
                    <a href="data:application/zip;base64,{zip_str}" download="curve_plots.zip" style="text-decoration: none; padding: 0.5rem; background-color: #28a745; color: white; border-radius: 0.25rem; display: inline-block;">
                        📦 Download All Plots as ZIP
                    </a>
                    """, unsafe_allow_html=True)
            
            # Show skipped curves if any
            if skipped_curves:
                st.markdown(f"""
                <div class="warning-box">
                    <strong>⚠️ Skipped Curves ({len(skipped_curves)}):</strong><br>
                    {', '.join([f'<span style="display: block;">• {s}</span>' for s in skipped_curves[:5]])}
                    {'<br><em>...and {len(skipped_curves)-5} more</em>' if len(skipped_curves) > 5 else ''}
                </div>
                """, unsafe_allow_html=True)
                
        except Exception as e:
            st.markdown(f"""
            <div class="error-box">
                <strong>❌ Plot Generation Error:</strong><br>
                <code>{str(e)}</code><br>
                <small>Please check your data format and try again.</small>
            </div>
            """, unsafe_allow_html=True)
            # Clean up any open figures on error
            plt.close('all')

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #6c757d;'>
    <p>Advanced Curve Plotter v1.0 | Built with ❤️ using Streamlit & Matplotlib</p>
</div>
""", unsafe_allow_html=True)
