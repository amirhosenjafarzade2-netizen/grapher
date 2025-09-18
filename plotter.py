import matplotlib.pyplot as plt
import numpy as np
from adjustText import adjust_text

DEFAULT_COLORS = [
    '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
    '#aec7e8', '#ffbb78', '#98df8a', '#ff9896', '#c5b0d5', '#c49c94', '#f7b6d2', '#c7c7c7', '#dbdb8d', '#9edae5',
    '#393b79', '#ad494a', '#8c6d31', '#d6616b', '#b5cf6b', '#7b4173', '#ce6dbd', '#637939', '#6b6ecf', '#d4b9da',
    '#843c39', '#de9ed6', '#7b4f4b', '#a55194', '#ce1256'
]

def plot_graphs(data_ref, use_colorful, num_colors, bg_color, legend_loc, custom_legends, show_grid, 
                grid_major_x, grid_minor_x, grid_major_y, grid_minor_y, x_min, x_max, y_min, y_max, 
                x_pos, y_pos, x_major_int, x_minor_int, y_major_int, y_minor_int, 
                title, x_label, y_label, plot_grouping, auto_scale_y, stop_y_exit, stop_x_exit, debug=False,
                invert_y_axis=False, figsize=(10, 6), dpi=300):
    """
    Plot polynomial curves with improved handling for large ranges and degree limits.
    """
    figs = []
    colors = DEFAULT_COLORS[:min(num_colors, len(DEFAULT_COLORS))] if use_colorful else ['black']
    skipped_curves = []
    
    # Input validation
    if x_min > x_max:
        raise ValueError(f"x_min ({x_min}) must be <= x_max ({x_max})")
    if not data_ref:
        return figs, ["No data provided for plotting"]
    
    # Map user-friendly legend_loc to Matplotlib loc
    loc_map = {
        "Upper Right": "upper right",
        "Upper Left": "upper left",
        "Lower Right": "lower right",
        "Lower Left": "lower left",
        "Center Left": "center left",
        "Center Right": "center right",
        "Upper Center": "upper center",
        "Lower Center": "lower center",
        "Center": "center",
        "Best": "best"
    }
    matplotlib_loc = loc_map.get(legend_loc, "upper right")

    # Parse custom legends
    custom_label_map = {}
    custom_color_map = {}
    if custom_legends:
        for line in custom_legends.split('\n'):
            line = line.strip()
            if not line:
                continue
            if ':' in line:
                try:
                    name, color = line.split(':', 1)
                    name = name.strip()
                    custom_label_map[name] = name
                    custom_color_map[name] = color.strip() if use_colorful else 'black'
                except ValueError:
                    skipped_curves.append(f"Invalid custom legend format: {line}")
            else:
                name = line.strip()
                custom_label_map[name] = name

    # Check if axes should be centered at (0,0)
    center_x = x_min < 0 < x_max
    center_y = y_min < 0 < y_max if not auto_scale_y else True

    # Determine number of points based on range size for better resolution
    x_range_width = x_max - x_min
    if x_range_width <= 100:
        num_points = 2000
    elif x_range_width <= 1000:
        num_points = 3000
    elif x_range_width <= 10000:
        num_points = 5000
    else:
        num_points = 8000  # For very large ranges like -10000 to 10000

    def plot_single_curve(ax, entry, color, label, x_min, x_max, y_min, y_max, auto_scale_y, 
                         stop_y_exit, stop_x_exit, center_x, center_y, x_pos, y_pos, 
                         x_major_int, x_minor_int, y_major_int, y_minor_int, 
                         x_label, y_label, show_grid, grid_major_x, grid_minor_x, 
                         grid_major_y, grid_minor_y, invert_y_axis, use_colorful, title_suffix=""):
        """
        Helper function to plot a single curve with common logic.
        """
        name = entry['name']
        try:
            coeffs = np.array(entry['coefficients'], dtype=float)
        except (ValueError, TypeError) as e:
            skipped_curves.append(f"Curve {name}: Invalid coefficients ({str(e)})")
            return False
        
        # Check polynomial degree limit
        degree = len(coeffs) - 1
        if degree > 10:
            skipped_curves.append(f"Curve {name}: Degree {degree} exceeds maximum allowed (10). Truncated to degree 10.")
            coeffs = coeffs[:11]  # Keep only up to degree 10 (11 coefficients)

        # Generate x values
        p1_full = np.linspace(x_min, x_max, num_points)
        
        # Evaluate polynomial with error handling
        try:
            y_vals = np.polyval(coeffs, p1_full)
        except Exception as e:
            skipped_curves.append(f"Curve {name}: Polynomial evaluation failed ({str(e)})")
            return False

        if np.all(np.isnan(y_vals)) or np.all(np.isinf(y_vals)):
            skipped_curves.append(f"Curve {name}: No valid polynomial output (all NaN/Inf)")
            return False

        # Find valid points (finite values)
        valid = np.isfinite(y_vals)
        
        # Apply x limits (should always be true for linspace, but keep for safety)
        valid = valid & (p1_full >= x_min) & (p1_full <= x_max)
        
        # Apply y limits if not auto-scaling
        if not auto_scale_y:
            valid = valid & (y_vals >= y_min) & (y_vals <= y_max)

        p_plot = p1_full[valid]
        y_plot = y_vals[valid]

        # Handle stop_y_exit - only truncate after first exit, not before
        if stop_y_exit and not auto_scale_y and len(p_plot) > 0:
            # Find first point that exits y-range (but only after entering)
            in_range = (y_vals >= y_min) & (y_vals <= y_max) & np.isfinite(y_vals)
            exit_points = np.where(~in_range & np.roll(in_range, 1))[0]
            if len(exit_points) > 0:
                first_exit_idx = exit_points[0]
                # Only truncate from first exit onward if we had some valid points before
                if np.any(in_range[:first_exit_idx]):
                    valid[first_exit_idx:] = False
                    p_plot = p1_full[valid]
                    y_plot = y_vals[valid]
                    skipped_curves.append(f"Curve {name}: Truncated at x={p1_full[first_exit_idx]:.2f}, y={y_vals[first_exit_idx]:.2f}")

        # Handle stop_x_exit
        if stop_x_exit and len(p_plot) > 0:
            # This should rarely trigger with linspace, but included for completeness
            x_valid = (p1_full >= x_min) & (p1_full <= x_max)
            x_exit_idx = np.where(~x_valid)[0]
            if len(x_exit_idx) > 0:
                first_exit_idx = x_exit_idx[0]
                valid[first_exit_idx:] = False
                p_plot = p1_full[valid]
                y_plot = y_vals[valid]
                skipped_curves.append(f"Curve {name}: X-truncated at x={p1_full[first_exit_idx]:.2f}")

        if len(p_plot) < 2:
            skipped_curves.append(f"Curve {name}: Insufficient valid points ({len(p_plot)})")
            return False

        # Plot the curve
        try:
            ax.plot(p_plot, y_plot, color=color, linewidth=2.5, label=label if use_colorful else None)
        except Exception as e:
            skipped_curves.append(f"Curve {name}: Plotting failed ({str(e)})")
            return False

        # Add label for non-colorful mode
        if not use_colorful and len(p_plot) > 0:
            y_range = y_max - y_min if not auto_scale_y else (max(y_plot) - min(y_plot))
            x_range = x_max - x_min
            end_x, end_y = p_plot[-1], y_plot[-1] - 0.05 * y_range if y_range > 0 else y_plot[-1]
            
            # Avoid label overlap by adjusting position
            text = ax.text(end_x, end_y, label, fontsize=8, ha='left', va='center',
                          bbox=dict(boxstyle="round,pad=0.3", facecolor=bg_color, alpha=0.8))
            return True

        return True

    if plot_grouping == "All in One":
        # Single plot - collect all data first for auto-scaling
        fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
        fig.patch.set_facecolor(bg_color)
        ax.set_facecolor(bg_color)
        
        label_positions = []
        texts = []
        all_y_vals = []
        plot_data = []
        successful_plots = 0

        # First pass: collect data and compute auto-scale if needed
        for i, entry in enumerate(data_ref):
            if 'name' not in entry or 'coefficients' not in entry:
                skipped_curves.append(f"Entry {i}: Missing 'name' or 'coefficients' key")
                continue
                
            name = entry['name']
            color = custom_color_map.get(name, colors[i % len(colors)]) if use_colorful else 'black'
            label = custom_label_map.get(name, name)
            
            # Temporary plot to get y values for auto-scaling
            temp_fig, temp_ax = plt.subplots(figsize=(1,1))
            success = plot_single_curve(temp_ax, entry, color, label, x_min, x_max, 
                                       y_min, y_max, True, stop_y_exit, stop_x_exit, 
                                       center_x, center_y, x_pos, y_pos, 
                                       x_major_int, x_minor_int, y_major_int, y_minor_int,
                                       x_label, y_label, show_grid, grid_major_x, grid_minor_x,
                                       grid_major_y, grid_minor_y, invert_y_axis, use_colorful)
            plt.close(temp_fig)
            
            if success and hasattr(temp_ax, 'lines') and temp_ax.lines:
                # Extract y data from the temporary plot
                temp_y = temp_ax.lines[0].get_ydata()
                if len(temp_y) > 0:
                    all_y_vals.extend(temp_y)
                    plot_data.append((name, entry, color, label, i))
                    successful_plots += 1

        # Apply auto-scaling if needed
        if auto_scale_y and all_y_vals and successful_plots > 0:
            y_min_new = min(all_y_vals)
            y_max_new = max(all_y_vals)
            y_range = y_max_new - y_min_new
            if y_range > 0:
                y_min = y_min_new - 0.1 * y_range
                y_max = y_max_new + 0.1 * y_range
            else:
                # Handle constant functions
                y_min = y_min_new - 1
                y_max = y_max_new + 1
            center_y = y_min < 0 < y_max

        # Second pass: actual plotting
        for name, entry, color, label, i in plot_data:
            success = plot_single_curve(ax, entry, color, label, x_min, x_max, 
                                       y_min, y_max, auto_scale_y, stop_y_exit, stop_x_exit, 
                                       center_x, center_y, x_pos, y_pos, 
                                       x_major_int, x_minor_int, y_major_int, y_minor_int,
                                       x_label, y_label, show_grid, grid_major_x, grid_minor_x,
                                       grid_major_y, grid_minor_y, invert_y_axis, use_colorful)
            
            if success and not use_colorful:
                # Adjust text positions to avoid overlap
                if hasattr(ax, 'texts') and len(ax.texts) > 1:
                    adjust_text(ax.texts, ax=ax, only_move={'points': 'y', 'text': 'xy'})

        # Axis setup
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        ax.set_xlim(x_min, x_max)
        ax.set_ylim(y_min, y_max)
        if invert_y_axis:
            ax.invert_yaxis()

        # Center spines at (0,0) if ranges include negative and positive values
        if center_x and center_y:
            ax.spines['left'].set_position('zero')
            ax.spines['bottom'].set_position('zero')
            ax.spines['right'].set_color('none')
            ax.spines['top'].set_color('none')
            ax.xaxis.set_ticks_position('bottom' if x_pos.lower() == 'bottom' else 'top')
            ax.yaxis.set_ticks_position('left' if y_pos.lower() == 'left' else 'right')
            ax.xaxis.set_label_position(x_pos.lower())
            ax.yaxis.set_label_position(y_pos.lower())
        else:
            ax.xaxis.set_label_position(x_pos.lower())
            ax.xaxis.set_ticks_position(x_pos.lower())
            ax.yaxis.set_label_position(y_pos.lower())
            ax.yaxis.set_ticks_position(y_pos.lower())

        # Grid setup
        if show_grid:
            grid_color = '#D3D3D3' if use_colorful else 'black'
            ax.grid(True, which='major', color=grid_color, alpha=0.5 if use_colorful else 0.3)
            if grid_minor_x > 0 and grid_minor_y > 0:
                ax.grid(True, which='minor', color=grid_color, linestyle='--', alpha=0.5 if use_colorful else 0.2)
            ax.xaxis.set_major_locator(plt.MultipleLocator(grid_major_x))
            if grid_minor_x > 0:
                ax.xaxis.set_minor_locator(plt.MultipleLocator(grid_minor_x))
            ax.yaxis.set_major_locator(plt.MultipleLocator(grid_major_y))
            if grid_minor_y > 0:
                ax.yaxis.set_minor_locator(plt.MultipleLocator(grid_minor_y))

        # Ticks setup
        if x_major_int > 0:
            ax.xaxis.set_major_locator(plt.MultipleLocator(x_major_int))
        if x_minor_int > 0:
            ax.xaxis.set_minor_locator(plt.MultipleLocator(x_minor_int))
        if y_major_int > 0:
            ax.yaxis.set_major_locator(plt.MultipleLocator(y_major_int))
        if y_minor_int > 0:
            ax.yaxis.set_minor_locator(plt.MultipleLocator(y_minor_int))

        # Legend
        bbox = (1.05, 0.5) if 'right' in matplotlib_loc else (-0.05, 0.5) if 'left' in matplotlib_loc else \
               (0.5, 1.05) if 'upper' in matplotlib_loc else (0.5, -0.05) if 'lower' in matplotlib_loc else None
        
        if use_colorful and ax.get_legend_handles_labels()[0]:
            ax.legend(loc=matplotlib_loc, bbox_to_anchor=bbox, fontsize=8, frameon=True, edgecolor='black')
        elif not use_colorful and ax.texts:
            ax.legend(['Custom Labels'], loc=matplotlib_loc, bbox_to_anchor=bbox, fontsize=8, frameon=True, edgecolor='black')

        ax.set_title(f"{title} ({successful_plots} curves)")
        figs.append((fig, "All Curves"))
        
    else:
        # One plot per curve
        for i, entry in enumerate(data_ref):
            if 'name' not in entry or 'coefficients' not in entry:
                skipped_curves.append(f"Entry {i}: Missing 'name' or 'coefficients' key")
                continue
                
            name = entry['name']
            color = custom_color_map.get(name, colors[0]) if use_colorful else 'black'
            label = custom_label_map.get(name, name)
            
            fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
            fig.patch.set_facecolor(bg_color)
            ax.set_facecolor(bg_color)
            
            # Determine y limits for this curve if auto-scaling
            curve_y_min, curve_y_max = y_min, y_max
            if auto_scale_y:
                temp_fig, temp_ax = plt.subplots(figsize=(1,1))
                plot_single_curve(temp_ax, entry, color, label, x_min, x_max, 
                                 y_min, y_max, True, stop_y_exit, stop_x_exit, 
                                 center_x, center_y, x_pos, y_pos, 
                                 x_major_int, x_minor_int, y_major_int, y_minor_int,
                                 x_label, y_label, show_grid, grid_major_x, grid_minor_x,
                                 grid_major_y, grid_minor_y, invert_y_axis, use_colorful)
                if hasattr(temp_ax, 'lines') and temp_ax.lines:
                    temp_y = temp_ax.lines[0].get_ydata()
                    if len(temp_y) > 0:
                        curve_y_min = min(temp_y) - 0.1 * (max(temp_y) - min(temp_y))
                        curve_y_max = max(temp_y) + 0.1 * (max(temp_y) - min(temp_y))
                plt.close(temp_fig)
            
            success = plot_single_curve(ax, entry, color, label, x_min, x_max, 
                                       curve_y_min, curve_y_max, auto_scale_y, stop_y_exit, stop_x_exit, 
                                       center_x, center_y, x_pos, y_pos, 
                                       x_major_int, x_minor_int, y_major_int, y_minor_int,
                                       x_label, y_label, show_grid, grid_major_x, grid_minor_x,
                                       grid_major_y, grid_minor_y, invert_y_axis, use_colorful)
            
            if not success:
                plt.close(fig)
                continue

            # Axis setup
            ax.set_xlabel(x_label)
            ax.set_ylabel(y_label)
            ax.set_xlim(x_min, x_max)
            ax.set_ylim(curve_y_min, curve_y_max)
            if invert_y_axis:
                ax.invert_yaxis()

            # Center spines
            if center_x and (curve_y_min < 0 < curve_y_max):
                ax.spines['left'].set_position('zero')
                ax.spines['bottom'].set_position('zero')
                ax.spines['right'].set_color('none')
                ax.spines['top'].set_color('none')
                ax.xaxis.set_ticks_position('bottom' if x_pos.lower() == 'bottom' else 'top')
                ax.yaxis.set_ticks_position('left' if y_pos.lower() == 'left' else 'right')
                ax.xaxis.set_label_position(x_pos.lower())
                ax.yaxis.set_label_position(y_pos.lower())
            else:
                ax.xaxis.set_label_position(x_pos.lower())
                ax.xaxis.set_ticks_position(x_pos.lower())
                ax.yaxis.set_label_position(y_pos.lower())
                ax.yaxis.set_ticks_position(y_pos.lower())

            # Grid
            if show_grid:
                grid_color = '#D3D3D3' if use_colorful else 'black'
                ax.grid(True, which='major', color=grid_color, alpha=0.5 if use_colorful else 0.3)
                if grid_minor_x > 0 and grid_minor_y > 0:
                    ax.grid(True, which='minor', color=grid_color, linestyle='--', alpha=0.5 if use_colorful else 0.2)
                ax.xaxis.set_major_locator(plt.MultipleLocator(grid_major_x))
                if grid_minor_x > 0:
                    ax.xaxis.set_minor_locator(plt.MultipleLocator(grid_minor_x))
                ax.yaxis.set_major_locator(plt.MultipleLocator(grid_major_y))
                if grid_minor_y > 0:
                    ax.yaxis.set_minor_locator(plt.MultipleLocator(grid_minor_y))

            # Ticks
            if x_major_int > 0:
                ax.xaxis.set_major_locator(plt.MultipleLocator(x_major_int))
            if x_minor_int > 0:
                ax.xaxis.set_minor_locator(plt.MultipleLocator(x_minor_int))
            if y_major_int > 0:
                ax.yaxis.set_major_locator(plt.MultipleLocator(y_major_int))
            if y_minor_int > 0:
                ax.yaxis.set_minor_locator(plt.MultipleLocator(y_minor_int))

            # Legend
            bbox = (1.05, 0.5) if 'right' in matplotlib_loc else (-0.05, 0.5) if 'left' in matplotlib_loc else \
                   (0.5, 1.05) if 'upper' in matplotlib_loc else (0.5, -0.05) if 'lower' in matplotlib_loc else None
            
            if use_colorful and ax.get_legend_handles_labels()[0]:
                ax.legend(loc=matplotlib_loc, bbox_to_anchor=bbox, fontsize=8, frameon=True, edgecolor='black')
            elif len(ax.texts) > 0:
                ax.legend(['Custom Label'], loc=matplotlib_loc, bbox_to_anchor=bbox, fontsize=8, frameon=True, edgecolor='black')

            ax.set_title(f"{title} - {name}")
            figs.append((fig, name))

    if debug:
        print(f"Debug: Processed {len(figs)} plots, skipped {len(skipped_curves)} curves:")
        for skip in skipped_curves:
            print(f"  - {skip}")

    return figs, skipped_curves
