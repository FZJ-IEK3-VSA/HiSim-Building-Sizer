"""Module for postprocessing building sizer results."""

import sys
from pathlib import Path
import pandas as pd
from typing import List
from dataclasses import dataclass, fields
import matplotlib.pyplot as plt
import seaborn as sns
import re

# Add the parent directory to the system path
sys.path.append("/fast/home/k-rieck/repositories/HiSim")
from hisim.building_sizer_utils.interface_configs.kpi_config import (
    KPIConfig,
    KPIForRatingInOptimization,
)

@dataclass
class PrettyKpiLabels:
    """Class for generating pretty kpi labels."""
    kpi_column: str
    min_or_max_winner: str
    def __post_init__(self):
        self.pretty_label = self.make_pretty_label(kpi_column=self.kpi_column)
        self.multiindex_output_column = self.make_multiindex_output_column(kpi_column=self.kpi_column)


    def make_pretty_label(self, kpi_column):
        """Make pretty label."""
        # Simple approach
        label = kpi_column.replace("_", " ").title()  # "Annualized Total Costs In Euro Per M2"

        # Optional: make units nicer
        label = label.replace("In Euro Per M2", "[€/m²]")
        label = label.replace("In Kg Per M2", "[kgCO2/m²]")
        label = label.replace("In Kwh Per M2", "[kWh/m²]")
        label = label.replace("In Celsius", "[°C]")
        label = label.replace("In Celsius Hour", "[°C*h]")
        label = label.replace("In Percent", "[%]")
        label = label.replace("In Euro", "[€]")
        return label

    def make_multiindex_output_column(self, kpi_column):
        """Make multiindex output column."""
        mulitindex_output_column = ("Output", kpi_column)
        return mulitindex_output_column
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


def get_min_or_max_row_for_column(df: pd.DataFrame, file_path: Path, column: str, find_min_or_max: str) -> pd.Series | None:
    """Read a csv file and return the row with the minimum or maximum value for a given column."""
    input_columns = [col for col in df.columns if col[0] == "Input"]

    if find_min_or_max == "min":
        # identify row with minimum value of column
        # selected_row = df.loc[df[column].idxmin()].copy()
        selected_row = df.loc[df[column].idxmin(),  input_columns + [column]]
    elif find_min_or_max == "max":
        # identify row with maximum value of column
        # selected_row = df.loc[df[column].idxmax()].copy()
        selected_row = df.loc[df[column].idxmax(),  input_columns + [column]]
    else:
        raise ValueError("Need min or max option.")

    # add filepath to source_file column
    selected_row[("Input", "source_file")] = str(file_path)
    return selected_row


def read_building_sizer_results(file_path: Path):
    """read building sizer results."""
    # read csv
    try:
        df = pd.read_csv(file_path, header=[0, 1])  # Expecting MultiIndex columns

        return df
    except Exception as e:
        print(f"Error reading and processing {file_path}: {e}")
        return None


def collect_building_sizer_results_and_find_kpi_winners(files: List[Path], kpi_column: PrettyKpiLabels, parent_folder: Path,):
    """Collect building sizer results and find kpi winners."""
    collected_rows = []
    for file_path in files:
        # read each buildig sizer result
        df = read_building_sizer_results(file_path=file_path)
        # find row with min or max value
        selected_row = get_min_or_max_row_for_column(df=df, file_path=file_path, column=kpi_column.multiindex_output_column, find_min_or_max=kpi_column.min_or_max_winner)
        if selected_row is not None:
            collected_rows.append(selected_row)

    # make df out of selected rows
    df_selected_rows = pd.DataFrame(collected_rows)
    # save as csv
    save_minima_or_maxima_to_csv(df=df_selected_rows, column=kpi_column.kpi_column, output_dir=parent_folder, find_min_or_max=kpi_column.min_or_max_winner)
    del df_selected_rows


def save_minima_or_maxima_to_csv(df: pd.DataFrame, column: str, output_dir: Path, find_min_or_max: str) -> None:
    """Save the collected minima or maxima DataFrame to a csv file."""
    output_file = output_dir / f"all_{find_min_or_max}_{column}.csv"
    df.to_csv(output_file, index=False)
    print(f"Saved {find_min_or_max} for column {column} to: {output_file}")


def find_kpi_winners_for_all_buildings(
    parent_folder: Path,
    kpi_columns: List[PrettyKpiLabels],
    filename: str = "building_sizer_results.csv",
) -> None:
    """Find for all building archetypes of one bs request the kpi winners.

    Choose the kpi you want to filter and if you want to find minimum or maximum values.
    """

    files = go_through_parent_folder_and_find_all_building_sizer_results(
        parent_folder, filename
    )

    for kpi_column in kpi_columns:
        collect_building_sizer_results_and_find_kpi_winners(files=files, kpi_column=kpi_column, parent_folder=parent_folder)
        

 # --------------------------------

