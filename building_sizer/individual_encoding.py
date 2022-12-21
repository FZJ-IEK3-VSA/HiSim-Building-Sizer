import json
import random
from dataclasses import dataclass, field
from typing import List

from dataclasses_json import dataclass_json
from hisim.modular_household.interface_configs.system_config import SystemConfig  # type: ignore


class BuildingSizerException(Exception):

    """Exception for errors in the Building Sizer."""


@dataclass_json
@dataclass
class SizingOptions:

    """Contains all relevant information to encode and decode system configs."""

    pv_peak_power: List[float] = field(
        default_factory=lambda: [6e2, 1.2e3, 1.8e3, 3e3, 6e3, 9e3, 12e3, 15e3]
    )
    battery_capacity: List[float] = field(
        default_factory=lambda: [0.3, 0.6, 1.5, 3, 5, 7.5, 10, 15]
    )
    buffer_volume: List[float] = field(
        default_factory=lambda: [200, 300, 500, 750, 1000, 1500, 3000]
    )
    # these lists define the layout of the individual vectors
    bool_attributes: List[str] = field(
        default_factory=lambda: ["pv_included", "battery_included"]
    )
    discrete_attributes: List[str] = field(
        default_factory=lambda: ["pv_peak_power", "battery_capacity"]
    )
    # this list defines the probabilites of each component to be included at the beginning
    probabilities: List[float] = field(default_factory=lambda: [0.8, 0.4])

    def __post_init__(self):
        """Checks if every element of attribute list bool_attributes and list discrete_attributes
        is also attribute of class SystemConfig."""
        for name in self.bool_attributes + self.discrete_attributes:
            if not hasattr(SystemConfig, name):
                raise Exception(
                    f"Invalid vector attribute: SystemConfig has no member '{name}'"
                )
        for name in self.discrete_attributes:
            if not hasattr(self, name):
                raise Exception(
                    f"Missing list of allowed values: SizingOptions has no member '{name} '"
                    f"specifying allowed values for the attribute of the same name"
                )


@dataclass_json
@dataclass
class Individual:

    """System config as numerical vectors."""

    bool_vector: List[bool] = field(default_factory=list)
    discrete_vector: List[float] = field(default_factory=list)

    @staticmethod
    def create_random_individual(options: SizingOptions) -> "Individual":
        """Creates random individual.

        Parameters
        ----------
        options: SizingOptions
            Instance of dataclass sizing options.
            It contains a list of all available options for sizing of each component.

        """
        individual = Individual()
        # randomly assign the bool attributes True or False
        assert len(options.probabilities) == len(options.bool_attributes), (
            "Invalid SizingOptions: members probabilities and bool_attributes have different length. "
            "There must be one probability for each bool attribute."
        )
        for probability in options.probabilities:
            dice = random.uniform(0, 1)  # random number between zero and one
            individual.bool_vector.append(dice < probability)
        # randomly assign the discrete attributes depending on the allowed values
        for component in options.discrete_attributes:
            allowed_values = getattr(options, component)
            individual.discrete_vector.append(random.choice(allowed_values))
        return individual


@dataclass_json
@dataclass
class RatedIndividual:

    """System config as numerical vectors with assosiated fitness function value."""

    individual: Individual
    rating: float


def create_individual_from_config(
    system_config: SystemConfig, options: SizingOptions
) -> Individual:
    """Creates discrete and boolean vector from given SystemConfig."""
    bool_vector: List[bool] = [
        getattr(system_config, name) for name in options.bool_attributes
    ]
    discrete_vector: List[float] = [
        getattr(system_config, name) for name in options.discrete_attributes
    ]
    return Individual(bool_vector, discrete_vector)


def create_config_from_individual(
    individual: Individual, options: SizingOptions
) -> SystemConfig:
    """
    Creates a SystemConfig object from the bool and discrete vectors of an
    Individual object. For this, the SizingOptions object is needed.
    """
    # create a default SystemConfig object
    system_config = SystemConfig()
    # assign the bool attributes
    assert len(options.bool_attributes) == len(
        individual.bool_vector
    ), "Invalid individual: wrong number of bool parameters"
    for i, name in enumerate(options.bool_attributes):
        setattr(system_config, name, individual.bool_vector[i])
    # assign the discrete attributes
    assert len(options.discrete_attributes) == len(
        individual.discrete_vector
    ), "Invalid individual: wrong number of discrete parameters"
    for i, name in enumerate(options.discrete_attributes):
        setattr(system_config, name, individual.discrete_vector[i])
    return system_config


def create_random_system_configs(
    number: int, options: SizingOptions
) -> List[SystemConfig]:
    """
    Creates the desired number of random SystemConfig objects
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
    with open("./random_system_configs.json", "w", encoding="utf-8") as f:
        json.dump(configs, f)
