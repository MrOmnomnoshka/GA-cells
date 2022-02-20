import src.researches.constants as constants
from src.researches.GA.Chromosome import Chromosome

from PyQt5.QtWidgets import QTableWidgetItem


class PopulationData:
    generation_counter = 0
    current_generation = 0
    population = list()
    table_data = list()

    def __init__(self, result_table):
        self.result_table = result_table

    def clear(self):
        self.generation_counter = 0
        self.current_generation = 0
        self.population.clear()
        self.table_data.clear()

    def save_result_table_state(self):
        data = []
        for row in range(self.result_table.rowCount()):
            data.append([])
            for column in range(self.result_table.columnCount()):
                item = self.result_table.item(row, column)
                # We suppose data are strings
                data[row].append(item.text())

        self.table_data.append(data)

    def change_result_table_by_generation(self, generation):
        for row in range(self.result_table.rowCount()):
            for column in range(self.result_table.columnCount()):
                if self.table_data:
                    self.result_table.setItem(row, column, QTableWidgetItem(self.table_data[generation][row][column]))

    def create_first_population(self):
        self.population = [[]]  # clear old data
        for i in range(constants.POPULATION_SIZE):
            agent = Chromosome()
            agent.generate_all_params()
            self.population[0].append(agent)
