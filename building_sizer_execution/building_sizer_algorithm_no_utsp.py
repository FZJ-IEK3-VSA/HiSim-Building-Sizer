"""
Building Sizer for use as a provider in the UTSP.
The Building Sizer works iteratively. In each iteration, the results of some HiSim calculations are processed: the "fitness" of each HiSIM configuration
is evaluated and the best configurations are selected. Depending on these, the next generation is created by one evolution of the evolutionary algorithm.
So, the next HiSim configurations that need to be calculated are determined and sent as requests to the UTSP. Afterwards, a new Building Sizer request
is sent to the UTSP for the next iteration. This Building Sizer request contains all previously sent HiSim requests so it can obtain the results
of these requests and work with them.
To allow the client who sent the initial Building Sizer request to follow the separate Building Sizer iterations, each iteration returns the request
for the next Building Sizer iteration as a result to the UTSP (and thereby also to the client).
"""

import dataclasses
import time
import subprocess
from typing import Any, Dict, List, Optional, Tuple
import json
import os
import dataclasses_json
import re
import sys
from building_sizer_execution import (
    individual_encoding_no_utsp,
    evolutionary_algorithm_no_utsp as evo_alg,
    hisim_simulation_no_utsp,
)

# Add the parent directory to the system path
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
from hisim.building_sizer_utils.interface_configs.kpi_config import (
    KPIConfig,
    KPIForRatingInOptimization,
)
from hisim import hisim_main
from hisim.simulationparameters import SimulationParameters
from hisim.postprocessingoptions import PostProcessingOptions
from hisim.result_path_provider import (
    ResultPathProviderSingleton,
    SortingOptionEnum,
)


@dataclasses_json.dataclass_json
@dataclasses.dataclass
class BuildingSizerRequest:
    """
    A request object for the building sizer. Contains all necessary data for
    a single building sizer iteration. Can be used to create the request object
    for the subsequent iteration.
    """

    #: number of iterations the evolutionary algorithm should have
    remaining_iterations: int = 3
    #: number of iterations where the decision of which size the components should have is evaluated
    discrete_iterations: int = 9

    # parameters for the evolutionary algorithm
    #: number of individuals considered in each population
    population_size: int = 5  # number of individuals to be created
    #: probability for each individual for doing crossover with the next individual
    crossover_probability: float = 0.2
    #: probability for each individual for mutating
    mutation_probability: float = 0.4
    #: SizingOptions object, containing information for decoding and encoding individuals
    options: individual_encoding_no_utsp.SizingOptions = dataclasses.field(
        default_factory=individual_encoding_no_utsp.SizingOptions()
    )
    #: kpi for rating simulation results
    kpi_for_rating: KPIForRatingInOptimization = KPIForRatingInOptimization.TOTAL_COSTS
    # parameters for HiSim
    #: builing parameters of HiSIM (independet of system config, climate, house type, etc. need to be defined)
    archetype_config_: Optional[ArcheTypeConfig] = None
    # stores the HiSim requests triggered in earlier iterations
    #: HiSim requests from earlier iterations
    requisite_hisim_config_paths: List[str] = dataclasses.field(default_factory=list)

    def get_hash(self):
        """Generate a hash for BuildingSizerRequest."""
        request = BuildingSizerRequest(
            self.remaining_iterations,
            self.discrete_iterations,
            self.population_size,
            self.crossover_probability,
            self.mutation_probability,
            self.options,
            self.archetype_config_,
            self.requisite_hisim_config_paths,
            self.kpi_for_rating,
        )
        config_str = json.dumps(request.to_dict())
        config_str_hash = hash(config_str)
        return config_str_hash

    def create_subsequent_request(
        self, hisim_config_paths: List[str]
    ) -> "BuildingSizerRequest":
        """
        Creates a request object for the next building sizer iteration.
        Copies all properties except for the requisite hisim requests and remaining_iterations.

        :param hisim_requests: the hisim requests that are required for the next iteration
        :type hisim_requests: List[TimeSeriesRequest]
        :return: the request object for the next iteration
        :rtype: BuildingSizerRequest
        """
        return dataclasses.replace(
            self,
            remaining_iterations=self.remaining_iterations - 1,
            requisite_hisim_config_paths=hisim_config_paths,
        )


