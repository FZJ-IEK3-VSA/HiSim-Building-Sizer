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
energy_system_map_new = {
    "OilHeating + Conventional Radiator + PV 0% + NoBatteryAndEMS": "Oil-R-PV0",
    "OilHeating + Conventional Radiator + PV 100% + NoBatteryAndEMS": "Oil-R-PV1",
    "OilHeating + Conventional Radiator + PV 100% + WithBatteryAndEMS": "Oil-R-PV1B",
    "OilHeating + Floorheating + PV 0% + NoBatteryAndEMS": "Oil-F-PV0",
    "OilHeating + Floorheating + PV 100% + NoBatteryAndEMS": "Oil-F-PV1",
    "OilHeating + Floorheating + PV 100% + WithBatteryAndEMS": "Oil-F-PV1B",
    "GasHeating + Conventional Radiator + PV 0% + NoBatteryAndEMS": "Gas-R-PV0",
    "GasHeating + Conventional Radiator + PV 100% + NoBatteryAndEMS": "Gas-R-PV1",
    "GasHeating + Conventional Radiator + PV 100% + WithBatteryAndEMS": "Gas-R-PV1B",
    "GasHeating + Floorheating + PV 0% + NoBatteryAndEMS": "Gas-F-PV0",
    "GasHeating + Floorheating + PV 100% + NoBatteryAndEMS": "Gas-F-PV1",
    "GasHeating + Floorheating + PV 100% + WithBatteryAndEMS": "Gas-F-PV1-B",
    "GasSolarThermal + Conventional Radiator + PV 0% + NoBatteryAndEMS": "GasSolar-R-PV0",
    "GasSolarThermal + Conventional Radiator + PV 100% + NoBatteryAndEMS": "GasSolar-R-PV1",
    "GasSolarThermal + Conventional Radiator + PV 100% + WithBatteryAndEMS": "GasSolar-R-PV1B",
    "GasSolarThermal + Floorheating + PV 0% + NoBatteryAndEMS": "GasSolar-F-PV0",
    "GasSolarThermal + Floorheating + PV 100% + NoBatteryAndEMS": "GasSolar-F-PV1",
    "GasSolarThermal + Floorheating + PV 100% + WithBatteryAndEMS": "GasSolar-F-PV1B",
    "PelletHeating + Conventional Radiator + PV 0% + NoBatteryAndEMS": "Pellet-R-PV0",
    "PelletHeating + Conventional Radiator + PV 100% + NoBatteryAndEMS": "Pellet-R-PV1",
    "PelletHeating + Conventional Radiator + PV 100% + WithBatteryAndEMS": "Pellet-R-PV1B",
    "PelletHeating + Floorheating + PV 0% + NoBatteryAndEMS": "Pellet-F-PV0",
    "PelletHeating + Floorheating + PV 100% + NoBatteryAndEMS": "Pellet-F-PV1",
    "PelletHeating + Floorheating + PV 100% + WithBatteryAndEMS": "Pellet-F-PV1B",
    "HydrogenHeating + Conventional Radiator + PV 0% + NoBatteryAndEMS": "Hydrogen-R-PV0",
    "HydrogenHeating + Conventional Radiator + PV 100% + NoBatteryAndEMS": "Hydrogen-R-PV1",
    "HydrogenHeating + Conventional Radiator + PV 100% + WithBatteryAndEMS": "Hydrogen-R-PV1B",
    "HydrogenHeating + Floorheating + PV 0% + NoBatteryAndEMS": "Hydrogen-F-PV0",
    "HydrogenHeating + Floorheating + PV 100% + NoBatteryAndEMS": "Hydrogen-F-PV1",
    "HydrogenHeating + Floorheating + PV 100% + WithBatteryAndEMS": "Hydrogen-F-PV1B",
    "DistrictHeating + Conventional Radiator + PV 0% + NoBatteryAndEMS": "District-R-PV0",
    "DistrictHeating + Conventional Radiator + PV 100% + NoBatteryAndEMS": "District-R-PV1",
    "DistrictHeating + Conventional Radiator + PV 100% + WithBatteryAndEMS": "District-R-PV1B",
    "DistrictHeating + Floorheating + PV 0% + NoBatteryAndEMS": "District-F-PV0",
    "DistrictHeating + Floorheating + PV 100% + NoBatteryAndEMS": "District-F-PV1",
    "DistrictHeating + Floorheating + PV 100% + WithBatteryAndEMS": "District-F-PV1B",
    "ElectricHeating + No HDS + PV 0% + NoBatteryAndEMS": "Electric-PV0",
    "ElectricHeating + No HDS + PV 100% + NoBatteryAndEMS": "Electric-PV1",
    "ElectricHeating + No HDS + PV 100% + WithBatteryAndEMS": "Electric-PV1B",
    "HeatPump + Conventional Radiator + PV 0% + NoBatteryAndEMS": "HeatPump-R-PV0",
    "HeatPump + Conventional Radiator + PV 100% + NoBatteryAndEMS": "HeatPump-R-PV1",
    "HeatPump + Conventional Radiator + PV 100% + WithBatteryAndEMS": "HeatPump-R-PV1B",
    "HeatPump + Floorheating + PV 0% + NoBatteryAndEMS": "HeatPump-F-PV0",
    "HeatPump + Floorheating + PV 100% + NoBatteryAndEMS": "HeatPump-F-PV1",
    "HeatPump + Floorheating + PV 100% + WithBatteryAndEMS": "HeatPump-F-PV1B",
    "HeatPumpSolarThermal + Conventional Radiator + PV 0% + NoBatteryAndEMS": "HeatPumpSolar-R-PV0",
    "HeatPumpSolarThermal + Conventional Radiator + PV 100% + NoBatteryAndEMS": "HeatPumpSolar-R-PV1",
    "HeatPumpSolarThermal + Conventional Radiator + PV 100% + WithBatteryAndEMS": "HeatPumpSolar-R-PV1B",
    "HeatPumpSolarThermal + Floorheating + PV 0% + NoBatteryAndEMS": "HeatPumpSolar-F-PV0",
    "HeatPumpSolarThermal + Floorheating + PV 100% + NoBatteryAndEMS": "HeatPumpSolar-F-PV1",
    "HeatPumpSolarThermal + Floorheating + PV 100% + WithBatteryAndEMS": "HeatPumpSolar-F-PV1B",
}
heating_system_map = {
    "OilHeating": 1,
    "GasHeating": 2,
    "GasSolarThermal": 3,
    "PelletHeating": 4,
    "HydrogenHeating": 5,
    "DistrictHeating": 6,
    "ElectricHeating": 7,
    "HeatPump": 8,
    "HeatPumpSolarThermal": 9, 
}
heating_system_map_new = {
    "OilHeating-R": 1,
    "OilHeating-F": 2,
    "GasHeating-R": 3,
    "GasHeating-F": 4,
    "GasSolarThermal-R": 5,
    "GasSolarThermal-F": 6,
    "PelletHeating-R": 7,
    "PelletHeating-F": 8,
    "HydrogenHeating-R": 9,
    "HydrogenHeating-F": 10,
    "DistrictHeating-R": 11,
    "DistrictHeating-F": 12,
    "ElectricHeating-": 13,
    "HeatPump-R": 14,
    "HeatPump-F": 15,
    "HeatPumpSolarThermal-R": 16,
    "HeatPumpSolarThermal-F": 17,
}

