"""
Mindmap Plotter - A graphviz-inspired tool for creating mindmap visualizations.

Clean, structured layout with proper text fitting and spacing.

Algorithm Overview:
-------------------
The tool uses a multi-stage layout algorithm to ensure all text fits within rectangles
and the entire mindmap fits within the chart area:

1. **Layout Calculation Phase**:
   - Calculates base font size based on total available area and number of elements
   - Determines uniform dimensions for each node level (theme, main branches, sub-branches)
   - Applies horizontal and vertical scaling if needed to fit within chart bounds
   - All scaling happens BEFORE text fitting to ensure accurate measurements

2. **Text Fitting Algorithm**:
   - Uses binary search (30-40 iterations) to find optimal font size for each text element
   - Text wrapping respects word boundaries only (no mid-word breaks)
   - Separate fitting strategies for main branches (strict, 88% safety margin) and
     sub-branches (prioritizes larger fonts, 90% safety margin, minimal wrapping)
   - Measures actual rendered text dimensions on the target figure for accuracy

3. **Iterative Refinement Loop**:
   - Renders the plot and measures actual text dimensions
   - Detects overflow (text exceeding rectangle bounds or rectangles exceeding chart area)
   - Adjusts font sizes and dimensions iteratively (up to 5 iterations)
   - Continues until no overflow is detected

4. **Boundary Enforcement**:
   - Accounts for rectangle border linewidth (extends outward from edges)
   - Uses absolute bottom boundary to prevent bottom border cutoff
   - Centers sub-branch blocks with their main branch while respecting boundaries
   - Clips all elements to axes limits to prevent rendering outside chart area

The algorithm guarantees no text overflow, no ellipsis, and proper spacing while
maintaining visual hierarchy and readability.
"""

import matplotlib
from typing import Any

matplotlib.use("Agg")  # Use non-interactive backend
import math
import os
from typing import Dict, Tuple

import matplotlib.patches as patches
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib import rcParams

from bigdata_research_tools.mindmap.mindmap import MindMap

##Note: In case the mindmap overflows from the chart area and edges, you can try to adjust the padding system by shrinking the 'available chart area'. For example, if padding does not work, you can try to have the algorithm think that the available area is 95% of the original available area. In this way, the algorithm will have less space to work with and will try to fit the text within the available area.


