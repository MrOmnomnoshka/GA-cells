from src.GA.Agent import Agent
from src.helper_classes.TableHeaders import TableHeaders
import src.constants as constants
from random import random
from copy import deepcopy


def calculate_fitness_by_params(zero_stress, zero_mass, stress_f, mass_f, cells_params):
    # Get best location by UI switches

    volume = pow(cells_params.volume, constants.FIT_VOLUME)
    size = pow(cells_params.volume_part, constants.FIT_SIZE)
    amount = pow(cells_params.amount, constants.FIT_AMOUNT)
    mass = pow(mass_f, constants.FIT_MASS)
    stress = pow(stress_f, constants.FIT_STRESS)
    fitness = volume * size * amount * mass * stress
    bias = 100  # For more relevant (beautiful) values
    print(volume, size, amount, mass, stress, fitness)
    return fitness * bias


def remap(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min


def start_new_generation(table_data, elite_list):
    table_data_new = []

    if constants.SAVE_ELITE:  # Elites goes on top of a table
        table_data_new = deepcopy(elite_list)

    while len(table_data_new) < constants.POPULATION_SIZE:
        # best_parents_data = p1_data, p2_data = selection_by_best_fitness(deepcopy(table_data))
        p1_data, p2_data = selection_by_roulette(table_data)
        parent1, parent2 = create_agent_from_table_data(p1_data), create_agent_from_table_data(p2_data)

        # Create new child by crossover
        agent = crossover(parent1, parent2)

        # Mutate child
        mutate(agent)

        # Accumulate all new data
        new_data_int = create_data_from_agent(agent)
        new_data_str = list(map(str, new_data_int))

        # Check is new one is already exist. Remake from scratch if it does
        if new_data_str[:-3] in [exist[:-3] for exist in table_data_new]:  # [:-3] -> ignore stress, status, fitness
            continue

        table_data_new.append(new_data_str)

    if constants.SAVE_ELITE:
        for i in range(len(elite_list)):
            table_data_new[i][TableHeaders.STATUS] = f"Elite {i + 1}"

    return table_data_new


def create_data_from_agent(agent):
    (x0, x1), (y0, y1), (z0, z1) = agent.working_zone
    return [agent.angles, agent.rotation, agent.size, agent.x_amount, agent.y_amount,
            x0, x1, y0, y1, z0, z1, '', '', '']


def find_elem_with_max_fitness(table_data):
    return max(table_data, key=lambda x: float(x[TableHeaders.FITNESS]))


def find_elem_with_min_fitness(table_data):
    return min(table_data, key=lambda x: float(x[TableHeaders.FITNESS]))


def selection_by_best_fitness(table_data):
    parent1 = find_elem_with_max_fitness(table_data)
    table_data.remove(parent1)
    parent2 = find_elem_with_max_fitness(table_data)
    return parent1, parent2


def selection_by_roulette(table_data, p_amount=2):
    # Sort all data in descending order
    tab_dat_s = sorted(table_data, key=lambda x: float(x[TableHeaders.FITNESS]), reverse=True)

    parents = []
    for i in range(p_amount):  # Amount of parents
        r = random() * sum((float(row[TableHeaders.FITNESS]) for row in tab_dat_s))  # Rand in scale of total fitness
        row_sum = 0  # Goes from start to an end
        for row in tab_dat_s:
            row_sum += float(row[TableHeaders.FITNESS])  # Add previous value if fails
            if r < row_sum:  # if success
                parents.append(row)
                tab_dat_s.remove(row)
                break
    return parents


def create_agent_from_table_data(table_data):
    # Create new agent
    agent = Agent()

    # Read data
    x_start = float(table_data[TableHeaders.DETAIL_X0])
    x_end = float(table_data[TableHeaders.DETAIL_X1])
    y_start = float(table_data[TableHeaders.DETAIL_Y0])
    y_end = float(table_data[TableHeaders.DETAIL_Y1])
    z_start = float(table_data[TableHeaders.DETAIL_Z0])
    z_end = float(table_data[TableHeaders.DETAIL_Z1])

    # Add data from table to agent
    agent.working_zone = ((x_start, x_end), (y_start, y_end), (z_start, z_end))
    agent.angles = int(table_data[TableHeaders.ANGLE_NUM])
    agent.rotation = int(table_data[TableHeaders.ROTATE_ANGLE])
    agent.size = int(table_data[TableHeaders.VOLUME_PART])
    agent.x_amount = int(table_data[TableHeaders.CELLS_OX])
    agent.y_amount = int(table_data[TableHeaders.CELLS_OY])
    return agent


def crossover(parent1, parent2):
    agent = Agent()
    agent.crossover_two_parents(parent1, parent2)
    return agent


def mutate(agent):
    if random() < constants.MUT_CHANSE / 100:
        agent.mutate_all_parameters()
