from src.researches.GA.Chromosome import Chromosome
from src.researches.TableHeaders import TableHeaders
import src.researches.constants as constants


def calculate_fitness_by_params(zero_stress, agent_stress, agent_size, agent_cells_amount, agent_working_zone):
    (x_0, x_1), (y_0, y_1) = agent_working_zone
    width, height = x_1 - x_0, y_1 - y_0
    area = width * height

    # # Maximize size and area function (best - max)
    s_remap = remap(agent_size, 0, 100, 0, area)
    fitness = area * 0.5 + s_remap
    # # ###########################################

    # Get 70% max_stress and max amount and max area (best - max)
    # delta_stress = abs(constants.MAX_STRESS * 0.7 - agent_stress)
    # a_remap = remap(agent_cells_amount, 0, 25, 0, area)
    # fitness = (area * 0.4 + a_remap * 1.4) * 0.2 - delta_stress
    # ###########################################

    # ??? ==============
    # s_remap = agent_size * 20 ############
    # a_remap = agent_cells_amount * 10

    # fitness = delta_stress - s_remap  # + a_remap ##############
    # ==============
    return fitness


def start_new_generation(parents, zero_stress, result_table, app):
    # print("parents:", parents)

    population = get_old_population(parents, result_table)

    for agent in population:
        # calculate_fitness(agent, zero_stress)
        fit = calculate_fitness_by_params(zero_stress, agent[1], agent[0].size, agent[0].x_amount * agent[0].y_amount,
                                          agent[0].working_zone)
        agent[2] = fit

    parent1_index, parent2_index = selection(population)
    parent1, parent2 = population[parent1_index][0], population[parent2_index][0]

    # Create new generation
    if constants.SAVE_PARENTS:
        new_generation = [parent1, parent2] + crossover_from_best(parent1, parent2, constants.POPULATION_SIZE - 2)
    else:
        new_generation = crossover_from_best(parent1, parent2, constants.POPULATION_SIZE)

    # for c in new_generation:
    #     print(c)

    # TODO: Делать это в PopData а не в ГА, может по этому и ломается
    # TODO: Вводить инфу в Попдату, а не в результ таблицу
    # TODO: Брать инфу от туда же
    # TODO(доп.): Сдлеать доп кнопку для выбора сохранять ли все резы, что бы можно было показывать из любого поколения
    # TODO(доп.): Добавить скрин рядом\в\где-то в строке, что бы было видно сразу, не заходя в "Результат"
    # TODO(доп.): Создать перменнуию или типо того для сигналов и передевать их все вместе а-ля "def fn(self, signals):"

    # Clear the table
    app.clear_result_table()
    for i in range(len(new_generation)):
        agent = new_generation[i]
        app.count_body_params_and_add_in_table(agent, i)

    if constants.SAVE_PARENTS:
        par_stress = (population[parent1_index][1], population[parent2_index][1])
        par_fitness = (population[parent1_index][2], population[parent2_index][2])
        app.add_parents_data(par_stress, par_fitness)


def get_old_population(parents, result_table):
    population = []
    for i in range(len(parents)):
        agent = Chromosome()
        copy_agent_from_table(result_table, i, agent)
        population.append([agent, parents[i][1], 0])
    return population


def copy_agent_from_table(result_table, index, agent):
    # TODO: REMAKE IT IN UI.py
    # read table
    x_start = float(result_table.item(index, TableHeaders.DETAIL_X0).text())
    x_end = float(result_table.item(index, TableHeaders.DETAIL_X1).text())
    y_start = float(result_table.item(index, TableHeaders.DETAIL_Y0).text())
    y_end = float(result_table.item(index, TableHeaders.DETAIL_Y1).text())

    # add data from table to agent
    agent.working_zone = ((x_start, x_end), (y_start, y_end))
    agent.angles = int(result_table.item(index, TableHeaders.ANGLE_NUM).text())
    agent.rotation = int(result_table.item(index, TableHeaders.ROTATE_ANGLE).text())
    agent.size = int(result_table.item(index, TableHeaders.VOLUME_PART).text())
    agent.x_amount = int(result_table.item(index, TableHeaders.CELLS_OX).text())
    agent.y_amount = int(result_table.item(index, TableHeaders.CELLS_OY).text())


# def calculate_fitness(agent, zero_stress):
#     agent_stress = agent[1]
#
#     if agent_stress == 0:
#         print("???")
#
#     agent_size = agent[0].size
#     agent_amount = agent[0].x_amount * agent[0].y_amount
#     agent_amount_max = agent[0].xa_max * agent[0].ya_max
#     delta_stress = abs(agent_stress - zero_stress)
#
#     # s_remap = remap(agent_size, 0, 100, 0, agent_stress)
#     # a_remap = remap(agent_amount, 0, agent_amount_max, 0, agent_stress)
#     s_remap = agent_size * delta_stress * 0.05
#     a_remap = agent_amount * delta_stress * 0.6
#
#     fitness = s_remap - delta_stress - a_remap
#     if fitness < 0:
#         fitness = 0
#     agent[2] = fitness


def remap(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min


def selection(population):
    fitness = []
    for agent in population:
        fitness.append(agent[2])

    best_1 = __find_best_1(fitness)
    copy = fitness.copy()
    copy.pop(best_1)
    best_2 = __find_best_1(copy)
    if best_2 >= best_1:  # if best_2 in list is located more to the right than the best_1
        best_2 += 1
    del copy
    return best_1, best_2


def __find_best_1(values):
    best_1 = 0
    for i in range(len(values)):
        if values[i] > values[best_1]:
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
