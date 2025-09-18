import matplotlib.pyplot as plt
import numpy as np
from adjustText import adjust_text

DEFAULT_COLORS = [
    '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
    '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
    '#aec7e8', '#ffbb78', '#98df8a', '#ff9896', '#c5b0d5'
]

def plot_graphs(data_ref, use_colorful, num_colors, bg_color, legend_loc, custom_legends, show_grid, 
                grid_major_x, grid_minor_x, grid_major_y, grid_minor_y, x_min, x_max, y_min, y_max, 
                x_pos, y_pos, x_major_int, x_minor_int, y_major_int, y_minor_int, 
                title, x_label, y_label, plot_grouping, auto_scale_y, debug=False):
    figs = []
    colors = DEFAULT_COLORS[:num_colors] if use_colorful else ['black'] * len(DEFAULT_COLORS)
    skipped_curves = []

    # Map user-friendly legend_loc to Matplotlib loc
    loc_map = {
        "Upper Right": "upper right",
        "Upper Left": "upper left",
        "Lower Right": "lower right",
        "Lower Left": "lower left",
        "Center Left": "center left"
    }
    matplotlib_loc = loc_map[legend_loc]

    # Parse custom legends
    custom_label_map = {}
    custom_color_map = {}
    if custom_legends:
        for line in custom_legends.split('\n'):
            if ':' in line:
                name, color = line.split(':', 1)
                custom_label_map[name.strip()] = name.strip()
                custom_color_map[name.strip()] = color.strip() if use_colorful else 'black'
            else:
                custom_label_map[line.strip()] = line.strip()

    if plot_grouping == "All in One":
        # Single plot
        fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
        fig.patch.set_facecolor(bg_color)
        ax.set_facecolor(bg_color)
        label_positions = []
        texts = []

        for i, entry in enumerate(data_ref):
            name = entry['name']
            coeffs = entry['coefficients']

            def polynomial(x, coeffs):
                try:
                    return (coeffs['a'] * x**5 + coeffs['b'] * x**4 + coeffs['c'] * x**3 +
                            coeffs['d'] * x**2 + coeffs['e'] * x + coeffs['f'])
                except Exception as e:
                    skipped_curves.append(f"Curve {name}: Polynomial evaluation failed ({str(e)})")
                    return np.nan

            p1_full = np.linspace(x_min, x_max, 100)
            y_vals = np.array([polynomial(p, coeffs) for p in p1_full])
            if np.all(np.isnan(y_vals)):
                skipped_curves.append(f"Curve {name}: No valid polynomial output")
                continue

            if not auto_scale_y:
                valid = (np.isfinite(y_vals)) & (y_vals >= y_min) & (y_vals <= y_max)
                p_plot = p1_full[valid]
                y_plot = y_vals[valid]
                if len(p_plot) > 0 and np.any(y_vals[~valid] > y_max):
                    # Find first index where y > y_max
                    exceed_idx = np.where((np.isfinite(y_vals)) & (y_vals > y_max))[0]
                    if len(exceed_idx) > 0:
                        valid[:exceed_idx[0]] = True
                        p_plot = p1_full[valid]
                        y_plot = y_vals[valid]
            else:
                valid = np.isfinite(y_vals)
                p_plot = p1_full[valid]
                y_plot = y_vals[valid]

            if len(p_plot) < 2:
                skipped_curves.append(f"Curve {name}: Insufficient valid points ({len(p_plot)})")
                continue

            color = custom_color_map.get(name, colors[i % len(colors)]) if use_colorful else 'black'
            label = custom_label_map.get(name, name)

            ax.plot(p_plot, y_plot, color=color, linewidth=2.5, label=label if use_colorful else None)

            if not use_colorful and p_plot.size > 0:
                end_x, end_y = p_plot[-1], y_plot[-1] - 300
                overlap = False
                for prev_x, prev_y in label_positions:
                    if abs(end_y - prev_y) < 300 and abs(end_x - prev_x) < 100:
                        overlap = True
                        break
                if overlap:
                    index = max(0, len(p_plot) - 11)
                    end_x, end_y = p_plot[index], y_plot[index] - 300
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
        ax.invert_yaxis()

        # Grid
        if show_grid:
            grid_color = '#D3D3D3' if use_colorful else 'black'
            ax.grid(True, which='major', color=grid_color, alpha=0.5 if use_colorful else 0.3)
            ax.grid(True, which='minor', color=grid_color, linestyle='-', alpha=0.5 if use_colorful else 0.2)
            ax.xaxis.set_major_locator(plt.MultipleLocator(grid_major_x))
            ax.xaxis.set_minor_locator(plt.MultipleLocator(grid_minor_x))
            ax.yaxis.set_major_locator(plt.MultipleLocator(grid_major_y))
            ax.yaxis.set_minor_locator(plt.MultipleLocator(grid_minor_y))

        # Ticks
        ax.xaxis.set_major_locator(plt.MultipleLocator(x_major_int))
        ax.xaxis.set_minor_locator(plt.MultipleLocator(x_minor_int))
        ax.yaxis.set_major_locator(plt.MultipleLocator(y_major_int))
        ax.yaxis.set_minor_locator(plt.MultipleLocator(y_minor_int))

        # Positions
        ax.xaxis.set_label_position(x_pos.lower())
        ax.xaxis.set_ticks_position(x_pos.lower())
        ax.yaxis.set_label_position(y_pos.lower())
        ax.yaxis.set_ticks_position(y_pos.lower())

        # Legend
        bbox = (1.05, 0.5) if 'left' in matplotlib_loc or 'right' in matplotlib_loc else None
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

            fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
            fig.patch.set_facecolor(bg_color)
            ax.set_facecolor(bg_color)

            def polynomial(x, coeffs):
                try:
                    return (coeffs['a'] * x**5 + coeffs['b'] * x**4 + coeffs['c'] * x**3 +
                            coeffs['d'] * x**2 + coeffs['e'] * x + coeffs['f'])
                except Exception as e:
                    skipped_curves.append(f"Curve {name}: Polynomial evaluation failed ({str(e)})")
                    return np.nan

            p1_full = np.linspace(x_min, x_max, 100)
            y_vals = np.array([polynomial(p, coeffs) for p in p1_full])
            if np.all(np.isnan(y_vals)):
                skipped_curves.append(f"Curve {name}: No valid polynomial output")
                continue

            if not auto_scale_y:
                valid = (np.isfinite(y_vals)) & (y_vals >= y_min) & (y_vals <= y_max)
                p_plot = p1_full[valid]
                y_plot = y_vals[valid]
                if len(p_plot) > 0 and np.any(y_vals[~valid] > y_max):
                    exceed_idx = np.where((np.isfinite(y_vals)) & (y_vals > y_max))[0]
                    if len(exceed_idx) > 0:
                        valid[:exceed_idx[0]] = True
                        p_plot = p1_full[valid]
                        y_plot = y_vals[valid]
            else:
                valid = np.isfinite(y_vals)
                p_plot = p1_full[valid]
                y_plot = y_vals[valid]

            if len(p_plot) < 2:
                skipped_curves.append(f"Curve {name}: Insufficient valid points ({len(p_plot)})")
                continue

            color = custom_color_map.get(name, colors[0]) if use_colorful else 'black'
            label = custom_label_map.get(name, name)

            ax.plot(p_plot, y_plot, color=color, linewidth=2.5, label=label if use_colorful else None)

            if not use_colorful and p_plot.size > 0:
                end_x, end_y = p_plot[-1], y_plot[-1] - 300
                text = ax.text(end_x, end_y, label, fontsize=8, ha='left', va='center')
                adjust_text([text], ax=ax, only_move={'points': 'y', 'text': 'xy'})

            # Axis setup
            ax.set_xlabel(x_label)
            ax.set_ylabel(y_label)
            ax.set_xlim(x_min, x_max)
            ax.set_ylim(y_min, y_max)
            ax.invert_yaxis()

            # Grid
            if show_grid:
                grid_color = '#D3D3D3' if use_colorful else 'black'
                ax.grid(True, which='major', color=grid_color, alpha=0.5 if use_colorful else 0.3)
                ax.grid(True, which='minor', color=grid_color, linestyle='-', alpha=0.5 if use_colorful else 0.2)
                ax.xaxis.set_major_locator(plt.MultipleLocator(grid_major_x))
                ax.xaxis.set_minor_locator(plt.MultipleLocator(grid_minor_x))
                ax.yaxis.set_major_locator(plt.MultipleLocator(grid_major_y))
                ax.yaxis.set_minor_locator(plt.MultipleLocator(grid_minor_y))

            # Ticks
            ax.xaxis.set_major_locator(plt.MultipleLocator(x_major_int))
            ax.xaxis.set_minor_locator(plt.MultipleLocator(x_minor_int))
            ax.yaxis.set_major_locator(plt.MultipleLocator(y_major_int))
            ax.yaxis.set_minor_locator(plt.MultipleLocator(y_minor_int))

            # Positions
            ax.xaxis.set_label_position(x_pos.lower())
            ax.xaxis.set_ticks_position(x_pos.lower())
            ax.yaxis.set_label_position(y_pos.lower())
            ax.yaxis.set_ticks_position(y_pos.lower())

            # Legend
            bbox = (1.05, 0.5) if 'left' in matplotlib_loc or 'right' in matplotlib_loc else None
            if use_colorful:
                ax.legend(loc=matplotlib_loc, bbox_to_anchor=bbox, fontsize=8, frameon=True, edgecolor='black')
            elif p_plot.size > 0:
                ax.legend(['Custom Label'], loc=matplotlib_loc, bbox_to_anchor=bbox, fontsize=8, frameon=True, edgecolor='black')

            ax.set_title(f"{title} - {name}")
            figs.append((fig, name))

    if debug:
        return figs, skipped_curves
    return figs
