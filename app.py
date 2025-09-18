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
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'data_processed' not in st.session_state:
    st.session_state.data_processed = False

st.markdown('<h1 class="main-header">Advanced Curve Plotter</h1>', unsafe_allow_html=True)
st.markdown("Plot polynomial curves with support for large ranges (-10000 to 10000) and degree 10 maximum.")

# Debug Toggle
st.sidebar.markdown("### 🔧 Debug & Settings")
debug = st.sidebar.checkbox("Enable Debug Mode", value=False, help="Show detailed data processing info")

# Large Range Support Toggle
large_range_mode = st.sidebar.checkbox(
    "Large Range Mode (-10000 to 10000)", 
    value=False, 
    help="Optimizes settings for very large axis ranges"
)

# Axis Ranges Section
st.markdown('<h2 class="section-header">🎯 Axis Configuration</h2>', unsafe_allow_html=True)

# Dynamic defaults based on large range mode
if large_range_mode:
    x_min_default, x_max_default = -10000.0, 10000.0
    y_min_default, y_max_default = -10000.0, 10000.0
    grid_x_default, tick_x_default = 2000.0, 1000.0
    grid_y_default, tick_y_default = 2000.0, 1000.0
else:
    x_min_default, x_max_default = -1000.0, 4000.0
    y_min_default, y_max_default = -1000.0, 1000.0
    grid_x_default, tick_x_default = 1000.0, 500.0
    grid_y_default, tick_y_default = 1000.0, 500.0

col_axis_options = st.columns([1, 1, 1, 1])
with col_axis_options[0]:
    auto_scale_y = st.checkbox(
        "🔄 Auto-Scale Y-Axis", 
        value=True if large_range_mode else False,
        help="Automatically adjust Y limits to fit all curves. Recommended for large ranges."
    )
with col_axis_options[1]:
    stop_y_exit = st.checkbox(
        "⏹️ Stop at Y-Exit", 
        value=False,
        help="Stop curves at first Y-range exit (prevents truncation of curves that re-enter)"
    )
with col_axis_options[2]:
    stop_x_exit = st.checkbox(
        "⏹️ Stop at X-Exit", 
        value=False,
        help="Stop curves at first X-range exit"
    )
with col_axis_options[3]:
    invert_y_axis = st.checkbox(
        "🔄 Invert Y-Axis", 
        value=False,
        help="Reverse Y-axis direction (depth increases upward)"
    )

col_range1, col_range2, col_range3, col_range4 = st.columns(4)
with col_range1:
    x_min = st.number_input(
        "X Min", 
        value=x_min_default, 
        help="Minimum X value (Pressure, psi)",
        key="x_min"
    )
with col_range2:
    x_max = st.number_input(
        "X Max", 
        value=x_max_default, 
        help="Maximum X value (Pressure, psi)",
        key="x_max"
    )
with col_range3:
    y_min_input = st.number_input(
        "Y Min", 
        value=y_min_default, 
        help="Minimum Y value (Depth, ft)",
        disabled=auto_scale_y,
        key="y_min_input"
    )
with col_range4:
    y_max_input = st.number_input(
        "Y Max", 
        value=y_max_default, 
        help="Maximum Y value (Depth, ft)",
        disabled=auto_scale_y,
        key="y_max_input"
    )