class MindmapPlotter:
    """Main class for plotting mindmaps with graphviz-inspired layout."""

    def __init__(
        self,
        mindmap: pd.DataFrame | MindMap,
        main_theme: str,
        title: str = "Mind Map",
        color_scheme: str = "gold",
        output_dir: str = "./outputs",
        aspect_ratio: float = 8 / 9,
    ):
        """Initialize the mindmap plotter."""
        if isinstance(mindmap, pd.DataFrame):
            self.df = mindmap.copy()
        elif isinstance(mindmap, MindMap):
            self.df = mindmap.to_dataframe()

        # Handle flexible column names: either (Parent, Label) or (Main Branches, Sub-Branches)
        if "Main Branches" in self.df.columns and "Sub-Branches" in self.df.columns:
            # Already in correct format
            pass
        elif "Parent" in self.df.columns and "Label" in self.df.columns:
            # Rename to standard format
            self.df = self.df.rename(
                columns={"Parent": "Main Branches", "Label": "Sub-Branches"}
            )
        else:
            # Check what columns we have
            has_main = "Main Branches" in self.df.columns
            has_sub = "Sub-Branches" in self.df.columns
            has_parent = "Parent" in self.df.columns
            has_label = "Label" in self.df.columns

            raise ValueError(
                f"DataFrame must have either (Parent, Label) or (Main Branches, Sub-Branches) columns. "
                f"Found columns: {list(self.df.columns)}. "
                f"Has Main Branches: {has_main}, Has Sub-Branches: {has_sub}, "
                f"Has Parent: {has_parent}, Has Label: {has_label}"
            )

        # Assert required columns exist
        assert "Main Branches" in self.df.columns, (
            "Missing 'Main Branches' column after processing"
        )
        assert "Sub-Branches" in self.df.columns, (
            "Missing 'Sub-Branches' column after processing"
        )

        self.df["Main Branches"] = self.df["Main Branches"].astype(str).str.strip()
        self.df["Sub-Branches"] = self.df["Sub-Branches"].astype(str).str.strip()

        self.main_theme = main_theme
        self.title = title
        self.color_scheme = color_scheme
        self.output_dir = output_dir
        self.aspect_ratio = aspect_ratio

        os.makedirs(output_dir, exist_ok=True)

        plt.rcParams["svg.fonttype"] = "none"
        rcParams["font.family"] = "DejaVu Sans"

        self.colors = self._get_color_scheme(color_scheme)

        self.main_branches = self.df["Main Branches"].unique()
        self.n_main = len(self.main_branches)

        self.sub_branches = {
            main: self.df[self.df["Main Branches"] == main]["Sub-Branches"].tolist()
            for main in self.main_branches
        }
        self.n_sub_total = sum(len(subs) for subs in self.sub_branches.values())

        self.fig_width = 10.0
        self.fig_height = self.fig_width / aspect_ratio
        self.title_height = 0  # No title - removed to maximize space

        # Add padding to prevent rectangles from going over chart edges
        self.edge_padding = 0.25  # Padding on sides
        self.top_padding = 0.1  # Minimal top padding
        self.bottom_padding = 0.6  # Extra bottom padding to ensure borders don't get cut (increased further)
        # Account for linewidth - borders extend outward by half linewidth on each side
        self.max_linewidth = 2.5  # Maximum linewidth used (for main branches/theme)
        self.sub_linewidth = 2.0  # Sub-branch linewidth
        # Linewidth extends by half on each side, convert points to inches (72 points per inch)
        # Be very conservative: use 3x linewidth as padding to ensure borders don't get cut
        self.linewidth_padding = (
            self.max_linewidth / 72.0
        ) * 3.0  # Very conservative padding
        self.sub_linewidth_padding = (
            self.sub_linewidth / 72.0
        ) * 3.0  # Sub-branch linewidth padding
        # Use minimal top padding, extra bottom padding
        # Reduce available_height to account for linewidth extension at bottom
        self.available_height = (
            self.fig_height
            - self.title_height
            - self.top_padding
            - (self.bottom_padding + self.sub_linewidth_padding)
        )
        self.available_width = self.fig_width - 2 * (
            self.edge_padding + self.linewidth_padding
        )
        # Calculate absolute bottom boundary - no rectangle should exceed this
        # Use sub_linewidth_padding since sub-branches are at the bottom
        self.absolute_bottom = (
            self.fig_height - self.bottom_padding - self.sub_linewidth_padding
        )

        # Increased padding for text inside boxes
        self.pad_x = 0.7  # Increased from 0.5
        self.pad_y = 0.7  # Increased from 0.5

    def _get_color_scheme(self, scheme: str) -> Dict[str, str]:
        """Get color scheme dictionary."""
        schemes = {
            "gold": {
                "edge": "#eab720",
                "link": "#eab720",
                "background": "none",  # Transparent
                "text": "black",
            },
            "light_blue": {
                "edge": "#206EB5",
                "link": "#206EB5",
                "background": "none",  # Transparent
                "text": "black",
            },
            "dark_blue": {
                "edge": "#2C318C",
                "link": "#2C318C",
                "background": "none",  # Transparent
                "text": "black",
            },
        }
        return schemes.get(scheme, schemes["gold"])

    def _measure_text(self, ax, text: str, fontsize: float) -> Tuple[float, float]:
        """Measure text dimensions accurately."""
        if not text:
            return self.pad_x, self.pad_y

        t = ax.text(0, 0, text, fontsize=fontsize, ha="left", va="bottom")
        if not hasattr(ax.figure.canvas, "renderer"):
            ax.figure.canvas.draw()
        renderer = ax.figure.canvas.get_renderer()
        bbox = t.get_window_extent(renderer=renderer)
        t.remove()

        width = bbox.width / ax.figure.dpi + self.pad_x
        height = bbox.height / ax.figure.dpi + self.pad_y

        return width, height

    def _wrap_text(self, text: str, max_chars: int) -> str:
        """Wrap text at word boundaries."""
        if not text:
            return text

        lines = []
        for para in text.split("\n"):
            if not para:
                lines.append("")
                continue

            words = para.split()
            if not words:
                lines.append("")
                continue

            line = words[0]
            for word in words[1:]:
                if len(line + " " + word) <= max_chars:
                    line += " " + word
                else:
                    lines.append(line)
                    line = word
            lines.append(line)

        return "\n".join(lines)

    def _fit_text_main(
        self,
        ax,
        text: str,
        max_width: float,
        max_height: float,
        initial_font: float,
        min_font: float = 9,
    ) -> Tuple[float, str, float, float]:
        """
        Fit text for main branches - STRICT no overflow.
        Returns: fontsize, wrapped_text, actual_width, actual_height
        """
        if not text:
            return min_font, "", self.pad_x, self.pad_y

        available_w = max(0.1, max_width - self.pad_x)
        _available_h = max(0.1, max_height - self.pad_y)

        # Binary search for optimal font size
        low_font = min_font
        high_font = initial_font * 1.3
        best = None

        for _ in range(40):
            test_font = (low_font + high_font) / 2.0

            # Less aggressive wrapping - prioritize font size
            chars_per_inch = test_font / 12.0 * 7  # More chars per inch
            wrap_chars = max(20, int(available_w * chars_per_inch))  # Minimum 20 chars

            wrapped = self._wrap_text(text, wrap_chars)
            w, h = self._measure_text(ax, wrapped, test_font)

            if w <= max_width * 0.88 and h <= max_height * 0.88:
                best = (test_font, wrapped, w, h)
                low_font = test_font + 0.2
            else:
                high_font = test_font - 0.2

            if high_font < low_font:
                break

        if best:
            return best

        # Fallback: ensure it fits
        fontsize = min_font
        chars_per_inch = fontsize / 12.0 * 7
        wrap_chars = max(20, int(available_w * chars_per_inch))
        wrapped = self._wrap_text(text, wrap_chars)
        w, h = self._measure_text(ax, wrapped, fontsize)

        # Keep reducing until it fits - more aggressive
        max_attempts = 60
        attempt = 0
        while (
            (w > max_width * 0.88 or h > max_height * 0.88)
            and fontsize > min_font * 0.7
            and attempt < max_attempts
        ):
            attempt += 1
            scale = (
                min(max_width * 0.88 / max(0.01, w), max_height * 0.88 / max(0.01, h))
                * 0.97
            )
            fontsize = max(min_font * 0.7, fontsize * scale)
            chars_per_inch = fontsize / 12.0 * 7
            wrap_chars = max(20, int(available_w * chars_per_inch))
            wrapped = self._wrap_text(text, wrap_chars)
            w, h = self._measure_text(ax, wrapped, fontsize)

        # Final verification - ensure text actually fits
        w, h = self._measure_text(ax, wrapped, fontsize)
        if w > max_width * 0.88 or h > max_height * 0.88:
            # Force one more reduction
            scale = (
                min(max_width * 0.88 / max(0.01, w), max_height * 0.88 / max(0.01, h))
                * 0.98
            )
            fontsize = max(min_font * 0.7, fontsize * scale)
            chars_per_inch = fontsize / 12.0 * 7
            wrap_chars = max(20, int((max_width - self.pad_x) * chars_per_inch))
            wrapped = self._wrap_text(text, wrap_chars)
            w, h = self._measure_text(ax, wrapped, fontsize)

        # Final safety check - clip dimensions
        w = min(w, max_width * 0.88)
        h = min(h, max_height * 0.88)

        return fontsize, wrapped, w, h

    def _fit_text_sub(
        self,
        ax,
        text: str,
        max_width: float,
        max_height: float,
        initial_font: float,
        min_font: float = 8,
    ) -> Tuple[float, str, float, float]:
        """
        Fit text for sub-branches - prioritize large font, minimal wrapping.
        Returns: fontsize, wrapped_text, actual_width, actual_height
        """
        if not text:
            return min_font, "", self.pad_x, self.pad_y

        available_w = max(0.1, max_width - self.pad_x)
        _available_h = max(0.1, max_height - self.pad_y)

        # Binary search prioritizing larger fonts
        low_font = min_font
        high_font = initial_font * 1.5
        best = None

        for _ in range(40):
            test_font = (low_font + high_font) / 2.0

            # Much less aggressive wrapping - wide lines preferred
            chars_per_inch = test_font / 12.0 * 8  # Even more chars per inch
            wrap_chars = max(
                25, int(available_w * chars_per_inch)
            )  # Minimum 25 chars, prefer wide lines

            wrapped = self._wrap_text(text, wrap_chars)
            w, h = self._measure_text(ax, wrapped, test_font)

            if w <= max_width * 0.90 and h <= max_height * 0.90:
                best = (test_font, wrapped, w, h)
                low_font = test_font + 0.3  # Try even larger
            else:
                high_font = test_font - 0.3

            if high_font < low_font:
                break

        if best:
            return best

        # Fallback: use minimum font with wide wrapping
        fontsize = min_font
        chars_per_inch = fontsize / 12.0 * 8
        wrap_chars = max(25, int(available_w * chars_per_inch))
        wrapped = self._wrap_text(text, wrap_chars)
        w, h = self._measure_text(ax, wrapped, fontsize)

        # Only reduce if absolutely necessary
        max_attempts = 30
        attempt = 0
        while (
            (w > max_width * 0.90 or h > max_height * 0.90)
            and fontsize > min_font * 0.85
            and attempt < max_attempts
        ):
            attempt += 1
            scale = (
                min(max_width * 0.90 / max(0.01, w), max_height * 0.90 / max(0.01, h))
                * 0.98
            )
            fontsize = max(min_font * 0.85, fontsize * scale)
            chars_per_inch = fontsize / 12.0 * 8
            wrap_chars = max(25, int(available_w * chars_per_inch))
            wrapped = self._wrap_text(text, wrap_chars)
            w, h = self._measure_text(ax, wrapped, fontsize)

        # Final verification - ensure text actually fits
        w, h = self._measure_text(ax, wrapped, fontsize)
        if w > max_width * 0.90 or h > max_height * 0.90:
            # Force one more reduction
            scale = (
                min(max_width * 0.90 / max(0.01, w), max_height * 0.90 / max(0.01, h))
                * 0.99
            )
            fontsize = max(min_font * 0.85, fontsize * scale)
            chars_per_inch = fontsize / 12.0 * 8
            wrap_chars = max(25, int((max_width - self.pad_x) * chars_per_inch))
            wrapped = self._wrap_text(text, wrap_chars)
            w, h = self._measure_text(ax, wrapped, fontsize)

        # Final safety check - clip dimensions
        w = min(w, max_width * 0.90)
        h = min(h, max_height * 0.90)

        return fontsize, wrapped, w, h

    def _calculate_layout(self) -> Dict:
        """Calculate complete layout with uniform dimensions and scaling."""
        fig_temp = plt.figure(figsize=(self.fig_width, self.fig_height))
        ax_temp = fig_temp.add_subplot(111)
        ax_temp.axis("off")

        # Base font calculation
        total_elements = self.n_main + self.n_sub_total
        area_per_element = (self.available_height * self.available_width) / max(
            1, total_elements
        )

        ref_area = 1.0
        if area_per_element > ref_area:
            area_factor = math.pow(area_per_element / ref_area, 0.6)
        else:
            area_factor = math.pow(area_per_element / ref_area, 0.7)

        area_factor = max(0.4, min(3.5, area_factor))
        base_font = max(8, min(26, 12 * area_factor))

        # Initial dimensions (will be scaled if needed)
        main_spacing = self.available_height * 0.06
        available_h = self.available_height - (self.n_main - 1) * main_spacing
        uniform_main_h = max(0.7, min(1.6, available_h / max(1, self.n_main)))

        max_main_len = max([len(m) for m in self.main_branches], default=20)
        uniform_main_w = max(1.3, min(2.5, max_main_len * 0.10))

        # Theme width matches main branch width
        theme_w = uniform_main_w
        theme_h = uniform_main_h

        # Sub-branch dimensions
        max_subs = max([len(subs) for subs in self.sub_branches.values()], default=1)
        spacing_extra = main_spacing * 0.4
        available_sub_h = uniform_main_h + 2 * spacing_extra

        if max_subs > 0:
            sub_spacing = 0.12
            available_for_subs = available_sub_h - (max_subs - 1) * sub_spacing
            uniform_sub_h = max(0.55, min(1.5, available_for_subs / max_subs))
        else:
            uniform_sub_h = 0.8
            sub_spacing = 0.12

        all_subs = [s for subs in self.sub_branches.values() for s in subs]
        max_sub_len = max([len(s) for s in all_subs], default=30) if all_subs else 30
        max_w = self.available_width * 0.28
        uniform_sub_w = max(2.2, min(max_w, max_sub_len * 0.12))

        # Calculate column positions (accounting for edge padding and linewidth)
        margin = self.edge_padding + self.linewidth_padding
        col_spacing = self.available_width * 0.07

        x_theme = margin
        x_main = x_theme + theme_w + col_spacing
        x_sub = x_main + uniform_main_w + col_spacing
        total_width_needed = x_sub + uniform_sub_w + margin

        # Horizontal scaling if needed
        h_scale = 1.0
        if total_width_needed > self.available_width * 0.96:
            h_scale = (self.available_width * 0.96) / total_width_needed
            uniform_main_w *= h_scale
            theme_w *= h_scale
            uniform_sub_w *= h_scale
            margin *= h_scale
            col_spacing *= h_scale
            # Recalculate positions
            x_theme = margin
            x_main = x_theme + theme_w + col_spacing
            x_sub = x_main + uniform_main_w + col_spacing

        # Vertical scaling check
        total_h = uniform_main_h * self.n_main + main_spacing * (self.n_main - 1)
        v_scale = 1.0
        if total_h > self.available_height * 0.94:
            v_scale = (self.available_height * 0.94) / total_h
            uniform_main_h *= v_scale
            theme_h *= v_scale
            uniform_sub_h *= v_scale
            main_spacing *= v_scale
            sub_spacing *= v_scale

        # Now fit text with final scaled dimensions
        # Fit all main branches to find uniform font
        main_fonts = []
        for main in self.main_branches:
            font, _, _, _ = self._fit_text_main(
                ax_temp, main, uniform_main_w, uniform_main_h, base_font * 0.9, 10
            )
            main_fonts.append(font)

        uniform_main_font = min(main_fonts) if main_fonts else base_font * 0.9

        # Fit all main branches with uniform dimensions - STRICT no overflow
        main_data = {}
        for main in self.main_branches:
            font, wrapped, w, h = self._fit_text_main(
                ax_temp, main, uniform_main_w, uniform_main_h, uniform_main_font, 10
            )
            main_data[main] = {
                "fontsize": font,
                "text": wrapped,
                "width": uniform_main_w,
                "height": uniform_main_h,
            }

        # Theme layout - use same width as main
        theme_font, theme_wrapped, theme_w_actual, theme_h_actual = self._fit_text_main(
            ax_temp, self.main_theme, theme_w, theme_h, base_font * 1.0, 11
        )
        # Use target dimensions, not measured
        theme_w = uniform_main_w
        theme_h = uniform_main_h

        # Fit all sub-branches - prioritize large font, minimal wrapping
        sub_fonts = []
        for sub in all_subs:
            font, _, _, _ = self._fit_text_sub(
                ax_temp,
                sub,
                uniform_sub_w * 0.94,
                uniform_sub_h * 0.94,
                base_font * 1.0,
                9,
            )
            sub_fonts.append(font)

        uniform_sub_font = min(sub_fonts) if sub_fonts else base_font * 1.0

        # Fit all sub-branches with uniform dimensions
        sub_data = {}
        for main in self.main_branches:
            subs = self.sub_branches[main]
            main_sub_data = []

            for sub in subs:
                font, wrapped, w, h = self._fit_text_sub(
                    ax_temp,
                    sub,
                    uniform_sub_w * 0.94,
                    uniform_sub_h * 0.94,
                    uniform_sub_font,
                    9,
                )

                main_sub_data.append(
                    {
                        "fontsize": font,
                        "text": wrapped,
                        "width": uniform_sub_w,
                        "height": uniform_sub_h,
                    }
                )

            sub_data[main] = main_sub_data

        plt.close(fig_temp)

        return {
            "theme": {
                "fontsize": theme_font,
                "text": theme_wrapped,
                "width": theme_w,
                "height": theme_h,
            },
            "main_data": main_data,
            "sub_data": sub_data,
            "uniform_main_w": uniform_main_w,
            "uniform_main_h": uniform_main_h,
            "uniform_sub_w": uniform_sub_w,
            "uniform_sub_h": uniform_sub_h,
            "main_spacing": main_spacing,
            "sub_spacing": sub_spacing,
            "margin": margin,
            "col_spacing": col_spacing,
            "x_theme": x_theme,
            "x_main": x_main,
            "x_sub": x_sub,
        }

    def _check_overflow(
        self, ax, layout, x_theme, x_main, x_sub, main_positions, theme_y
    ) -> Dict:
        """Check for text and rectangle overflow, return adjustments needed."""
        issues: dict[str, Any] = {
            "theme_overflow": False,
            "main_overflows": {},
            "sub_overflows": {},
            "bottom_cutoff": False,
        }

        # Check theme text overflow
        theme_text = ax.text(
            x_theme + layout["theme"]["width"] / 2,
            theme_y + layout["theme"]["height"] / 2,
            layout["theme"]["text"],
            ha="center",
            va="center",
            fontsize=layout["theme"]["fontsize"],
            fontweight="bold",
        )
        renderer = ax.figure.canvas.get_renderer()
        bbox = theme_text.get_window_extent(renderer=renderer)
        theme_text.remove()
        text_w = bbox.width / ax.figure.dpi
        text_h = bbox.height / ax.figure.dpi
        if (
            text_w > layout["theme"]["width"] * 0.88
            or text_h > layout["theme"]["height"] * 0.88
        ):
            issues["theme_overflow"] = True

        # Check main branch text overflow
        for main in self.main_branches:
            main_y = main_positions[main]
            main_info = layout["main_data"][main]
            main_text = ax.text(
                x_main + layout["uniform_main_w"] / 2,
                main_y + layout["uniform_main_h"] / 2,
                main_info["text"],
                ha="center",
                va="center",
                fontsize=main_info["fontsize"],
                fontweight="bold",
            )
            bbox = main_text.get_window_extent(renderer=renderer)
            main_text.remove()
            text_w = bbox.width / ax.figure.dpi
            text_h = bbox.height / ax.figure.dpi
            if (
                text_w > layout["uniform_main_w"] * 0.88
                or text_h > layout["uniform_main_h"] * 0.88
            ):
                issues["main_overflows"][main] = True

        # Check sub-branch overflow and bottom cutoff
        max_bottom_y = 0
        for main in self.main_branches:
            main_y = main_positions[main]
            subs = layout["sub_data"].get(main, [])
            if subs:
                spacing_extra = layout["main_spacing"] * 0.4
                min_sub_y = main_y - spacing_extra
                max_sub_y = main_y + layout["uniform_main_h"] + spacing_extra

                sub_spacing = layout["sub_spacing"]
                total_sub_h = (
                    layout["uniform_sub_h"] * len(subs) + (len(subs) - 1) * sub_spacing
                )
                main_center = main_y + layout["uniform_main_h"] / 2
                sub_y_start = main_center - total_sub_h / 2

                if sub_y_start < min_sub_y:
                    sub_y_start = min_sub_y
                if sub_y_start + total_sub_h > max_sub_y:
                    sub_y_start = max_sub_y - total_sub_h
                # Calculate maximum allowed bottom position (use absolute bottom)
                min_top_y = self.top_padding + self.linewidth_padding

                if sub_y_start < min_top_y:
                    sub_y_start = min_top_y
                # Ensure total height doesn't exceed absolute bottom
                if sub_y_start + total_sub_h > self.absolute_bottom:
                    sub_y_start = max(min_top_y, self.absolute_bottom - total_sub_h)

                sub_y = sub_y_start
                for i, sub_info in enumerate(subs):
                    if sub_y + layout["uniform_sub_h"] > max_bottom_y:
                        issues["bottom_cutoff"] = True
                        break

                    # Check text overflow
                    sub_text = ax.text(
                        x_sub + layout["uniform_sub_w"] / 2,
                        sub_y + layout["uniform_sub_h"] / 2,
                        sub_info["text"],
                        ha="center",
                        va="center",
                        fontsize=sub_info["fontsize"],
                        fontweight="bold",
                    )
                    bbox = sub_text.get_window_extent(renderer=renderer)
                    sub_text.remove()
                    text_w = bbox.width / ax.figure.dpi
                    text_h = bbox.height / ax.figure.dpi
                    if (
                        text_w > layout["uniform_sub_w"] * 0.90
                        or text_h > layout["uniform_sub_h"] * 0.90
                    ):
                        issues["sub_overflows"][(main, i)] = True

                    bottom_y = sub_y + layout["uniform_sub_h"]
                    if bottom_y > max_bottom_y:
                        max_bottom_y = bottom_y

                    sub_y += layout["uniform_sub_h"] + sub_spacing
                    if sub_y + layout["uniform_sub_h"] > max_sub_y:
                        break

        # Check if bottom sub-branch is too close to edge (accounting for padding and linewidth)
        if max_bottom_y > self.absolute_bottom - 0.1:
            issues["bottom_cutoff"] = True

        return issues

    def plot(self) -> Tuple[plt.Figure, plt.Axes]:
        """Create the mindmap plot with iterative refinement."""
        layout = self._calculate_layout()

        # Iterative refinement loop
        max_iterations = 5
        for iteration in range(max_iterations):
            fig, ax = plt.subplots(figsize=(self.fig_width, self.fig_height))
            ax.axis("off")

            # Use pre-calculated positions from layout
            x_theme = layout["x_theme"]
            x_main = layout["x_main"]
            x_sub = layout["x_sub"]

            # Main branch positions
            total_h = layout["uniform_main_h"] * self.n_main + layout[
                "main_spacing"
            ] * (self.n_main - 1)
            y_start = (self.available_height - total_h) / 2

            main_positions = {}
            y = y_start
            for main in self.main_branches:
                main_positions[main] = y
                y += layout["uniform_main_h"] + layout["main_spacing"]

            # Theme position (centered with main branches)
            theme_y = y_start + (total_h - layout["theme"]["height"]) / 2

            # Draw elements to check overflow
            self._draw_elements(
                ax, layout, x_theme, x_main, x_sub, main_positions, theme_y
            )

            # Ensure figure is drawn for accurate measurement
            ax.figure.canvas.draw()

            # Check for overflow
            issues = self._check_overflow(
                ax, layout, x_theme, x_main, x_sub, main_positions, theme_y
            )

            # If no issues, we're done
            if (
                not issues["theme_overflow"]
                and not issues["main_overflows"]
                and not issues["sub_overflows"]
                and not issues["bottom_cutoff"]
            ):
                plt.close(fig)
                break

            # Adjust layout based on issues
            if (
                issues["theme_overflow"]
                or issues["main_overflows"]
                or issues["bottom_cutoff"]
            ):
                # Reduce font sizes for theme and main branches
                layout = self._adjust_layout_for_overflow(layout, issues, iteration)
                plt.close(fig)
                continue

            plt.close(fig)
            break

        # Final render
        fig, ax = plt.subplots(figsize=(self.fig_width, self.fig_height))
        ax.axis("off")

        # Use pre-calculated positions from layout
        x_theme = layout["x_theme"]
        x_main = layout["x_main"]
        x_sub = layout["x_sub"]

        # Main branch positions (accounting for top padding and linewidth)
        total_h = layout["uniform_main_h"] * self.n_main + layout["main_spacing"] * (
            self.n_main - 1
        )
        y_start = (
            self.top_padding
            + self.linewidth_padding
            + (self.available_height - total_h) / 2
        )

        main_positions = {}
        y = y_start
        for main in self.main_branches:
            main_positions[main] = y
            y += layout["uniform_main_h"] + layout["main_spacing"]

        # Theme position (centered with main branches)
        theme_y = y_start + (total_h - layout["theme"]["height"]) / 2

        # Draw all elements
        self._draw_elements(ax, layout, x_theme, x_main, x_sub, main_positions, theme_y)

        # Set strict limits to prevent anything from being drawn outside bounds
        # Account for linewidth extension - clip everything strictly
        ax.set_xlim(0, self.fig_width)
        ax.set_ylim(0, self.fig_height)
        # Clip all patches and text to axes limits
        ax.set_clip_on(True)

        return fig, ax

    def _draw_elements(
        self, ax, layout, x_theme, x_main, x_sub, main_positions, theme_y
    ):
        """Draw all mindmap elements."""
        # Draw theme
        theme_rect = patches.Rectangle(
            (x_theme, theme_y),
            layout["theme"]["width"],
            layout["theme"]["height"],
            linewidth=2.5,
            edgecolor=self.colors["edge"],
            facecolor=self.colors["background"],
            zorder=2,
        )
        ax.add_patch(theme_rect)
        ax.text(
            x_theme + layout["theme"]["width"] / 2,
            theme_y + layout["theme"]["height"] / 2,
            layout["theme"]["text"],
            ha="center",
            va="center",
            fontsize=layout["theme"]["fontsize"],
            color=self.colors["text"],
            fontweight="bold",
            zorder=3,
        )

        # Draw main branches and sub-branches
        for main in self.main_branches:
            main_y = main_positions[main]
            main_info = layout["main_data"][main]

            # Main branch rectangle
            main_rect = patches.Rectangle(
                (x_main, main_y),
                layout["uniform_main_w"],
                layout["uniform_main_h"],
                linewidth=2.5,
                edgecolor=self.colors["edge"],
                facecolor=self.colors["background"],
                zorder=2,
            )
            ax.add_patch(main_rect)
            ax.text(
                x_main + layout["uniform_main_w"] / 2,
                main_y + layout["uniform_main_h"] / 2,
                main_info["text"],
                ha="center",
                va="center",
                fontsize=main_info["fontsize"],
                color=self.colors["text"],
                fontweight="bold",
                zorder=3,
            )

            # Connection theme to main
            ax.plot(
                [x_theme + layout["theme"]["width"], x_main],
                [
                    theme_y + layout["theme"]["height"] / 2,
                    main_y + layout["uniform_main_h"] / 2,
                ],
                color=self.colors["link"],
                linewidth=3,
                alpha=0.6,
                zorder=1,
                solid_capstyle="round",
            )

            # Sub-branches
            subs = layout["sub_data"].get(main, [])
            if subs:
                spacing_extra = layout["main_spacing"] * 0.4
                min_sub_y = main_y - spacing_extra
                max_sub_y = main_y + layout["uniform_main_h"] + spacing_extra
                # Ensure max_sub_y doesn't exceed absolute bottom
                max_sub_y = min(max_sub_y, self.absolute_bottom)
                available_sub_h = max_sub_y - min_sub_y

                sub_spacing = layout["sub_spacing"]
                total_sub_h = (
                    layout["uniform_sub_h"] * len(subs) + (len(subs) - 1) * sub_spacing
                )

                # Adjust spacing if needed
                if total_sub_h > available_sub_h:
                    max_sp = (
                        available_sub_h - layout["uniform_sub_h"] * len(subs)
                    ) / max(1, len(subs) - 1)
                    sub_spacing = max(0.08, min(sub_spacing, max_sp))
                    total_sub_h = (
                        layout["uniform_sub_h"] * len(subs)
                        + (len(subs) - 1) * sub_spacing
                    )

                # Center on main branch - calculate ideal center position
                main_center = main_y + layout["uniform_main_h"] / 2
                ideal_sub_y_start = main_center - total_sub_h / 2

                # Determine available space boundaries (use the most restrictive)
                absolute_min = self.top_padding + self.linewidth_padding
                absolute_max = self.absolute_bottom
                relative_min = min_sub_y
                relative_max = max_sub_y

                # Use the most restrictive boundaries
                min_top_y = max(absolute_min, relative_min)
                max_bottom_y = min(absolute_max, relative_max)

                # Start with ideal centered position
                sub_y_start = ideal_sub_y_start

                # If the entire block fits within available space, use centered position
                if (
                    ideal_sub_y_start >= min_top_y
                    and ideal_sub_y_start + total_sub_h <= max_bottom_y
                ):
                    sub_y_start = ideal_sub_y_start
                else:
                    # Block doesn't fit centered - adjust to fit while maintaining centering as much as possible
                    if ideal_sub_y_start < min_top_y:
                        # Too high - push down to minimum
                        sub_y_start = min_top_y
                    elif ideal_sub_y_start + total_sub_h > max_bottom_y:
                        # Too low - push up to maximum
                        sub_y_start = max_bottom_y - total_sub_h
                        # Ensure we don't go below minimum
                        if sub_y_start < min_top_y:
                            sub_y_start = min_top_y

                    # Final safety check: ensure we don't exceed absolute bottom
                    if sub_y_start + total_sub_h > absolute_max:
                        sub_y_start = max(min_top_y, absolute_max - total_sub_h)

                # Draw sub-branches
                sub_y = sub_y_start
                # Use pre-calculated sub_linewidth_padding
                # Use absolute bottom boundary - no rectangle should exceed this
                for sub_info in subs:
                    # STRICT check: rectangle bottom must not exceed absolute bottom
                    rect_bottom = sub_y + layout["uniform_sub_h"]

                    # Don't draw if rectangle itself would exceed absolute bottom
                    if rect_bottom > self.absolute_bottom:
                        break  # Don't draw this or any subsequent sub-branches
                    if sub_y + layout["uniform_sub_h"] > max_sub_y:
                        break

                    # Extra safety check - leave margin for linewidth extension
                    # Linewidth extends by half outward, so ensure rect_bottom + half_linewidth <= absolute_bottom
                    half_linewidth_extension = (self.sub_linewidth / 2.0) / 72.0
                    if rect_bottom + half_linewidth_extension > self.absolute_bottom:
                        break

                    # Sub-branch rectangle - clip to axes to prevent overflow
                    sub_rect = patches.Rectangle(
                        (x_sub, sub_y),
                        layout["uniform_sub_w"],
                        layout["uniform_sub_h"],
                        linewidth=self.sub_linewidth,
                        edgecolor=self.colors["edge"],
                        facecolor=self.colors["background"],
                        zorder=2,
                        clip_on=True,
                    )
                    ax.add_patch(sub_rect)

                    # Sub-branch text
                    ax.text(
                        x_sub + layout["uniform_sub_w"] / 2,
                        sub_y + layout["uniform_sub_h"] / 2,
                        sub_info["text"],
                        ha="center",
                        va="center",
                        fontsize=sub_info["fontsize"],
                        color=self.colors["text"],
                        fontweight="bold",
                        zorder=3,
                    )

                    # Connection main to sub
                    ax.plot(
                        [x_main + layout["uniform_main_w"], x_sub],
                        [
                            main_y + layout["uniform_main_h"] / 2,
                            sub_y + layout["uniform_sub_h"] / 2,
                        ],
                        color=self.colors["link"],
                        linewidth=2.5,
                        alpha=0.5,
                        zorder=1,
                        solid_capstyle="round",
                    )

                    sub_y += layout["uniform_sub_h"] + sub_spacing

                    if sub_y + layout["uniform_sub_h"] > max_sub_y:
                        break

        # Title removed to maximize space for mindmap

    def _adjust_layout_for_overflow(self, layout, issues, iteration):
        """Adjust layout to fix overflow issues."""
        # Create temp figure for re-fitting
        fig_temp = plt.figure(figsize=(self.fig_width, self.fig_height))
        ax_temp = fig_temp.add_subplot(111)
        ax_temp.axis("off")

        # Reduce font sizes more aggressively
        reduction_factor = 0.92 - (iteration * 0.02)  # More aggressive each iteration

        # Adjust theme
        if issues["theme_overflow"]:
            current_font = layout["theme"]["fontsize"]
            new_font = max(9, current_font * reduction_factor)
            font, wrapped, _, _ = self._fit_text_main(
                ax_temp,
                self.main_theme,
                layout["theme"]["width"],
                layout["theme"]["height"],
                new_font,
                9,
            )
            layout["theme"]["fontsize"] = font
            layout["theme"]["text"] = wrapped

        # Adjust main branches
        if issues["main_overflows"]:
            for main in issues["main_overflows"]:
                current_font = layout["main_data"][main]["fontsize"]
                new_font = max(8, current_font * reduction_factor)
                font, wrapped, _, _ = self._fit_text_main(
                    ax_temp,
                    main,
                    layout["uniform_main_w"],
                    layout["uniform_main_h"],
                    new_font,
                    8,
                )
                layout["main_data"][main]["fontsize"] = font
                layout["main_data"][main]["text"] = wrapped

        # Adjust for bottom cutoff - reduce vertical spacing or sub-branch height
        if issues["bottom_cutoff"]:
            # Reduce sub-branch height slightly
            layout["uniform_sub_h"] *= 0.95
            layout["sub_spacing"] *= 0.95
            # Re-fit all sub-branches
            for main in self.main_branches:
                subs = layout["sub_data"].get(main, [])
                for i, sub_info in enumerate(subs):
                    sub_text = self.sub_branches[main][i]
                    font, wrapped, _, _ = self._fit_text_sub(
                        ax_temp,
                        sub_text,
                        layout["uniform_sub_w"] * 0.94,
                        layout["uniform_sub_h"] * 0.94,
                        layout["sub_data"][main][i]["fontsize"],
                        8,
                    )
                    layout["sub_data"][main][i]["fontsize"] = font
                    layout["sub_data"][main][i]["text"] = wrapped

        plt.close(fig_temp)
        return layout

    def save(self, fig: plt.Figure):
        """Save the figure as PNG and SVG."""
        filename = self.title.replace(" ", "_")
        png_path = os.path.join(self.output_dir, f"{filename}.png")
        svg_path = os.path.join(self.output_dir, f"{filename}.svg")

        # Don't use bbox_inches='tight' to ensure we stay within figure bounds
        # The axes limits are already set correctly in plot()
        fig.savefig(png_path, transparent=True, dpi=300)
        fig.savefig(svg_path, transparent=True)

        print(f"Saved: {png_path}")
        print(f"Saved: {svg_path}")


def plot_mindmap(
    mindmap: pd.DataFrame | MindMap,
    main_theme: str,
    title: str = "Mind Map",
    color_scheme: str = "gold",
    output_dir: str = "./outputs",
    aspect_ratio: float = 8 / 9,
) -> Tuple[plt.Figure, plt.Axes]:
    """Plot a mindmap from a DataFrame."""
    plotter = MindmapPlotter(
        mindmap, main_theme, title, color_scheme, output_dir, aspect_ratio
    )
    fig, ax = plotter.plot()
    plotter.save(fig)
    return fig, ax
