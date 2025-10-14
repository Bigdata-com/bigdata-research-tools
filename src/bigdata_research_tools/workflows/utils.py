"""
Script with any common helper functions used across the workflows.
"""

from pandas import DataFrame


def get_scored_df(
    df: DataFrame, index_columns: list[str], pivot_column: str
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