@dataclasses_json.dataclass_json
@dataclasses.dataclass
class BuildingSizerConfig:
    """
    Building sizer config class containing the initial building sizer request and the hisim simulation parameters.
    """

    initial_building_sizer_request: Dict
    hisim_simulation_parameters: Dict


@dataclasses_json.dataclass_json
@dataclasses.dataclass
class BuildingSizerResult:
    """
    Result object of the building sizer. Contains all results of a single building
    sizer iteration. The finished flag indicates whether it was the final iteration.
    If not, the building sizer request for the subsequent iteration is contained in
    the property subsequent_request.
    """

    #: status of building sizer iteration
    finished: bool
    #: placeholder for hisim configurations, matching the results
    subsequent_building_sizer_request: Optional[BuildingSizerRequest] = None
    #: placeholder for results of the building sizer
    result: Any = None


def create_hisim_configs(
    system_configs: List[EnergySystemConfig],
    request: BuildingSizerRequest,
    main_building_sizer_request_directory: str,
) -> List[str]:
    """
    Creates and sends one time series request to the utsp for every passed hisim configuration

    :param system_confgis: list of HiSIM system configurations (individuals)
    :type system_configs: List[system_config.SystemConfig]
    :param request: request to the Building Sizer
    :type request: BuildingSizerRequest
    :return: list of HiSIM requests
    :rtype: List[TimeSeriesRequest]

    """

    # Create modular household configs for hisim request
    hisim_configs = [
        ModularHouseholdConfig(system_config, request.archetype_config_)
        for system_config in system_configs
    ]

    hisim_config_paths: List[str] = []

    # save configs in folder
    for config in hisim_configs:
        # get hash for each config
        config_hash = config.get_hash()
        # make configs directory
        directory_name = os.path.join(
            main_building_sizer_request_directory, "cluster_modular_configs"
        )
        if not os.path.isdir(directory_name):
            os.makedirs(directory_name)
        filename = os.path.join(directory_name, f"config_{config_hash}.json")
        hisim_config_paths.append(filename)
        with open(filename, "w", encoding="utf-8") as config_file:
            json.dump(config.to_dict(), config_file, indent=4)

    return hisim_config_paths


def create_subsequent_building_sizer_request(
    request: BuildingSizerRequest, hisim_config_paths: List[str]
) -> BuildingSizerRequest:
    """
    Sends the request for the next building_sizer iteration to the UTSP, including the previously sent hisim requests.

    :param request: request to the Building Sizer
    :type request: BuildingSizerRequest
    :param hisim_requests: list of HiSIM requests
    :type hisim_requests: List[TimeSeriesRequest]
    :return: request to the building sizer
    :rtype: TimeSeriesRequest
    """
    subsequent_building_sizer_request = request.create_subsequent_request(
        hisim_config_paths
    )

    return subsequent_building_sizer_request


