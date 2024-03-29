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
from typing import Any, Dict, List, Optional, Tuple

import dataclasses_json
from hisim.modular_household.interface_configs import (  # type: ignore
    archetype_config,
    kpi_config,
    modular_household_config,
    system_config,
)
from utspclient import client  # type: ignore
from utspclient.datastructures import (
    CalculationStatus,
    ResultDelivery,
    ResultFileRequirement,
    TimeSeriesRequest,
)

from building_sizer import individual_encoding, evolutionary_algorithm as evo_alg


@dataclasses_json.dataclass_json
@dataclasses.dataclass
class BuildingSizerRequest:
    """
    A request object for the building sizer. Contains all necessary data for
    a single building sizer iteration. Can be used to create the request object
    for the subsequent iteration.
    """
    #: url for connection to the UTSP
    url: str
    #: password for the connection to the UTSP
    api_key: str = ""
    #: Version of the building sizer
    building_sizer_version: str = ""
    #: Version of HiSIM the building sizer calls upon
    hisim_version: str = ""
    #: number of iterations the evolutionary algorithm should have
    remaining_iterations: int = 3
    #: number of iterations where the decision of which components to use is evaluated.
    boolean_iterations: int = 3
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
    options: individual_encoding.SizingOptions = dataclasses.field(
        default=individual_encoding.SizingOptions()
    )

    # parameters for HiSim
    #: builing parameters of HiSIM (independet of system config, climate, house type, etc. need to be defined)
    archetype_config_: Optional[archetype_config.ArcheTypeConfig] = None

    # stores the HiSim requests triggered in earlier iterations
    #: HiSim requests from earlier iterations
    requisite_requests: List[TimeSeriesRequest] = dataclasses.field(
        default_factory=list
    )

    def create_subsequent_request(
        self, hisim_requests: List[TimeSeriesRequest]
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
            requisite_requests=hisim_requests,
        )


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
    subsequent_request: Optional[TimeSeriesRequest] = None
    #: placeholder for results of the building sizer
    result: Any = None


def send_hisim_requests(
    system_configs: List[system_config.SystemConfig], request: BuildingSizerRequest
) -> List[TimeSeriesRequest]:
    """
    Creates and sends one time series request to the utsp for every passed hisim configuration

    :param system_confgis: list of HiSIM system configurations (individuals)
    :type system_configs: List[system_config.SystemConfig]
    :param request: request to the Building Sizer
    :type request: BuildingSizerRequest
    :return: list of HiSIM requests
    :rtype: List[TimeSeriesRequest]

    """
    # Determine the provider name for the hisim request
    provider_name = "hisim"
    if request.hisim_version:
        # If a hisim version is specified, use that version
        provider_name += f"-{request.hisim_version}"
    # Create modular household configs for hisim request
    configs = [
        modular_household_config.ModularHouseholdConfig(
            system_config, request.archetype_config_
        )
        for system_config in system_configs
    ]
    # Prepare the time series requests
    hisim_requests = [
        TimeSeriesRequest(
            sim_config.to_json(),  # type: ignore
            provider_name,
            required_result_files={"kpi_config.json": ResultFileRequirement.REQUIRED},
        )
        for sim_config in configs
    ]
    # Send the requests
    for hisim_request in hisim_requests:
        reply = client.send_request(request.url, hisim_request, request.api_key)
        assert reply.status not in [
            CalculationStatus.CALCULATIONFAILED,
            CalculationStatus.UNKNOWN,
        ], (
            f"Sending the following hisim request returned {reply.status}:\n"
            f"{hisim_request.simulation_config}\nError message: {reply.info}"
        )
    return hisim_requests


def send_building_sizer_request(
    request: BuildingSizerRequest, hisim_requests: List[TimeSeriesRequest]
) -> TimeSeriesRequest:
    """
    Sends the request for the next building_sizer iteration to the UTSP, including the previously sent hisim requests.

    :param request: request to the Building Sizer
    :type request: BuildingSizerRequest
    :param hisim_requests: list of HiSIM requests
    :type hisim_requests: List[TimeSeriesRequest]
    :return: request to the building sizer
    :rtype: TimeSeriesRequest
    """
    subsequent_request_config = request.create_subsequent_request(hisim_requests)
    config_json: str = subsequent_request_config.to_json()  # type: ignore
    # Determine the provider name for the building sizer
    provider_name = "building_sizer"
    if request.building_sizer_version:
        # If a building sizer version is specified, use that version
        provider_name += f"-{request.building_sizer_version}"
    next_request = TimeSeriesRequest(config_json, provider_name)
    client.send_request(request.url, next_request, request.api_key)
    return next_request