# Range validation with better UX
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
    - Supports large ranges (-10000 to 10000)
    """)
    
    uploaded_file = st.file_uploader(
        "Choose Excel file", 
        type=['xlsx', 'xls'],
        help="Upload your polynomial data"
    )

with col_upload2:
    # Preview button
    if uploaded_file is not None and st.button("👁️ Preview Data", key="preview"):
        with st.spinner("Previewing data..."):
            preview_result = preview_data(uploaded_file, max_rows=3)
            if "error" not in preview_result:
                st.markdown("""
                <div class="success-box">
                    <strong>✅ Data Preview:</strong>
                </div>
                """, unsafe_allow_html=True)
                st.json({
                    "Rows": preview_result["rows"],
                    "Columns": preview_result["columns"],
                    "Sample Row": preview_result["first_row"][:5]  # Show first 5 columns
                })
            else:
                st.markdown(f"""
                <div class="error-box">
                    <strong>❌ Preview Error:</strong> {preview_result["error"]}
                </div>
                """, unsafe_allow_html=True)

# Handle no file upload
if not uploaded_file and not debug:
    st.markdown("""
    <div class="warning-box">
        <strong>⚠️ No File Uploaded:</strong> Please upload an Excel file to generate plots
    </div>
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
        index=0 if large_range_mode else 1
    )
    use_colorful = color_mode == "Colorful"
    
    if use_colorful:
        num_colors = st.slider(
            "Number of Colors", 
            min_value=5, 
            max_value=50, 
            value=min(35, len(uploaded_file) if uploaded_file else 35)
        )
    else:
        num_colors = 1
        
    bg_color = st.color_picker(
        "Background Color", 
        value='#F8F9FA' if use_colorful else '#FFFFFF'
    )

with col_style2:
    st.subheader("Layout")
    legend_loc = st.selectbox(
        "Legend Position", 
        ["Upper Right", "Upper Left", "Lower Right", "Lower Left", 
         "Center Left", "Center Right", "Upper Center", "Lower Center", "Best"],
        index=8  # "Best" for automatic placement
    )
    
    plot_grouping = st.radio(
        "Plot Grouping", 
        ["All in One", "One per Curve"],
        horizontal=True,
        help="All in One: All curves on single plot | One per Curve: Separate plot per curve"
    )
    
    custom_legends = st.text_area(
        "Custom Legends (Optional)", 
        placeholder="Curve1: #ff0000\nCurve2\nCurve3: #00ff00",
        help="Format: 'name: #hex_color' or just 'name' (one per line)",
        height=80
    )

# Grid and Ticks Section
st.markdown('<h2 class="section-header">📐 Grid & Ticks</h2>', unsafe_allow_html=True)

show_grid = st.checkbox("Show Grid", value=True)

col_grid1, col_grid2 = st.columns(2)
with col_grid1:
    st.subheader("X-Axis (Pressure)")
    grid_major_x = st.number_input(
        "Major Grid Spacing", 
        value=grid_x_default, 
        min_value=1e-10,
        step=grid_x_default * 0.1
    )
    grid_minor_x = st.number_input(
        "Minor Grid Spacing", 
        value=grid_x_default * 0.2, 
        min_value=1e-10,
        step=grid_x_default * 0.05
    )
    x_major_int = st.number_input(
        "Major Tick Interval", 
        value=tick_x_default, 
        min_value=1e-10,
        step=tick_x_default * 0.1
    )
    x_minor_int = st.number_input(
        "Minor Tick Interval", 
        value=tick_x_default * 0.2, 
        min_value=1e-10,
        step=tick_x_default * 0.05
    )

with col_grid2:
    st.subheader("Y-Axis (Depth)")
    grid_major_y = st.number_input(
        "Major Grid Spacing", 
        value=grid_y_default, 
        min_value=1e-10,
        step=grid_y_default * 0.1
    )
    grid_minor_y = st.number_input(
        "Minor Grid Spacing", 
        value=grid_y_default * 0.2, 
        min_value=1e-10,
        step=grid_y_default * 0.05
    )
    y_major_int = st.number_input(
        "Major Tick Interval", 
        value=tick_y_default, 
        min_value=1e-10,
        step=tick_y_default * 0.1
    )
    y_minor_int = st.number_input(
        "Minor Tick Interval", 
        value=tick_y_default * 0.2, 
        min_value=1e-10,
        step=tick_y_default * 0.05
    )

