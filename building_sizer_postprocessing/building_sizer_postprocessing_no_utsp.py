"""Module for postprocessing building sizer results."""

import sys
from pathlib import Path
import pandas as pd
from typing import List, Optional
from dataclasses import dataclass
import matplotlib.pyplot as plt
import seaborn as sns
import re
import textwrap
from matplotlib.colors import rgb2hex

# Add the parent directory to the system path
sys.path.append("/fast/home/k-rieck/repositories/HiSim")
from hisim.postprocessing.chartbase import ChartFontsAndSize

energy_system_map = {
    "DistrictHeating + Conventional Radiator + PV 0% + NoBatteryAndEMS": 1,
    "DistrictHeating + Conventional Radiator + PV 100% + NoBatteryAndEMS": 2,
    "DistrictHeating + Conventional Radiator + PV 100% + WithBatteryAndEMS": 3,
    "DistrictHeating + Floorheating + PV 0% + NoBatteryAndEMS": 4,
    "DistrictHeating + Floorheating + PV 100% + NoBatteryAndEMS": 5,
    "DistrictHeating + Floorheating + PV 100% + WithBatteryAndEMS": 6,
    "ElectricHeating + No HDS + PV 0% + NoBatteryAndEMS": 7,
    "ElectricHeating + No HDS + PV 100% + NoBatteryAndEMS": 8,
    "ElectricHeating + No HDS + PV 100% + WithBatteryAndEMS": 9,
    "GasHeating + Conventional Radiator + PV 0% + NoBatteryAndEMS": 10,
    "GasHeating + Conventional Radiator + PV 100% + NoBatteryAndEMS": 11,
    "GasHeating + Conventional Radiator + PV 100% + WithBatteryAndEMS": 12,
    "GasHeating + Floorheating + PV 0% + NoBatteryAndEMS": 13,
    "GasHeating + Floorheating + PV 100% + NoBatteryAndEMS": 14,
    "GasHeating + Floorheating + PV 100% + WithBatteryAndEMS": 15,
    "GasSolarThermal + Conventional Radiator + PV 0% + NoBatteryAndEMS": 16,
    "GasSolarThermal + Conventional Radiator + PV 100% + NoBatteryAndEMS": 17,
    "GasSolarThermal + Conventional Radiator + PV 100% + WithBatteryAndEMS": 18,
    "GasSolarThermal + Floorheating + PV 0% + NoBatteryAndEMS": 19,
    "GasSolarThermal + Floorheating + PV 100% + NoBatteryAndEMS": 20,
    "GasSolarThermal + Floorheating + PV 100% + WithBatteryAndEMS": 21,
    "HeatPump + Conventional Radiator + PV 0% + NoBatteryAndEMS": 22,
    "HeatPump + Conventional Radiator + PV 100% + NoBatteryAndEMS": 23,
    "HeatPump + Conventional Radiator + PV 100% + WithBatteryAndEMS": 24,
    "HeatPump + Floorheating + PV 0% + NoBatteryAndEMS": 25,
    "HeatPump + Floorheating + PV 100% + NoBatteryAndEMS": 26,
    "HeatPump + Floorheating + PV 100% + WithBatteryAndEMS": 27,
    "HeatPumpSolarThermal + Conventional Radiator + PV 0% + NoBatteryAndEMS": 28,
    "HeatPumpSolarThermal + Conventional Radiator + PV 100% + NoBatteryAndEMS": 29,
    "HeatPumpSolarThermal + Conventional Radiator + PV 100% + WithBatteryAndEMS": 30,
    "HeatPumpSolarThermal + Floorheating + PV 0% + NoBatteryAndEMS": 31,
    "HeatPumpSolarThermal + Floorheating + PV 100% + NoBatteryAndEMS": 32,
    "HeatPumpSolarThermal + Floorheating + PV 100% + WithBatteryAndEMS": 33,
    "HydrogenHeating + Conventional Radiator + PV 0% + NoBatteryAndEMS": 34,
    "HydrogenHeating + Conventional Radiator + PV 100% + NoBatteryAndEMS": 35,
    "HydrogenHeating + Conventional Radiator + PV 100% + WithBatteryAndEMS": 36,
    "HydrogenHeating + Floorheating + PV 0% + NoBatteryAndEMS": 37,
    "HydrogenHeating + Floorheating + PV 100% + NoBatteryAndEMS": 38,
    "HydrogenHeating + Floorheating + PV 100% + WithBatteryAndEMS": 39,
    "OilHeating + Conventional Radiator + PV 0% + NoBatteryAndEMS": 40,
    "OilHeating + Conventional Radiator + PV 100% + NoBatteryAndEMS": 41,
    "OilHeating + Conventional Radiator + PV 100% + WithBatteryAndEMS": 42,
    "OilHeating + Floorheating + PV 0% + NoBatteryAndEMS": 43,
    "OilHeating + Floorheating + PV 100% + NoBatteryAndEMS": 44,
    "OilHeating + Floorheating + PV 100% + WithBatteryAndEMS": 45,
    "PelletHeating + Conventional Radiator + PV 0% + NoBatteryAndEMS": 46,
    "PelletHeating + Conventional Radiator + PV 100% + NoBatteryAndEMS": 47,
    "PelletHeating + Conventional Radiator + PV 100% + WithBatteryAndEMS": 48,
    "PelletHeating + Floorheating + PV 0% + NoBatteryAndEMS": 49,
    "PelletHeating + Floorheating + PV 100% + NoBatteryAndEMS": 50,
    "PelletHeating + Floorheating + PV 100% + WithBatteryAndEMS": 51,
}


