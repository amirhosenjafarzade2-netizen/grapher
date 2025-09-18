""")

uploaded_file = st.file_uploader(
    "Choose Excel file", 
    type=['xlsx', 'xls'],
    help="Upload your polynomial data"
)

with col_upload2:
if uploaded_file is not None:
    if st.button("👁️ Preview Data"):
        with st.spinner("Previewing data..."):
            preview_result = preview_data(uploaded_file, max_rows=3)
            if "error" not in preview_result:
                with st.container():
                    st.markdown("""
                    <div class="success-box">
                        <strong>✅ Data Preview:</strong>
                    </div>
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
    ["Upper Right", "Upper Left", "Lower Right", "Lower Left", 
     "Center Left", "Center Right", "Upper Center", "Lower Center", "Best"],
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
# Use reasonable defaults for Y (will be overridden by auto-scale)
y_range_estimate = 2000.0  # Default estimate
grid_major_y_default = max(1e-10, y_range_estimate / 10)
grid_minor_y_default = max(1e-10, y_range_estimate / 50)
y_major_int_default = max(1e-10, y_range_estimate / 8)
y_minor_int_default = max(1e-10, y_range_estimate / 40)

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

# Axis Position Section
col_axis_pos1, col_axis_pos2 = st.columns(2)
with col_axis_pos1:
x_pos = st.radio("X-Axis Position", ["Bottom", "Top"], index=0, key="x_pos")
with col_axis_pos2:
y_pos = st.radio("Y-Axis Position", ["Left", "Right"], index=0, key="y_pos")

# Labels Section
st.markdown('<h2 class="section-header">✏️ Labels & Title</h2>', unsafe_allow_html=True)

col_labels1, col_labels2 = st.columns(2)
with col_labels1:
title = st.text_input("Chart Title", value="Polynomial Curve Analysis", key="title")
with col_labels2:
x_label = st.text_input("X-Axis Label", value="Pressure Gradient, psi", key="x_label")

y_label = st.text_input("Y-Axis Label", value="True Vertical Depth, ft", key="y_label")

# Generate Button Section
if st.button("🚀 Generate Plot(s)", type="primary", use_container_width=True):
# Clear previous plots
plt.close('all')

# Set y limits based on auto-scale
y_min = y_min_input if not auto_scale_y else None
y_max = y_max_input if not auto_scale_y else None

