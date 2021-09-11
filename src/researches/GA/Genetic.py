from src.researches.GA.Chromosome import Chromosome
from src.researches.ResultTableHeaders import ResultTableHeaders


def start_new_generation(parents, zero_stress, result_table, app):
    print("parents:", parents)

    population = []
    for i in range(len(parents)):
        agent = Chromosome()
        copy_agent_from_table(result_table, i, agent)
        population.append([agent, parents[i][1], 0])

    calculate_fitness(population, zero_stress)

    parent1_index, parent2_index = selection(population)
    parent1, parent2 = population[parent1_index][0], population[parent2_index][0]

    new_generation = crossover_from_best(parent1, parent2, result_table.rowCount())
    for c in new_generation:
        print(c)

    # Clear the table
    app.clear_result_table()
    for i in range(len(new_generation)):
        agent = new_generation[i]
        app.count_body_params_add_add_in_table(agent, i)


def copy_agent_from_table(result_table, index, agent):
    # TODO: REMAKE IT IN UI.py
    # read table
    x_start = float(result_table.item(index, ResultTableHeaders.DETAIL_X0).text())
    x_end = float(result_table.item(index, ResultTableHeaders.DETAIL_X1).text())
    y_start = float(result_table.item(index, ResultTableHeaders.DETAIL_Y0).text())
    y_end = float(result_table.item(index, ResultTableHeaders.DETAIL_Y1).text())

    # add data from table to agent
    agent.working_zone = ((x_start, x_end), (y_start, y_end))
    agent.angles = int(result_table.item(index, ResultTableHeaders.ANGLE_NUM).text())
    agent.rotation = int(result_table.item(index, ResultTableHeaders.ROTATE_ANGLE).text())
    agent.size = int(result_table.item(index, ResultTableHeaders.VOLUME_PART).text())
    agent.x_amount = int(result_table.item(index, ResultTableHeaders.CELLS_OX).text())
    agent.y_amount = int(result_table.item(index, ResultTableHeaders.CELLS_OY).text())


def calculate_fitness(population, zero_stress):
    for agent in population:
        agent_stress = agent[1]
        agent_size = agent[0].size
        delta_stress = abs(agent_stress - zero_stress)

        fitness = delta_stress - agent_size * 5
        if fitness < 0:
            fitness = 0
        agent[2] = fitness


def selection(population):
    fitness = []
    for agent in population:
        fitness.append(agent[2])

    best_1 = __find_best_1(fitness)
    copy = fitness.copy()
    copy.pop(best_1)
    best_2 = __find_best_1(copy)
    if best_2 >= best_1:
        best_2 += 1
    del copy
    return best_1, best_2


def __find_best_1(values):
    best_1 = 0
    for i in range(len(values)):
        if values[i] < values[best_1]:
            best_1 = i
    return best_1


def crossover_from_best(parent1, parent2, pop_size):
    new_generation = []
    for i in range(pop_size):
        agent = Chromosome()
        agent.crossover_two_parents(parent1, parent2)
        agent.mutate_all_parameters()
        new_generation.append(agent)
    return new_generation
