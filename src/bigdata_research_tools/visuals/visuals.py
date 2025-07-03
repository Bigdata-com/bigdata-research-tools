from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from bigdata_research_tools.settings import check_libraries_installed


def check_plotly_dependencies() -> bool:
    """
    Check if the required Plotly dependencies are installed.
    Will look for the `plotly` package.
    """
    return check_libraries_installed(["plotly"])


class ExposureDashboard:
    """
    A configurable dashboard for analyzing thematic exposure of companies.
    """

    base_config = {
        # Column names
        "company_column": "Company",
        "industry_column": "Industry",
        "composite_score_column": "Composite Score",
        # Dashboard layout
        "dashboard_height": 1600,
        "dashboard_width": 1800,
        "row_heights": [0.25, 0.25, 0.25, 0.25],
        "vertical_spacing": 0.18,
        "horizontal_spacing": 0.1,
        # Industry analysis
        "industry_height": 500,
        "industry_width": 1000,
        # Color schemes
        "heatmap_colorscale": "YlGnBu",
        "total_scores_colorscale": "Viridis",
        "scatter_colorscale": "Turbo",
        "themes_colorscale": "Reds_r",
        "industry_colorscale": "YlOrRd",
        # Visualization parameters
        "top_themes_count": 3,
        "scatter_size_multiplier": 80,
        "scatter_size_ref": 0.15,
        "scatter_opacity": 0.7,
        "text_font_size": 10,
        "tick_font_size": 9,
        "tick_angle": 45,
        # Margins
        "main_margin": {"l": 60, "r": 50, "t": 100, "b": 50},
        "industry_margin": {"l": 60, "r": 50, "t": 80, "b": 50},
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the dashboard with configuration parameters.

        Parameters:
        -----------
        config : dict, optional
            Configuration dictionary with dashboard settings
        """
        self.config = {**self.base_config, **(config or {})}

    def create_dashboard(
        self,
        df_company: pd.DataFrame,
        n_companies: int = 10,
        theme_columns: Optional[List[str]] = None,
    ) -> Tuple[go.Figure, go.Figure]:
        """
        Creates a comprehensive dashboard for analyzing thematic exposure of companies.

        Parameters:
        -----------
        df_company : pandas.DataFrame
            DataFrame containing company data
        n_companies : int, default=10
            Number of companies to include in the analysis
        theme_columns : list, optional
            List of theme column names. If None, will be auto-detected

        Returns:
        --------
        tuple
            A tuple containing two Plotly figures:
            - Main dashboard with four panels
            - Industry-level analysis heatmap
        """
        # Validate input data
        self._validate_dataframe(df_company)

        # Select top n companies and reset index
        df = df_company[:n_companies].reset_index(drop=True).copy()

        # Extract theme column names
        if theme_columns is None:
            theme_columns = self._extract_theme_columns(df)

        # Create subplots layout
        fig = self._create_subplot_layout()

        # Add each visualization to the dashboard
        self._add_raw_scores_heatmap(fig, df, theme_columns)
        self._add_total_scores_barchart(fig, df)
        self._add_top_themes_by_company_scatter(fig, df, theme_columns)
        self._add_dominant_themes_barchart(fig, df, theme_columns)

        # Create industry-level analysis as a separate figure
        industry_fig = self._create_industry_analysis(df, theme_columns)

        # Format the main dashboard layout
        self._format_dashboard_layout(fig)

        return fig, industry_fig

    def _validate_dataframe(self, df: pd.DataFrame) -> None:
        """Validate that the dataframe has required columns."""
        required_cols = [
            self.config["company_column"],
            self.config["industry_column"],
            self.config["composite_score_column"],
        ]

        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")

    def _extract_theme_columns(self, df: pd.DataFrame) -> List[str]:
        """Extract theme column names from the dataframe."""
        start_idx = self.config["theme_start_col"]
        end_idx = self.config["theme_end_col"]

        if end_idx == -1:
            # Find the index of composite score column
            composite_col = self.config["composite_score_column"]
            end_idx = df.columns.get_loc(composite_col)

        return list(df.iloc[:, start_idx:end_idx].columns)

    def _create_subplot_layout(self) -> go.Figure:
        """Create the subplot layout for the main dashboard."""
        return make_subplots(
            rows=4,
            cols=1,
            specs=[
                [{"type": "heatmap"}],
                [{"type": "bar"}],
                [{"type": "scatter"}],
                [{"type": "bar"}],
            ],
            row_heights=self.config["row_heights"],
            column_widths=[2],
            vertical_spacing=self.config["vertical_spacing"],
            horizontal_spacing=self.config["horizontal_spacing"],
            subplot_titles=self.config["subplot_titles"],
        )

    def _add_raw_scores_heatmap(
        self, fig: go.Figure, df: pd.DataFrame, theme_columns: List[str]
    ) -> None:
        """Add a heatmap of raw thematic scores to the dashboard."""
        company_col = self.config["company_column"]

        heatmap_z = df[theme_columns].values
        heatmap_x = theme_columns
        heatmap_y = df[company_col].tolist()

        fig.add_trace(
            go.Heatmap(
                z=heatmap_z,
                x=heatmap_x,
                y=heatmap_y,
                colorscale=self.config["heatmap_colorscale"],
                text=heatmap_z.astype(int),
                texttemplate="%{text}",
                showscale=True,
            ),
            row=1,
            col=1,
        )

    def _add_total_scores_barchart(self, fig: go.Figure, df: pd.DataFrame) -> None:
        """Add a horizontal bar chart of total thematic scores by company."""
        company_col = self.config["company_column"]
        score_col = self.config["composite_score_column"]

        companies = df[company_col].tolist()
        total_scores = df[score_col].tolist()

        # Sort by score for better visualization (highest first)
        sorted_indices = np.argsort(total_scores)[::-1]
        sorted_companies = [companies[i] for i in sorted_indices]
        sorted_scores = [total_scores[i] for i in sorted_indices]

        fig.add_trace(
            go.Bar(
                y=sorted_companies,
                x=sorted_scores,
                orientation="h",
                marker=dict(
                    color=sorted_scores,
                    colorscale=self.config["total_scores_colorscale"],
                    showscale=False,
                ),
                text=sorted_scores,
                textposition="outside",
                textfont=dict(size=self.config["text_font_size"]),
            ),
            row=2,
            col=1,
        )

    def _add_top_themes_by_company_scatter(
        self, fig: go.Figure, df: pd.DataFrame, theme_columns: List[str]
    ) -> None:
        """Add a scatter plot showing the top thematic exposures for each company."""
        company_col = self.config["company_column"]
        top_count = self.config["top_themes_count"]

        max_score = df[theme_columns].values.max()
        companies_unique = df[company_col].unique()

        for i, company in enumerate(companies_unique):
            company_data = df[df[company_col] == company]
            if len(company_data) == 0:
                continue

            company_row = company_data.iloc[0]
            company_scores = company_row[theme_columns].values

            # Get indices of top themes
            top_indices = np.argsort(company_scores)[-top_count:]

            x_values = []
            y_values = []
            sizes = []
            hover_texts = []

            for idx in top_indices:
                if company_scores[idx] > 0:  # Only plot if score > 0
                    theme = theme_columns[idx]
                    score = company_scores[idx]
                    size = (score / max_score) * self.config["scatter_size_multiplier"]

                    x_values.append(company)
                    y_values.append(theme)
                    sizes.append(size)
                    hover_texts.append(f"{company}<br>{theme}: {int(score)}")

            if len(x_values) > 0:
                fig.add_trace(
                    go.Scatter(
                        x=x_values,
                        y=y_values,
                        mode="markers",
                        marker=dict(
                            size=sizes,
                            sizemode="area",
                            sizeref=self.config["scatter_size_ref"],
                            color=i,
                            colorscale=self.config["scatter_colorscale"],
                            showscale=False,
                            opacity=self.config["scatter_opacity"],
                            line=dict(width=1, color="DarkSlateGrey"),
                        ),
                        text=hover_texts,
                        hoverinfo="text",
                        name=company,
                    ),
                    row=3,
                    col=1,
                )

    def _add_dominant_themes_barchart(
        self, fig: go.Figure, df: pd.DataFrame, theme_columns: List[str]
    ) -> None:
        """Add a horizontal bar chart showing the most dominant themes across all companies."""
        # Calculate totals for each theme across all companies
        theme_totals = df[theme_columns].sum()
        theme_names = theme_totals.index.tolist()
        theme_values = theme_totals.values.tolist()

        # Sort themes by value (descending)
        sorted_indices = np.argsort(theme_values)[::-1]
        top_themes = [theme_names[i] for i in sorted_indices]
        top_values = [theme_values[i] for i in sorted_indices]

        fig.add_trace(
            go.Bar(
                y=top_themes,
                x=top_values,
                orientation="h",
                marker=dict(
                    color=top_values,
                    colorscale=self.config["themes_colorscale"],
                    showscale=False,
                ),
                text=top_values,
                textposition="outside",
                textfont=dict(size=self.config["text_font_size"]),
            ),
            row=4,
            col=1,
        )

    def _create_industry_analysis(
        self, df: pd.DataFrame, theme_columns: List[str]
    ) -> go.Figure:
        """Create a separate heatmap showing average thematic scores by industry."""
        industry_col = self.config["industry_column"]

        # Group by industry and calculate mean scores
        industry_data = []

        for industry, group in df.groupby(industry_col):
            for theme in theme_columns:
                industry_data.append(
                    {"Industry": industry, "Theme": theme, "Score": group[theme].mean()}
                )

        industry_df = pd.DataFrame(industry_data)

        # Create a pivot table for the heatmap
        industry_pivot = industry_df.pivot(
            index="Industry", columns="Theme", values="Score"
        )

        # Create the industry analysis figure
        industry_fig = go.Figure(
            data=go.Heatmap(
                z=industry_pivot.values,
                x=industry_pivot.columns,
                y=industry_pivot.index,
                colorscale=self.config["industry_colorscale"],
                text=np.round(industry_pivot.values, 1),
                texttemplate="%{text}",
            )
        )

        # Format the industry analysis figure
        industry_fig.update_layout(
            title=self.config["industry_title"],
            height=self.config["industry_height"],
            width=self.config["industry_width"],
            margin=self.config["industry_margin"],
        )

        return industry_fig

    def _format_dashboard_layout(self, fig: go.Figure) -> None:
        """Format the dashboard layout with appropriate titles, margins, and axis labels."""
        axis_titles = self.config["axis_titles"]

        # Update overall layout
        fig.update_layout(
            height=self.config["dashboard_height"],
            width=self.config["dashboard_width"],
            title_text=self.config["main_title"],
            showlegend=False,
            margin=self.config["main_margin"],
        )

        # Update axis titles and formatting
        fig.update_xaxes(
            title_text="",
            row=1,
            col=1,
            tickangle=self.config["tick_angle"],
            tickfont=dict(size=self.config["tick_font_size"]),
            automargin=True,
        )
        fig.update_yaxes(
            title_text=axis_titles["company"], row=1, col=1, automargin=True
        )
        fig.update_xaxes(
            title_text=axis_titles["total_score"], row=2, col=1, automargin=True
        )
        fig.update_yaxes(title_text="", row=2, col=1)
        fig.update_xaxes(title_text="", row=3, col=1, automargin=True)
        fig.update_yaxes(title_text=axis_titles["theme"], row=3, col=1)
        fig.update_xaxes(
            title_text=axis_titles["total_score_across"], row=4, col=1, automargin=True
        )