@dataclass
class PrettyKpiLabels:
    """Class for generating pretty kpi labels."""

    kpi_column: str
    min_or_max_winner: str

    def __post_init__(self):
        self.pretty_label = self.make_pretty_label(kpi_column=self.kpi_column)
        self.multiindex_output_column = self.make_multiindex_output_column(
            kpi_column=self.kpi_column
        )
        self.unit = self.find_unit(pretty_label=self.pretty_label)

    def make_pretty_label(self, kpi_column):
        """Make pretty label."""
        # Simple approach
        label = kpi_column.replace(
            "_", " "
        ).title()  # "Annualized Total Costs In Euro Per M2"

        # Optional: make units nicer
        label = label.replace("In Euro Per M2", "[€/m²]")
        label = label.replace("In Kg Per M2", "[kgCO2/m²]")
        label = label.replace("In Kwh Per M2", "[kWh/m²]")
        label = label.replace("In Celsius Hour", "[°C*h]")
        label = label.replace("In Celsius", "[°C]")
        label = label.replace("In Percent", "[%]")
        label = label.replace("In Euro", "[€]")
        label = label.replace("In Keuro", "[k€]")
        return label

    def make_multiindex_output_column(self, kpi_column):
        """Make multiindex output column."""
        mulitindex_output_column = ("Output", kpi_column)
        return mulitindex_output_column

    def find_unit(self, pretty_label: str):
        """Find unit."""
        # Extract the content in brackets, including the brackets
        match = re.search(r"\[.*?\]", pretty_label)
        if match:
            unit = match.group(0)  # includes brackets: "[€/m²]"
        else:
            unit = ""
        return unit