with st.spinner("Processing curves..."):
    start_time = time.time()
    
    try:
        # Load data with error handling
        if debug:
            data_ref, skipped_rows = load_reference_data(uploaded_file, debug=True)
        else:
            data_ref = load_reference_data(uploaded_file, debug=False)
            skipped_rows = []
        
        processing_time = time.time() - start_time
        
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
        max_degree = max(len(d['coefficients']) - 1 for d in data_ref)
        st.markdown(f"""
        <div class="success-box">
            <strong>✅ Data Loaded Successfully!</strong><br>
            • {len(data_ref)} curves processed in {processing_time:.2f}s<br>
            • Max degree: {max_degree} (limited to 10)<br>
            • Range: X=[{x_min:.1f}, {x_max:.1f}], Y={'Auto-scale' if auto_scale_y else f'[{y_min_input:.1f}, {y_max_input:.1f}]'}
        </div>
        """, unsafe_allow_html=True)
        
        if skipped_rows and debug:
            with st.container():
                st.markdown(f"""
                <div class="warning-box">
                    <strong>⚠️ {len(skipped_rows)} rows skipped:</strong>
                </div>
                """, unsafe_allow_html=True)
                for skip in skipped_rows[:5]:
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
            figsize=(10, 6),
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
                            "Name": entry['name'][:20],
                            "Degree": degree,
                            "Coefficients": len(entry['coefficients']),
                            "Row": entry.get('row_index', 'N/A')
                        })
                    st.dataframe(pd.DataFrame(debug_data), use_container_width=True)
                
                with col_debug2:
                    if skipped_curves:
                        st.subheader("🚫 Skipped Curves")
                        skipped_df = pd.DataFrame({
                            "Reason": [s.split(': ', 1)[1] if ': ' in s else s for s in skipped_curves[:10]],
                            "Curve": [s.split('Curve ')[1].split(':')[0] if 'Curve ' in s else 'N/A' for s in skipped_curves[:10]]
                        })
                        st.dataframe(skipped_df, use_container_width=True)
                    
                    # Range info
                    st.subheader("📏 Plot Ranges")
                    x_range_width = x_max - x_min
                    st.metric("X Range Width", f"{x_range_width:,.0f}")
                    if auto_scale_y:
                        st.metric("Y Range", "Auto-computed from data")
                    else:
                        y_range_width = y_max_input - y_min_input
                        st.metric("Y Range Width", f"{y_range_width:,.0f}")
        
        # Display Plots
        st.markdown('<h2 class="section-header">📈 Generated Plots</h2>', unsafe_allow_html=True)
        
        if plot_grouping == "All in One" and len(figs) == 1 and len(data_ref) > 20:
            st.markdown(f"""
            <div class="warning-box">
                <strong>⚠️ Dense Plot:</strong> {len(data_ref)} curves on one plot may be hard to read. 
                Consider using "One per Curve" for better visibility.
            </div>
            """, unsafe_allow_html=True)
        
        # Show plots in columns if multiple
        if plot_grouping == "One per Curve" and len(figs) > 1:
            cols = st.columns(min(2, len(figs)))
            for i, (fig, curve_name) in enumerate(figs):
                with cols[i % len(cols)]:
                    st.markdown(f"### {curve_name}")
                    st.pyplot(fig)
                    
                    # Download button
                    buf = BytesIO()
                    safe_name = "".join(c for c in str(curve_name) if c.isalnum() or c in (' ', '-', '_')).rstrip()
                    filename = f"curve_{safe_name}.png"
                    
                    fig.savefig(buf, format="png", bbox_inches='tight', dpi=300, facecolor=fig.get_facecolor())
                    buf.seek(0)
                    b64 = base64.b64encode(buf.read()).decode()
                    
                    st.markdown(f"""
                    <a href="data:image/png;base64,{b64}" download="{filename}" 
                       style="background-color: #1f77b4; color: white; padding: 0.5rem 1rem; 
                       border-radius: 0.25rem; text-decoration: none; display: inline-block; margin: 0.5rem 0;">
                        💾 Download {curve_name}
                    </a>
                    """, unsafe_allow_html=True)
                    
                    plt.close(fig)
        else:
            # Single plot or all in one
            for i, (fig, curve_name) in enumerate(figs):
                plot_title = f"Plot {i+1}" + (f": {curve_name}" if plot_grouping == "One per Curve" else "")
                st.markdown(f"### {plot_title}")
                
                st.pyplot(fig)
                
                # Download button
                buf = BytesIO()
                safe_name = "".join(c for c in str(curve_name) if c.isalnum() or c in (' ', '-', '_')).rstrip()
                filename = f"all_curves.png" if plot_grouping == "All in One" else f"curve_{safe_name}.png"
                
                fig.savefig(buf, format="png", bbox_inches='tight', dpi=300, facecolor=fig.get_facecolor())
                buf.seek(0)
                b64 = base64.b64encode(buf.read()).decode()
                
                st.markdown(f"""
                <a href="data:image/png;base64,{b64}" download="{filename}" 
                   style="background-color: #1f77b4; color: white; padding: 0.5rem 1rem; 
                   border-radius: 0.25rem; text-decoration: none; display: inline-block; margin: 0.5rem 0;">
                    💾 Download {filename}
                </a>
                """, unsafe_allow_html=True)
                
                plt.close(fig)
        
        # Performance summary
        total_time = time.time() - start_time
        st.markdown(f"""
        <div class="success-box">
            <strong>🎉 Plot(s) Generated Successfully!</strong><br>
            • {len(figs)} plot(s) created in {total_time:.2f}s<br>
            • Resolution: 300 DPI | Size: 10x6 inches<br>
            • Range handling: Automatic (supports -10000 to 10000+)
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
<p>Advanced Curve Plotter | Automatic range handling | Max degree 10 | Built with Streamlit</p>
</div>
""", unsafe_allow_html=True)
