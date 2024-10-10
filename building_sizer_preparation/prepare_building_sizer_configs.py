"""Module to prepare building sizer configs."""
import sys
import os
import json
import datetime
import csv
from typing import Dict, List
from building_sizer_execution.building_sizer_algorithm_no_utsp import (
    BuildingSizerRequest,
)
from building_sizer_execution.individual_encoding_no_utsp import SizingOptions

# Add the parent directory to the system path
sys.path.append("/fast/home/k-rieck/repositories/HiSim")
from hisim.simulationparameters import SimulationParameters
from hisim.postprocessingoptions import PostProcessingOptions
from hisim.building_sizer_utils.interface_configs.archetype_config import (
    ArcheTypeConfig,
)
from hisim.building_sizer_utils.interface_configs.kpi_config import (
    KPIForRatingInOptimization,
)


def collect_archetype_configs(path_to_archetype_config_collection: str) -> List[Dict]:
    """Read archetpye configs (building configs) from config collection.
    The configs should be in json format.
    """
    list_with_building_archetype_configs: List[Dict] = []
    # Loop through the directory
    for filename in os.listdir(path_to_archetype_config_collection):
        if filename.endswith(".json"):  # Check if the file is a JSON file
            file_path = os.path.join(path_to_archetype_config_collection, filename)
            with open(file_path, "r", encoding="utf-8") as archetype_config_file:
                household_config_dict = json.load(archetype_config_file)
                list_with_building_archetype_configs.append(household_config_dict)
    return list_with_building_archetype_configs


def write_job_array_config_file(
    job_array_config_folder: str, directory_with_all_configs: str, timestamp: str
):
    """Write job array config file."""
    # make filename
    if not os.path.exists(job_array_config_folder):
        os.makedirs(job_array_config_folder)
    job_array_config_csv_file = os.path.join(
        job_array_config_folder, f"bs_job_array_{timestamp}.csv"
    )
    index = 1
    # open the file of the job array config
    with open(job_array_config_csv_file, "w", encoding="utf-8") as file:

        # write header of the job array config file
        writer = csv.writer(file)
        writer.writerow(["ArrayTaskID", "HiSimConfigPath"])
        # iterate over all the config paths
        for index, config_path in enumerate(os.listdir(directory_with_all_configs)):
            # write job_array config with task array and path
            writer.writerow(
                [str(index), os.path.join(directory_with_all_configs, config_path)]
            )
            index = index + 1


def generate_configs_for_building_sizer_request(
    path_to_archetype_config_collection: str,
    path_to_save_building_sizer_configs: str,
    initial_building_sizer_request: BuildingSizerRequest,
    hisim_simulation_parameters: SimulationParameters,
):
    """Create configs for building sizer requests for each building archetype."""
    # get dict of hisim simulation parameters
    hisim_simu_params_dict: Dict = {
        "hisim_simulation_parameters": hisim_simulation_parameters.to_dict()
    }
    # iterate over building archetype configs
    list_with_building_archetype_configs = collect_archetype_configs(
        path_to_archetype_config_collection=path_to_archetype_config_collection
    )
    for index, building_archetype_config in enumerate(
        list_with_building_archetype_configs
    ):

        # get dict of initial building sizer request and add building archetype dict to intial building sizer request
        building_archetype_config: ArcheTypeConfig = ArcheTypeConfig.from_dict(
            building_archetype_config
        )
        initial_building_sizer_request.archetype_config_ = building_archetype_config
        initial_building_sizer_request_dict: Dict = {
            "initial_building_sizer_request": initial_building_sizer_request.to_dict()
        }

        # combine all data and make one big dict and save as json
        combined_dict = {
            **initial_building_sizer_request_dict,
            **hisim_simu_params_dict,
        }

        # get hash of combined dict
        config_str = json.dumps(combined_dict, indent=4)
        config_str_hash = hash(config_str)
        # prepare folder to save
        now = datetime.datetime.now().strftime("%Y%m%d-%H%M")
        folder = os.path.join(
            path_to_save_building_sizer_configs, f"bs_request_configs_{now}"
        )
        if not os.path.exists(folder):
            os.makedirs(folder)

        # save combined dict as json
        json_filename = os.path.join(folder, f"bs_request_{config_str_hash}.json")
        with open(json_filename, "w", encoding="utf-8") as config_file:
            config_file.write(config_str)
    # write all config filepaths to csv to create job array
    job_array_config_folder = os.path.abspath(
        os.path.join(path_to_save_building_sizer_configs, os.pardir, "bs_job_arrays")
    )
    write_job_array_config_file(
        job_array_config_folder=job_array_config_folder,
        directory_with_all_configs=folder,
        timestamp=now,
    )
    print("Generation of building sizer configs was successful.")


def main():
    """Run config generation for building sizer execution."""
    # -----------------------------------------------------------------------------------------------------------
    # Create an initial simulation configuration for the building sizer
    options = SizingOptions()
    initial_building_sizer_request = BuildingSizerRequest(
        remaining_iterations=6,
        discrete_iterations=6,
        population_size=6,
        crossover_probability=0.5,
        mutation_probability=0.5,
        options=options,
        kpi_for_rating=KPIForRatingInOptimization.INVESTMENT_COSTS,
    )
    # -----------------------------------------------------------------------------------------------------------
    # Set hisim simulation parameters
    year = 2021
    seconds_per_timestep = 60 * 15
    my_simulation_parameters = SimulationParameters.full_year(
        year=year, seconds_per_timestep=seconds_per_timestep
    )
    # set postprocessing options
    my_simulation_parameters.post_processing_options.append(
        PostProcessingOptions.PREPARE_OUTPUTS_FOR_SCENARIO_EVALUATION
    )
    my_simulation_parameters.post_processing_options.append(
        PostProcessingOptions.COMPUTE_OPEX
    )
    my_simulation_parameters.post_processing_options.append(
        PostProcessingOptions.COMPUTE_CAPEX
    )
    my_simulation_parameters.post_processing_options.append(
        PostProcessingOptions.COMPUTE_KPIS
    )
    my_simulation_parameters.post_processing_options.append(
        PostProcessingOptions.WRITE_KPIS_TO_JSON
    )
    my_simulation_parameters.post_processing_options.append(
        PostProcessingOptions.WRITE_KPIS_TO_JSON_FOR_BUILDING_SIZER
    )
    # set logging level to 1
    my_simulation_parameters.logging_level = 3
    # -----------------------------------------------------------------------------------------------------------
    # path to building archetype collection
    path_to_archetype_config_collection = "/fast/home/k-rieck/jobs_hisim/cluster-hisim-paper/job_array_for_hisim_mass_simus/hisim_config_collection/builda_samples_20240924_1024_for_building_sizer"
    # path to building sizer configs
    path_to_save_building_sizer_configs = (
        "/fast/home/k-rieck/HiSim-Building-Sizer/building_sizer_preparation/bs_configs"
    )
    print(
        "Start generation of building sizer configs with: \n"
        f"initial building sizer request {initial_building_sizer_request} \n"
        f"hisim simulation parameters {my_simulation_parameters}."
    )
    generate_configs_for_building_sizer_request(
        path_to_archetype_config_collection=path_to_archetype_config_collection,
        path_to_save_building_sizer_configs=path_to_save_building_sizer_configs,
        initial_building_sizer_request=initial_building_sizer_request,
        hisim_simulation_parameters=my_simulation_parameters,
    )
    # -----------------------------------------------------------------------------------------------------------


if __name__ == "__main__":
    main()
