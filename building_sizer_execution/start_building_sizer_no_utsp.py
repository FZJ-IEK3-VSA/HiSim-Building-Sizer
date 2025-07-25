"""Sends a building sizer request to the UTSP and waits until the calculation is finished."""

import sys
import json
import os
import time
import numpy as np
import re
from datetime import datetime
from typing import Dict, List, Union, Optional, Tuple, Any

import matplotlib.pyplot as plt  # type: ignore
import pandas as pd
import fnmatch

# Add the parent directory to the system path
sys.path.append("/fast/home/k-rieck/HiSim-Building-Sizer/")
from building_sizer_execution import building_sizer_algorithm_no_utsp
from building_sizer_execution.building_sizer_algorithm_no_utsp import (
    BuildingSizerRequest,
    BuildingSizerResult,
    BuildingSizerConfig,
)

# Add the parent directory to the system path
sys.path.append("/fast/home/k-rieck/repositories/HiSim")
from hisim.building_sizer_utils.interface_configs.archetype_config import (
    ArcheTypeConfig,
)
from hisim.building_sizer_utils.interface_configs.kpi_config import (
    KPIConfig,
    KPIForRatingInOptimization,
)
from hisim.simulationparameters import SimulationParameters

sys.path.append(
    "/fast/home/k-rieck/jobs_hisim/cluster-hisim-paper/job_array_for_hisim_mass_simus/cluster_job_management"
)
from job_management_functions import make_finish_flag_for_successful_executions


def plot_ratings_of_each_iteration_as_boxplots(
    ratings: List[List[float]],
    main_building_sizer_request_directory: str,
    request: BuildingSizerRequest,
) -> None:
    """
    Generate a boxplot for each generation showing the range of ratings

    :param ratings: nested list, creating a list of ratings for each generation
    :type ratings: List[List[float]]
    """
    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_subplot(111)
    ax.set_xlabel("Iterations")
    ax.set_ylabel(f"{request.kpi_for_rating.value}")
    # Creating plot
    _ = ax.boxplot(ratings)  # type: ignore
    # show plot
    plt.show()
    plt.savefig(
        os.path.join(
            main_building_sizer_request_directory, "ratings_per_iteration_boxplots.png"
        )
    )


