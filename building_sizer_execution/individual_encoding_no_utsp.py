"""
Translation of HiSIM system configurations to boolean and discrete vectors, which can be treated by the evolutionary algorithms, and back.
Classes to gather information needed for the Translator as well as combine informations describing individuals.
(HiSIM system config, boolean and discrete vectors as well as fitness or rating)
"""

import json
import sys
import random
from dataclasses import dataclass, field
from typing import List

from dataclasses_json import dataclass_json

sys.path.append("/fast/home/k-rieck/repositories/HiSim")
from hisim.building_sizer_utils.interface_configs.system_config import (
    EnergySystemConfig,
)
from hisim.loadtypes import HeatingSystems, ComponentType


class BuildingSizerException(Exception):
    """Exception for errors in the Building Sizer."""


@dataclass_json
@dataclass
class SizingOptions:
    """Contains all relevant information to encode and decode system configs."""

    #: list of all shares of maximum rooftop PV power potential
    share_of_maximum_pv_potential: List[float] = field(
        default_factory=lambda: [round(i * 0.1, 1) for i in range(11)]
    )
    #: list of heating system for space heating and domestic hot water
    heating_system: List[HeatingSystems] = field(
        default_factory=lambda: [HeatingSystems.HEAT_PUMP, HeatingSystems.GAS_HEATING]
    )
    #: list of heat distribution systems
    heat_distribution_system: List[ComponentType] = field(
        default_factory=lambda: [
            ComponentType.HEAT_DISTRIBUTION_SYSTEM_FLOORHEATING,
            ComponentType.HEAT_DISTRIBUTION_SYSTEM_RADIATOR,
        ]
    )
    #: list of bools indicating if battery and energy management system (EMS) are included
    use_battery_and_ems: List[bool] = (field(default_factory=lambda: [True, False]),)

    #: list of technologies with different sizing options (discrete attributes) used within the optimization
    discrete_attributes: List[str] = field(
        default_factory=lambda: [
            "share_of_maximum_pv_potential",
            "heating_system",
            "heat_distribution_system",
            "use_battery_and_ems",
        ]
    )
    # this list defines the probabilites of each component to be included at the beginning
    #: defines probability of each component to be considered at the initial configurations
    # probabilities: List[float] = field(default_factory=lambda: [0.8, 0.4])

    # def __post_init__(self):
    #     """Checks if every element of attribute list bool_attributes and list discrete_attributes
    #     is also attribute of class EnergySystemConfig."""
    #     for name in self.bool_attributes + self.discrete_attributes:
    #         if not hasattr(EnergySystemConfig, name):
    #             raise Exception(
    #                 f"Invalid vector attribute: SystemConfig has no member '{name}'"
    #             )
    #     for name in self.discrete_attributes:
    #         if not hasattr(self, name):
    #             raise Exception(
    #                 f"Missing list of allowed values: SizingOptions has no member '{name} '"
    #                 f"specifying allowed values for the attribute of the same name"
    #             )


@dataclass_json
@dataclass
class Individual:
    """System config as numerical vectors."""

    discrete_vector: List[float] = field(default_factory=list)

    @staticmethod
    def create_random_individual(options: SizingOptions) -> "Individual":
        """Creates random individual.

        :param options: Contains all available options for the sizing of each component.
        :tpye options: SizingOptions

        :return: Individual with bool and discrete vector.
        :rtype individual: Individual
        """
        individual = Individual()
        discrete_vector = []

        # We'll store values temporarily by name
        temp_values = {}

        for component in options.discrete_attributes:
            allowed_values = getattr(options, component)

            if component == "share_of_maximum_pv_potential":
                pv_share = random.choice(allowed_values)
                temp_values[component] = pv_share
                discrete_vector.append(pv_share)

            elif component == "use_battery_and_ems":
                pv_share = temp_values.get("share_of_maximum_pv_potential", 0)
                if pv_share == 0.0:
                    battery_allowed_values = [False]
                else:
                    battery_allowed_values = getattr(options, component)
                battery_choice = random.choice(battery_allowed_values)
                discrete_vector.append(battery_choice)

            else:
                discrete_vector.append(random.choice(allowed_values))

        individual.discrete_vector = discrete_vector
        return individual

        # for component in options.discrete_attributes:
        #     allowed_values = getattr(options, component)
        #     individual.discrete_vector.append(random.choice(allowed_values))
        # return individual


@dataclass_json
@dataclass
class RatedIndividual:
    """System config as numerical vectors with associated fitness function value."""

    #: the individual object, containing a system config encoded as numerical vectors
    individual: Individual
    #: the fitness function value of the individual
    rating: float


def create_individual_from_config(
    system_config: EnergySystemConfig, options: SizingOptions
) -> Individual:
    """Creates discrete and boolean vector from given SystemConfig.

    :parameter system_config: Household System configuration - input to HiSIM simulation.
    :type system_config: SystemConfig
    :parameter options: Contains all available options for the sizing of each component.
    :type options: SizingOptions

    :return: Individual with bool and discrete vector.
    :rtype: Individual
    """
    # bool_vector: List[bool] = [
    #     getattr(system_config, name) for name in options.bool_attributes
    # ]
    discrete_vector: List[float] = [
        getattr(system_config, name) for name in options.discrete_attributes
    ]
    return Individual(discrete_vector)  # Individual(bool_vector, discrete_vector)


def create_config_from_individual(
    individual: Individual, options: SizingOptions
) -> EnergySystemConfig:
    """
    Creates a SystemConfig object from the bool and discrete vectors of an
    Individual object. For this, the SizingOptions object is needed.

    :param individual: Individual with bool and discrete vector.
    :tpye individual: Individual
    :param options: Contains all available options for the sizing of each component.
    :type options: SizingOptions

    :return: Household System configuration - input to HiSIM simulation.
    :rtype: SystemConfig
    """
    # create a default SystemConfig object
    system_config = EnergySystemConfig()
    # assign the bool attributes
    # assert len(options.bool_attributes) == len(
    #     individual.bool_vector
    # ), "Invalid individual: wrong number of bool parameters"
    # for i, name in enumerate(options.bool_attributes):
    #     setattr(system_config, name, individual.bool_vector[i])
    # assign the discrete attributes
    assert len(options.discrete_attributes) == len(
        individual.discrete_vector
    ), "Invalid individual: wrong number of discrete parameters"
    for i, name in enumerate(options.discrete_attributes):
        setattr(system_config, name, individual.discrete_vector[i])
    return system_config


def create_random_system_configs(
    number: int, options: SizingOptions
) -> List[EnergySystemConfig]:
    """
    Creates the desired number of random individuals (HiSIM system configurations).

    :param number: number of individuals in a population
    :type number: int
    :param options: Contains all available options for the sizing of each component.
    :type options: SizingOptions
    :return: list of HiSIM system configurations providing input to HiSIM simulations
    :rtype: hisim_configs: List[SystemConfig]
    """
    hisim_configs = []
    for _ in range(number):
        # Create a random Individual
        individual = Individual.create_random_individual(options)
        # Convert the Individual to a SystemConfig object and
        # append it to the list
        hisim_configs.append(create_config_from_individual(individual, options))
    return hisim_configs


def save_system_configs_to_file(configs: List[str]) -> None:
    """Writes List of system configurations to json file.

    :param congigs: List of system configurations, in string formaat.
    :type configs: List[str]
    """
    with open("./random_system_configs.json", "w", encoding="utf-8") as f:
        json.dump(configs, f)