def get_results_from_requisite_requests(
    requisite_requests: List[TimeSeriesRequest], url: str, api_key: str = ""
) -> Dict[str, ResultDelivery]:
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
    return {
        request.simulation_config: client.request_time_series_and_wait_for_delivery(
            url, request, api_key
        )
        for request in requisite_requests
    }


def trigger_next_iteration(
    request: BuildingSizerRequest, hisim_configs: List[system_config.SystemConfig]
) -> TimeSeriesRequest:
    """
    Sends the specified HiSim requests to the UTSP, and afterwards sends the request for the next building sizer iteration.

    :param hisim_configs: the requisite HiSim requests started by the last iteration
    :type hisim_configs: List[str]
    :return: the building sizer request for the next iteration
    :rtype: TimeSeriesRequest
    """
    # Send the new requests to the UTSP
    hisim_requests = send_hisim_requests(hisim_configs, request)
    # Send a new building_sizer request to trigger the next building sizer iteration. This must be done after sending the
    # requisite hisim requests to guarantee that the UTSP will not be blocked.
    return send_building_sizer_request(request, hisim_requests)


def decide_on_mode(
    iteration: int, boolean_iterations: int, discrete_iterations: int
) -> str:
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
    iteration_in_subiteration = iteration % (boolean_iterations + discrete_iterations)
    if iteration_in_subiteration > discrete_iterations:
        return "bool"
    else:
        return "discrete"


def building_sizer_iteration(
    request: BuildingSizerRequest,
) -> Tuple[Optional[TimeSeriesRequest], Any]:
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
    results = get_results_from_requisite_requests(
        request.requisite_requests, request.url, request.api_key
    )

    # Get the relevant result files from all requisite requests and turn them into rated individuals
    rated_individuals = []
    for sim_config_str, result in results.items():

        # Extract the rating for each HiSim config
        # TODO: check if rating works
        kpi_instance: kpi_config.KPIConfig = kpi_config.KPIConfig.from_json(result.data["kpi_config.json"].decode())  # type: ignore
        rating = kpi_instance.get_kpi()
        config: modular_household_config.ModularHouseholdConfig = modular_household_config.ModularHouseholdConfig.from_json(sim_config_str)  # type: ignore
        individual = individual_encoding.create_individual_from_config(
            config.system_config_, request.options
        )
        r = individual_encoding.RatedIndividual(individual, rating)
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
        r_cross=request.crossover_probability,
        r_mut=request.mutation_probability,
        mode=decide_on_mode(
            iteration=request.remaining_iterations,
            boolean_iterations=request.boolean_iterations,
            discrete_iterations=request.discrete_iterations,
        ),
        options=request.options,
    )

    # combine combine parents and children
    new_individuals.extend(parent_individuals)

    # delete duplicates
    new_individuals = evo_alg.unique(new_individuals)

    # TODO: termination condition; exit, when the overall calculation is over
    if request.remaining_iterations == 0:
        return None, "my final results"

    # convert individuals back to HiSim SystemConfigs
    hisim_configs: List[system_config.SystemConfig] = []
    for individual in new_individuals:
        system_config_instance = individual_encoding.create_config_from_individual(
            individual, request.options
        )
        hisim_configs.append(system_config_instance)

    # trigger the next iteration with the new hisim configurations
    next_request = trigger_next_iteration(request, hisim_configs)
    # return the building sizer request for the next iteration, and the result of this iteration
    return next_request, f"my interim results ({request.remaining_iterations})"


def main():
    """One iteration in the building sizer."""

    # Read the request file
    input_path = "/input/request.json"
    with open(input_path) as input_file:
        request_json = input_file.read()
    request: BuildingSizerRequest = BuildingSizerRequest.from_json(request_json)  # type: ignore
    # Check if there are hisim requests from previous iterations
    if request.requisite_requests:
        # Execute one building sizer iteration
        next_request, result = building_sizer_iteration(request)
    else:
        # First iteration; initialize algorithm and specify initial hisim requests
        initial_hisim_configs = individual_encoding.create_random_system_configs(
            request.population_size, request.options
        )
        next_request = trigger_next_iteration(request, initial_hisim_configs)
        result = "My first iteration result"

    # Create result file specifying whether a further iteration was triggered
    finished = next_request is None
    building_sizer_result = BuildingSizerResult(finished, next_request, result)
    building_sizer_result_json = building_sizer_result.to_json()  # type: ignore

    with open("/results/status.json", "w+") as result_file:
        result_file.write(building_sizer_result_json)


if __name__ == "__main__":
    main()
