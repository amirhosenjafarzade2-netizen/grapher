import matplotlib.pyplot as plt
import numpy as np
from adjustText import adjust_text

DEFAULT_COLORS = [
    '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
    '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
    '#aec7e8', '#ffbb78', '#98df8a', '#ff9896', '#c5b0d5'
]

def plot_graphs(data_ref, use_colorful, num_colors, bg_color, legend_loc, custom_legends, scale_type, show_grid, grid_major_x, grid_minor_x,
                grid_major_y, grid_minor_y, func_type, x_min, x_max, y_min, y_max, x_pos, y_pos, plot_frame,
                x_major_int, x_minor_int, y_major_int, y_minor_int, allow_reentry_x, allow_reentry_y, title, x_label, y_label, plot_grouping):
    figs = []
    colors = DEFAULT_COLORS[:num_colors] if use_colorful else ['black'] * len(DEFAULT_COLORS)

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
            degree = entry['degree']

            if func_type == 'Polynomial':
                def polynomial(x, coeffs):
                    return np.polyval(coeffs, x)
                p1_full = np.linspace(x_min, x_max * (1.5 if allow_reentry_x else 1.0), 200)
                y_vals = polynomial(p1_full, coeffs)

                segments = []
                current_seg = []
                for p, y in zip(p1_full, y_vals):
                    in_x = x_min <= p <= x_max if not allow_reentry_x else True
                    in_y = y_min <= y <= y_max if not allow_reentry_y else True
                    if np.isfinite(y) and in_x and in_y:
                        current_seg.append((p, y))
                    else:
                        if current_seg:
                            segments.append(current_seg)
                            current_seg = []
                        if not (allow_reentry_x or allow_reentry_y):
                            break
                if current_seg:
                    segments.append(current_seg)

                if not segments:
                    continue

                color = custom_color_map.get(name, colors[i % len(colors)]) if use_colorful else 'black'
                label = custom_label_map.get(name, name)

                for seg in segments:
                    p_plot, y_plot = zip(*seg)
                    ax.plot(p_plot, y_plot, color=color, linewidth=2.5, label=label if use_colorful else None)

                if not use_colorful and segments:
                    end_seg = segments[-1]
                    end_x, end_y = end_seg[-1]
                    end_y -= (y_max - y_min) / 100
                    text = ax.text(end_x, end_y, label, fontsize=8, ha='left', va='center')
                    texts.append(text)
                    label_positions.append((end_x, end_y))

        if not use_colorful:
            adjust_text(texts, ax=ax)

        # Axis setup
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        ax.set_xlim(x_min, x_max)
        ax.set_ylim(y_min, y_max)
        if scale_type == 'Log-Log' and x_min > 0 and y_min > 0:
            ax.set_xscale('log')
            ax.set_yscale('log')
        ax.invert_yaxis()

        # Grid
        if show_grid:
            grid_color = '#D3D3D3' if use_colorful else 'black'
            ax.grid(True, which='major', color=grid_color, alpha=0.5)
            ax.grid(True, which='minor', color=grid_color, linestyle='-', alpha=0.2)
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

        # Frame
        if plot_frame == 'Only Axes':
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)

        # Legend
        bbox = (1.05, 0.5) if 'left' in legend_loc or 'right' in legend_loc else None
        if use_colorful:
            ax.legend(loc=legend_loc, bbox_to_anchor=bbox, fontsize=8)
        else:
            ax.legend(['Custom Labels'], loc=legend_loc, bbox_to_anchor=bbox, fontsize=8)

        ax.set_title(title)
        figs.append((fig, "All Curves"))
    else:
        # One plot per curve
        for entry in data_ref:
            name = entry['name']
            coeffs = entry['coefficients']
            degree = entry['degree']

            fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
            fig.patch.set_facecolor(bg_color)
            ax.set_facecolor(bg_color)

            if func_type == 'Polynomial':
                def polynomial(x, coeffs):
                    return np.polyval(coeffs, x)
                p1_full = np.linspace(x_min, x_max * (1.5 if allow_reentry_x else 1.0), 200)
                y_vals = polynomial(p1_full, coeffs)

                segments = []
                current_seg = []
                for p, y in zip(p1_full, y_vals):
                    in_x = x_min <= p <= x_max if not allow_reentry_x else True
                    in_y = y_min <= y <= y_max if not allow_reentry_y else True
                    if np.isfinite(y) and in_x and in_y:
                        current_seg.append((p, y))
                    else:
                        if current_seg:
                            segments.append(current_seg)
                            current_seg = []
                        if not (allow_reentry_x or allow_reentry_y):
                            break
                if current_seg:
                    segments.append(current_seg)

                if not segments:
                    continue

                color = custom_color_map.get(name, colors[0]) if use_colorful else 'black'
                label = custom_label_map.get(name, name)

                for seg in segments:
                    p_plot, y_plot = zip(*seg)
                    ax.plot(p_plot, y_plot, color=color, linewidth=2.5, label=label if use_colorful else None)

                if not use_colorful and segments:
                    end_seg = segments[-1]
                    end_x, end_y = end_seg[-1]
                    end_y -= (y_max - y_min) / 100
                    text = ax.text(end_x, end_y, label, fontsize=8, ha='left', va='center')
                    adjust_text([text], ax=ax)

            # Axis setup
            ax.set_xlabel(x_label)
            ax.set_ylabel(y_label)
            ax.set_xlim(x_min, x_max)
            ax.set_ylim(y_min, y_max)
            if scale_type == 'Log-Log' and x_min > 0 and y_min > 0:
                ax.set_xscale('log')
                ax.set_yscale('log')
            ax.invert_yaxis()

            # Grid
            if show_grid:
                grid_color = '#D3D3D3' if use_colorful else 'black'
                ax.grid(True, which='major', color=grid_color, alpha=0.5)
                ax.grid(True, which='minor', color=grid_color, linestyle='-', alpha=0.2)
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

            # Frame
            if plot_frame == 'Only Axes':
                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)

            # Legend
            bbox = (1.05, 0.5) if 'left' in legend_loc or 'right' in legend_loc else None
            if use_colorful:
                ax.legend(loc=legend_loc, bbox_to_anchor=bbox, fontsize=8)
            else:
                ax.legend(['Custom Label'], loc=legend_loc, bbox_to_anchor=bbox, fontsize=8)

            ax.set_title(f"{title} - {name}")
            figs.append((fig, name))

    return figs
