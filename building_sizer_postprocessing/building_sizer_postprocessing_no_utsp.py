"""Module for postprocessing building sizer results."""

import sys
from pathlib import Path
import pandas as pd
from typing import List
from dataclasses import dataclass, fields

# Add the parent directory to the system path
sys.path.append("/fast/home/k-rieck/repositories/HiSim")
from hisim.building_sizer_utils.interface_configs.kpi_config import (
    KPIConfig,
    KPIForRatingInOptimization,
)


def go_through_parent_folder_and_find_all_building_sizer_results(
    parent_folder: str, file_name: str = "building_sizer_results.csv"
):
    parent_folder = Path(parent_folder)
    bs_result_csv_files = list(parent_folder.rglob(file_name))
    if not bs_result_csv_files:
        raise ValueError(
            f"Could not find any {file_name} in parent folder {str(parent_folder)}"
        )
    return bs_result_csv_files


def get_min_row_for_column(file_path: Path, column: str) -> pd.Series | None:
    """Read a csv file and return the row with the minimum value for a given column."""
    try:
        df = pd.read_csv(file_path)
        if column not in df.columns:
            print(f"Column {column} not found in {file_path}")
            return None
        # identify row with minimum value of column
        min_row = df.loc[df[column].idxmin()].copy()
        # add filepath to source_file column
        min_row["source_file"] = str(file_path)
        return min_row
    except Exception as e:
        print(f"Error reading and processing {file_path}: {e}")
        return None


def collect_min_rows(files: List[Path], column: str) -> pd.DataFrame:
    """Collect minimum rows for a given column from a list of files."""
    collected = []
    for file_path in files:
        row = get_min_row_for_column(file_path, column)
        if row is not None:
            collected.append(row)
    return pd.DataFrame(collected)


def save_minima_to_csv(df: pd.DataFrame, column: str, output_dir: Path) -> None:
    """Save the collected minima DataFrame to a csv file."""
    output_file = output_dir / f"all_min_{column}.csv"
    df.to_csv(output_file, index=False)
    print(f"Saved minima for column {column} to: {output_file}")


def run_minima_extraction(
    parent_folder: Path,
    columns: List[str],
    filename: str = "building_sizer_results.csv",
) -> None:
    """Run the full process for all target columns."""
    files = go_through_parent_folder_and_find_all_building_sizer_results(
        parent_folder, filename
    )
    for column in columns:
        result_df = collect_min_rows(files, column)
        if not result_df.empty:
            save_minima_to_csv(result_df, column, parent_folder)
        else:
            print(f"No data found for column: {column}")


# ---------- Run It ----------
if __name__ == "__main__":
    PARENT_FOLDER = Path(
        "/fast/home/k-rieck/hisim_building_clustering/test_results/F_hisim_building_sizer_optimization/2/bs_requests_20250804_2139"
    )
    kpi_config_fields = [f.name for f in fields(KPIConfig)]
    print(kpi_config_fields)
    COLUMNS_OF_INTEREST = kpi_config_fields  # Add more as needed

    run_minima_extraction(PARENT_FOLDER, COLUMNS_OF_INTEREST)
