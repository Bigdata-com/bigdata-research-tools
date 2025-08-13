from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from bigdata_research_tools.settings import check_libraries_installed
from bigdata_research_tools.visuals.visuals import ExposureDashboard


def check_plotly_dependencies() -> bool:
    """
    Check if the required Plotly dependencies are installed.
    Will look for the `plotly` package.
    """
    return check_libraries_installed(["plotly"])


class RiskExposureDashboard(ExposureDashboard):
    """
    A configurable dashboard for analyzing risk exposure of companies.
    """

    default_config = {
        # Column names
        "sector_column": "Sector",
        "theme_start_col": 4,  # Index where theme columns start
        "theme_end_col": -1,  # Index where theme columns end
        # Titles
        "main_title": "Risk Exposure Analysis Dashboard",
        "industry_title": "Industry-Level Risk Exposure (Average Scores)",
        "subplot_titles": [
            "Risk Exposure Heatmap (Raw Scores)",
            "Total Risk Exposure Score",
            "Top Risk Exposures by Company",
            "Risk Exposure Scores across Sub-Themes",
        ],
        "axis_titles": {
            "company": "Company",
            "theme": "Sub-Scenario",
            "total_score": "Total Score",
            "total_score_across": "Total Score Across Companies",
        },
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the dashboard with configuration parameters.

        Parameters:
        -----------
        config : dict, optional
            Configuration dictionary with dashboard settings
        """
        # Merge: parent base_config -> subclass default_config -> user config
        merged = {**self.base_config, **self.default_config, **(config or {})}
        super().__init__(merged)


def create_risk_exposure_dashboard(
    df_company: pd.DataFrame,
    n_companies: int = 10,
    config: Optional[Dict[str, Any]] = None,
) -> Tuple[go.Figure, go.Figure]:
    """
    Creates a comprehensive dashboard for analyzing risk exposure of companies.

    Parameters:
    -----------
    df_company : pandas.DataFrame
        DataFrame containing company data with columns for 'Company', 'Industry',
        'Composite Score', and multiple risk exposure columns.
    n_companies : int, default=10
        Number of companies to include in the analysis.
    config : dict, optional
        Configuration dictionary to customize the dashboard appearance and behavior

    Returns:
    --------
    tuple
        A tuple containing two Plotly figures:
        - Main dashboard with four panels (heatmap, bar chart, scatter, bar chart)
        - Industry-level analysis heatmap
    """
    if not check_plotly_dependencies():
        raise ImportError(
            "Required Plotly dependencies are not installed. Please install 'plotly' package."
        )
    else:
        dashboard = RiskExposureDashboard(config)
        return dashboard.create_dashboard(df_company, n_companies)
