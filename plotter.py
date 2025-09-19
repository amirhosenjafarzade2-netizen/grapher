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
        "Best": "best"
    }
    matplotlib_loc = loc_map.get(legend_loc, "best")

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

    # Determine number of points based on range size for better resolution
    x_range_width = x_max - x_min
    if x_range_width <= 100:
        num_points = 2000
    elif x_range_width <= 1000:
        num_points = 3000
    elif x_range_width <= 10000:
        num_points = 5000
    else:
        num_points = 8000

    def evaluate_curve_for_scaling(entry, x_min, x_max, disable_stop_logic=True):
        """Evaluate curve to get y-range for auto-scaling without plotting."""
        try:
            coeffs = np.array(entry['coefficients'], dtype=float)
        except (ValueError, TypeError):
            return None, None
        
        # Check polynomial degree limit
        degree = len(coeffs) - 1
        if degree > 10:
            coeffs = coeffs[:11]
        
        # Generate x values and evaluate
        x_vals = np.linspace(x_min, x_max, num_points)
        try:
            y_vals = np.polyval(coeffs, x_vals)
        except:
            return None, None
        
        # Filter finite values
        finite_mask = np.isfinite(y_vals)
        if np.sum(finite_mask) < 2:
            return None, None
        
        y_finite = y_vals[finite_mask]
        
        # Apply stop logic only if explicitly requested for scaling
        if not disable_stop_logic and stop_y_exit and y_min is not None and y_max is not None:
            y_in_bounds = (y_finite >= y_min) & (y_finite <= y_max)
            y_enter = y_in_bounds & ~np.roll(y_in_bounds, 1)
            y_enter[0] = y_in_bounds[0]
            
            if np.any(y_enter):
                first_enter_idx = np.where(y_enter)[0][0]
                y_finite = y_finite[first_enter_idx:]
        
        return y_finite, None

    def plot_single_curve(ax, entry, color, label, x_min, x_max, y_min, y_max, auto_scale_y, 
                         stop_y_exit, stop_x_exit, center_x, center_y, x_pos, y_pos, 
                         x_major_int, x_minor_int, y_major_int, y_minor_int, 
                         x_label, y_label, show_grid, grid_major_x, grid_minor_x, 
                         grid_major_y, grid_minor_y, invert_y_axis, use_colorful, title_suffix="",
                         current_y_min=None, current_y_max=None):
        """
        Helper function to plot a single curve with common logic.
        """
        name = entry['name']
        try:
            coeffs = np.array(entry['coefficients'], dtype=float)
        except (ValueError, TypeError) as e:
            skipped_curves.append(f"Curve {name}: Invalid coefficients ({str(e)})")
            return False, None, None
        
        # Check polynomial degree limit
        degree = len(coeffs) - 1
        if degree > 10:
            skipped_curves.append(f"Curve {name}: Degree {degree} exceeds maximum allowed (10). Truncated to degree 10.")
            coeffs = coeffs[:11]

        # Generate x values
        p1_full = np.linspace(x_min, x_max, num_points)
        
        # Evaluate polynomial with error handling
        try:
            y_vals = np.polyval(coeffs, p1_full)
        except Exception as e:
            skipped_curves.append(f"Curve {name}: Polynomial evaluation failed ({str(e)})")
            return False, None, None

        if np.all(np.isnan(y_vals)) or np.all(np.isinf(y_vals)):
            skipped_curves.append(f"Curve {name}: No valid polynomial output (all NaN/Inf)")
            return False, None, None

        # INITIAL VALIDITY CHECK: Finite values only
        finite_mask = np.isfinite(y_vals)
        p1_finite = p1_full[finite_mask]
        y_finite = y_vals[finite_mask]

        if len(p1_finite) < 2:
            skipped_curves.append(f"Curve {name}: Insufficient finite points ({len(p1_finite)})")
            return False, None, None

        # APPLY X BOUNDS STOP LOGIC (if enabled)
        if stop_x_exit:
            x_in_bounds = (p1_finite >= x_min) & (p1_finite <= x_max)
            x_enter = x_in_bounds & ~np.roll(x_in_bounds, 1)
            x_enter[0] = x_in_bounds[0]
            
            if np.any(x_enter):
                first_enter_idx = np.where(x_enter)[0][0]
                x_stop_mask = np.zeros_like(x_in_bounds, dtype=bool)
                x_stop_mask[first_enter_idx:] = True
                p1_bounded = p1_finite[x_stop_mask]
                y_bounded = y_finite[x_stop_mask]
                
                if debug:
                    skipped_curves.append(f"Curve {name}: X-stop applied from x={p1_bounded[0]:.2f}")
            else:
                skipped_curves.append(f"Curve {name}: Never entered x bounds")
                return False, None, None
        else:
            p1_bounded = p1_finite
            y_bounded = y_finite

        # APPLY Y BOUNDS STOP LOGIC (if enabled and not auto-scaling)
        effective_y_min = current_y_min if current_y_min is not None else y_min
        effective_y_max = current_y_max if current_y_max is not None else y_max
        
        if stop_y_exit and not auto_scale_y and effective_y_min is not None and effective_y_max is not None:
            y_in_bounds = (y_bounded >= effective_y_min) & (y_bounded <= effective_y_max)
            y_enter = y_in_bounds & ~np.roll(y_in_bounds, 1)
            y_enter[0] = y_in_bounds[0]
            
            if np.any(y_enter):
                first_enter_idx = np.where(y_enter)[0][0]
                y_stop_mask = np.zeros_like(y_in_bounds, dtype=bool)
                y_stop_mask[first_enter_idx:] = True
                p1_final = p1_bounded[y_stop_mask]
                y_final = y_bounded[y_stop_mask]
                
                if debug:
                    first_exit_x = p1_final[0] if len(p1_final) > 0 else x_min
                    first_exit_y = y_final[0] if len(y_final) > 0 else effective_y_min
                    skipped_curves.append(f"Curve {name}: Y-stop applied from x={first_exit_x:.2f}, y={first_exit_y:.2f}")
            else:
                skipped_curves.append(f"Curve {name}: Never entered y bounds [{effective_y_min}, {effective_y_max}]")
                return False, None, None
        else:
            p1_final = p1_bounded
            y_final = y_bounded

        # FINAL VALIDATION: Ensure we have enough points to plot
        if len(p1_final) < 2:
            skipped_curves.append(f"Curve {name}: Insufficient points after boundary filtering ({len(p1_final)})")
            return False, None, None

        # Apply additional y bounds for non-auto-scaling (safety check)
        if not auto_scale_y and effective_y_min is not None and effective_y_max is not None:
            y_mask = (y_final >= effective_y_min) & (y_final <= effective_y_max)
            p1_final = p1_final[y_mask]
            y_final = y_final[y_mask]

        if len(p1_final) < 2:
            skipped_curves.append(f"Curve {name}: No points remain after y clipping")
            return False, None, None

        # Store for potential label positioning
        plot_data = (p1_final, y_final)
        
        # PLOT THE CURVE
        try:
            line, = ax.plot(p1_final, y_final, color=color, linewidth=2.5, label=label if use_colorful else None)
        except Exception as e:
            skipped_curves.append(f"Curve {name}: Plotting failed ({str(e)})")
            return False, None, None

        # Add label for non-colorful mode
        if not use_colorful and len(p1_final) > 0:
            y_range = (effective_y_max - effective_y_min) if effective_y_min is not None and effective_y_max is not None else (max(y_final) - min(y_final))
            end_x, end_y = p1_final[-1], y_final[-1]
            if y_range > 0:
                end_y = max(effective_y_min, min(effective_y_max, end_y - 0.05 * y_range))
            
            text = ax.text(end_x, end_y, label, fontsize=8, ha='left', va='center',
                          bbox=dict(boxstyle="round,pad=0.3", facecolor=bg_color, alpha=0.8))
        
        return True, line, plot_data

    def setup_axes(ax, x_min, x_max, y_min, y_max, center_x, center_y, x_pos, y_pos, 
                   x_major_int, x_minor_int, y_major_int, y_minor_int, x_label, y_label, 
                   show_grid, grid_major_x, grid_minor_x, grid_major_y, grid_minor_y, 
                   invert_y_axis, title, use_colorful, matplotlib_loc, bg_color, successful_plots=0):
        """Centralized axis and grid setup."""
        # Basic axis setup
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        ax.set_xlim(x_min, x_max)
        if y_min is not None and y_max is not None:
            ax.set_ylim(y_min, y_max)
        if invert_y_axis:
            ax.invert_yaxis()

        # Spine positioning
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

        # Grid setup (consolidated - only once!)
        if show_grid:
            grid_color = '#D3D3D3' if use_colorful else 'black'
            ax.grid(True, which='major', color=grid_color, alpha=0.5 if use_colorful else 0.3)
            if grid_minor_x > 0 and grid_minor_y > 0:
                ax.grid(True, which='minor', color=grid_color, linestyle='--', alpha=0.3 if use_colorful else 0.2)
        
        # Consolidated tick setup (overrides grid locators if specified)
        if x_major_int > 0:
            ax.xaxis.set_major_locator(plt.MultipleLocator(x_major_int))
        elif grid_major_x > 0:
            ax.xaxis.set_major_locator(plt.MultipleLocator(grid_major_x))
        
        if x_minor_int > 0:
            ax.xaxis.set_minor_locator(plt.MultipleLocator(x_minor_int))
        elif grid_minor_x > 0:
            ax.xaxis.set_minor_locator(plt.MultipleLocator(grid_minor_x))
        
        if y_major_int > 0:
            ax.yaxis.set_major_locator(plt.MultipleLocator(y_major_int))
        elif grid_major_y > 0:
            ax.yaxis.set_major_locator(plt.MultipleLocator(grid_major_y))
        
        if y_minor_int > 0:
            ax.yaxis.set_minor_locator(plt.MultipleLocator(y_minor_int))
        elif grid_minor_y > 0:
            ax.yaxis.set_minor_locator(plt.MultipleLocator(grid_minor_y))

        # Legend setup
        bbox = (1.05, 0.5) if 'right' in matplotlib_loc else (-0.05, 0.5) if 'left' in matplotlib_loc else \
               (0.5, 1.05) if 'upper' in matplotlib_loc else (0.5, -0.05) if 'lower' in matplotlib_loc else None
        
        handles, labels = ax.get_legend_handles_labels()
        if use_colorful and handles:
            ax.legend(handles, labels, loc=matplotlib_loc, bbox_to_anchor=bbox, fontsize=8, frameon=True, edgecolor='black')
        elif not use_colorful and hasattr(ax, 'texts') and ax.texts:
            # Create a dummy handle for text-based legends
            from matplotlib.lines import Line2D
            dummy_handle = Line2D([0], [0], color='black', linewidth=2)
            ax.legend([dummy_handle], ['Curves'], loc=matplotlib_loc, bbox_to_anchor=bbox, fontsize=8, frameon=True, edgecolor='black')

        # Title
        plot_title = f"{title} - {title_suffix}" if title_suffix else title
        if successful_plots > 0:
            plot_title += f" ({successful_plots} curves)"
        ax.set_title(plot_title)

    if plot_grouping == "All in One":
        # Single plot - collect all data first for auto-scaling
        fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
        fig.patch.set_facecolor(bg_color)
        ax.set_facecolor(bg_color)
        
        all_y_vals = []
        plot_data = []
        successful_plots = 0

        # First pass: collect data for auto-scaling (efficient evaluation)
        for i, entry in enumerate(data_ref):
            if 'name' not in entry or 'coefficients' not in entry:
                skipped_curves.append(f"Entry {i}: Missing 'name' or 'coefficients' key")
                continue
                
            name = entry['name']
            y_range, _ = evaluate_curve_for_scaling(entry, x_min, x_max, disable_stop_logic=not stop_y_exit)
            
            if y_range is not None and len(y_range) > 0:
                all_y_vals.extend(y_range)
                color = custom_color_map.get(name, colors[i % len(colors)]) if use_colorful else 'black'
                label = custom_label_map.get(name, name)
                plot_data.append((name, entry, color, label, i))
                successful_plots += 1

        # Apply auto-scaling if needed
        final_y_min, final_y_max = y_min, y_max
        center_y = y_min is not None and y_max is not None and y_min < 0 < y_max
        if auto_scale_y and all_y_vals and successful_plots > 0:
            y_min_new = min(all_y_vals)
            y_max_new = max(all_y_vals)
            y_range = y_max_new - y_min_new
            if y_range > 0:
                final_y_min = y_min_new - 0.1 * y_range
                final_y_max = y_max_new + 0.1 * y_range
            else:
                final_y_min = y_min_new - 1
                final_y_max = y_max_new + 1
            center_y = final_y_min < 0 < final_y_max

        # Second pass: actual plotting - FIXED PARAMETER ORDER
        all_lines = []
        all_texts = []
        for name, entry, color, label, i in plot_data:
            success, line, plot_data_info = plot_single_curve(
                ax, entry, color, label, x_min, x_max, final_y_min, final_y_max, 
                auto_scale_y, stop_y_exit, stop_x_exit, center_x, center_y, x_pos, y_pos, 
                x_major_int, x_minor_int, y_major_int, y_minor_int, x_label, y_label, 
                show_grid, grid_major_x, grid_minor_x, grid_major_y, grid_minor_y, 
                invert_y_axis, use_colorful, current_y_min=final_y_min, current_y_max=final_y_max
            )
            
            if success:
                if line:
                    all_lines.append(line)
                if not use_colorful and plot_data_info:
                    # Text labels added during plotting
                    if hasattr(ax, 'texts'):
                        all_texts.extend(ax.texts)
        
        # Adjust text positions if needed
        if not use_colorful and len(ax.texts) > 1:
            try:
                adjust_text(ax.texts, ax=ax, only_move={'points': 'y', 'text': 'xy'})
            except:
                pass  # Gracefully handle adjustText failures

        # Setup axes once
        setup_axes(ax, x_min, x_max, final_y_min, final_y_max, center_x, center_y, x_pos, y_pos, 
                  x_major_int, x_minor_int, y_major_int, y_minor_int, x_label, y_label, 
                  show_grid, grid_major_x, grid_minor_x, grid_major_y, grid_minor_y, 
                  invert_y_axis, title, use_colorful, matplotlib_loc, bg_color, successful_plots)
        
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
            center_y = center_x  # Default to x-centering logic
            if auto_scale_y:
                y_range, _ = evaluate_curve_for_scaling(entry, x_min, x_max, disable_stop_logic=not stop_y_exit)
                if y_range is not None and len(y_range) > 0:
                    y_min_curve = min(y_range)
                    y_max_curve = max(y_range)
                    y_range_val = y_max_curve - y_min_curve
                    if y_range_val > 0:
                        curve_y_min = y_min_curve - 0.1 * y_range_val
                        curve_y_max = y_max_curve + 0.1 * y_range_val
                    else:
                        curve_y_min = y_min_curve - 1
                        curve_y_max = y_max_curve + 1
                    center_y = center_y and curve_y_min < 0 < curve_y_max
            
            # FIXED: Correct parameter order for single curve plotting
            success, line, plot_data_info = plot_single_curve(
                ax, entry, color, label, x_min, x_max, curve_y_min, curve_y_max, 
                auto_scale_y, stop_y_exit, stop_x_exit, center_x, center_y, x_pos, y_pos, 
                x_major_int, x_minor_int, y_major_int, y_minor_int, x_label, y_label, 
                show_grid, grid_major_x, grid_minor_x, grid_major_y, grid_minor_y, 
                invert_y_axis, use_colorful, title_suffix=name, 
                current_y_min=curve_y_min, current_y_max=curve_y_max
            )
            
            if not success:
                plt.close(fig)
                continue

            # Setup axes once per figure
            setup_axes(ax, x_min, x_max, curve_y_min, curve_y_max, center_x, center_y, x_pos, y_pos, 
                      x_major_int, x_minor_int, y_major_int, y_minor_int, x_label, y_label, 
                      show_grid, grid_major_x, grid_minor_x, grid_major_y, grid_minor_y, 
                      invert_y_axis, title, use_colorful, matplotlib_loc, bg_color, successful_plots=1)
            
            figs.append((fig, name))

    if debug:
        print(f"Debug: Processed {len(figs)} plots, skipped {len(skipped_curves)} curves:")
        for skip in skipped_curves:
            print(f"  - {skip}")

    return figs, skipped_curves