def get_results_from_requisite_hisim_configs(
    requisite_hisim_config_paths: List[str], main_building_sizer_request_directory: str, hisim_simulation_parameters: SimulationParameters
) -> Dict[str, Dict]:
    """
    Collects the results from the HiSim requests sent in the previous iteration.

    :param requisite_requests: List of previous HiSIM requests
    :type requisite_requests: List[TimeSeriesRequest]
    :param url: url for connection to the UTSP
    :type url: str
    :param api_key: password for the connection to the UTSP
    :type api_key: str
    :return: dictionary of processed hisim requests (HiSIM results)
    :rtype: Dict[str, ResultDelivery]
    """
    # run HiSim for each config and get kpis and store in dictionary
    # set result dictionary
    result_dict: Dict = {}

    for index, hisim_config_path in enumerate(requisite_hisim_config_paths):
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
        household_module = "household_gas_or_heatpump"
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
        hisim_simulation_parameters.result_directory = (
            ResultPathProviderSingleton().get_result_directory_name()
        )
        # run hisim simulation
        hisim_main.main(
            path_to_module=f"/fast/home/k-rieck/repositories/HiSim/system_setups/{household_module}.py",
            my_module_config=hisim_config_path,
            my_simulation_parameters=hisim_simulation_parameters,
        )
        print(f"-----hisim simualtion {index} finsihed!-----", "\n", "\n")
        # get results for each simulation
        kpi_json = "kpi_config_for_building_sizer.json"
        with open(
            os.path.join(hisim_simulation_parameters.result_directory, kpi_json),
            "r",
            encoding="utf-8",
        ) as result_file:
            kpis_building_sizer = json.load(result_file)
        # add configs and respective kpis to dictionary
        result_dict.update({hisim_config_path: kpis_building_sizer})
    return result_dict