hds_map = {
    "Floorheating": "F",
    "Conventional Radiator": "R",
    "No HDS": ""
}
pv_map = {
    1.0: "PV1",
    0.0: "PV0"
}
batt_ems_map = {
    True: "B",
    False: ""
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
        self.hisim_chartbase.fontsize_legend = 12
        self.hisim_chartbase.fontsize_label = 14
        self.hisim_chartbase.fontsize_ticks = 12
        self.year = year

        # find kpi winner among the bs results
        self.find_kpi_winners_for_all_buildings(kpi_columns=columns_of_interest)
        # collect bs results, sort according to building types and make plots
        self.collect_all_bs_results_and_plot(kpi_columns=columns_of_interest, resume_all_bs_results_in_excel=False)

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
        # remove duplicates
        df_selected_rows = self.remove_duplicates_from_df(df_selected_rows)
        # save as csv
        self.save_minima_or_maxima_to_csv(
            df=df_selected_rows,
            column=kpi_column.kpi_column,
            find_min_or_max=kpi_column.min_or_max_winner,
        )
        return df_selected_rows

    def remove_duplicates_from_df(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove duplicate rows from the DataFrame."""
        # drop duplicates (keeps first occurrence)
        before = len(df)
        # check duplicates based on ("Input", "building_id")
        # reset index so index column does not interfere
        dup_mask = df.duplicated(subset=[("Input", "building_id"), ("Input", "energy_system_combination")], keep=False)
        duplicates = df[dup_mask]

        print(f"Found {duplicates.shape[0]} duplicate rows.")

        # remove duplicates (keep first occurrence)
        df = df.drop_duplicates(subset=[("Input", "building_id"), ("Input", "energy_system_combination")])
        after = len(df)
        print(f"Removed {before - after} duplicate rows.")
        return df

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
        resume_all_bs_results_in_excel: bool = False
    ):
        files = self.go_through_input_folder_and_find_all_building_sizer_results(
            filename
        )
        for kpi_column in kpi_columns:
            df_collected = self.collect_building_sizer_results(
                files=files, kpi_column=kpi_column, resume_all_bs_results_in_excel=resume_all_bs_results_in_excel
            )
            self.filter_by_building_type(df=df_collected, kpi_column=kpi_column)
            self.filter_by_age(df=df_collected, kpi_column=kpi_column)

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
                energy_system_column=("Input", "energy_system_id_str"),
            )
            self.plot_boxplot_energy_systems(
                df=filtered_sorted_df,
                output_dir=b_type_folder,
                kpi_column=kpi_column,
                building_type=b_type,
                hue_column=hue_column,
                energy_system_column=("Input", "energy_system_id_str"),
            )
            # self.sns_scatter_with_labels(
            #     df=filtered_sorted_df,
            #     output_dir=b_type_folder,
            #     kpi_column=kpi_column,
            #     building_type=b_type,
            #     hue_column=hue_column,
            #     energy_system_column=("Input", "heating_system_hds"),
                
            # )

    def filter_by_age(
        self,
        df: pd.DataFrame,
        kpi_column: PrettyKpiLabels,
        building_code_column: str = ("Input", "construction_year"),
        hue_column: str = ("Input", "building_id"),
        energy_system_column: tuple = ("Input", "energy_system_combination"),
    ):
        age_filter = {"before_1900": 1900, "after_1900": 1900}

        for age_group, year in age_filter.items():
            age_folder = self.output_folder / age_group
            age_folder.mkdir(parents=True, exist_ok=True)
            if "before" in age_group:
                filtered_df = df[df[building_code_column] <= year]
            elif "after" in age_group:
                filtered_df = df[df[building_code_column] > year]
            # Add new column with numeric mapping
            filtered_df.loc[:, ("Input", "energy_system_id")] = filtered_df[energy_system_column].map(
                energy_system_map
            )
            filtered_df.loc[:, ("Input", "energy_system_id_str")] = filtered_df[energy_system_column].map(
                energy_system_map_new
            )
            filtered_df.loc[:, ("Input", "hds_id")] = filtered_df[("Input", "heat_distribution_system")].map(
                hds_map
            )
            filtered_df.loc[:, ("Input", "pv_id")] = filtered_df[("Input", "share_of_maximum_pv_potential")].map(
                pv_map
            )
            filtered_df.loc[:, ("Input", "batt_ems_id")] = filtered_df[("Input", "use_battery_and_ems")].map(
                batt_ems_map
            )
            filtered_df.to_csv(
                age_folder / f"filtered_df_{age_group}_{kpi_column.kpi_column}.csv",
                index=False,
            )
            self.plot_ratings_of_each_energy_system_config_as_scatterplot(
                df=filtered_df,
                output_dir=age_folder,
                kpi_column=kpi_column,
                building_type=age_group,
                hue_column=hue_column,
                energy_system_column=("Input", "energy_system_id_str"),
            )
            self.plot_boxplot_energy_systems(
                df=filtered_df,
                output_dir=age_folder,
                kpi_column=kpi_column,
                building_type=age_group,
                hue_column=hue_column,
                energy_system_column=("Input", "energy_system_id_str"),
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

        # Sort them (optional: alphabetically)
        remaining_systems_sorted = sorted(remaining_systems)

        # Combine
        final_system_order = sorted_reference_systems + remaining_systems_sorted

        # Apply Categorical sorting
        df = df.copy()
        df[energy_system_column] = pd.Categorical(
            df[energy_system_column], categories=final_system_order, ordered=True
        )
        # Add new column with numeric mapping
        df.loc[:, ("Input", "energy_system_id")] = df[energy_system_column].map(
            energy_system_map
        )
        df.loc[:, ("Input", "energy_system_id_str")] = df[energy_system_column].map(
            energy_system_map_new
        )
        df.loc[:, ("Input", "hds_id")] = df[("Input", "heat_distribution_system")].map(
            hds_map
        )
        df.loc[:, ("Input", "pv_id")] = df[("Input", "share_of_maximum_pv_potential")].map(
            pv_map
        )
        df.loc[:, ("Input", "batt_ems_id")] = df[("Input", "use_battery_and_ems")].map(
            batt_ems_map
        )
        df[("Input", "heating_system_hds")] = df[("Input", "heating_system")].astype(str) + "-" + df[("Input", "hds_id")].astype(str)
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

        # Define the full desired order
        desired_order = list(energy_system_map_new.values())

        # Map original column to short names
        df['energy_system_sort'] = df[("Input", "energy_system_combination")].map(energy_system_map_new)
        df = df[~df['energy_system_sort'].astype(str).str.endswith("PV1", na=False)]
        

        # Keep only those categories that exist in the DataFrame
        present_categories = [c for c in desired_order if c in df['energy_system_sort'].unique()]

        # Print which ones are missing
        missing_categories = set(desired_order) - set(present_categories)
        if missing_categories:
            print("Dropping empty categories from x-axis:", missing_categories)

        # Apply categorical order only with present categories
        df['energy_system_sort'] = pd.Categorical(
            df['energy_system_sort'],
            categories=present_categories,
            ordered=True
        )

        # Create larger figure
        ax = self._create_figure_and_labels(kpi_column=kpi_column)
        ax.get_figure().set_size_inches(12,4)  # adjust after ax already exists
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
        required_cols = [
            kpi_column.multiindex_output_column,
            energy_system_column,
        ]
        if [col for col in required_cols if col not in df.columns]:
            raise KeyError(f"One of the columns {kpi_column.multiindex_output_column}, {energy_system_column}, or {hue_column} is missing in the DataFrame.")

        # Scatterplot: for legend and point emphasis
        # Count unique hue values
        num_hues = df[hue_column].nunique()
        sns.scatterplot(
            data=df,
            x='energy_system_sort', # energy_system_column,
            y=kpi_column.multiindex_output_column,
            hue=hue_column,
            s=80,# if num_hues <= 10 else 10,
            ax=ax,
            legend=False if num_hues > 10 else "full",  # hide legend if > 10 hues
            palette=palette,
        )
        ax.set_xlabel("")   # remove x-axis label

        # Make dotted vertical line after each Nth category
        for index, xi in enumerate(df["energy_system_sort"].cat.categories):
            if index % 2 == 0:  # adjust N as needed
                ax.axvline(x=xi, color="gray", linestyle=":")

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
        ax.set_xticks(range(len(present_categories)))
        ax.set_xticklabels(present_categories, rotation=45, ha="right", fontsize=10)

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

    def sns_scatter_with_labels(
        self,
        df: pd.DataFrame,
        output_dir: Path,
        kpi_column: PrettyKpiLabels,
        building_type: str,
        hue_column: tuple,
        energy_system_column: tuple = ("Input", "heating_system_hds"),
        label_cols: List[tuple] = [("Input", "pv_id"), ("Input", "batt_ems_id")],
    ):
        # Use your own figure helper (remove plt.subplots to avoid overwriting)
        fig, ax = plt.subplots(
            figsize=(8,6), dpi=self.hisim_chartbase.dpi
        )
        ax.set_xlabel(
            "", fontsize=self.hisim_chartbase.fontsize_label
        )
        ax.set_ylabel(
            "\n".join(textwrap.wrap(kpi_column.pretty_label, width=30)),
            fontsize=self.hisim_chartbase.fontsize_label,
        )
        ax.yaxis.grid(True, linestyle="--", alpha=0.7)
        plt.tick_params(labelsize=self.hisim_chartbase.fontsize_ticks)

        # Reset index to avoid duplicates
        df = df.reset_index(drop=True)
        # Define the order explicitly
        desired_order = list(heating_system_map_new.keys())

        # Map each combination to its heating system (substring match or lookup)
        def extract_system(combination: str) -> str:
            for system in desired_order:
                if system in combination:
                    return system
            return None

        df["system_order_key"] = df[energy_system_column].map(extract_system)

        # Convert the plotted column into a categorical ordered by that key
        df[energy_system_column] = pd.Categorical(
            df[energy_system_column],
            categories=sorted(
                df[energy_system_column].unique(),
                key=lambda x: desired_order.index(extract_system(x))
            ),
            ordered=True
        )
        rows_to_drop = []
        for idx, row in df.iterrows():
            label = "".join(str(row[col]) for col in label_cols if col in df.columns)
            if label == "PV0":
                rows_to_drop.append(idx)

        df = df.drop(rows_to_drop)

        # Check required columns
        required_cols = [kpi_column.multiindex_output_column, energy_system_column]
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            raise KeyError(f"Missing columns in df: {missing}")

        # Unique hues + palette
        unique_hues = df[hue_column].unique()
        palette = sns.color_palette(n_colors=len(unique_hues))

        # Save hue-color table
        hue_color_table = pd.DataFrame(
            {
                hue_column: unique_hues,
                "color": [rgb2hex(c) for c in palette],  # convert RGB to hex
            }
        )

        hue_color_table.to_csv(output_dir / "hue_color_table.csv")

        # Scatterplot
        sns.scatterplot(
            data=df,
            x=energy_system_column,
            y=kpi_column.multiindex_output_column,
            hue=hue_column,
            s=100,
            ax=ax,
            legend=False if len(unique_hues) > 10 else "full",
            palette=palette,
        )
        # Rotate and resize x-ticks
        ax.tick_params(axis='x', rotation=45)
        for x_tick in ax.get_xticklabels():
            ax.axvline(x=x_tick.get_position()[0], color="gray", linestyle=":")

        # Add labels
        for _, row in df.iterrows():
            label = "".join(str(row[col]) for col in label_cols if col in df.columns)
            ax.annotate(
                label,
                xy=(row[energy_system_column], row[kpi_column.multiindex_output_column]),
                xytext=(-1, 1),              # shift left (-x) and up (+y)
                textcoords="offset points",  # interpret xytext as offset in points
                ha="right",                  # align right so label ends at marker
                va="bottom",                 # text sits above the marker
                fontsize=8
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
        plt.xlabel("")

        # Save figure
        filepath = output_dir / f"{kpi_column.kpi_column}_per_energy_system_{building_type}_scatter_test.png"
        # plt.tight_layout()
        plt.savefig(filepath, dpi=self.hisim_chartbase.dpi, bbox_inches="tight")
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
        ax.get_figure().set_size_inches(12, 4)  # adjust after ax already exists
        df = df.reset_index(drop=True)

        # --- Ensure only present categories are used ---
        # Define the full desired order
        desired_order = list(energy_system_map_new.values())

        # Map original column to short names
        df['energy_system_sort'] = df[("Input", "energy_system_combination")].map(energy_system_map_new)
        if 'energy_system_sort' not in df.columns:
            raise KeyError("'energy_system_sort' column was not created; check mapping.")

        # Keep only those categories that exist in the DataFrame
        present_categories = [c for c in desired_order if c in df['energy_system_sort'].unique()]

        # Print which ones are missing
        missing_categories = set(desired_order) - set(present_categories)
        if missing_categories:
            print("Dropping empty categories from x-axis:", missing_categories)

        # --- Boxplot ---
        sns.boxplot(
            data=df,
            x="energy_system_sort",   # use column name, not Series
            y=kpi_column.multiindex_output_column,
            ax=ax,
            linewidth=1,
            color="lightgreen",
            order=present_categories,
            showfliers=False,   # hide outliers
        )
        ax.set_xlabel("")   # remove x-axis label

        # --- Fix x-ticks (only present categories) ---
        plt.tick_params(labelsize=self.hisim_chartbase.fontsize_ticks)
        ax.set_xticks(range(len(present_categories)))
        ax.set_xticklabels(present_categories, rotation=45, ha="right", fontsize=10)

        # Save figure
        plot_file = (
            output_dir
            / f"{kpi_column.kpi_column}_boxplot_per_energy_system_{building_type}_PV_comparison.png"
        )
        # plt.tight_layout()
        plt.savefig(plot_file, dpi=self.hisim_chartbase.dpi, bbox_inches="tight")
        plt.close()
        print("Saved boxplot:", plot_file)

        # --- Compute and save statistics ---
        value_col = kpi_column.multiindex_output_column
        values_series = df[value_col]
        groups_series = df["energy_system_sort"]
        grouped = values_series.groupby(groups_series)

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
        self, files: List[Path], kpi_column: PrettyKpiLabels, resume_all_bs_results_in_excel: bool
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
        # remove duplicates
        df_collected = self.remove_duplicates_from_df(df_collected)

        # save all as excel if wanted
        if resume_all_bs_results_in_excel:
            with pd.ExcelWriter(self.output_folder / f"all_bs_results_{self.year}.xlsx", engine="openpyxl") as writer:
                used_names = set()
                for file_path in files:
                    # read each building sizer result
                    df = self.read_building_sizer_results(file_path=file_path)
                    building_id = df[("Input", "building_id")].iloc[0]

                    # drop duplicates (keep first occurrence by default)
                    df = df.drop_duplicates()
                    df.columns = df.columns.get_level_values(-1)  # keep only last level

                    # ensure sheet name length ≤ 31 chars and unique
                    sheet_name = building_id[:31]  # Excel sheet name limit

                    # skip duplicates
                    if sheet_name in used_names:
                        print(f"Skipping duplicate sheet: {sheet_name}")
                        continue

                    used_names.add(sheet_name)

                    # write to Excel
                    df.to_excel(writer, sheet_name=sheet_name, index=False)

        return df_collected


# ---------- Run It ----------
if __name__ == "__main__":
    year = "2024"
    config_year_request_path_string = (
        f"F_hisim_building_sizer_optimization/0/{year}/bs_requests_20250910_1226"
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
        # / "worst"
    )
    # samples_all_tries = "F_hisim_building_sizer_optimization/16_new/samples_all/2050/20250910"
    # # samples_hundred = "F_hisim_building_sizer_optimization/16_new/samples_100/2050/bs_requests_20250831_2309"
    # # samples_thousand = "F_hisim_building_sizer_optimization/16_new/samples_1000/2050/" # 20250831"
    # year = "2050"
    # INPUT_FOLDER = Path("/fast/central/projects/2022-k-rieck-phd/paper_2_clustering_german_building_stock/hisim_building_clustering_analysis/") / samples_all_tries
    # OUTPUT_FOLDER = Path(
    #     "/fast/home/k-rieck/Thesis_2022-2025/Results/Clustering_Sachsen_Config_16/") / samples_all_tries # / "worst"
    # -------------------------------------------------------------------------------
    # Find min values
    FIND_MIN_OR_MAX = "min"
    kpi_config_fields_min = [
        "annualized_total_costs_in_euro_per_m2",
        "annualized_energy_costs_in_euro_per_m2",
        "annualized_maintenance_costs_in_euro_per_m2",
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
    FIND_MIN_OR_MAX = "max"
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
