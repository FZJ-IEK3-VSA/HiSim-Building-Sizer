"""Run HiSim simulation."""
# Add the parent directory to the system path
import sys
import re
import os
import json
from typing import Dict, Optional
sys.path.append("/fast/home/k-rieck/repositories/HiSim")
from hisim.building_sizer_utils.interface_configs.system_config import (
    EnergySystemConfig,
)
from hisim.building_sizer_utils.interface_configs.archetype_config import (
    ArcheTypeConfig,
)
from hisim.building_sizer_utils.interface_configs.modular_household_config import (
    ModularHouseholdConfig,
)
from hisim.building_sizer_utils.interface_configs.kpi_config import KPIConfig
from hisim import hisim_main
from hisim.simulationparameters import SimulationParameters
from hisim.postprocessingoptions import PostProcessingOptions
from hisim.result_path_provider import (
    ResultPathProviderSingleton,
    SortingOptionEnum,
)
from hisim import log

def run_hisim_simulation_and_collect_kpis(
    hisim_config_path: str, household_module: str, main_building_sizer_request_directory: str, result_dict_path: str) -> Dict[str, Dict]:
    """
    Collects the results from the HiSim request.
    """
    # run HiSim for each config and get kpis and store in dictionary
    # set simulation parameters here
    year = 2021
    seconds_per_timestep = 60 * 15
    my_simulation_parameters = SimulationParameters.one_day_only(
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
        PostProcessingOptions.COMPUTE_KPIS)
    my_simulation_parameters.post_processing_options.append(
        PostProcessingOptions.WRITE_KPIS_TO_JSON
    )
    my_simulation_parameters.post_processing_options.append(
        PostProcessingOptions.WRITE_KPIS_TO_JSON_FOR_BUILDING_SIZER
    )
    # set logging level to 1
    my_simulation_parameters.logging_level = 3
    household_module = household_module
    path_to_module = f"/fast/home/k-rieck/repositories/HiSim/system_setups/{household_module}.py"
    # set hisim results directory
    # if requisite_hisim_config_path is given, get hash number and sampling mode for result path
    if hisim_config_path is not None:
        config_filename_splitted = hisim_config_path.split("/")
        scenario_hash_string = re.findall(r"\-?\d+", config_filename_splitted[-1])[
            0
        ]
        further_result_folder_description = config_filename_splitted[-2]

    hisim_result_directory = os.path.join(
        main_building_sizer_request_directory, "hisim_results"
    )

    ResultPathProviderSingleton().set_important_result_path_information(
        module_directory=hisim_result_directory,
        model_name=household_module,
        further_result_folder_description=os.path.join(
            *[further_result_folder_description,]
        ),
        variant_name="_",
        scenario_hash_string=scenario_hash_string,
        sorting_option=SortingOptionEnum.MASS_SIMULATION_WITH_HASH_ENUMERATION,
    )
    # make dir if not exist yet
    if not os.path.isdir(ResultPathProviderSingleton().get_result_directory_name()):
        os.makedirs(ResultPathProviderSingleton().get_result_directory_name())
    my_simulation_parameters.result_directory = (
        ResultPathProviderSingleton().get_result_directory_name()
    )
    # run hisim simulation
    hisim_main.main(
        path_to_module=path_to_module,
        my_module_config=hisim_config_path,
        my_simulation_parameters=my_simulation_parameters,
    )

    # get results for each simulation
    kpi_json = "kpi_config_for_building_sizer.json"
    with open(
        os.path.join(my_simulation_parameters.result_directory, kpi_json),
        "r",
        encoding="utf-8",
    ) as result_file:
        kpis_building_sizer = json.load(result_file)
    # add configs and respective kpis to dictionary
    current_result_dict = {hisim_config_path: kpis_building_sizer}


    # Step 2: Open the JSON file, read the content, and load it into a Python dictionary
    with open(result_dict_path, 'r') as file:
        data = json.load(file)

    # Step 3: Append the new dictionary (this assumes `data` is a dictionary)
    data.update(current_result_dict)

    # Step 4: Write the updated dictionary back to the JSON file
    with open(result_dict_path, 'w') as file:
        json.dump(data, file, indent=4)
        print(f"write {data} to {result_dict_path}")

if __name__ == "__main__":
    if len(sys.argv) < 5:
        log.information("HiSim simulation script needs four arguments.")
        sys.exit(1)
    HISIM_CONFIG_PATH = sys.argv[1]
    HOUSEHOLD_MODULE = sys.argv[2]
    MAIN_REQUEST_DIRECTORY = sys.argv[3]
    RESULT_DICT_PATH = sys.argv[4]

    print("calling " + HOUSEHOLD_MODULE + " with config " + HISIM_CONFIG_PATH + " and request directory " + MAIN_REQUEST_DIRECTORY)
    run_hisim_simulation_and_collect_kpis(hisim_config_path=HISIM_CONFIG_PATH,
                                          household_module=HOUSEHOLD_MODULE,
                                          main_building_sizer_request_directory=MAIN_REQUEST_DIRECTORY,
                                          result_dict_path=RESULT_DICT_PATH)


