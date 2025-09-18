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
    figs = []
    colors = DEFAULT_COLORS[:min(num_colors, len(DEFAULT_COLORS))] if use_colorful else ['black']
    skipped_curves = []

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
    center_y = y_min < 0 < y_max

    if plot_grouping == "All in One":
        # Single plot
        fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
        fig.patch.set_facecolor(bg_color)
        ax.set_facecolor(bg_color)
        label_positions = []
        texts = []

        # Collect data for all curves and compute auto-scale if needed
        all_y_vals = []
        plot_data = []
        for i, entry in enumerate(data_ref):
            name = entry['name']
            coeffs = entry['coefficients']

            # Warn for high-degree polynomials
            if len(coeffs) > 10:
                skipped_curves.append(f"Curve {name}: High-degree polynomial (degree {len(coeffs)-1}) may cause numerical instability")

            p1_full = np.linspace(x_min, x_max, 1000)
            try:
                y_vals = np.polyval(coeffs, p1_full)
            except Exception as e:
                skipped_curves.append(f"Curve {name}: Polynomial evaluation failed ({str(e)})")
                continue

            if np.all(np.isnan(y_vals)):
                skipped_curves.append(f"Curve {name}: No valid polynomial output")
                continue

            # Apply x and y limits
            valid = np.isfinite(y_vals)
            if not auto_scale_y:
                valid = valid & (y_vals >= y_min) & (y_vals <= y_max)
            valid = valid & (p1_full >= x_min) & (p1_full <= x_max)

            p_plot = p1_full[valid]
            y_plot = y_vals[valid]

            # Stop at first exit if specified
            if stop_y_exit and not auto_scale_y and len(p_plot) > 0:
                y_exit_idx = np.where((np.isfinite(y_vals)) & ((y_vals < y_min) | (y_vals > y_max)))[0]
                if len(y_exit_idx) > 0:
                    valid[y_exit_idx[0]:] = False
                    p_plot = p1_full[valid]
                    y_plot = y_vals[valid]
                    skipped_curves.append(f"Curve {name}: Stopped at x={p1_full[y_exit_idx[0]]:.2f}, y={y_vals[y_exit_idx[0]]:.2f} (exceeds y_min={y_min} or y_max={y_max})")

            if stop_x_exit and len(p_plot) > 0:
                x_exit_idx = np.where((p1_full < x_min) | (p1_full > x_max))[0]
                if len(x_exit_idx) > 0:
                    valid[x_exit_idx[0]:] = False
                    p_plot = p1_full[valid]
                    y_plot = y_vals[valid]
                    skipped_curves.append(f"Curve {name}: Stopped at x={p1_full[x_exit_idx[0]]:.2f}, y={y_vals[x_exit_idx[0]]:.2f} (exceeds x_min={x_min} or x_max={x_max})")

            if len(p_plot) < 2:
                skipped_curves.append(f"Curve {name}: Insufficient valid points ({len(p_plot)})")
                continue

            plot_data.append((name, p_plot, y_plot, i))
            if auto_scale_y and len(y_plot) > 0:
                all_y_vals.extend(y_plot)

        if auto_scale_y and all_y_vals:
            y_min = min(all_y_vals) - 0.1 * abs(min(all_y_vals))
            y_max = max(all_y_vals) + 0.1 * abs(max(all_y_vals))
            center_y = y_min < 0 < y_max  # Recompute if changed

        # Now plot the data
        for name, p_plot, y_plot, i in plot_data:
            color = custom_color_map.get(name, colors[i % len(colors)]) if use_colorful else 'black'
            label = custom_label_map.get(name, name)

            ax.plot(p_plot, y_plot, color=color, linewidth=2.5, label=label if use_colorful else None)

            if not use_colorful and p_plot.size > 0:
                end_x, end_y = p_plot[-1], y_plot[-1] - 0.05 * (y_max - y_min)
                overlap = False
                for prev_x, prev_y in label_positions:
                    if abs(end_y - prev_y) < 0.05 * (y_max - y_min) and abs(end_x - prev_x) < 0.05 * (x_max - x_min):
                        overlap = True
                        break
                if overlap:
                    index = max(0, len(p_plot) - 11)
                    end_x, end_y = p_plot[index], y_plot[index] - 0.05 * (y_max - y_min)
                text = ax.text(end_x, end_y, label, fontsize=8, ha='left', va='center')
                texts.append(text)
                label_positions.append((end_x, end_y))

        if not use_colorful and texts:
            adjust_text(texts, ax=ax, only_move={'points': 'y', 'text': 'xy'})

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
            # Adjust tick positions based on x_pos, y_pos
            ax.xaxis.set_ticks_position('bottom' if x_pos.lower() == 'bottom' else 'top')
            ax.yaxis.set_ticks_position('left' if y_pos.lower() == 'left' else 'right')
            ax.xaxis.set_label_position(x_pos.lower())
            ax.yaxis.set_label_position(y_pos.lower())
        else:
            # Default spine positions
            ax.xaxis.set_label_position(x_pos.lower())
            ax.xaxis.set_ticks_position(x_pos.lower())
            ax.yaxis.set_label_position(y_pos.lower())
            ax.yaxis.set_ticks_position(y_pos.lower())

        # Grid
        if show_grid:
            grid_color = '#D3D3D3' if use_colorful else 'black'
            ax.grid(True, which='major', color=grid_color, alpha=0.5 if use_colorful else 0.3)
            ax.grid(True, which='minor', color=grid_color, linestyle='--', alpha=0.5 if use_colorful else 0.2)
            ax.xaxis.set_major_locator(plt.MultipleLocator(grid_major_x))
            ax.xaxis.set_minor_locator(plt.MultipleLocator(grid_minor_x))
            ax.yaxis.set_major_locator(plt.MultipleLocator(grid_major_y))
            ax.yaxis.set_minor_locator(plt.MultipleLocator(grid_minor_y))

        # Ticks
        ax.xaxis.set_major_locator(plt.MultipleLocator(x_major_int))
        ax.xaxis.set_minor_locator(plt.MultipleLocator(x_minor_int))
        ax.yaxis.set_major_locator(plt.MultipleLocator(y_major_int))
        ax.yaxis.set_minor_locator(plt.MultipleLocator(y_minor_int))

        # Legend
        bbox = (1.05, 0.5) if 'right' in matplotlib_loc else ( -0.05, 0.5) if 'left' in matplotlib_loc else (0.5, 1.05) if 'upper' in matplotlib_loc else (0.5, -0.05) if 'lower' in matplotlib_loc else None
        if use_colorful and ax.get_legend_handles_labels()[0]:
            ax.legend(loc=matplotlib_loc, bbox_to_anchor=bbox, fontsize=8, frameon=True, edgecolor='black')
        elif not use_colorful and texts:
            ax.legend(['Custom Labels'], loc=matplotlib_loc, bbox_to_anchor=bbox, fontsize=8, frameon=True, edgecolor='black')

        ax.set_title(title)
        figs.append((fig, "All Curves"))
    else:
        # One plot per curve
        for entry in data_ref:
            name = entry['name']
            coeffs = entry['coefficients']

            # Warn for high-degree polynomials
            if len(coeffs) > 10:
                skipped_curves.append(f"Curve {name}: High-degree polynomial (degree {len(coeffs)-1}) may cause numerical instability")

            fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
            fig.patch.set_facecolor(bg_color)
            ax.set_facecolor(bg_color)

            p1_full = np.linspace(x_min, x_max, 1000)
            try:
                y_vals = np.polyval(coeffs, p1_full)
            except Exception as e:
                skipped_curves.append(f"Curve {name}: Polynomial evaluation failed ({str(e)})")
                continue

            if np.all(np.isnan(y_vals)):
                skipped_curves.append(f"Curve {name}: No valid polynomial output")
                continue

            # Apply x and y limits
            valid = np.isfinite(y_vals)
            if not auto_scale_y:
                valid = valid & (y_vals >= y_min) & (y_vals <= y_max)
            valid = valid & (p1_full >= x_min) & (p1_full <= x_max)

            p_plot = p1_full[valid]
            y_plot = y_vals[valid]

            # Stop at first exit if specified
            if stop_y_exit and not auto_scale_y and len(p_plot) > 0:
                y_exit_idx = np.where((np.isfinite(y_vals)) & ((y_vals < y_min) | (y_vals > y_max)))[0]
                if len(y_exit_idx) > 0:
                    valid[y_exit_idx[0]:] = False
                    p_plot = p1_full[valid]
                    y_plot = y_vals[valid]
                    skipped_curves.append(f"Curve {name}: Stopped at x={p1_full[y_exit_idx[0]]:.2f}, y={y_vals[y_exit_idx[0]]:.2f} (exceeds y_min={y_min} or y_max={y_max})")

            if stop_x_exit and len(p_plot) > 0:
                x_exit_idx = np.where((p1_full < x_min) | (p1_full > x_max))[0]
                if len(x_exit_idx) > 0:
                    valid[x_exit_idx[0]:] = False
                    p_plot = p1_full[valid]
                    y_plot = y_vals[valid]
                    skipped_curves.append(f"Curve {name}: Stopped at x={p1_full[x_exit_idx[0]]:.2f}, y={y_vals[x_exit_idx[0]]:.2f} (exceeds x_min={x_min} or x_max={x_max})")

            if len(p_plot) < 2:
                skipped_curves.append(f"Curve {name}: Insufficient valid points ({len(p_plot)})")
                continue

            if auto_scale_y and len(y_plot) > 0:
                curve_y_min = min(y_plot) - 0.1 * abs(min(y_plot))
                curve_y_max = max(y_plot) + 0.1 * abs(max(y_plot))
                ax.set_ylim(curve_y_min, curve_y_max)
                center_y = curve_y_min < 0 < curve_y_max

            color = custom_color_map.get(name, colors[0]) if use_colorful else 'black'
            label = custom_label_map.get(name, name)

            ax.plot(p_plot, y_plot, color=color, linewidth=2.5, label=label if use_colorful else None)

            if not use_colorful and p_plot.size > 0:
                end_x, end_y = p_plot[-1], y_plot[-1] - 0.05 * (y_max - y_min)
                text = ax.text(end_x, end_y, label, fontsize=8, ha='left', va='center')
                adjust_text([text], ax=ax, only_move={'points': 'y', 'text': 'xy'})

            # Axis setup
            ax.set_xlabel(x_label)
            ax.set_ylabel(y_label)
            ax.set_xlim(x_min, x_max)
            if not auto_scale_y:
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

            # Grid
            if show_grid:
                grid_color = '#D3D3D3' if use_colorful else 'black'
                ax.grid(True, which='major', color=grid_color, alpha=0.5 if use_colorful else 0.3)
                ax.grid(True, which='minor', color=grid_color, linestyle='--', alpha=0.5 if use_colorful else 0.2)
                ax.xaxis.set_major_locator(plt.MultipleLocator(grid_major_x))
                ax.xaxis.set_minor_locator(plt.MultipleLocator(grid_minor_x))
                ax.yaxis.set_major_locator(plt.MultipleLocator(grid_major_y))
                ax.yaxis.set_minor_locator(plt.MultipleLocator(grid_minor_y))

            # Ticks
            ax.xaxis.set_major_locator(plt.MultipleLocator(x_major_int))
            ax.xaxis.set_minor_locator(plt.MultipleLocator(x_minor_int))
            ax.yaxis.set_major_locator(plt.MultipleLocator(y_major_int))
            ax.yaxis.set_minor_locator(plt.MultipleLocator(y_minor_int))

            # Legend
            bbox = (1.05, 0.5) if 'right' in matplotlib_loc else ( -0.05, 0.5) if 'left' in matplotlib_loc else (0.5, 1.05) if 'upper' in matplotlib_loc else (0.5, -0.05) if 'lower' in matplotlib_loc else None
            if use_colorful:
                ax.legend(loc=matplotlib_loc, bbox_to_anchor=bbox, fontsize=8, frameon=True, edgecolor='black')
            elif p_plot.size > 0:
                ax.legend(['Custom Label'], loc=matplotlib_loc, bbox_to_anchor=bbox, fontsize=8, frameon=True, edgecolor='black')

            ax.set_title(f"{title} - {name}")
            figs.append((fig, name))

    return figs, skipped_curves
