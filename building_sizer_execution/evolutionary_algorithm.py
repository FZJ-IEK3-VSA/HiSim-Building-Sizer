""" 
Evolutionary algorithms evaluate the fitness of various individuals of a population - and inspired by biology - combine them randomly to a new generation.
The fitter the individuals the better the chance to propagate.
In this context an individual would be a specified building configurations for HiSIM calls
and the new generation is built by combination and variation of parameters in the building configuration.
This file incoporates one step of the evolutionary algorithm creating a new population based on a rated one.
In addition, the file includes all necesary functions for the evaluation step: mutation, crossover, selection,... .
"""

# -*- coding: utf-8 -*-
from typing import List, Tuple
import random

from building_sizer_execution import individual_encoding


def unique(
    individuals: List[individual_encoding.Individual],
) -> List[individual_encoding.Individual]:
    """
    Compares all individuals and deletes duplicates.

    :param rated_individuals: list of all individuals (HiSIM configurations) and KPIs (HiSIM results)
    :type rated_individuals: List[individual_encoding.RatedIndividual]
    :param population_size: amount of individuals to be selected
    :tpye population_size: int
    :return: shortened list of individuals (HiSIM configurations) and KPIs (HiSIM results) 
    :rtype: List[individual_encoding.RatedIndividual]

    """
    len_individuals = len(individuals)

    # get index of all duplicates
    delete_index = []
    for i in range(len_individuals):
        for j in range(i + 1, len_individuals):
            if individuals[i] == individuals[j]:
                delete_index.append(j)

    # select not duplicated values
    filtered_individuals = []
    for i in range(len_individuals):
        if i not in delete_index:
            filtered_individuals.append(individuals[i])
    return filtered_individuals


def selection(
    rated_individuals: List[individual_encoding.RatedIndividual], population_size: int
) -> List[individual_encoding.RatedIndividual]:
    """
    Selects best individuals.

    :param rated_individuals: list of all individuals
    :type rated_individuals: List[individual_encoding.RatedIndividual]
    :param population_size: amount of individuals to be selected
    :type population_size: int
    :return: list of individuals with best rating (fitness)
    :rtype: List[individual_encoding.RatedIndividual]

    """
    # Sort individuals decendingly using their rating
    individuals = sorted(rated_individuals, key=lambda ri: ri.rating, reverse=True)
    # Only select the best individuals, adhering to the population size
    individuals = individuals[:population_size]
    # shuffle the selected individuals to allow more variation during crossover
    random.shuffle(individuals)
    return individuals


def complete_population(
    original_parents: List[individual_encoding.Individual],
    population_size: int,
    options: individual_encoding.SizingOptions,
) -> List[individual_encoding.Individual]:
    """
    Adds random individuals to population, if the population size is too small.
    
    :param original_parents: list of individuals of original population
    :type original_parents: List[individual_encoding.Individual]
    :param population_size: number of individuals the population should finally contain
    :type population_size: int
    :param options: contains all available options for the sizing of each component.
    :type options: individual_encoding.SizingOptions:
    
    :return: list of individuals of the completed population
    :rtype: completed_population: List[individual_encoding.Individual]        
    """
    len_parents = len(original_parents)
    for _ in range(population_size - len_parents):
        individual = individual_encoding.Individual.create_random_individual(
            options=options
        )
        original_parents.append(individual)
    return original_parents


def crossover_conventional(
    parent1: individual_encoding.Individual, parent2: individual_encoding.Individual
) -> Tuple[individual_encoding.Individual, individual_encoding.Individual]:
    """
    Combines two individuals (parents) to two new individuals (children).
    This is done by randomly generating an index and exchanging parts of the bitstrings, which describe individuals.

    :param parent1: encoding of first parent used for cross over
    :type parent1: individual_encoding.RatedIndividual
    :param parent2: encoding of second parent used for cross over
    :type parent2: individual_encoding.RatedIndividual
    :return: encoding of childs resulting from cross over
    :rtype child1: Tuple[individual_encoding.RatedIndividual,individual_encoding.RatedIndividual]
    """
    vector_bool_1 = parent1.bool_vector[:]  # cloning all relevant lists
    vector_discrete_1 = parent1.discrete_vector[:]
    vector_bool_2 = parent2.bool_vector[:]  # cloning all relevant lists
    vector_discrete_2 = parent2.discrete_vector[:]

    # select cross over point, which is not exactly the end or the beginning of the string
    assert len(vector_bool_1) >= len(
        vector_discrete_1
    ), "Bool vector of one parent is shorter than discrete vector"
    crossover_pt = random.randint(1, len(vector_bool_1) - 1)

    # create children by cross over
    child_bool_1 = vector_bool_1[:crossover_pt] + vector_bool_2[crossover_pt:]
    child_bool_2 = vector_bool_2[:crossover_pt] + vector_bool_1[crossover_pt:]

    if crossover_pt < len(vector_discrete_1):
        # Additional discrete crossover only if the crossover point lies in the range of the bool_vector, where the bool-elements
        # have associated discrete elements.
        # Assumes that all bool elements with associated discrete elements are located in the beginning of the bool_vector.
        child_discrete_1 = (
            vector_discrete_1[:crossover_pt] + vector_discrete_2[crossover_pt:]
        )
        child_discrete_2 = (
            vector_discrete_2[:crossover_pt] + vector_discrete_1[crossover_pt:]
        )
    else:
        # no crossover among the discrete elements --> simply use the discrete vectors of the parents
        child_discrete_1 = vector_discrete_1
        child_discrete_2 = vector_discrete_2

    child1 = individual_encoding.Individual(
        bool_vector=child_bool_1, discrete_vector=child_discrete_1
    )
    child2 = individual_encoding.Individual(
        bool_vector=child_bool_2, discrete_vector=child_discrete_2
    )

    return child1, child2