def collect_all_bs_results_and_plot(
    parent_folder: Path,
    kpi_columns: List[PrettyKpiLabels],
    filename: str = "building_sizer_results.csv",):
    files = go_through_parent_folder_and_find_all_building_sizer_results(
        parent_folder, filename
    )
    for kpi_column in kpi_columns:
        df_collected = collect_building_sizer_results(files=files, kpi_column=kpi_column)
        filter_by_building_type(df=df_collected, parent_folder=parent_folder, kpi_column=kpi_column)

def filter_by_building_type(df: pd.DataFrame, parent_folder: Path, kpi_column: PrettyKpiLabels, building_code_column: str = ("Input", "building_code"), hue_column: str = ("Input", "building_id"), energy_system_column: tuple = ("Input", "energy_system_combination")):
    buildig_types = ["SFH", "TH", "MFH", "AB"]

    for b_type in buildig_types:
        b_type_folder = parent_folder / b_type
        b_type_folder.mkdir(parents=True, exist_ok=True)
        filtered_df = df[df[building_code_column].str.contains(b_type)]
        filtered_sorted_df = sort_df_according_to_one_building(df=filtered_df, kpi_column=kpi_column, energy_system_column=energy_system_column, building_code_column=building_code_column, reference_house="001.002")
        filtered_sorted_df.to_csv(b_type_folder / f"filtered_df_{b_type}.csv", index=False)
        plot_ratings_of_each_energy_system_config_as_scatterplot(df=filtered_sorted_df, output_dir=b_type_folder, kpi_column=kpi_column, building_type=b_type, hue_column=hue_column, energy_system_column=energy_system_column)

def sort_df_according_to_one_building(df: pd.DataFrame, kpi_column: PrettyKpiLabels, energy_system_column: str, reference_house: str, building_code_column: str = ("Input", "building_code")):
    # Get the systems used by the reference house
    reference_df = df[df[building_code_column].str.contains(reference_house)]

    # Sort those systems by KPI
    if kpi_column.min_or_max_winner == "min":
        ascending = False
    elif kpi_column.min_or_max_winner == "max":
        ascending = True
    else:
        raise ValueError(f"Unvalid value for min_or_max_winner: {kpi_column.min_or_max_winner}")

    sorted_reference_systems = (
        reference_df.sort_values(by=kpi_column.multiindex_output_column, ascending=ascending)[energy_system_column].tolist()
    )
    # print("len sorted ref systems,", len(sorted_reference_systems))

    # Ensure unique and preserve order
    sorted_reference_systems = list(dict.fromkeys(sorted_reference_systems))
    # print("len sorted ref systems,", len(sorted_reference_systems))

    # Get all unique systems in full dataset
    all_systems = df[energy_system_column].unique().tolist()
    # print("all systems", len(all_systems))
    
    # Find the ones not in the reference house
    remaining_systems = [s for s in all_systems if s not in sorted_reference_systems]
    # print("remaining systems", len(remaining_systems))
    
    # Sort them (optional: alphabetically)
    remaining_systems_sorted = sorted(remaining_systems)

    # Combine
    final_system_order = sorted_reference_systems + remaining_systems_sorted
    # print("final systems", len(final_system_order))

    # Apply Categorical sorting
    df = df.copy()
    df[energy_system_column] = pd.Categorical(
        df[energy_system_column],
        categories=final_system_order,
        ordered=True
    )
    # print(df[("Input", "building_code")].value_counts())
    ref_systems = set(df[df[("Input", "building_code")].str.contains(reference_house)][("Input", "energy_system_combination")])
    all_systems = set(df[("Input", "energy_system_combination")].unique())

    missing = all_systems - ref_systems

    if missing:
        print(f"Reference house {reference_house} is missing these systems:", missing)
    return df

def natural_sort_key(s):
    """Sort strings like 'AB.001.002' in natural order."""
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split('([0-9]+)', str(s))]


