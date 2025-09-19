import streamlit as st
import matplotlib.pyplot as plt
from data_loader import load_reference_data
from plotter import plot_graphs
from io import BytesIO
import base64
import numpy as np
import pandas as pd
import time
import zipfile

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
    .info-box {background-color: #d1ecf1; padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #17a2b8;}
    .stNumberInput > div > div > div > div {width: 100%;}
    .curve-selector {background-color: #f8f9fa; padding: 1rem; border-radius: 0.5rem; margin: 0.5rem 0;}
    .selection-mode {background-color: #e9ecef; padding: 1rem; border-radius: 0.5rem; margin: 0.5rem 0;}
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-header">Advanced Curve Plotter</h1>', unsafe_allow_html=True)
st.markdown("Plot polynomial curves with automatic range handling (from -10000 to 10000 and beyond)")

# Debug Toggle
debug = st.sidebar.checkbox("Enable Debug Mode", value=False, help="Show detailed data processing info")

# Data Upload Section - FIRST THING
st.markdown('<h2 class="section-header">📁 Data Upload</h2>', unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    "Choose Excel file", 
    type=['xlsx', 'xls'], 
    help="Upload your polynomial data", 
    key="uploaded_file"
)

# Load data immediately after upload
data = []
skipped_info = []

if uploaded_file is not None:
    with st.spinner("Loading data..."):
        uploaded_file.seek(0)
        data, skipped_info = load_reference_data(uploaded_file, debug=debug)
        
        if data:
            st.markdown(f"""
            <div class="success-box">
                ✅ Data loaded successfully! Found {len(data)} valid curves
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="error-box">
                ❌ No valid data found in the file. Please check the Excel format.
            </div>
            """, unsafe_allow_html=True)
            if skipped_info:
                with st.expander("🔍 Show validation details"):
                    for skip in skipped_info:
                        st.write(f"• {skip}")
            st.stop()
elif debug:
    with st.spinner("Loading sample data..."):
        data, skipped_info = load_reference_data(None, debug=True)
        st.markdown(f"""
        <div class="success-box">
            🧪 Debug Mode: Using sample data ({len(data)} curves)
        </div>
        """, unsafe_allow_html=True)

# Stop if no data
if not data:
    st.markdown("""
    <div class="warning-box">
        ⚠️ No data loaded. Please upload an Excel file to continue.
    </div>
    """, unsafe_allow_html=True)
    st.stop()

if debug:
    with st.expander("🔍 Debug Information"):
        st.write("**Loaded Data:**")
        st.json(data)
        if skipped_info:
            st.markdown("**Skipped Rows:**")
            for skip in skipped_info[:10]:  # Show first 10
                st.write(f"• {skip}")

# Axis Ranges Section - NOW SAFE TO RENDER
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

# Y-axis controls with conditional rendering and layout
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
        y_min_input = -1000.0
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
        y_max_input = 1000.0
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

# Curve Selection Mode - NOW SAFE SINCE WE HAVE DATA
st.markdown('<h2 class="section-header">🗂️ Plot Selection Mode</h2>', unsafe_allow_html=True)

plot_mode = st.radio(
    "Choose plotting mode:",
    [
        "📊 All Selected Curves in One Graph",
        "📈 One Graph per Curve", 
        "🔍 Two Curves Comparison (for intersections)"
    ],
    index=0,
    key="plot_mode",
    horizontal=True
)

selected_data = []

if plot_mode == "📊 All Selected Curves in One Graph":
    # Show all curve selection for combined plot
    st.markdown('<div class="selection-mode">')
    st.markdown("**Select curves to include in the combined plot:**")
    
    num_cols = min(3, len(data))  # Don't create more columns than curves
    curves_per_col = (len(data) + num_cols - 1) // num_cols
    cols = st.columns(num_cols)
    
    for col_idx in range(num_cols):
        with cols[col_idx]:
            st.markdown(f'<div class="curve-selector">', unsafe_allow_html=True)
            start_idx = col_idx * curves_per_col
            end_idx = min(start_idx + curves_per_col, len(data))
            for i in range(start_idx, end_idx):
                entry = data[i]
                curve_name = entry.get('name', f'Curve {i+1}')
                if st.checkbox(
                    curve_name, 
                    value=True, 
                    key=f"select_all_mode_{i}",
                    help=f"Toggle {curve_name} for plotting"
                ):
                    selected_data.append(entry)
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Select All/None buttons
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("✅ Select All Curves", key="select_all_mode", use_container_width=True):
            selected_data.clear()
            for entry in data:
                selected_data.append(entry)
            st.rerun()
    with col_btn2:
        if st.button("❌ Deselect All Curves", key="deselect_all_mode", use_container_width=True):
            selected_data.clear()
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    num_selected = len(selected_data)
    st.markdown(f"""
    <div class="info-box">
        📊 **Summary:** {num_selected} of {len(data)} curves selected for combined plot
    </div>
    """, unsafe_allow_html=True)
    
    if num_selected < 1:
        st.markdown("""
        <div class="error-box">
            ❌ Please select at least one curve to plot
        </div>
        """, unsafe_allow_html=True)
        st.stop()

elif plot_mode == "📈 One Graph per Curve":
    # Show selection for individual plots
    st.markdown('<div class="selection-mode">')
    st.markdown("**Select curves for individual plots:**")
    
    # Select all by default for individual plots
    select_all_individual = st.checkbox(
        "Plot all curves individually", 
        value=True, 
        key="select_all_individual"
    )
    
    if not select_all_individual:
        num_cols = min(3, len(data))
        curves_per_col = (len(data) + num_cols - 1) // num_cols
        cols = st.columns(num_cols)
        
        for col_idx in range(num_cols):
            with cols[col_idx]:
                st.markdown(f'<div class="curve-selector">', unsafe_allow_html=True)
                start_idx = col_idx * curves_per_col
                end_idx = min(start_idx + curves_per_col, len(data))
                for i in range(start_idx, end_idx):
                    entry = data[i]
                    curve_name = entry.get('name', f'Curve {i+1}')
                    if st.checkbox(
                        curve_name, 
                        value=True, 
                        key=f"select_individual_{i}",
                        help=f"Create individual plot for {curve_name}"
                    ):
                        selected_data.append(entry)
                st.markdown('</div>', unsafe_allow_html=True)
        
        # Individual select/deselect buttons
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("✅ Select All for Individual", key="select_all_individual_btn", use_container_width=True):
                selected_data.clear()
                for entry in data:
                    selected_data.append(entry)
                st.rerun()
        with col_btn2:
            if st.button("❌ Deselect All Individual", key="deselect_individual", use_container_width=True):
                selected_data.clear()
                st.rerun()
    
    else:
        # If "plot all" is selected, include all curves
        selected_data = data.copy()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    num_selected = len(selected_data)
    st.markdown(f"""
    <div class="info-box">
        📈 **Summary:** Will create {num_selected} individual plots
    </div>
    """, unsafe_allow_html=True)
    
    if num_selected < 1:
        st.markdown("""
        <div class="error-box">
            ❌ Please select at least one curve to plot
        </div>
        """, unsafe_allow_html=True)
        st.stop()

else:  # Two curves comparison mode
    st.markdown('<div class="selection-mode">')
    st.markdown("**Select two curves for comparison and intersection analysis:**")
    
    col_pair1, col_pair2 = st.columns([1, 1])
    
    with col_pair1:
        st.markdown("**Curve 1:**")
        curve1_options = [entry.get('name', f'Curve {i+1}') for i, entry in enumerate(data)]
        selected_curve1_idx = st.selectbox(
            "Choose first curve:",
            range(len(curve1_options)),
            format_func=lambda i: curve1_options[i],
            key="select_curve1"
        )
    
    with col_pair2:
        st.markdown("**Curve 2:**")
        # Filter out the first selected curve
        available_curve2_options = [curve1_options[i] for i in range(len(curve1_options)) if i != selected_curve1_idx]
        selected_curve2_idx = st.selectbox(
            "Choose second curve:",
            range(len(available_curve2_options)),
            format_func=lambda i: available_curve2_options[i],
            key="select_curve2"
        )
        selected_curve2_original_idx = [i for i in range(len(curve1_options)) if i != selected_curve1_idx][selected_curve2_idx]
    
    # Add selected curves
    if selected_curve1_idx < len(data):
        selected_data.append(data[selected_curve1_idx])
    if 'selected_curve2_original_idx' in locals() and selected_curve2_original_idx < len(data):
        selected_data.append(data[selected_curve2_original_idx])
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    curve1_name = curve1_options[selected_curve1_idx]
    curve2_name = available_curve2_options[selected_curve2_idx] if available_curve2_options else "No second curve"
    st.markdown(f"""
    <div class="info-box">
        🔍 **Comparison:** {curve1_name} vs {curve2_name}
    </div>
    """, unsafe_allow_html=True)

# Determine plot_grouping based on mode
if plot_mode == "📊 All Selected Curves in One Graph":
    plot_grouping = "All in One"
elif plot_mode == "📈 One Graph per Curve":
    plot_grouping = "One per Curve"
else:  # Two curves comparison
    plot_grouping = "All in One"  # Show both in one graph for intersection analysis

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
            min_value=1, 
            max_value=min(50, len(selected_data) if selected_data else 10), 
            value=min(5, len(selected_data) if selected_data else 5), 
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
    custom_legends = st.text_area(
        "Custom Legends (Optional)", 
        placeholder="Curve1: #ff0000\nCurve2\nCurve3: #00ff00", 
        help="Format: 'name: #hex_color' or just 'name' (one per line)", 
        height=80, 
        key="custom_legends"
    )

# Advanced Analytics Section (only show intersection for relevant modes)
st.markdown('<h2 class="section-header">🔬 Advanced Analytics</h2>', unsafe_allow_html=True)
col_analytics1, col_analytics2, col_analytics3 = st.columns(3)

with col_analytics1:
    if plot_mode in ["📊 All Selected Curves in One Graph", "🔍 Two Curves Comparison (for intersections)"]:
        intersect_mode = st.checkbox(
            "🔍 Enable Intersection Finder", 
            value=plot_mode == "🔍 Two Curves Comparison (for intersections)", 
            help="Find and mark collision points between curves",
            key="intersect_mode"
        )
    else:
        intersect_mode = False
        st.markdown("🔍 *Intersection only available for combined plots*")

with col_analytics2:
    plot_deriv = st.checkbox(
        "📈 Plot Derivatives", 
        value=False, 
        help="Show derivative curves as dashed lines",
        key="plot_deriv"
    )

with col_analytics3:
    show_integral = st.checkbox(
        "📊 Show Integrals in Legend", 
        value=False, 
        help="Calculate and display definite integrals from X Min to X Max",
        key="show_integral"
    )

# Grid and Ticks Section
st.markdown('<h2 class="section-header">📐 Grid & Ticks</h2>', unsafe_allow_html=True)
show_grid = st.checkbox("Show Grid", value=True, key="show_grid")
col_grid1, col_grid2 = st.columns(2)

with col_grid1:
    st.subheader("X-Axis (Pressure)")
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
    if auto_scale_y:
        y_range = 2000
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
            # Ensure we have selected data
            if not selected_data:
                st.error("No curves selected for plotting!")
                st.stop()
            
            # Determine Y-axis limits for auto-scaling
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
            if plot_mode == "🔍 Two Curves Comparison (for intersections)":
                title = f"Intersection Analysis: {selected_data[0].get('name', 'Curve1')} vs {selected_data[1].get('name', 'Curve2')}"
            x_label = "Pressure (psi)"
            y_label = "Depth (ft)"
            figsize = (12, 8) if plot_grouping == "One per Curve" else (14, 10)
            dpi = 300
            
            # Call plot_graphs with all parameters
            figs, skipped_curves = plot_graphs(
                data_ref=selected_data,
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
                y_min=y_min_final,
                y_max=y_max_final,
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
                dpi=dpi,
                intersect_mode=intersect_mode,
                plot_deriv=plot_deriv,
                show_integral=show_integral
            )
            
            # Display plots
            if not figs:
                st.markdown("""
                <div class="warning-box">
                    ⚠️ No plots generated. Check the skipped curves below.
                </div>
                """, unsafe_allow_html=True)
            else:
                mode_msg = ""
                if plot_mode == "📊 All Selected Curves in One Graph":
                    mode_msg = f" ({len(selected_data)} curves in one plot)"
                elif plot_mode == "📈 One Graph per Curve":
                    mode_msg = f" ({len(selected_data)} individual plots)"
                elif plot_mode == "🔍 Two Curves Comparison (for intersections)":
                    mode_msg = " (comparison with intersections)"
                
                success_msg = f"✅ Generated {len(figs)} plot{'' if len(figs) == 1 else 's'}{mode_msg}"
                if intersect_mode and plot_mode != "📈 One Graph per Curve":
                    success_msg += " with intersection points!"
                
                st.markdown(f"""
                <div class="success-box">
                    {success_msg}
                </div>
                """, unsafe_allow_html=True)
                
                for i, (fig, curve_name) in enumerate(figs):
                    display_name = curve_name if plot_grouping == "One per Curve" else f"{plot_mode} - {curve_name}"
                    st.subheader(f"Plot {i+1}: {display_name}")
                    
                    # Display plot
                    st.pyplot(fig)
                    
                    # Download button for individual plots
                    buf = BytesIO()
                    fig.savefig(buf, format='png', bbox_inches='tight', dpi=dpi)
                    buf.seek(0)
                    img_str = base64.b64encode(buf.read()).decode()
                    safe_name = curve_name.replace(' ', '_').replace('/', '_')[:50]
                    mode_suffix = plot_mode.replace(" ", "_").replace("(", "").replace(")", "").replace(",", "")[:20]
                    st.markdown(f"""
                    <a href="data:image/png;base64,{img_str}" download="curve_plot_{i+1}_{mode_suffix}_{safe_name}.png" style="text-decoration: none; padding: 0.5rem; background-color: #007bff; color: white; border-radius: 0.25rem; display: inline-block;">
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
                            safe_name = f"plot_{i+1}_{curve_name.replace(' ', '_').replace('/', '_')[:50]}.png"
                            zip_file.writestr(safe_name, buf.getvalue())
                    
                    zip_buffer.seek(0)
                    zip_str = base64.b64encode(zip_buffer.read()).decode()
                    zip_filename = f"curve_plots_{plot_mode.replace(' ', '_').replace('(', '').replace(')', '').replace(',', '')[:30]}.zip"
                    st.markdown(f"""
                    <a href="data:application/zip;base64,{zip_str}" download="{zip_filename}" style="text-decoration: none; padding: 0.5rem; background-color: #28a745; color: white; border-radius: 0.25rem; display: inline-block;">
                        📦 Download All Plots as ZIP
                    </a>
                    """, unsafe_allow_html=True)
            
            # Show skipped curves if any
            if skipped_curves:
                with st.expander(f"⚠️ Skipped Curves ({len(skipped_curves)})", expanded=False):
                    for skip in skipped_curves[:10]:
                        st.write(f"• {skip}")
                    if len(skipped_curves) > 10:
                        st.write(f"... and {len(skipped_curves) - 10} more")
                
        except Exception as e:
            st.markdown(f"""
            <div class="error-box">
                <strong>❌ Plot Generation Error:</strong><br>
                <code>{str(e)}</code><br>
                <small>Please check your data format and try again.</small>
            </div>
            """, unsafe_allow_html=True)
            plt.close('all')

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #6c757d;'>
    <p>Advanced Curve Plotter v2.2 | Data-First Flow | Built with ❤️ using Streamlit & Matplotlib</p>
</div>
""", unsafe_allow_html=True)