def mutation_bool(
    parent: individual_encoding.Individual,
) -> individual_encoding.Individual:
    """
    Slightly changes individual by randomly changing one bit of the boolean bitstring, which describes an individual.

    :param parent: encoding of parent used for mutation
    :type parent: individual_encoding.Individual
    :return: encoding of first resulting child from cross over
    :rtype: individual_encoding.RatedIndividual
    """
    vector_bool = parent.bool_vector[:]
    bit = random.randint(0, len(vector_bool) - 1)
    vector_bool[bit] = not vector_bool[bit]
    child = individual_encoding.Individual(
        bool_vector=vector_bool, discrete_vector=parent.discrete_vector
    )
    return child


def mutation_discrete(
    parent: individual_encoding.Individual, options: individual_encoding.SizingOptions
) -> individual_encoding.Individual:
    """
    Slightly changes individual by randomly changing one bit of the discrete bitstring, which describes an individual.

    :param parent: encoding of parent used for mutation
    :type parent: individual_encoding.Individual
    :param options: contains all available options for the sizing of each component
    :type options: individual_encoding.SizingOptions
    :return: encoding of first resulting child from cross over
    :rtype: individual_encoding.RatedIndividual
    """
    vector_discrete = parent.discrete_vector[:]
    bit = random.randint(0, len(vector_discrete) - 1)

    vector_discrete[bit] = random.choice(
        getattr(options, options.discrete_attributes[bit])
    )
    child = individual_encoding.Individual(
        bool_vector=parent.bool_vector, discrete_vector=vector_discrete
    )
    return child


def evolution(
    parents: List[individual_encoding.Individual],
    r_cross: float,
    r_mut: float,
    mode: str,
    options: individual_encoding.SizingOptions,
) -> List[individual_encoding.Individual]:
    """
    One step of the evolutionary algorithm (evolution) not including the selection process.
    Random numbers are generated to decide if cross over, mutation or nothing is considered for the creation of a new generation.

    :param parents:  list of rated individuals
    :type parents: List[individual_encoding.RatedIndividual]
    :param r_cross: cross over probability.
    :type r_cross: float
    :param r_mut: mutation probability
    :type r_mut: float
    :param mode: iteration mode: "bool" or "discrete"
    :type mode: str
    :type options: contains all available options for the sizing of each component
    :type options: individual_encoding.SizingOptions
    :return: list of unrated individuals
    :rtype: List[individual_encoding.Individual]
    """

    # get array length
    len_parents = len(parents)
    # index to randomly select parents
    # maybe remove sel part because parents are already shuffeled (sel=0)
    sel = random.randint(0, len_parents - 1)
    # initialize new population
    children = []
    # initialize while loop
    pop = 0

    while pop < len_parents:
        # randomly generate number which indicates if cross over will happen or not...
        o = random.random()

        if o < r_cross:
            # initilize parents
            parent1 = parents[(sel + pop) % len_parents]
            parent2 = parents[(sel + pop + 1) % len_parents]
            # cross over: two children resulting from cross over are added to the family
            child1, child2 = crossover_conventional(parent1=parent1, parent2=parent2)
            # append children to new population
            children.append(child1)
            children.append(child2)
            pop = pop + 2

        elif o < (r_cross + r_mut):
            # choose individual for mutation
            parent = parents[(sel + pop) % len_parents]
            # mutation
            if mode == "bool":
                child = mutation_bool(parent=parent)
            elif mode == "discrete":
                child = mutation_discrete(parent=parent, options=options)
            else:
                raise ValueError(
                    "variable for mode is not defined, choose either discrete or bool."
                )
            children.append(child)
            pop = pop + 1

        else:
            pop = pop + 1

    return children