def plot_ratings_of_each_energy_system_config_as_scatterplot(
    df: pd.DataFrame,
    output_dir: Path,
    kpi_column: PrettyKpiLabels,
    building_type: str,
    hue_column: tuple,
    energy_system_column: tuple = ("Input", "energy_system_combination"),
) -> None:
    """
    Generate scatter plot for all energy system configs and their ratings.
    """
    # Sort hue values naturally (e.g., AB.001.001 < AB.001.010)
    sorted_hues = sorted(df[hue_column].unique(), key=natural_sort_key)
    df = df.copy()
    df[hue_column] = pd.Categorical(df[hue_column], categories=sorted_hues, ordered=True)

    # Create larger figure
    fig = plt.figure(figsize=(22, 7))
    ax = fig.add_subplot(111)

    # Set labels
    ax.set_xlabel("Energy system combination")
    ax.set_ylabel(kpi_column.pretty_label)
    # Enable y-axis grid
    ax.yaxis.grid(True, linestyle='--', alpha=0.7)

    # Lineplot: lines between same hue values
    sns.lineplot(
        data=df,
        x=energy_system_column,
        y=kpi_column.multiindex_output_column,
        hue=hue_column,
        marker='o',
        linewidth=1,
        markersize=5,
        ax=ax,
        legend=False
    )

    # Scatterplot: for legend and point emphasis
    sns.scatterplot(
        data=df,
        x=energy_system_column,
        y=kpi_column.multiindex_output_column,
        hue=hue_column,
        s=30,
        ax=ax,
        legend=True
    )

    # Rotate and resize x-ticks
    plt.xticks(rotation=45, ha="right", fontsize=8)
    

    # Move legend outside
    ax.legend(
        title=hue_column[1] if isinstance(hue_column, tuple) else hue_column,
        loc='best',
        frameon=True
    )

    # Adjust layout
    plt.tight_layout()

    # Save figure
    filepath = output_dir / f"{kpi_column.kpi_column}_per_energy_system_{building_type}.png"
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    print("Made plot for", kpi_column.kpi_column, building_type, " and saved here: ", filepath, "\n")

def save_collected_results_to_csv(df: pd.DataFrame, column: str, output_dir: Path,) -> None:
    """Save the collected minima or maxima DataFrame to a csv file."""
    output_file = output_dir / f"all_bs_results_{column}.csv"
    df.to_csv(output_file, index=False)
    print(f"Saved all bs results for column {column} to: {output_file}")

def get_kpi_for_energy_system_combination_and_append_to_collection(df: pd.DataFrame, kpi_column: str, building_column: str = ("Input", "building_id"), energy_system_column: str = ("Input", "energy_system_combination")):
    """Get kpi the energy system combination of each result and append to collection."""

    df_subset = df[[building_column, energy_system_column, kpi_column]]
    df_subset = df.sort_values(by=[kpi_column])
    return df_subset

def collect_building_sizer_results(files: List[Path], kpi_column: PrettyKpiLabels):
    collected_dfs = []
    for file_path in files:
        # read each buildig sizer result
        df = read_building_sizer_results(file_path=file_path)
        # filter df
        # Get all input columns
        input_cols = df.loc[:, df.columns.get_level_values(0) == "Input"]

        # Select one output column
        kpi_df = df.loc[:, [kpi_column.multiindex_output_column]]

        # Combine them into one DataFrame
        filtered_df = pd.concat([input_cols, kpi_df], axis=1)

        if not filtered_df.empty:
            collected_dfs.append(filtered_df)

    # make df out of selected dfs
    df_collected = pd.concat(collected_dfs, axis=0)
    return df_collected


# ---------- Run It ----------
if __name__ == "__main__":
    PARENT_FOLDER = Path(
        "/fast/home/k-rieck/hisim_building_clustering/test_results/test_building_types/F_hisim_building_sizer_optimization/0/2050/bs_requests_20250813_1435"
    )
    # -------------------------------------------------------------------------------
    # Find min values
    FIND_MIN_OR_MAX = "min"
    kpi_config_fields_min = ["annualized_total_costs_in_euro_per_m2", "annualized_energy_costs_in_euro_per_m2", "annualized_net_investment_costs_in_euro_per_m2", "annualized_total_co2_emissions_in_kg_per_m2", "annualized_energy_co2_emissions_in_kg_per_m2", "annualized_purchased_energy_consumption_in_kwh_per_m2", "total_upfront_net_investment_costs_in_euro"]

    column_of_interest_min = [PrettyKpiLabels(kpi_column=kpi_field, min_or_max_winner=FIND_MIN_OR_MAX) for kpi_field in kpi_config_fields_min]
    COLUMNS_OF_INTEREST = column_of_interest_min  # Add more as needed

    find_kpi_winners_for_all_buildings(parent_folder=PARENT_FOLDER, kpi_columns=COLUMNS_OF_INTEREST)

    # -------------------------------------------------------------------------------
    # Find max values
    FIND_MIN_OR_MAX = "max"
    kpi_config_fields_max = ["self_sufficiency_rate_all_energy_in_percent"]

    column_of_interest_max = [PrettyKpiLabels(kpi_column=kpi_field, min_or_max_winner=FIND_MIN_OR_MAX) for kpi_field in kpi_config_fields_max]
    COLUMNS_OF_INTEREST = column_of_interest_max  # Add more as needed

    find_kpi_winners_for_all_buildings(parent_folder=PARENT_FOLDER, kpi_columns=COLUMNS_OF_INTEREST)

    # -------------------------------------------------------------------------------
    # Collect all bs results and tranpsose
    COLUMNS_OF_INTEREST = column_of_interest_min + column_of_interest_max
    collect_all_bs_results_and_plot(parent_folder=PARENT_FOLDER, kpi_columns=COLUMNS_OF_INTEREST)

