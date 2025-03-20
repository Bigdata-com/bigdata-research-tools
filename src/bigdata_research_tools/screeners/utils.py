from typing import List

from pandas import DataFrame

from bigdata_research_tools.excel import ExcelManager, check_excel_dependencies


def get_scored_df(
    df: DataFrame, index_columns: List[str], pivot_column: str
) -> DataFrame:
    """
    Calculate a Composite Score by pivoting the received DataFrame.

    Args:
        df: The DataFrame to pivot.
        index_columns: The index columns to use for the pivot.
        pivot_column: The column to pivot. Different values of this column
            will be used as columns in the pivoted DataFrame. The Composite
            Score will be calculated by summing the values of these columns.
    Returns:
        The pivoted DataFrame with the Composite Score.
        Columns:
            - The index columns.
            - The values of the pivot_column.
            - The Composite Score.
    """
    df_pivot = df.pivot_table(
        df, index=index_columns, columns=pivot_column, aggfunc="size", fill_value=0
    )
    df_pivot["Composite Score"] = df_pivot.sum(axis=1)
    df_pivot = df_pivot.reset_index()
    df_pivot.columns.name = None
    df_pivot.index.name = None
    df_pivot = df_pivot.sort_values(by="Composite Score", ascending=False).reset_index(
        drop=True
    )
    return df_pivot


def save_factor_to_excel(
    file_path: str,
    df_company: DataFrame,
    df_industry: DataFrame,
    df_semantic_labels: DataFrame,
) -> None:
    """
    Save the factor functions output to an Excel file.

    Args:
        file_path: The path to the Excel file.
        df_company: The DataFrame with the output by company.
        df_industry: The DataFrame with the output by industry.
        df_semantic_labels: The DataFrame with the semantic labels.

    Returns:
        None.
    """
    if file_path and check_excel_dependencies():
        excel_manager = ExcelManager()

        excel_args = [
            (df_company, "By Company", (2, 4)),
            (df_industry, "By Industry", (2, 2)),
            (df_semantic_labels, "Semantic Labels", (0, 0)),
        ]
        excel_manager.save_workbook(excel_args, file_path)
        excel_manager.beautify_workbook(file_path)
