from src.GA.Chromosome import Chromosome
from src.helper_classes.TableHeaders import TableHeaders
import src.constants as constants
from random import random


def calculate_fitness_by_params(zero_stress, zero_mass, stress, mass, calc_param, body_params):
    # # Get best location (area↑, size↑, stress↓, mass↓)
    # fitness = body_params.area * calc_param.volume_part * 1/stress * 1/mass
    #
    # # Get best location (area↑, size↑, stress↓)
    # fitness = body_params.area * calc_param.volume_part * 1/stress

    # Get best location (area↑, size↑, amount↑, stress↓)
    fitness = body_params.area * calc_param.volume_part * calc_param.cells_ox * calc_param.cells_oy * 1/stress
    return fitness  # TODO: add GUI switchers for this


def remap(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min


def start_new_generation(table_data, full_table):
    best_parents_data = p1_data, p2_data = selection_by_best_fitness(table_data)
    parent1, parent2 = create_agent_from_table_data(p1_data), create_agent_from_table_data(p2_data)
    index1, index2 = full_table.index(p1_data), full_table.index(p2_data)

    # Create new generation
    if constants.SAVE_PARENTS:
        new_generation = [parent1, parent2] + crossover_from_best(parent1, parent2, constants.POPULATION_SIZE - 2)
    else:
        new_generation = crossover_from_best(parent1, parent2, constants.POPULATION_SIZE)

    table_data_new = []
    for agent in new_generation:
        new_data_int = create_data_from_agent(agent)
        new_data_str = list(map(str, new_data_int))
        table_data_new.append(new_data_str)

    if constants.SAVE_PARENTS:
        for i in range(2):
            table_data_new[i][TableHeaders.STATUS] = f"Parent {i + 1}"
            table_data_new[i][TableHeaders.STRESS] = str(best_parents_data[i][TableHeaders.STRESS])
            table_data_new[i][TableHeaders.FITNESS] = str(best_parents_data[i][TableHeaders.FITNESS])

    return table_data_new, index1, index2


def create_data_from_agent(agent):
    (x0, x1), (y0, y1) = agent.working_zone
    return [agent.angles, agent.rotation, agent.size, agent.x_amount, agent.y_amount,
            x0, x1, y0, y1, constants.Z_MIN, constants.Z_MAX, '', '', '']


def find_max_fitness(table_data):
    return max(table_data, key=lambda x: float(x[TableHeaders.FITNESS]))


def selection_by_best_fitness(table_data):
    parent1 = find_max_fitness(table_data)
    table_data.remove(parent1)
    parent2 = find_max_fitness(table_data)
    return parent1, parent2


def create_agent_from_table_data(table_data):
    # Create new agent
    agent = Chromosome()

    # Read data
    x_start = float(table_data[TableHeaders.DETAIL_X0])
    x_end = float(table_data[TableHeaders.DETAIL_X1])
    y_start = float(table_data[TableHeaders.DETAIL_Y0])
    y_end = float(table_data[TableHeaders.DETAIL_Y1])

    # Add data from table to agent
    agent.working_zone = ((x_start, x_end), (y_start, y_end))
    agent.angles = int(table_data[TableHeaders.ANGLE_NUM])
    agent.rotation = int(table_data[TableHeaders.ROTATE_ANGLE])
    agent.size = int(table_data[TableHeaders.VOLUME_PART])
    agent.x_amount = int(table_data[TableHeaders.CELLS_OX])
    agent.y_amount = int(table_data[TableHeaders.CELLS_OY])
    return agent


def crossover_from_best(parent1, parent2, pop_size):
    new_generation = []
    for i in range(pop_size):
        agent = Chromosome()
        agent.crossover_two_parents(parent1, parent2)
        if random() <= constants.MUT_CHANSE / 100:
            agent.mutate_all_parameters()
        new_generation.append(agent)
    return new_generation