# Axis Position Section
col_axis_pos1, col_axis_pos2 = st.columns(2)
with col_axis_pos1:
    x_pos = st.radio("X-Axis Position", ["Bottom", "Top"], index=0)
with col_axis_pos2:
    y_pos = st.radio("Y-Axis Position", ["Left", "Right"], index=0)

# Labels Section
st.markdown('<h2 class="section-header">✏️ Labels & Title</h2>', unsafe_allow_html=True)

col_labels1, col_labels2 = st.columns(2)
with col_labels1:
    title = st.text_input("Chart Title", value="Polynomial Curve Analysis")
with col_labels2:
    x_label = st.text_input("X-Axis Label", value="Pressure Gradient, psi")

y_label = st.text_input("Y-Axis Label", value="True Vertical Depth, ft", key="y_label")

# Generate Button Section
if st.button("🚀 Generate Plot(s)", type="primary", use_container_width=True):
    # Clear previous plots
    plt.close('all')
    
    # Set y limits based on auto-scale
    y_min = y_min_input if not auto_scale_y else None
    y_max = y_max_input if not auto_scale_y else None
    
    with st.spinner(f"Processing {len(uploaded_file)} curves..."):
        start_time = time.time()
        
        try:
            # Load data with error handling
            if debug:
                data_ref, skipped_rows = load_reference_data(uploaded_file, debug=True)
            else:
                data_ref = load_reference_data(uploaded_file, debug=False)
                skipped_rows = []
            
            processing_time = time.time() - start_time
            st.session_state.data_processed = True
            
            if not data_ref:
                st.markdown("""
                <div class="error-box">
                    <strong>❌ No Valid Data:</strong> Failed to load curves from Excel file. 
                    Check format: Column A = Name, Column B+ = Coefficients.
                </div>
                """, unsafe_allow_html=True)
                if debug and skipped_rows:
                    st.markdown("**Debug Info:**")
                    for skip in skipped_rows:
                        st.write(f"• {skip}")
                st.stop()
            
            # Summary
            st.markdown(f"""
            <div class="success-box">
                <strong>✅ Data Loaded Successfully!</strong><br>
                • {len(data_ref)} curves processed in {processing_time:.2f}s<br>
                • Max degree: {max(len(d['coefficients'])-1 for d in data_ref)}<br>
                {'• Auto-scaling Y-axis enabled' if auto_scale_y else '• Fixed Y-range: [{y_min_input:.1f}, {y_max_input:.1f}]'}
            </div>
            """, unsafe_allow_html=True)
            
            if skipped_rows and debug:
                st.markdown(f"""
                <div class="warning-box">
                    <strong>⚠️ {len(skipped_rows)} rows skipped:</strong>
                </div>
                """, unsafe_allow_html=True)
                for skip in skipped_rows[:5]:  # Show first 5
                    st.write(f"• {skip}")
                if len(skipped_rows) > 5:
                    st.write(f"... and {len(skipped_rows)-5} more")
            
            # Generate plots
            result = plot_graphs(
                data_ref=data_ref,
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
                y_min=y_min,
                y_max=y_max,
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
                figsize=(12, 8) if large_range_mode else (10, 6),
                dpi=300
            )
            
            figs, skipped_curves = result
            
            if not figs:
                st.markdown("""
                <div class="error-box">
                    <strong>❌ No Plots Generated:</strong> All curves were skipped. Enable debug mode for details.
                </div>
                """, unsafe_allow_html=True)
                if debug and skipped_curves:
                    for skip in skipped_curves:
                        st.write(f"• {skip}")
                st.stop()
            
            # Debug Information (if enabled)
            if debug:
                with st.expander("🔍 Detailed Debug Information", expanded=False):
                    col_debug1, col_debug2 = st.columns(2)
                    
                    with col_debug1:
                        st.subheader("📊 Loaded Curves")
                        debug_data = []
                        for entry in data_ref:
                            degree = len(entry['coefficients']) - 1
                            debug_data.append({
                                "Name": entry['name'][:20],  # Truncate long names
                                "Degree": degree,
                                "Coefficients": len(entry['coefficients']),
                                "Original Row": entry.get('row_index', 'N/A')
                            })
                        st.dataframe(pd.DataFrame(debug_data), use_container_width=True)
                    
                    with col_debug2:
                        if skipped_curves:
                            st.subheader("🚫 Skipped Curves")
                            skipped_df = pd.DataFrame({
                                "Reason": [s.split(': ', 1)[1] if ': ' in s else s 
                                         for s in skipped_curves[:10]],
                                "Curve": [s.split('Curve ')[1].split(':')[0] if 'Curve ' in s else 'N/A'
                                        for s in skipped_curves[:10]]
                            })
                            st.dataframe(skipped_df, use_container_width=True)
                        
                        # Range info
                        st.subheader("📏 Final Plot Ranges")
                        x_range = x_max - x_min
                        st.metric("X Range Width", f"{x_range:,.0f}")
                        if auto_scale_y:
                            st.metric("Y Range (Auto)", "Computed from data")
                        else:
                            y_range = y_max_input - y_min_input
                            st.metric("Y Range Width", f"{y_range:,.0f}")
            
            # Display Plots
            st.markdown('<h2 class="section-header">📈 Generated Plots</h2>', unsafe_allow_html=True)
            
            if plot_grouping == "All in One" and len(figs) == 1 and len(data_ref) > 20:
                st.markdown("""
                <div class="warning-box">
                    <strong>⚠️ Dense Plot:</strong> {len(data_ref)} curves on one plot may be hard to read. 
                    Consider using "One per Curve" for better visibility.
                </div>
                """, unsafe_allow_html=True)
            
            plot_columns = 1 if plot_grouping == "All in One" else 2
            for i, (fig, curve_name) in enumerate(figs):
                # Create subheader
                plot_title = f"Plot {i+1}" + (f": {curve_name}" if plot_grouping == "One per Curve" else "")
                st.markdown(f"### {plot_title}")
                
                # Display plot
                st.pyplot(fig)
                
                # Download button
                buf = BytesIO()
                safe_name = "".join(c for c in str(curve_name) if c.isalnum() or c in (' ', '-', '_')).rstrip()
                filename = f"curve_plot_{i+1}_{safe_name}.png" if plot_grouping == "One per Curve" else f"all_curves_{i+1}.png"
                
                fig.savefig(buf, format="png", bbox_inches='tight', dpi=300, facecolor=fig.get_facecolor())
                buf.seek(0)
                b64 = base64.b64encode(buf.read()).decode()
                
                st.markdown(f"""
                <a href="data:image/png;base64,{b64}" download="{filename}" 
                   class="stButton > button" style="background-color: #1f77b4; color: white; padding: 0.5rem 1rem; border-radius: 0.25rem; text-decoration: none;">
                    💾 Download {filename}
                </a>
                """, unsafe_allow_html=True)
                
                plt.close(fig)  # Free memory
            
            # Performance summary
            total_time = time.time() - start_time
            st.markdown(f"""
            <div class="success-box">
                <strong>🎉 Plot(s) Generated Successfully!</strong><br>
                • {len(figs)} plot(s) created in {total_time:.2f}s<br>
                • Resolution: 300 DPI | Size: {('12x8' if large_range_mode else '10x6')} inches
            </div>
            """, unsafe_allow_html=True)
            
        except Exception as e:
            st.markdown(f"""
            <div class="error-box">
                <strong>❌ Unexpected Error:</strong> {str(e)}<br>
                Enable debug mode and try again for more details.
            </div>
            """, unsafe_allow_html=True)
            if debug:
                st.exception(e)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #6c757d;'>
    <p>Advanced Curve Plotter | Supports polynomials up to degree 10 | Large range optimized</p>
</div>
""", unsafe_allow_html=True)