def add_energy_system_labels(df: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    """Add a column 'energy_system_label' to the DataFrame based on specified keys."""

    def make_label(row):
        """Make label for one row."""
        label_parts = []
        for key in keys:
            value = row[key]

            if pd.isna(value):
                part = f"{key}=NaN"

            elif key == "share_of_maximum_pv_potential":
                try:
                    part = f"PV {round(float(value) * 100)}%"
                except Exception as e:
                    raise ValueError(
                        f"Invalid value for {key}: {value} ({type(value)}): {e}"
                    )

            elif key == "use_battery_and_ems":
                try:
                    value = bool(value)
                    part = "WithBatteryAndEMS" if value else "NoBatteryAndEMS"
                except Exception as e:
                    raise ValueError(
                        f"Invalid boolean for {key}: {value} ({type(value)}): {e}"
                    )

            elif isinstance(value, (str, float, int, np.integer, np.floating)):
                part = str(value)

            else:
                raise ValueError(f"Unexpected value for {key}: {value} ({type(value)})")

            label_parts.append(part)

        return " + ".join(label_parts)

    df["energy_system_combination"] = df.apply(make_label, axis=1)
    return df


def plot_ratings_of_each_energy_system_config_as_scatterplot(
    dataframe_with_ratings: pd.DataFrame,
    request: BuildingSizerRequest,
    main_building_sizer_request_directory: str,
) -> None:
    """
    Generate scatter plot for all energy system configs and their ratings.
    """
    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_subplot(111)
    # set labels
    ax.set_xlabel("Energy system combination")
    ax.set_ylabel(str(request.kpi_for_rating.value))
    print("DEBUG", dataframe_with_ratings["energy_system_combination"])
    # Creating plot
    plt.scatter(x=dataframe_with_ratings["energy_system_combination"], y=dataframe_with_ratings[str(request.kpi_for_rating.value)])  # type: ignore
    # Rotating X-axis labels
    plt.xticks(rotation=45, ha="right", fontsize=6)
    plt.tight_layout()
    # show plot
    plt.show()
    plt.savefig(
        os.path.join(
            main_building_sizer_request_directory,
            "ratings_per_energy_system_scatter.png",
        )
    )


# TODO: this is already called in building sizer iteration or why is it double?
def get_hisim_kpis_of_iteration(
    main_building_sizer_request_directory: str,
) -> Dict[str, Dict]:
    """
    Returns the KPIs (results of HiSIM calculation) for one generation of HiSim configurations

    :param building_sizer_config: the building sizer request for the generation
    :type building_sizer_config: BuildingSizerRequest
    :return: a dict mapping each HiSim configuration to its KPIs
    :rtype: Dict[float]
    """
    # read through hisim results folder and collect all results instead of running hisim simulation again
    kpi_values = None
    hisim_config_values = None
    hisim_kpis: Dict = {}
    # Walk through all subdirectories
    for root, dirs, files in os.walk(main_building_sizer_request_directory):
        for filename in files:

            if fnmatch.fnmatch(
                filename, "*_kpi_config_for_building_sizer.json"
            ):  # Match specific file pattern (e.g., *.txt)
                file_path = os.path.join(root, filename)
                # Open and read the file, then append its content to the list
                with open(file_path, "r", encoding="utf-8") as file:
                    kpi_values = json.load(file)

            if kpi_values is not None and fnmatch.fnmatch(
                filename, "data_for_scenario_evaluation.json"
            ):  # Match specific file pattern (e.g., *.txt)
                file_path_1 = os.path.join(root, filename)
                # Open and read the file, then append its content to the list
                with open(file_path_1, "r", encoding="utf-8") as file:
                    hisim_config_values = json.load(file)["myModuleConfig"]
                    hisim_config_values_str = str(hisim_config_values)
                    # make dict of these two
                    dicti = {hisim_config_values_str: kpi_values}
                    hisim_kpis.update(dicti)

    return hisim_kpis


def get_rating(kpi_dict: Dict, request: BuildingSizerRequest) -> float:
    """Computes the fitness or rating of one individual (hisim configuration).

    :kpi: List of key performance indicatiors - results of HiSIM simulation.
    :type kpi: str
    :return: fitness or rating of the individual (hisim configuration)
    :rtype: float
    """

    return round(KPIConfig.from_dict(kpi_dict).get_kpi_for_rating(chosen_kpi=request.kpi_for_rating), 2)  # type: ignore


def get_ratings(kpis_dicts: List[Dict], request: BuildingSizerRequest) -> List[float]:
    """Computes the fitness or rating of multiple individuals (hisim configurations).

    :kpis: List of HiSIM simulation results (key performance indicatiors).
    :type kpis: str
    :return: list of fitness or rating of the individuals (hisim configurations)
    :rtype: List[float]
    """

    return [get_rating(kpi_dict, request) for kpi_dict in kpis_dicts]


def return_config_as_dict(hisim_config_str: str) -> Dict:
    """
    Helper method for testing, that extracts only the relevant fields of a system config
    to print them in a clearer way.
    :param hisim_config: a system configuration of HiSIM
    :type hisim_config: str
    :return: a system configuration of HiSIM containing only the parameters changing within the evolutionary algorithm
    :rtype: str
    """
    # get dict from str
    modular_hh_config_dict = eval(hisim_config_str)
    sys_config = modular_hh_config_dict["energy_system_config_"]

    minimal = {k: sys_config[k] for k in sys_config.keys()}
    hisim_config_json = json.dumps(minimal)
    d_config = json.loads(hisim_config_json)
    return d_config


def load_config_and_meta(
    building_sizer_config_file: Union[str, BuildingSizerConfig],
) -> Tuple[BuildingSizerConfig, str, str, dict]:
    """Load config and meta data."""
    if isinstance(building_sizer_config_file, str) and os.path.exists(
        building_sizer_config_file.rstrip("\r")
    ):
        with open(
            building_sizer_config_file.rstrip("\r"), encoding="unicode_escape"
        ) as config_file:
            my_config_dict = json.load(config_file)
            my_config = BuildingSizerConfig.from_dict(my_config_dict)  # type: ignore

        # get datetime and hash value from building_sizer_config_filename
        bs_config_datetime_string = building_sizer_config_file.split("/")[-2].split(
            "_"
        )[-1]
        bs_config_hash_string = re.findall(
            r"\-?\d+", building_sizer_config_file.split("_")[-1]
        )[0]

    elif isinstance(building_sizer_config_file, BuildingSizerConfig):
        my_config = building_sizer_config_file
        # create datetime and hash value from building_sizer_config_filename
        bs_config_datetime_string = datetime.now().strftime("%Y%m%d_%H%M")
        my_config_dict = my_config.to_dict()
        config_str = json.dumps(my_config_dict, indent=4)
        bs_config_hash_string = hash(config_str)

    else:
        raise FileNotFoundError(
            f"The building sizer config file does not exist or is not readable: {building_sizer_config_file}"
        )
    return my_config, bs_config_datetime_string, bs_config_hash_string, my_config_dict


def prepare_output_dir(
    base_dir: str, datetime_str: str, hash_str: str, config_dict: dict
) -> str:
    """Prepare output dir."""
    request_dir = os.path.join(
        base_dir, f"bs_requests_{datetime_str}", f"bs_request_{hash_str}"
    )
    os.makedirs(request_dir, exist_ok=True)
    with open(os.path.join(request_dir, "bs_config.json"), "w", encoding="utf-8") as f:
        json.dump(config_dict, f, ensure_ascii=False, indent=4)
    return request_dir


def wait_for_result(result_file: str, timeout: int = 600):
    """Wait for result."""
    start_time = time.time()
    while not os.path.exists(result_file):
        if time.time() - start_time > timeout:
            raise TimeoutError(f"Result file '{result_file}' not created in time.")
        time.sleep(10)


def get_result_from_json(result_file: str) -> BuildingSizerResult:
    """Get result from json."""
    with open(result_file, "r", encoding="utf-8") as file:
        status_json = json.load(file)

    building_sizer_result: BuildingSizerResult = BuildingSizerResult.from_dict(
        status_json
    )
    return building_sizer_result


def run_one_iteration(
    request,
    output_dir,
    sim_params,
    result_file,
    all_kpis,
    rating_lists,
    iteration_counter: int,
):
    """Run one iteration."""
    print(f"--- RUNNING ITERATION NO. {iteration_counter}---", "\n")
    building_sizer_algorithm_no_utsp.main_without_utsp(
        request=request,
        main_building_sizer_request_directory=output_dir,
        hisim_simulation_parameters=sim_params,
    )
    wait_for_result(result_file)
    result = get_result_from_json(result_file)
    kpis = get_hisim_kpis_of_iteration(output_dir)
    if kpis:
        all_kpis.append(kpis)
        rating_lists.append(get_ratings(kpis.values(), request))
        for config_str, kpi in kpis.items():
            print(
                "Config:",
                return_config_as_dict(config_str),
                "→",
                request.kpi_for_rating.value,
                "=",
                get_rating(kpi, request),
            )
            print("---")
    iteration_counter += 1
    return all_kpis, rating_lists, result, iteration_counter


def main(
    building_sizer_config_file: Union[str, BuildingSizerConfig],
    building_sizer_result_folder: Optional[str] = None,
):
    """
    Default function to call the building sizer.

    Hard coded Input Parameters
    ---------------------------
    :param bulding_sizer_version: Version of the building sizer
    :type building_sizer_version: str
    :param hisim_version: Version of HiSIM the building sizer calls upon
    :type hisim_version: str
    :param remaining_iterations: number of iterations the evolutionary algorithm should have
    :type remaining_iterations: int
    :param boolean_iterations: number of iterations where the decision of which components to use is evaluated.
    :tpye boolean_iterations: int
    :param discrete_iterations: number of iterations where the decision of which size the components should have is evaluated
    :tpye discrete_iterations: int
    :param population_sizer: number of individuals considered in each population
    :tpye population_size: int
    :param crossover_probabiltiy: number of individuals considered in each population
    :tpye crossover_probabiltiy: float
    :param mutation_probabiltiy: number of individuals considered in each population
    :tpye mutation_probabiltiy: float
    :param options: number of individuals considered in each population
    :tpye options: individual_encoding.SizingOptions
    :archetype_config_: builing parameters of HiSIM (independet of system config, climate, house type, etc. need to be defined)
    :tpye archetype_config_: archetype_config.ArcheTypeConfig
    """
    start = datetime.now()
    iteration_counter = 0

    # open json config
    my_config, bs_config_datetime_string, bs_config_hash_string, my_config_dict = (
        load_config_and_meta(building_sizer_config_file)
    )

    # Get Hisim simulation parameters
    hisim_simulation_parameters = SimulationParameters.from_dict(
        my_config.hisim_simulation_parameters
    )
    # Create an initial simulation configuration for the building sizer
    initial_building_sizer_request = BuildingSizerRequest.from_dict(
        my_config.initial_building_sizer_request
    )

    # create folder where everything related to this building sizer request is stored
    if building_sizer_result_folder is None:
        building_sizer_result_folder = os.path.join(
            os.path.abspath(os.path.join(os.getcwd(), os.pardir)),
            "building_sizer_results",
        )
    main_building_sizer_request_directory = prepare_output_dir(
        base_dir=building_sizer_result_folder,
        datetime_str=bs_config_datetime_string,
        hash_str=bs_config_hash_string,
        config_dict=my_config_dict,
    )
    result_path = os.path.join(
        main_building_sizer_request_directory, "results", "status.json"
    )
    previous_hashes = {initial_building_sizer_request.get_hash()}
    iterations, all_kpis, rating_lists = [], [], []
    # === First iteration (always run) for initialization ===
    print("\n--- INITIALIZATION ITERATION ---")
    all_kpis, rating_lists, result_obj, iteration_counter = run_one_iteration(
        initial_building_sizer_request,
        main_building_sizer_request_directory,
        hisim_simulation_parameters,
        result_path,
        all_kpis,
        rating_lists,
        iteration_counter,
    )

    while not result_obj.finished and result_obj.subsequent_building_sizer_request:
        request = result_obj.subsequent_building_sizer_request
        request_hash = request.get_hash()
        if request_hash in previous_hashes:
            raise RuntimeError(f"Loop detected: {request}")
        previous_hashes.add(request_hash)
        iterations.append(request)
        print("--- OPTIMIZATION ITERATION ---")
        all_kpis, rating_lists, result_obj, iteration_counter = run_one_iteration(
            request,
            main_building_sizer_request_directory,
            hisim_simulation_parameters,
            result_path,
            all_kpis,
            rating_lists,
            iteration_counter,
        )

    if not any(all_kpis):
        raise ValueError("No HiSIM KPIs collected. Check config or simulation.")

    plot_ratings_of_each_iteration_as_boxplots(
        rating_lists, main_building_sizer_request_directory, request
    )
    df_only_ratings = create_table_with_all_energy_system_configs_and_hisim_kpis(
        all_kpis, main_building_sizer_request_directory, request
    )
    plot_ratings_of_each_energy_system_config_as_scatterplot(
        df_only_ratings, request, main_building_sizer_request_directory
    )
    make_finish_flag_for_successful_executions(main_building_sizer_request_directory)
    print(f"Finished. Optimization took {datetime.now() - start}.")


def create_table_with_all_energy_system_configs_and_hisim_kpis(
    generations: Dict,
    main_building_sizer_request_directory: str,
    request: BuildingSizerRequest,
) -> pd.DataFrame:
    """
    Writes csv containing all kpi values (HiSIM results) of all individuals (HiSim configuration) of each generation (iteration).

    :param generation: List of all individuals (HiSIM configurations) and KPIs (HiSIM results) in each generation (iteartion)
    :type generation: List[Dict[str, str]]
    """
    all_data: Dict = {}
    only_ratings: Dict = {}

    for iteration, generation in enumerate(generations):
        for hisim_config_path, kpi_dict in generation.items():
            d_config = return_config_as_dict(hisim_config_path)
            d_kpi = kpi_dict
            d_total = dict(d_config, **d_kpi)
            d_total["iteration"] = iteration

            rating_kpi = get_rating(kpi_dict, request)
            d_only_ratings = dict(
                d_config, **{f"{request.kpi_for_rating.value}": rating_kpi}
            )
            d_only_ratings["iteration"] = iteration

            for name, value in d_total.items():
                if name not in all_data:
                    all_data[name] = []
                if isinstance(value, float):
                    value = round(value, 2)
                all_data[name].append(value)

            for name, value in d_only_ratings.items():
                if name not in only_ratings:
                    only_ratings[name] = []
                if isinstance(value, float):
                    value = round(value, 2)
                only_ratings[name].append(value)

    df = pd.DataFrame.from_dict(all_data)
    df_all_ratings = pd.DataFrame.from_dict(only_ratings)
    # merge config columns
    df = add_energy_system_labels(df=df, keys=d_config.keys())
    df_all_ratings = add_energy_system_labels(df=df_all_ratings, keys=d_config.keys())

    # sort according to kpi for rating
    sorted_df_all_ratings = df_all_ratings.sort_values(
        by=[str(request.kpi_for_rating.value)]
    )
    df.to_csv(
        os.path.join(
            main_building_sizer_request_directory, "building_sizer_results.csv"
        )
    )
    return sorted_df_all_ratings


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Building sizer algorithm needs one argument.")
        sys.exit(1)
    BUILDING_SIZER_CONFIG_FILENAME = sys.argv[1]
    print("start building sizer with config " + BUILDING_SIZER_CONFIG_FILENAME)
    main(building_sizer_config_file=BUILDING_SIZER_CONFIG_FILENAME)
