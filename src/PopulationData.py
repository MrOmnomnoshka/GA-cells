import src.constants as constants
from src.helper_classes.TableHeaders import TableHeaders
from src.GA.Agent import Agent

from PyQt5.QtWidgets import QTableWidgetItem


class PopulationData:

    def __init__(self):
        self.generation_counter = 0
        self.table_data = []
        self.elite_list = []
        self.max_fitness_for_all_time = list()

    def clear(self):
        self.generation_counter = 0
        self.table_data.clear()
        self.elite_list.clear()
        self.max_fitness_for_all_time.clear()

    def get_current_table_data(self):
        return self._get_index_table_data(self.generation_counter)

    def get_previous_table_data(self):
        return self._get_index_table_data(self.generation_counter - 1)

    def _get_index_table_data(self, index):
        return self.table_data[index]

    def get_current_table_row_data(self, row):
        return self.table_data[self.generation_counter][row]

    def add_status_stress_fitness_data(self, row, status, stress, fitness):
        data = self.table_data[self.generation_counter][row]
        data[TableHeaders.STATUS] = status
        data[TableHeaders.STRESS] = stress
        data[TableHeaders.FITNESS] = fitness
        # data.extend((status, stress, fitness))

    def change_result_table_by_generation(self, result_table, generation):
        if self.table_data:
            result_table.setRowCount(constants.POPULATION_SIZE)
            for row in range(result_table.rowCount()):
                for column in range(result_table.columnCount()):
                    result_table.setItem(row, column, QTableWidgetItem(self.table_data[generation][row][column]))

    def save_first_state_of_table(self, result_table):
        self.clear()
        data = []
        for row in range(result_table.rowCount()):
            data.append([])
            for column in range(result_table.columnCount()):
                item = result_table.item(row, column)
                data[row].append(item.text())  # We suppose data are strings in PyQt5 format
        self.table_data = [data]

    def create_first_population(self):
        population = []
        # population = [Agent(3+i, 0, 80, 3, 3, ((-100, 100), (-150, 150), (-10, 10)))
        #               for i in range(constants.POPULATION_SIZE)]
        for i in range(constants.POPULATION_SIZE):
            agent = Agent()
            agent.generate_all_params()
            # agent = Agent(((4, 6), (-16, -13), (-15, 15)), 4, 218, 9, 2, 1, True)
            # agent = Agent(((-100, 100), (-150, 150), (-10, 10)), 3, 0, 100, 1, 1, True)
            population.append(agent)
        return population