class BuildingSizerPostprocessor:
    """BuildingSizerPostprocessor. Use for analyzing and visualizing the bs results."""

    def __init__(
        self,
        input_folder: str,
        output_folder: Optional[str],
        columns_of_interest: List[PrettyKpiLabels],
        year: str,
    ):
        """Init function."""
        # set folders
        self.input_folder = Path(input_folder)
        if output_folder is None:
            self.output_folder = self.input_folder
        else:
            self.output_folder = Path(output_folder)
            self.output_folder.mkdir(parents=True, exist_ok=True)

        self.hisim_chartbase = ChartFontsAndSize()
        self.hisim_chartbase.figsize = (6, 4)
        self.hisim_chartbase.dpi = 100
        self.hisim_chartbase.fontsize_legend = 10
        self.year = year

        # find kpi winner among the bs results
        self.find_kpi_winners_for_all_buildings(kpi_columns=columns_of_interest)
        # collect bs results, sort according to building types and make plots
        self.collect_all_bs_results_and_plot(kpi_columns=columns_of_interest)

    def go_through_input_folder_and_find_all_building_sizer_results(
        self, file_name: str = "building_sizer_results.csv"
    ):
        bs_result_csv_files = list(self.input_folder.rglob(file_name))
        if not bs_result_csv_files:
            raise ValueError(
                f"Could not find any {file_name} in parent folder {str(self.input_folder)}"
            )
        print(f"Found {len(bs_result_csv_files)} building sizer result files.")
        return bs_result_csv_files

    def get_min_or_max_row_for_column(
        self, df: pd.DataFrame, file_path: Path, column: str, find_min_or_max: str
    ) -> pd.Series | None:
        """Read a csv file and return the row with the minimum or maximum value for a given column."""
        input_columns = [col for col in df.columns if col[0] == "Input"]

        if find_min_or_max == "min":
            # identify row with minimum value of column
            # selected_row = df.loc[df[column].idxmin()].copy()
            selected_row = df.loc[df[column].idxmin(), input_columns + [column]]
        elif find_min_or_max == "max":
            # identify row with maximum value of column
            # selected_row = df.loc[df[column].idxmax()].copy()
            selected_row = df.loc[df[column].idxmax(), input_columns + [column]]
        else:
            raise ValueError("Need min or max option.")

        # add filepath to source_file column
        selected_row[("Input", "source_file")] = str(file_path)
        return selected_row

    def read_building_sizer_results(self, file_path: Path):
        """read building sizer results."""
        # read csv
        try:
            df = pd.read_csv(file_path, header=[0, 1])  # Expecting MultiIndex columns

            return df
        except Exception as e:
            print(f"Error reading and processing {file_path}: {e}")
            return None

    def collect_building_sizer_results_and_find_kpi_winners(
        self, files: List[Path], kpi_column: PrettyKpiLabels
    ):
        """Collect building sizer results and find kpi winners."""
        collected_rows = []
        for file_path in files:
            # read each buildig sizer result
            df = self.read_building_sizer_results(file_path=file_path)
            # find row with min or max value
            selected_row = self.get_min_or_max_row_for_column(
                df=df,
                file_path=file_path,
                column=kpi_column.multiindex_output_column,
                find_min_or_max=kpi_column.min_or_max_winner,
            )
            if selected_row is not None:
                collected_rows.append(selected_row)

        # make df out of selected rows
        df_selected_rows = pd.DataFrame(collected_rows)
        # save as csv
        self.save_minima_or_maxima_to_csv(
            df=df_selected_rows,
            column=kpi_column.kpi_column,
            find_min_or_max=kpi_column.min_or_max_winner,
        )
        return df_selected_rows

    def save_minima_or_maxima_to_csv(
        self, df: pd.DataFrame, column: str, find_min_or_max: str
    ) -> None:
        """Save the collected minima or maxima DataFrame to a csv file."""
        output_file = (
            self.output_folder / f"all_{self.year}_{find_min_or_max}_{column}.csv"
        )
        df.to_csv(output_file, index=False)
        print(f"Saved {find_min_or_max} for column {column} to: {output_file}")

    def find_kpi_winners_for_all_buildings(
        self,
        kpi_columns: List[PrettyKpiLabels],
        filename: str = "building_sizer_results.csv",
    ) -> None:
        """Find for all building archetypes of one bs request the kpi winners.

        Choose the kpi you want to filter and if you want to find minimum or maximum values.
        """

        files = self.go_through_input_folder_and_find_all_building_sizer_results(
            filename
        )
        with pd.ExcelWriter(
            self.output_folder / f"resume_all_kpi_winners_{self.year}.xlsx",
            engine="openpyxl",
        ) as writer:
            for kpi_column in kpi_columns:
                # find kpi winners
                df_selected_rows = (
                    self.collect_building_sizer_results_and_find_kpi_winners(
                        files=files, kpi_column=kpi_column
                    )
                )
                # write winners to excel sheet
                sheet_name = str(kpi_column.kpi_column)[
                    :31
                ]  # (Excel sheet names max 31 chars)
                df_selected_rows.to_excel(writer, sheet_name=sheet_name, index=True)

    def collect_all_bs_results_and_plot(
        self,
        kpi_columns: List[PrettyKpiLabels],
        filename: str = "building_sizer_results.csv",
    ):
        files = self.go_through_input_folder_and_find_all_building_sizer_results(
            filename
        )
        for kpi_column in kpi_columns:
            df_collected = self.collect_building_sizer_results(
                files=files, kpi_column=kpi_column
            )
            self.filter_by_building_type(df=df_collected, kpi_column=kpi_column)

    def filter_by_building_type(
        self,
        df: pd.DataFrame,
        kpi_column: PrettyKpiLabels,
        building_code_column: str = ("Input", "building_code"),
        hue_column: str = ("Input", "building_id"),
        energy_system_column: tuple = ("Input", "energy_system_combination"),
    ):
        buildig_types = ["SFH", "TH", "MFH", "AB"]

        for b_type in buildig_types:
            b_type_folder = self.output_folder / b_type
            b_type_folder.mkdir(parents=True, exist_ok=True)
            filtered_df = df[df[building_code_column].str.contains(b_type)]
            filtered_sorted_df = self.sort_df_according_to_one_building(
                df=filtered_df,
                kpi_column=kpi_column,
                energy_system_column=energy_system_column,
                building_code_column=building_code_column,
                reference_house="001.002",
            )
            filtered_sorted_df.to_csv(
                b_type_folder / f"filtered_df_{b_type}_{kpi_column.kpi_column}.csv",
                index=False,
            )
            self.plot_ratings_of_each_energy_system_config_as_scatterplot(
                df=filtered_sorted_df,
                output_dir=b_type_folder,
                kpi_column=kpi_column,
                building_type=b_type,
                hue_column=hue_column,
                energy_system_column=("Input", "energy_system_id"),
            )
            self.plot_boxplot_energy_systems(
                df=filtered_sorted_df,
                output_dir=b_type_folder,
                kpi_column=kpi_column,
                building_type=b_type,
                hue_column=hue_column,
                energy_system_column=("Input", "energy_system_id"),
            )

    def sort_df_according_to_one_building(
        self,
        df: pd.DataFrame,
        kpi_column: PrettyKpiLabels,
        energy_system_column: str,
        reference_house: str,
        building_code_column: str = ("Input", "building_code"),
    ):
        # Get the systems used by the reference house
        reference_df = df[df[building_code_column].str.contains(reference_house)]

        # Sort those systems by KPI
        if kpi_column.min_or_max_winner == "min":
            ascending = False
        elif kpi_column.min_or_max_winner == "max":
            ascending = True
        else:
            raise ValueError(
                f"Unvalid value for min_or_max_winner: {kpi_column.min_or_max_winner}"
            )

        sorted_reference_systems = reference_df.sort_values(
            by=kpi_column.multiindex_output_column, ascending=ascending
        )[energy_system_column].tolist()
        # print("len sorted ref systems,", len(sorted_reference_systems))

        # Ensure unique and preserve order
        sorted_reference_systems = list(dict.fromkeys(sorted_reference_systems))
        # print("len sorted ref systems,", len(sorted_reference_systems))

        # Get all unique systems in full dataset
        all_systems = df[energy_system_column].unique().tolist()
        # print("all systems", len(all_systems))

        # Find the ones not in the reference house
        remaining_systems = [
            s for s in all_systems if s not in sorted_reference_systems
        ]
        # print("remaining systems", len(remaining_systems))

        # Sort them (optional: alphabetically)
        remaining_systems_sorted = sorted(remaining_systems)

        # Combine
        final_system_order = sorted_reference_systems + remaining_systems_sorted
        # print("final systems", len(final_system_order))

        # Apply Categorical sorting
        df = df.copy()
        df[energy_system_column] = pd.Categorical(
            df[energy_system_column], categories=final_system_order, ordered=True
        )
        # Add new column with numeric mapping
        df[("Input", "energy_system_id")] = df[energy_system_column].map(
            energy_system_map
        )
        ref_systems = set(
            df[df[("Input", "building_code")].str.contains(reference_house)][
                ("Input", "energy_system_combination")
            ]
        )
        all_systems = set(df[("Input", "energy_system_combination")].unique())

        missing = all_systems - ref_systems

        if missing:
            print(
                f"Reference house {reference_house} is missing these systems:", missing
            )
        return df

    def natural_sort_key(self, s):
        """Sort strings like 'AB.001.002' in natural order."""
        return [
            int(text) if text.isdigit() else text.lower()
            for text in re.split("([0-9]+)", str(s))
        ]

    def plot_ratings_of_each_energy_system_config_as_scatterplot(
        self,
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
        # # Sort hue values naturally (e.g., AB.001.001 < AB.001.010)
        df, kpi_column, sorted_hues = self._prepare_plot_data(
            df=df, kpi_column=kpi_column, hue_column=hue_column
        )

        # Create larger figure
        ax = self._create_figure_and_labels(kpi_column=kpi_column)
        # reset index to avoid dubplicated indices
        df = df.reset_index(drop=True)
        # Lineplot: lines between same hue values
        unique_hues = df[hue_column].unique()
        num_hues = len(unique_hues)

        # Build the same palette Seaborn will use
        palette = sns.color_palette(n_colors=num_hues)

        # Build a hue → color mapping table
        hue_color_table = pd.DataFrame(
            {
                hue_column: unique_hues,
                "color": [rgb2hex(c) for c in palette],  # convert RGB to hex
            }
        )

        # Optional: also add counts if useful
        hue_color_table["count"] = df[hue_column].map(df[hue_column].value_counts())
        hue_color_table.to_csv(output_dir / "hue_color_table.csv")

        sns.lineplot(
            data=df,
            x=energy_system_column,
            y=kpi_column.multiindex_output_column,
            hue=hue_column,
            marker="o",
            linewidth=1,
            markersize=5,
            ax=ax,
            legend=False,
            palette=palette,
        )

        # Scatterplot: for legend and point emphasis
        # Count unique hue values
        num_hues = df[hue_column].nunique()
        sns.scatterplot(
            data=df,
            x=energy_system_column,
            y=kpi_column.multiindex_output_column,
            hue=hue_column,
            s=30,
            ax=ax,
            legend=False if num_hues > 10 else "full",  # hide legend if > 10 hues
            palette=palette,
        )

        # Make dotted vertical line after each energy system every 6 points
        x_values = sorted(energy_system_map.values())  # ensure they are in order
        x_ticks = []
        for xi in x_values[
            ::3
        ]:  # every 6th point because 9 heating systems and 54 total options -> 54/9 = 6
            ax.axvline(x=xi, color="gray", linestyle=":")
            x_ticks.append(xi)

        # Set x-axis limits and ticks
        ax.set_xlim(x_values[0] - 1, x_values[-1] + 1)
        ax.set_xticks(x_ticks)  # show ticks at all x_values

        # Rotate and resize x-ticks
        ax.set_xticklabels(
            x_ticks,
            rotation=45,
            ha="right",
            fontsize=self.hisim_chartbase.fontsize_ticks,
        )

        # Find min and max y values
        y_values = df[kpi_column.multiindex_output_column]
        min_y = y_values.min()
        max_y = y_values.max()

        # Plot markers for min and max
        if kpi_column.min_or_max_winner == "min":
            min_color = "lightgreen"
            max_color = "lightcoral"
        else:
            min_color = "lightcoral"
            max_color = "lightgreen"

        # Add horizontal lines
        ax.axhline(
            min_y,
            color=min_color,
            linestyle="--",
            linewidth=1.5,
            label=f"Min: {min_y:.2f} {kpi_column.unit}",
        )
        ax.axhline(
            max_y,
            color=max_color,
            linestyle="--",
            linewidth=1.5,
            label=f"Max: {max_y:.2f} {kpi_column.unit}",
        )

        # Move legend outside
        ax.legend(
            loc="best",
            frameon=True,
            fontsize=self.hisim_chartbase.fontsize_legend,
        )
        plt.tick_params(labelsize=self.hisim_chartbase.fontsize_ticks)

        # Adjust layout
        plt.tight_layout()

        # Save figure
        filepath = (
            output_dir
            / f"{kpi_column.kpi_column}_per_energy_system_{building_type}.png"
        )
        plt.savefig(filepath, dpi=self.hisim_chartbase.dpi, bbox_inches="tight")
        print(
            "Made plot for",
            kpi_column.kpi_column,
            building_type,
            " and saved here: ",
            filepath,
            "\n",
        )
        plt.close()

    def _prepare_plot_data(
        self,
        df: pd.DataFrame,
        kpi_column: PrettyKpiLabels,
        hue_column: tuple,
    ) -> pd.DataFrame:
        """
        Shared preparation steps for plotting:
        - Copy dataframe
        - Sort hue values naturally
        - Rescale KPI if needed
        - Return prepared DataFrame
        """
        df = df.copy()

        # Sort hue values naturally
        sorted_hues = sorted(df[hue_column].unique(), key=self.natural_sort_key)
        df[hue_column] = pd.Categorical(
            df[hue_column], categories=sorted_hues, ordered=True
        )

        # Rescale upfront costs if necessary
        if "total_upfront" in kpi_column.kpi_column:
            new_kpi_column = "total_upfront_net_investment_costs_in_keuro"
            kpi_column = PrettyKpiLabels(
                kpi_column=new_kpi_column, min_or_max_winner="min"
            )
            df[kpi_column.multiindex_output_column] = (
                df[("Output", "total_upfront_net_investment_costs_in_euro")] / 1000
            )

        return df, kpi_column, sorted_hues

    def _create_figure_and_labels(
        self,
        kpi_column: PrettyKpiLabels,
    ) -> plt.Axes:
        """Shared figure setup for both scatter and boxplots."""
        fig, ax = plt.subplots(
            figsize=self.hisim_chartbase.figsize, dpi=self.hisim_chartbase.dpi
        )
        ax.set_xlabel(
            "Energy system combination", fontsize=self.hisim_chartbase.fontsize_label
        )
        ax.set_ylabel(
            "\n".join(textwrap.wrap(kpi_column.pretty_label, width=30)),
            fontsize=self.hisim_chartbase.fontsize_label,
        )
        ax.yaxis.grid(True, linestyle="--", alpha=0.7)
        plt.tick_params(labelsize=self.hisim_chartbase.fontsize_ticks)
        return ax

    def plot_boxplot_energy_systems(
        self,
        df: pd.DataFrame,
        output_dir: Path,
        kpi_column: PrettyKpiLabels,
        building_type: str,
        hue_column: tuple,
        energy_system_column: tuple = ("Input", "energy_system_combination"),
    ):
        """Boxplot for energy systems, including statistics and outlier flag."""
        df, kpi_column, sorted_hues = self._prepare_plot_data(
            df, kpi_column, hue_column
        )
        ax = self._create_figure_and_labels(kpi_column)
        # reset index to avoid dubplicated indices
        df = df.reset_index(drop=True)

        # Boxplot: one box per energy system, all data included
        sns.boxplot(
            data=df,
            x=energy_system_column,
            y=kpi_column.multiindex_output_column,
            ax=ax,
            # fliersize=2,
            linewidth=1,
            color="lightblue",
        )
        x_tick_labels = list(sorted(energy_system_map.values()))
        x_tick_positions = range(len(x_tick_labels))
        ax.set_xticks(x_tick_positions[::3])
        ax.set_xticklabels(
            x_tick_labels[::3],
            rotation=45,
            ha="right",
            fontsize=self.hisim_chartbase.fontsize_ticks,
        )
        # --- Compute and plot means ---
        value_col = kpi_column.multiindex_output_column
        values_series = df[value_col]
        groups_series = df[energy_system_column]
        grouped = values_series.groupby(groups_series)

        # Save figure
        plot_file = (
            output_dir
            / f"{kpi_column.kpi_column}_boxplot_per_energy_system_{building_type}.png"
        )
        plt.tight_layout()
        plt.savefig(plot_file, dpi=self.hisim_chartbase.dpi, bbox_inches="tight")
        plt.close()
        print("Saved boxplot:", plot_file)

        # --- Compute and save statistics ---
        # Basic stats
        stats = (
            grouped.describe(percentiles=[0.25, 0.5, 0.75])
            .rename(columns={"25%": "q1", "50%": "median", "75%": "q3"})
            .reset_index()
        )

        # Save stats
        stats_file = (
            output_dir / f"{kpi_column.kpi_column}_boxplot_stats_{building_type}.csv"
        )
        stats.to_csv(stats_file, index=False)
        print("Saved boxplot statistics:", stats_file)

    def save_collected_results_to_csv(
        self,
        df: pd.DataFrame,
        column: str,
        output_dir: Path,
    ) -> None:
        """Save the collected minima or maxima DataFrame to a csv file."""
        output_file = output_dir / f"all_bs_results_{column}.csv"
        df.to_csv(output_file, index=False)
        print(f"Saved all bs results for column {column} to: {output_file}")

    def get_kpi_for_energy_system_combination_and_append_to_collection(
        self,
        df: pd.DataFrame,
        kpi_column: str,
        building_column: str = ("Input", "building_id"),
        energy_system_column: str = ("Input", "energy_system_combination"),
    ):
        """Get kpi the energy system combination of each result and append to collection."""

        df_subset = df[[building_column, energy_system_column, kpi_column]]
        df_subset = df.sort_values(by=[kpi_column])
        return df_subset

    def collect_building_sizer_results(
        self, files: List[Path], kpi_column: PrettyKpiLabels
    ):
        collected_dfs = []
        for file_path in files:
            # read each buildig sizer result
            df = self.read_building_sizer_results(file_path=file_path)
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
    year = "2050"
    config_year_request_path_string = (
        f"F_hisim_building_sizer_optimization/0/{year}/bs_requests_20250825_1706"
    )
    INPUT_FOLDER = Path(
        "/fast/home/k-rieck/hisim_building_clustering/test_results/test_building_types/"
        + config_year_request_path_string
    )
    OUTPUT_FOLDER = (
        Path(
            "/fast/home/k-rieck/Thesis_2022-2025/Results/Sensitivity_Analysis_12_Building_Types/"
            + config_year_request_path_string
        )
        / "worst"
    )
    # year = "2050"
    # INPUT_FOLDER = Path("/fast/central/projects/2022-k-rieck-phd/paper_2_clustering_german_building_stock/hisim_building_clustering_analysis/F_hisim_building_sizer_optimization/16/2050")
    # OUTPUT_FOLDER = Path(
    #     "/fast/home/k-rieck/Thesis_2022-2025/Results/Clustering_Sachsen_Config_16/" + "F_hisim_building_sizer_optimization/16/2050/new"
    # ) # / "worst"
    # -------------------------------------------------------------------------------
    # Find min values
    FIND_MIN_OR_MAX = "max"
    kpi_config_fields_min = [
        "annualized_total_costs_in_euro_per_m2",
        "annualized_energy_costs_in_euro_per_m2",
        "annualized_net_investment_costs_in_euro_per_m2",
        "annualized_total_co2_emissions_in_kg_per_m2",
        "annualized_energy_co2_emissions_in_kg_per_m2",
        "annualized_purchased_energy_consumption_in_kwh_per_m2",
        "total_upfront_net_investment_costs_in_euro",
        "deviation_from_min_indoor_temperature_in_celsius_hour",
    ]

    column_of_interest_min = [
        PrettyKpiLabels(kpi_column=kpi_field, min_or_max_winner=FIND_MIN_OR_MAX)
        for kpi_field in kpi_config_fields_min
    ]
    # COLUMNS_OF_INTEREST = column_of_interest_min  # Add more as needed

    # find_kpi_winners_for_all_buildings(parent_folder=INPUT_FOLDER, kpi_columns=COLUMNS_OF_INTEREST)

    # -------------------------------------------------------------------------------
    # Find max values
    FIND_MIN_OR_MAX = "min"
    kpi_config_fields_max = [
        "self_sufficiency_rate_all_energy_in_percent",
        "minimum_indoor_temperature_in_celsius",
    ]

    column_of_interest_max = [
        PrettyKpiLabels(kpi_column=kpi_field, min_or_max_winner=FIND_MIN_OR_MAX)
        for kpi_field in kpi_config_fields_max
    ]
    # COLUMNS_OF_INTEREST = column_of_interest_max  # Add more as needed

    # find_kpi_winners_for_all_buildings(parent_folder=INPUT_FOLDER, kpi_columns=COLUMNS_OF_INTEREST)

    # -------------------------------------------------------------------------------
    # Collect all bs results and tranpsose
    COLUMNS_OF_INTEREST = column_of_interest_min + column_of_interest_max
    # collect_all_bs_results_and_plot(parent_folder=INPUT_FOLDER, kpi_columns=COLUMNS_OF_INTEREST)

    bs_postprocessor = BuildingSizerPostprocessor(
        input_folder=INPUT_FOLDER,
        output_folder=OUTPUT_FOLDER,
        columns_of_interest=COLUMNS_OF_INTEREST,
        year=year,
    )
