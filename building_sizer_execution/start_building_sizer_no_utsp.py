"""Sends a building sizer request to the UTSP and waits until the calculation is finished."""
import sys
import json
import os
import time
import re
from datetime import datetime
from typing import Dict, List

import matplotlib.pyplot as plt  # type: ignore
import pandas as pd
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


def plot_ratings_of_each_iteration_as_boxplots(
    ratings: List[List[float]], main_building_sizer_request_directory: str, request: BuildingSizerRequest
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
    plt.savefig(os.path.join(main_building_sizer_request_directory, "ratings_per_iteration_boxplots.png"))

def plot_ratings_of_each_energy_system_config_as_scatterplot(
    dataframe_with_ratings: pd.DataFrame, request: BuildingSizerRequest, main_building_sizer_request_directory: str
) -> None:
    """
    Generate scatter plot for all energy system configs and their ratings.
    """
    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_subplot(111)
    ax.set_xlabel("Energy system combination")
    # sort according to certain column
    sorted_df = dataframe_with_ratings.sort_values(by=[str(request.kpi_for_rating.value)])
    # merge config columns
    sorted_df['energy_system_combination'] = sorted_df['heating_system'] + " + PV " + (sorted_df['share_of_maximum_pv_potential']*100).astype(str) + "%"

    ax.set_ylabel(str(request.kpi_for_rating.value))
    # Creating plot
    plt.scatter(x=sorted_df['energy_system_combination'], y=sorted_df[str(request.kpi_for_rating.value)])  # type: ignore
    # Rotating X-axis labels
    plt.xticks(rotation = 45, ha='right')
    plt.tight_layout()
    # show plot
    plt.show()
    plt.savefig(os.path.join(main_building_sizer_request_directory, "ratings_per_energy_system_scatter.png"))

# TODO: this is already called in building sizer iteration or why is it double?
def get_hisim_kpis_of_iteration(
    building_sizer_request: BuildingSizerRequest,
    main_building_sizer_request_directory: str,
    hisim_simulation_parameters: SimulationParameters,
    all_hisim_kpis_list: List[Dict]
) -> Dict[str, Dict]:
    """
    Returns the KPIs (results of HiSIM calculation) for one generation of HiSim configurations

    :param building_sizer_config: the building sizer request for the generation
    :type building_sizer_config: BuildingSizerRequest
    :return: a dict mapping each HiSim configuration to its KPIs
    :rtype: Dict[float]
    """
    # print("RUN HISIM SIMU AGAIN AND GET HISIM KPIS OF THIS ITERATION FOR RATING.")
    # hisim_kpis = building_sizer_algorithm_no_utsp.get_results_from_requisite_hisim_configs_slurm(
    #     requisite_hisim_config_paths=building_sizer_request.requisite_hisim_config_paths,
    #     main_building_sizer_request_directory=main_building_sizer_request_directory,
    #     hisim_simulation_parameters=hisim_simulation_parameters,
    # )

    # read through hisim results folder and collect all results instead of running hisim simulation again
    import fnmatch
    kpi_values = None
    hisim_config_values = None
    hisim_kpis: Dict = {}
    # Walk through all subdirectories
    for root, dirs, files in os.walk(main_building_sizer_request_directory):
        for filename in files:

            if fnmatch.fnmatch(filename, 'kpi_config_for_building_sizer.json'):  # Match specific file pattern (e.g., *.txt)
                file_path = os.path.join(root, filename)
                # Open and read the file, then append its content to the list
                with open(file_path, 'r', encoding='utf-8') as file:
                    kpi_values = json.load(file) 

            if kpi_values is not None and fnmatch.fnmatch(filename, 'data_for_scenario_evaluation.json'):  # Match specific file pattern (e.g., *.txt)
                file_path_1 = os.path.join(root, filename)
                # Open and read the file, then append its content to the list
                with open(file_path_1, 'r', encoding='utf-8') as file:
                    hisim_config_values = json.load(file)["myModuleConfig"]
                    hisim_config_values_str = str(hisim_config_values)
                    # make dict of these two
                    dicti = {hisim_config_values_str: kpi_values}
                    hisim_kpis.update(dicti)
                    # # avoid duplicated results
                    # if all_hisim_kpis_list != []:
                    #     for previous_hisim_kpi_dict in all_hisim_kpis_list:
                    #         if hisim_config_values_str not in previous_hisim_kpi_dict.keys():
                    #             print("new hisim results are appended to list. ")
                    #             hisim_kpis.update(dicti)
                    #         else:
                    #             print("hisim results are not appended because they already exist. ")

    return hisim_kpis


def get_rating(kpi_dict: Dict, request: BuildingSizerRequest) -> float:
    """Computes the fitness or rating of one individual (hisim configuration).

    :kpi: List of key performance indicatiors - results of HiSIM simulation.
    :type kpi: str
    :return: fitness or rating of the individual (hisim configuration)
    :rtype: float
    """

    return KPIConfig.from_dict(kpi_dict).get_kpi_for_rating(chosen_kpi=request.kpi_for_rating)  # type: ignore


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
    # with open(hisim_config_path, "r", encoding="utf-8") as json_file:
    #     modular_hh_config = json.load(json_file)
    sys_config = modular_hh_config_dict["energy_system_config_"]
    keys = [
        "heating_system",
        "share_of_maximum_pv_potential",
    ]
    minimal = {k: sys_config[k] for k in keys}
    hisim_config_json = json.dumps(minimal)
    d_config = json.loads(hisim_config_json)
    return d_config


def main(building_sizer_config_filename: str):
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

    # open json config
    my_config: BuildingSizerConfig
    if isinstance(building_sizer_config_filename, str) and os.path.exists(
        building_sizer_config_filename.rstrip("\r")
    ):
        with open(
            building_sizer_config_filename.rstrip("\r"), encoding="unicode_escape"
        ) as config_file:
            my_config_dict = json.load(config_file)
            my_config = BuildingSizerConfig.from_dict(my_config_dict)  # type: ignore
    else:
        raise FileNotFoundError(
            f"The building sizer config filepath does not exist or is not readable: {building_sizer_config_filename}"
        )
    # Get Hisim simulation parameters
    hisim_simulation_parameters = SimulationParameters.from_dict(
        my_config.hisim_simulation_parameters
    )
    # Create an initial simulation configuration for the building sizer
    initial_building_sizer_request = BuildingSizerRequest.from_dict(
        my_config.initial_building_sizer_request
    )
    # get hash value from building_sizer_config_filename
    bs_config_datetime_string = building_sizer_config_filename.split("/")[-2].split(
        "_"
    )[-1]
    bs_config_hash_string = re.findall(
        r"\-?\d+", building_sizer_config_filename.split("_")[-1]
    )[0]
    # create folder where everything related to this building sizer request is stored
    main_building_sizer_request_directory = os.path.join(
        os.path.abspath(os.path.join(os.getcwd(), os.pardir)),
        "building_sizer_results",
        f"bs_requests_{bs_config_datetime_string}",
        f"bs_request_{bs_config_hash_string}",
    )

    if not os.path.isdir(main_building_sizer_request_directory):
        os.makedirs(main_building_sizer_request_directory)
    else:
        print(
            f"The directory for the initial building sizer request {main_building_sizer_request_directory} already exists. It will be overwritten."
        )
    # save building sizer config file also in main building sizer request directory
    with open(os.path.join(main_building_sizer_request_directory, f"bs_config.json"), "w", encoding="utf-8") as file:
        json.dump(my_config_dict, file, ensure_ascii=False, indent=4)

    # building_sizer_config_json = initial_building_sizer_request.to_json()  # type: ignore
    building_sizer_request = initial_building_sizer_request

    # Store the hash of each request in a set for loop detection
    previous_iterations = {building_sizer_request.get_hash()}

    # Store all iterations of building sizer requests in order
    building_sizer_iterations: List[BuildingSizerRequest] = []
    finished = False
    all_ratings = ""
    all_hisim_kpis = []
    all_ratings_list = []
    start = datetime.now()
    while not finished:
        print("\n")
        print("-----------------------------")
        print("NEXT ITERATION")
        print("-----------------------------")
        print("\n")

        # Get result by calling building_sier_algorithm_no_utsp locally
        building_sizer_algorithm_no_utsp.main_without_utsp(
            request=building_sizer_request,
            main_building_sizer_request_directory=main_building_sizer_request_directory,
            hisim_simulation_parameters=hisim_simulation_parameters,
        )

        # Define the path to the result file
        result_file = os.path.join(
            main_building_sizer_request_directory, "results", "status.json"
        )

        # Once the job is finished, check if the result file exists
        timeout = 600  # Timeout in seconds (adjust as needed)
        start_time = time.time()
        while not os.path.exists(result_file):
            if time.time() - start_time > timeout:
                raise TimeoutError(
                    f"Result file '{result_file}' was not created within the timeout period."
                )
            print(f"Waiting for '{result_file}' to be created...")
            time.sleep(10)

        # Once the file exists, read it
        # Get the content of the result file created by the Building Sizer
        with open(result_file, "r", encoding="utf-8",) as file:
            status_json = json.load(file)
            print("File read successfully:", status_json)
        building_sizer_result: BuildingSizerResult = BuildingSizerResult.from_dict(status_json)  # type: ignore

        # Check if this was the final iteration and the building sizer is finished
        finished = building_sizer_result.finished
        # Get the building sizer configuration for the next request
        if building_sizer_result.subsequent_building_sizer_request is not None:
            # overwrite old building sizer request with new request
            building_sizer_request = (
                building_sizer_result.subsequent_building_sizer_request
            )
            # Loop detection: check if the same building sizer request has been encountered before (that would result in an endless loop)
            request_hash = building_sizer_request.get_hash()

            if request_hash in previous_iterations:
                raise RuntimeError(
                    f"Detected a loop: the following building sizer request has already been sent before.\n{building_sizer_request}"
                )
            previous_iterations.add(request_hash)

            # Store the building sizer
            building_sizer_iterations.append(building_sizer_request)
            print(f"Interim results: {building_sizer_result.result}")
            # store the hisim kpis of this iteration (generation)
            hisim_kpis_of_this_iteration = get_hisim_kpis_of_iteration(
                building_sizer_request,
                main_building_sizer_request_directory,
                hisim_simulation_parameters,
                all_hisim_kpis
            )
            all_ratings += f"{list(hisim_kpis_of_this_iteration.values())}\n"
            all_hisim_kpis.append(hisim_kpis_of_this_iteration)
            all_ratings_list.append(
                get_ratings(
                    hisim_kpis_of_this_iteration.values(), building_sizer_request
                )
            )
            for (
                hisim_config_str,
                kpi_result_dict,
            ) in hisim_kpis_of_this_iteration.items():
                print(
                    "ratings of energy system config for this iteration",
                    return_config_as_dict(hisim_config_str),
                    ": ",
                    str(building_sizer_request.kpi_for_rating.value),
                    "= ",
                    get_rating(kpi_result_dict, building_sizer_request),
                )
                print("---")

    print(f"Finished. Optimization took {datetime.now() - start}.")
    print("len all hisim kpis", len(all_hisim_kpis))
    print("len hisim kpis of this iteration ", len(hisim_kpis_of_this_iteration))
    plot_ratings_of_each_iteration_as_boxplots(all_ratings_list, main_building_sizer_request_directory, building_sizer_request)

    df_all_ratings = create_table_with_all_energy_system_configs_and_hisim_kpis(all_hisim_kpis, main_building_sizer_request_directory,building_sizer_request)
    plot_ratings_of_each_energy_system_config_as_scatterplot(dataframe_with_ratings=df_all_ratings, request=building_sizer_request, main_building_sizer_request_directory=main_building_sizer_request_directory)

def create_table_with_all_energy_system_configs_and_hisim_kpis(generations: Dict, main_building_sizer_request_directory: str, request: BuildingSizerRequest) -> pd.DataFrame:
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
            d_only_ratings = dict(d_config, **{f"{request.kpi_for_rating.value}": rating_kpi})
            d_only_ratings["iteration"] = iteration
            
            for name, value in d_total.items():
                if name not in all_data:
                    all_data[name] = []
                all_data[name].append(value)

            for name, value in d_only_ratings.items():
                if name not in only_ratings:
                    only_ratings[name] = []
                only_ratings[name].append(value)

    df = pd.DataFrame.from_dict(all_data)
    df_all_ratings = pd.DataFrame.from_dict(only_ratings)
    df.to_csv(
        os.path.join(
            main_building_sizer_request_directory, "building_sizer_results.csv"
        )
    )
    return df_all_ratings


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Building sizer algorithm needs one argument.")
        sys.exit(1)
    BUILDING_SIZER_CONFIG_FILENAME = sys.argv[1]
    print("start building sizer with config " + BUILDING_SIZER_CONFIG_FILENAME)
    main(building_sizer_config_filename=BUILDING_SIZER_CONFIG_FILENAME)
