"""Sends a building sizer request to the UTSP and waits until the calculation is finished."""
import sys
import json
import os
from datetime import datetime
from typing import Dict, List

import matplotlib.pyplot as plt  # type: ignore
import pandas as pd
from building_sizer import building_sizer_algorithm_no_utsp, individual_encoding_no_utsp
from building_sizer.building_sizer_algorithm_no_utsp import (
    BuildingSizerRequest,
    BuildingSizerResult,
)

# Add the parent directory to the system path
sys.path.append("/fast/home/k-rieck/repositories/HiSim")
from hisim.building_sizer_utils.interface_configs.archetype_config import (
    ArcheTypeConfig,
)
from hisim.building_sizer_utils.interface_configs.kpi_config import KPIConfig


def plot_ratings(ratings: List[List[float]], main_building_sizer_request_directory: str) -> None:
    """
    Generate a boxplot for each generation showing the range of ratings

    :param ratings: nested list, creating a list of ratings for each generation
    :type ratings: List[List[float]]
    """
    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_subplot(111)
    ax.set_xlabel("Iterations")
    ax.set_ylabel("self consumption rate + autarky rate [%]")
    # Creating plot
    _ = ax.boxplot(ratings)  # type: ignore
    # show plot
    plt.show()
    plt.savefig(os.path.join(main_building_sizer_request_directory, "ratings_plot.png"))


def get_ratings_of_generation(
    building_sizer_request: BuildingSizerRequest,
    main_building_sizer_request_directory: str,
) -> Dict[str, str]:
    """
    Returns the KPIs (results of HiSIM calculation) for one generation of HiSim configurations

    :param building_sizer_config: the building sizer request for the generation
    :type building_sizer_config: BuildingSizerRequest
    :return: a dict mapping each HiSim configuration to its KPIs
    :rtype: Dict[float]
    """
    ratings = building_sizer_algorithm_no_utsp.get_results_from_requisite_hisim_configs(
        requisite_hisim_config_paths=building_sizer_request.requisite_hisim_config_paths,
        main_building_sizer_request_directory=main_building_sizer_request_directory,
    )

    return ratings


def get_rating(kpi_dict: Dict) -> float:
    """Computes the fitness or rating of one individual (hisim configuration).

    :kpi: List of key performance indicatiors - results of HiSIM simulation.
    :type kpi: str
    :return: fitness or rating of the individual (hisim configuration)
    :rtype: float
    """

    return KPIConfig.from_dict(kpi_dict).get_kpi()  # type: ignore


def get_ratings(kpis_dicts: List[Dict]) -> List[float]:
    """Computes the fitness or rating of multiple individuals (hisim configurations).

    :kpis: List of HiSIM simulation results (key performance indicatiors).
    :type kpis: str
    :return: list of fitness or rating of the individuals (hisim configurations)
    :rtype: List[float]
    """

    return [get_rating(kpi_dict) for kpi_dict in kpis_dicts]


def minimize_config(hisim_config_path: str) -> str:
    """
    Helper method for testing, that extracts only the relevant fields of a system config
    to print them in a clearer way.
    :param hisim_config: a system configuration of HiSIM
    :type hisim_config: str
    :return: a system configuration of HiSIM containing only the parameters changing within the evolutionary algorithm
    :rtype: str
    """

    with open(hisim_config_path, "r", encoding="utf-8") as json_file:
        modular_hh_config = json.load(json_file)
    sys_config = modular_hh_config["energy_system_config_"]
    keys = [
        "space_heating_system",
        "domestic_hot_water_heating_system",
        "share_of_maximum_pv_potential",
    ]
    minimal = {k: sys_config[k] for k in keys}
    return json.dumps(minimal)


def main(archetype_config: ArcheTypeConfig = ArcheTypeConfig()):
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

    options = individual_encoding_no_utsp.SizingOptions()

    # Create an initial simulation configuration for the building sizer
    initial_building_sizer_request = BuildingSizerRequest(
        remaining_iterations=10,
        discrete_iterations=10,
        population_size=3,
        crossover_probability=0.5,
        mutation_probability=0.5,
        options=options,
        archetype_config_=archetype_config,
    )
    # create folder where everything related to this building sizer request is stored
    main_building_sizer_request_directory = os.path.join(
        os.getcwd(), f"bs_request_{initial_building_sizer_request.get_hash()}"
    )
    if not os.path.isdir(main_building_sizer_request_directory):
        os.makedirs(main_building_sizer_request_directory)
    else:
        raise ValueError(
            f"The directory for the initial building sizer request {initial_building_sizer_request.get_hash()} already exists. It should not exist twice."
        )
    # save initial building sizer request
    with open(
        os.path.join(
            main_building_sizer_request_directory, "initial_building_sizer_request.json"
        ),
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(initial_building_sizer_request.to_dict(), file, indent=4)

    # building_sizer_config_json = initial_building_sizer_request.to_json()  # type: ignore
    building_sizer_request = initial_building_sizer_request

    # # Store the hash of each request in a set for loop detection
    previous_iterations = {building_sizer_request.get_hash()}

    # Store all iterations of building sizer requests in order
    building_sizer_iterations: List[BuildingSizerRequest] = []
    finished = False
    all_ratings = ""
    generations = []
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
        )

        # Get the content of the result file created by the Building Sizer
        # status_json = result.data["status.json"].decode()
        with open(
            os.path.join(
                main_building_sizer_request_directory, "results", "status.json"
            ),
            "r",
            encoding="utf-8",
        ) as file:
            status_json = json.load(file)
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
            # store the ratings of this generation
            generation = get_ratings_of_generation(
                building_sizer_request, main_building_sizer_request_directory
            )
            all_ratings += f"{list(generation.values())}\n"
            generations.append(generation)
            all_ratings_list.append(get_ratings(generation.values()))
            for hisim_config_path, kpi_result_dict in generation.items():
                print(
                    "ratings ",
                    minimize_config(hisim_config_path),
                    " - ",
                    get_rating(kpi_result_dict),
                )
                print("---")

    print(f"Finished. Optimization took {datetime.now() - start}.")
    plot_ratings(all_ratings_list, main_building_sizer_request_directory)

    create_table(generations, main_building_sizer_request_directory)


def create_table(generations: Dict, main_building_sizer_request_directory: str):
    """
    Writes csv containing all kpi values (HiSIM results) of all individuals (HiSim configuration) of each generation (iteration).

    :param generation: List of all individuals (HiSIM configurations) and KPIs (HiSIM results) in each generation (iteartion)
    :type generation: List[Dict[str, str]]
    """
    data: dict = {}
    for iteration, generation in enumerate(generations):
        for hisim_config_path, kpi_dict in generation.items():
            hisim_config_json = minimize_config(hisim_config_path)
            d_config = json.loads(hisim_config_json)
            d_kpi = kpi_dict
            d_total = dict(d_config, **d_kpi)
            d_total["iteration"] = iteration
            for name, value in d_total.items():
                if name not in data:
                    data[name] = []
                data[name].append(value)

    df = pd.DataFrame.from_dict(data)
    print(df)
    df.to_csv(
        os.path.join(
            main_building_sizer_request_directory, "building_sizer_results.csv"
        )
    )


if __name__ == "__main__":
    main()
