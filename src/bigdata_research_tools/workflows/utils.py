"""
Script with any common helper functions used across the workflows.
"""
from bigdata_client.models.search import DocumentType
from typing import List, Optional
from pandas import DataFrame
from bigdata_research_tools.excel import ExcelManager, check_excel_dependencies

def validate_params(**kwargs):
    """Validates parameters based on predefined rules."""

    document_scope = kwargs.get('document_scope')
    fiscal_year = kwargs.get('fiscal_year')

    # Skip validation if document_scope is not provided
    if document_scope is None:
        return

    if document_scope in [DocumentType.FILINGS, DocumentType.TRANSCRIPTS]:
        if fiscal_year is None:
            raise ValueError(f"fiscal_year is required when document_scope is {document_scope.value}")

    if document_scope == DocumentType.NEWS:
        if fiscal_year is not None:
            raise ValueError(f"fiscal_year must be None when document_scope is {document_scope.value}")

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


def save_to_excel(
    file_path: str,
    tables: dict[str, tuple[DataFrame, tuple[int, int]]],
) -> None:
    """
    Save multiple DataFrames to an Excel file using ExcelManager.

    Args:
        file_path: Destination path for the Excel file.
        tables: A dict mapping sheet names to (DataFrame, position) tuples.

    Returns:
        None.
    """
    if not file_path or not check_excel_dependencies():
        return

    excel_manager = ExcelManager()

    excel_args = [
        (df, sheet_name, position)
        for sheet_name, (df, position) in tables.items()
    ]

    excel_manager.save_workbook(excel_args, file_path)