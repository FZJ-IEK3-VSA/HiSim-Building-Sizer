"""Sends a building sizer request to the UTSP and waits until the calculation is finished."""

import json
from datetime import datetime
from typing import Dict, Iterable, List

import matplotlib.pyplot as plt  # type: ignore
import pandas as pd
from hisim.modular_household.interface_configs import kpi_config  # type: ignore
from utspclient import client  # type: ignore
from utspclient.datastructures import TimeSeriesRequest  # type: ignore

from building_sizer_execution import building_sizer_algorithm, individual_encoding
from building_sizer_execution.building_sizer_algorithm import (
    BuildingSizerRequest,
    BuildingSizerResult,
)

# Define URL and API key for the UTSP server
URL = "http://134.94.131.167:443/api/v1/profilerequest"
API_KEY = ""


def plot_ratings(ratings: List[List[float]]) -> None:
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


def get_ratings_of_generation(
    building_sizer_config: BuildingSizerRequest,
) -> Dict[str, str]:
    """
    Returns the KPIs (results of HiSIM calculation) for one generation of HiSim configurations

    :param building_sizer_config: the building sizer request for the generation
    :type building_sizer_config: BuildingSizerRequest
    :return: a dict mapping each HiSim configuration to its KPIs
    :rtype: Dict[float]
    """
    hisim_results = building_sizer_algorithm.get_results_from_requisite_requests(
        building_sizer_config.requisite_requests, URL, API_KEY
    )
    # Extract the rating for each HiSim config
    ratings = {
        config: result.data["kpi_config.json"].decode()
        for config, result in hisim_results.items()
    }
    return ratings


def get_rating(kpi: str) -> float:
    """Computes the fitness or rating of one individual (hisim configuration).

    :kpi: List of key performance indicatiors - results of HiSIM simulation.
    :type kpi: str
    :return: fitness or rating of the individual (hisim configuration)
    :rtype: float
    """

    return kpi_config.KPIConfig.from_json(kpi).get_kpi()  # type: ignore


def get_ratings(kpis: Iterable[str]) -> List[float]:
    """Computes the fitness or rating of multiple individuals (hisim configurations).

    :kpis: List of HiSIM simulation results (key performance indicatiors).
    :type kpis: str
    :return: list of fitness or rating of the individuals (hisim configurations)
    :rtype: List[float]
    """

    return [get_rating(s) for s in kpis]


def minimize_config(hisim_config: str) -> str:
    """
    Helper method for testing, that extracts only the relevant fields of a system config
    to print them in a clearer way.
    :param hisim_config: a system configuration of HiSIM
    :type hisim_config: str
    :return: a system configuration of HiSIM containing only the parameters changing within the evolutionary algorithm
    :rtype: str
    """

    modular_hh_config = json.loads(hisim_config)
    sys_config = modular_hh_config["system_config_"]
    keys = [
        "pv_included",
        "pv_peak_power",
        "battery_included",
        "battery_capacity",
        # "ev_included",
    ]
    minimal = {k: sys_config[k] for k in keys}
    return json.dumps(minimal)


def main():
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

    guid = ""  # .join(random.choices(string.ascii_uppercase + string.digits, k=10))

    # Set the parameters for the building sizer
    hisim_version = ""
    building_sizer_version = ""
    options = individual_encoding.SizingOptions()
    # options.probabilities.extend([0.5])
    # options.bool_attributes.extend(["ev_included"])

    # Create an initial simulation configuration for the building sizer
    initial_building_sizer_config = BuildingSizerRequest(
        URL,
        API_KEY,
        building_sizer_version,
        hisim_version,
        remaining_iterations=12,
        boolean_iterations=3,
        discrete_iterations=5,
        population_size=5,
        crossover_probability=0.2,
        mutation_probability=0.4,
        options=options,
        archetype_config_=None,
    )
    building_sizer_config_json = initial_building_sizer_config.to_json()  # type: ignore
    provider_name = "building_sizer" + (
        f"-{building_sizer_version}" if building_sizer_version else ""
    )
    # Create the initial building sizer request
    building_sizer_request = TimeSeriesRequest(
        building_sizer_config_json, provider_name, guid=guid,
    )

    # Store the hash of each request in a set for loop detection
    previous_iterations = {building_sizer_request.get_hash()}

    # Store all iterations of building sizer requests in order
    building_sizer_iterations: List[BuildingSizerRequest] = []
    finished = False
    all_ratings = ""
    generations = []
    all_ratings_list = []
    start = datetime.now()
    while not finished:
        # Wait until the request finishes and the results are delivered
        result = client.request_time_series_and_wait_for_delivery(
            URL, building_sizer_request, API_KEY
        )
        # Get the content of the result file created by the Building Sizer
        status_json = result.data["status.json"].decode()
        building_sizer_result: BuildingSizerResult = BuildingSizerResult.from_json(status_json)  # type: ignore
        # Check if this was the final iteration and the building sizer is finished
        finished = building_sizer_result.finished
        # Get the building sizer configuration for the next request
        if building_sizer_result.subsequent_request is not None:
            building_sizer_request = building_sizer_result.subsequent_request
            # Loop detection: check if the same building sizer request has been encountered before (that would result in an endless loop)
            request_hash = building_sizer_request.get_hash()
            if request_hash in previous_iterations:
                raise RuntimeError(
                    f"Detected a loop: the following building sizer request has already been sent before.\n{building_sizer_request}"
                )
            previous_iterations.add(request_hash)

            # Store the building sizer config
            building_sizer_config = BuildingSizerRequest.from_json(building_sizer_request.simulation_config)  # type: ignore
            building_sizer_iterations.append(building_sizer_config)
        print(f"Interim results: {building_sizer_result.result}")
        # store the ratings of this generation
        generation = get_ratings_of_generation(building_sizer_config)
        all_ratings += f"{list(generation.values())}\n"
        generations.append(generation)
        all_ratings_list.append(get_ratings(generation.values()))
        for bs_config, kpis in generation.items():
            print(minimize_config(bs_config), " - ", get_rating(kpis))
            print("---")

    print(f"Finished. Optimization took {datetime.now() - start}.")
    print(all_ratings)
    plot_ratings(all_ratings_list)

    create_table(generations)


def create_table(generations):
    """
    Writes csv containing all kpi values (HiSIM results) of all individuals (HiSim configuration) of each generation (iteration).

    :param generation: List of all individuals (HiSIM configurations) and KPIs (HiSIM results) in each generation (iteartion)
    :type generation: List[Dict[str, str]]
    """
    data: dict = {}
    for iteration, generation in enumerate(generations):
        for config, kpi in generation.items():
            config = minimize_config(config)
            d_config = json.loads(config)
            d_kpi = json.loads(kpi)
            d_total = dict(d_config, **d_kpi)
            d_total["iteration"] = iteration
            for name, value in d_total.items():
                if name not in data:
                    data[name] = []
                data[name].append(value)

    df = pd.DataFrame.from_dict(data)
    print(df)
    df.to_csv("./building_sizer_results.csv")


if __name__ == "__main__":
    main()
