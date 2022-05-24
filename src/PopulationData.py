import src.constants as constants
from src.helper_classes.TableHeaders import TableHeaders
from src.GA.Chromosome import Chromosome

from PyQt5.QtWidgets import QTableWidgetItem


class PopulationData:
    generation_counter = 0
    # population = []
    table_data = []

    def __init__(self, result_table):
        self.result_table = result_table

    def clear(self):
        self.generation_counter = 0
        # self.population.clear()
        self.table_data.clear()

    def get_current_table_data(self):
        return self.table_data[self.generation_counter]

    def get_current_table_row_data(self, row):
        return self.table_data[self.generation_counter][row]

    def add_status_stress_fitness_data(self, row, status, stress, fitness):
        data = self.table_data[self.generation_counter][row]
        data[TableHeaders.STATUS] = status
        data[TableHeaders.STRESS] = stress
        data[TableHeaders.FITNESS] = fitness
        # data.extend((status, stress, fitness))

    def change_result_table_by_generation(self, generation):
        if self.table_data:
            for row in range(self.result_table.rowCount()):
                for column in range(self.result_table.columnCount()):
                    self.result_table.setItem(row, column, QTableWidgetItem(self.table_data[generation][row][column]))

    def create_first_population(self):
        # # clear old data
        # self.population = [[]]
        population = []

        for i in range(constants.POPULATION_SIZE):
            agent = Chromosome()
            agent.generate_all_params()
            # agent = Chromosome(((35, 39), (3, 10)), 2, 0, 100, 1, 1)
            population.append(agent)
        return population

    def save_first_state_of_table(self):
        self.clear()
        data = []
        for row in range(self.result_table.rowCount()):
            data.append([])
            for column in range(self.result_table.columnCount()):
                item = self.result_table.item(row, column)
                data[row].append(item.text())  # We suppose data are strings
        self.table_data = [data]