def get_results_from_requisite_hisim_configs_slurm(
    requisite_hisim_config_paths: List[str],
    main_building_sizer_request_directory: str,
    hisim_simulation_parameters: SimulationParameters,
) -> Dict[str, Dict]:
    """
    Collects the results from the HiSim requests sent in the previous iteration.

    :param requisite_requests: List of previous HiSIM requests
    :type requisite_requests: List[TimeSeriesRequest]
    :param url: url for connection to the UTSP
    :type url: str
    :param api_key: password for the connection to the UTSP
    :type api_key: str
    :return: dictionary of processed hisim requests (HiSIM results)
    :rtype: Dict[str, ResultDelivery]
    """
    # run HiSim for each config and get kpis and store in dictionary
    # Step 1: Check if result_dict_path exists, if not create an empty dict in it
    result_dict_path = os.path.join(
        main_building_sizer_request_directory, "result_dict.json"
    )
    result_dict: Dict = {}
    if not os.path.exists(result_dict_path):
        with open(result_dict_path, "w") as file:
            json.dump(result_dict, file)
    job_ids = []
    for index, hisim_config_path in enumerate(requisite_hisim_config_paths):
        # Get result by calling building_sizer_algorithm_no_utsp on cluster
        # Serialize the `building_sizer_request` object to a JSON string
        json_hisim_params = json.dumps(hisim_simulation_parameters.to_dict())
        # SLURM script to execute
        slurm_script = "/fast/home/k-rieck/HiSim-Building-Sizer/cluster_requests/job_array_hisim_simulation.sh"

        # Call the SLURM script with subprocess and pass the two parameters
        slurm_result_hisim_simulation = subprocess.run(
            [
                "sbatch",
                slurm_script,
                hisim_config_path,
                "household_gas_or_heatpump",
                main_building_sizer_request_directory,
                result_dict_path,
                json_hisim_params,
            ],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Extract the job ID from the output of `sbatch`
        # if stdout is none check if any errors occured
        if slurm_result_hisim_simulation.stdout is None:
            print(f"Error: {slurm_result_hisim_simulation.stderr}")
        job_id = slurm_result_hisim_simulation.stdout.strip().split()[-1]
        print(f"Submitted SLURM job with ID {job_id}")
        job_ids.append(job_id)
    # Get the job state from the output
    # job_state = slurm_result_hisim_simulation.stdout.strip()
    # print("job state ", job_state)
    print("job ids", job_ids)
    # Wait for all SLURM jobs in job_ids to finish.
    while True:
        all_done = True
        for job_id in job_ids:
            # Check the status of a SLURM job using sacct.#
            try:
                result = subprocess.run(
                    ["squeue", "-j", str(job_id), "--noheader"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                # Get the job state from the output
                job_state = result.stdout.strip()
                print("job state while checking status", job_state)
            except subprocess.CalledProcessError as e:
                print(f"Error checking job status for {job_id}: {e}")
                job_state = None

            if job_state not in ["COMPLETED", "FAILED", "CANCELLED", ""]:
                all_done = False
                break

        if all_done:
            print("All jobs are done.")
            break
        else:
            print("Waiting for jobs to finish...")
            time.sleep(30)  # Wait for 1 minute before checking again

    # Once the job is finished, check if the result file exists
    timeout = 600  # Timeout in seconds (adjust as needed)
    start_time = time.time()
    while not result_dict:
        with open(result_dict_path, "r", encoding="utf-8") as result_file:
            result_dict = json.load(result_file)
        if time.time() - start_time > timeout:
            raise TimeoutError(
                f"Result dict {result_dict_path} was not filled within the timeout period."
            )
        print(f"Waiting for result dict {result_dict_path} to be filled with values...")
        time.sleep(10)

    if result_dict:
        return result_dict
    else:
        raise ValueError("Result dict is empty ", result_dict)


def trigger_next_iteration(
    request: BuildingSizerRequest,
    hisim_configs: List[EnergySystemConfig],
    main_building_sizer_request_directory: str,
) -> BuildingSizerRequest:
    """
    Sends the specified HiSim requests to the UTSP, and afterwards sends the request for the next building sizer iteration.

    :param hisim_configs: the requisite HiSim requests started by the last iteration
    :type hisim_configs: List[str]
    :return: the building sizer request for the next iteration
    :rtype: TimeSeriesRequest
    """
    # Send the new requests to the UTSP
    hisim_config_paths = create_hisim_configs(
        hisim_configs, request, main_building_sizer_request_directory
    )
    # Send a new building_sizer request to trigger the next building sizer iteration. This must be done after sending the
    # requisite hisim requests to guarantee that the UTSP will not be blocked.
    return create_subsequent_building_sizer_request(request, hisim_config_paths)


def decide_on_mode() -> str:  # (iteration: int, discrete_iterations: int) -> str:
    """Decides if iteration is boolean (which technology is included) or discrete (what size does the technology have).

    :param iteration: building sizer iteration
    :type iteration: int
    :param boolean_iterations: number of subsequent boolean iterations
    :type boolean_iterations: int
    :param discrete_iterations: number of subsequent discrete iterations
    :type discrete_iterations: int
    :return: iteration mode: "bool" or "discrete"
    :rtype: str
    """
    # no boolean system config values used here so far
    return "discrete"


def building_sizer_iteration(
    request: BuildingSizerRequest,
    main_building_sizer_request_directory: str,
    hisim_simulation_parameters: SimulationParameters,
) -> Tuple[Optional[BuildingSizerRequest], Any]:
    """
    Executes one iteration of the building sizer. Collects the results from all
    requisite hisim requests, selects the best individuals, generates new individuals
    using a genetic algorithm and finally sends the next hisim requests and building sizer
    request to the UTSP (if not in the last iteration).

    :param request: the request object for this iteration
    :type request: BuildingSizerRequest
    :return: the request object for the next building sizer iteration (if there is one), and
             the result of this iteration
    :rtype: Tuple[Optional[TimeSeriesRequest], Any]
    """
    print("RUN HISIM SIMU IN ITERATION TO FIND BEST INDIVIDUALS.")
    result_dict = get_results_from_requisite_hisim_configs_slurm(
        request.requisite_hisim_config_paths,
        main_building_sizer_request_directory,
        hisim_simulation_parameters,
    )
    print("result dict length after serialized slurm jobs", len(result_dict))
    # result_dict = get_results_from_requisite_hisim_configs(
    #     request.requisite_hisim_config_paths,
    #     main_building_sizer_request_directory,
    #     hisim_simulation_parameters,
    # )

    # Get the relevant result files from all requisite requests and turn them into rated individuals
    rated_individuals = []
    for sim_config_str, kpi_result in result_dict.items():

        # Extract the rating for each HiSim config
        # TODO: check if rating works
        kpi_instance: KPIConfig = KPIConfig.from_dict(kpi_result)  # type: ignore
        rating = kpi_instance.get_kpi_for_rating(chosen_kpi=request.kpi_for_rating)
        with open(sim_config_str, "r", encoding="utf-8") as hisim_config:
            config: ModularHouseholdConfig = ModularHouseholdConfig.from_dict(json.load(hisim_config))  # type: ignore
        individual = individual_encoding_no_utsp.create_individual_from_config(
            config.energy_system_config_, request.options
        )
        r = individual_encoding_no_utsp.RatedIndividual(individual, rating)
        rated_individuals.append(r)

    # select best individuals
    parents = evo_alg.selection(
        rated_individuals=rated_individuals, population_size=request.population_size
    )

    # pass individuals to genetic algorithm and receive list of new individuals back
    parent_individuals = [ri.individual for ri in parents]

    # add random individuals to complete the population, in case too many individual were duplicates
    # parent_individuals = evo_alg.complete_population(
    #     original_parents=parent_individuals,
    #     population_size=population_size,
    #     options=options,
    # )

    new_individuals = evo_alg.evolution(
        parents=parent_individuals,
        crossover_probability=request.crossover_probability,
        mutation_probability=request.mutation_probability,
        mode=decide_on_mode(),
        options=request.options,
    )

    # combine combine parents and children
    new_individuals.extend(parent_individuals)

    # delete duplicates
    new_individuals = evo_alg.unique(new_individuals)

    # TODO: termination condition; exit, when the overall calculation is over
    print(f"---remaing iterations, {request.remaining_iterations}")
    if request.remaining_iterations == 0:
        return None, "my final results"

    # convert individuals back to HiSim SystemConfigs
    hisim_configs: List[EnergySystemConfig] = []
    for individual in new_individuals:
        system_config_instance = individual_encoding_no_utsp.create_config_from_individual(
            individual, request.options
        )
        hisim_configs.append(system_config_instance)

    # trigger the next iteration with the new hisim configurations
    next_building_sizer_request = trigger_next_iteration(
        request, hisim_configs, main_building_sizer_request_directory
    )
    # return the building sizer request for the next iteration, and the result of this iteration
    return (
        next_building_sizer_request,
        f"my interim results ({request.remaining_iterations})",
    )


def main_without_utsp(
    request: BuildingSizerRequest,
    main_building_sizer_request_directory: str,
    hisim_simulation_parameters: SimulationParameters,
):
    """One iteration in the building sizer."""

    # Check if there are hisim requests from previous iterations
    if request.requisite_hisim_config_paths:
        # Execute one building sizer iteration
        (
            next_building_sizer_request,
            remaining_iterations_message,
        ) = building_sizer_iteration(
            request, main_building_sizer_request_directory, hisim_simulation_parameters
        )
    else:
        # First iteration; initialize algorithm and specify initial hisim requests
        initial_hisim_energy_system_configs = individual_encoding_no_utsp.create_random_system_configs(
            request.population_size, request.options
        )

        next_building_sizer_request = trigger_next_iteration(
            request,
            initial_hisim_energy_system_configs,
            main_building_sizer_request_directory,
        )
        remaining_iterations_message = "My first iteration result"

    # Create result file specifying whether a further iteration was triggered
    finished = next_building_sizer_request is None
    building_sizer_result = BuildingSizerResult(
        finished, next_building_sizer_request, remaining_iterations_message
    )

    building_sizer_result_json = building_sizer_result.to_json()  # type: ignore
    # Write results in path
    path = os.path.join(main_building_sizer_request_directory, "results", "status.json")
    isExist = os.path.exists(path)
    if not isExist:
        # Create a new directory because it does not exist
        os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w+", encoding="utf-8") as result_file:
        result_file.write(building_sizer_result_json)
