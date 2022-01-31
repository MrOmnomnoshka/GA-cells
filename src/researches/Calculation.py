import csv
import json
import os
import pathlib
import shutil
import ansys.mapdl
import re
import traceback
# from datetime import datetime
from time import sleep, strftime, localtime
from ansys.mapdl.core import launch_mapdl
import pandas as pd
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QTableWidgetItem

from src.researches.ResultTableHeaders import ResultTableHeaders
from src.researches.BodyParams import BodyParameters
from src.researches.Cells import NAngleCells, CircleCells, RectangleCells
from src.researches.Drawers import NAngleCellsDrawer, RectangleCellsDrawer
from src.researches.GA import Genetic
import src.researches.constants as constants


class CalculationParams:
    def __init__(self, rotate_angle: int, angle_num: int, volume_part: int, cells_ox: int, cells_oy: int):
        self.rotate_angle = rotate_angle
        self.angle_num = angle_num
        self.volume_part = volume_part
        self.cells_ox = cells_ox
        self.cells_oy = cells_oy


class CalculationContext:
    def __init__(self,
                 rotate_angle_start: int, rotate_angle_end: int, rotate_angle_step: int,
                 angle_num_start: int, angle_num_end: int, angle_num_step: int,
                 volume_part_start: int, volume_part_end: int, volume_part_step: int,
                 cells_ox_start: int, cells_ox_end: int, cells_ox_step: int,
                 cells_oy_start: int, cells_oy_end: int, cells_oy_step: int):
        self.rotate_angle_start = min(rotate_angle_start, rotate_angle_end)
        self.rotate_angle_end = max(rotate_angle_start, rotate_angle_end)
        self.rotate_angle_step = rotate_angle_step
        self.angle_num_start = min(angle_num_start, angle_num_end)
        self.angle_num_end = max(angle_num_start, angle_num_end)
        self.angle_num_step = angle_num_step
        self.volume_part_start = min(volume_part_start, volume_part_end)
        self.volume_part_end = max(volume_part_start, volume_part_end)
        self.volume_part_step = volume_part_step
        self.cells_ox_start = min(cells_ox_start, cells_ox_end)
        self.cells_ox_end = max(cells_ox_start, cells_ox_end)
        self.cells_ox_step = cells_ox_step
        self.cells_oy_start = min(cells_oy_start, cells_oy_end)
        self.cells_oy_end = max(cells_oy_start, cells_oy_end)
        self.cells_oy_step = cells_oy_step


class Calculation(QtCore.QThread):
    detail_fn = str
    load_schema_fn = str
    root_folder = str
    zero_stress = int
    generation_counter = 0
    min_stress_for_all_time = list()

    ansys_manager = None
    result_table = None
    app = None

    # Потоковая задача
    current_stress_signal = QtCore.pyqtSignal(str)  # Объявляем сигнал, с аргументом(int)
    zero_stress_signal = QtCore.pyqtSignal(str)  # Объявляем сигнал, с аргументом(int)
    threadFinish = QtCore.pyqtSignal()
    current_task = None

    def __init__(self):
        super().__init__()
        # self.results = {}  # TODO: all generations data in 1 place

    def run(self, *args, **kwargs):
        # Start ansys
        if self.ansys_manager is None:
            self.ansys_manager = self.force_start_ansys()

        # Start any experiment
        if self.current_task == 0:
            self.calculate_zero_stress()
        elif self.current_task == 1:
            self.calculate_next_iteration(self.result_table, self.app)
        elif self.current_task == 2:
            self.calculate_infinity(self.result_table, self.app)

        # Currect exit thread
        # self.threadFinish.emit()
        self.quit()

    def calculate_zero_stress(self):
        self.zero_stress_signal.emit(" *****")
        # TODO: uncomment
        # max_stress = self.research_zero_stress(self.ansys_manager)
        max_stress = 1061.04292

        if max_stress:
            self.zero_stress_signal.emit(str(max_stress))
            self.current_stress_signal.emit(str(max_stress))
            self.zero_stress = max_stress

    def calculate_next_iteration(self, result_table, app):
        if self.generation_counter >= constants.GENERATION_LIMIT:
            app.is_running = False
            return 0

        if self.generation_counter > 0:  # Not the first generation
            # Create new generation
            self.create_new_generation(result_table, app)

        # Count current generation
        self.calculate_current_research(result_table, app)

    def calculate_infinity(self, result_table, app):
        # An infinite cycle
        while app.is_running:  # Continue the experiment
            self.calculate_next_iteration(result_table, app)
            QtCore.QThread.msleep(250)
        else:
            sleep(1)  # not overload CPU on pause

    def create_new_generation(self, result_table, app):
        finished = self.get_all_finished_id_and_stress(result_table)

        if len(finished) >= 2:
            Genetic.start_new_generation(finished, self.zero_stress, result_table, app)
        else:
            # TODO: ??create and recalculate new generation??
            print("Bad News: Not enough parents.")
            pass

        # def show_current_fitness(self, result_table, zero_stress):
        #     finished = self.get_all_finished_id_and_stress(result_table)
        #
        #     population = Genetic.get_old_population(finished, result_table)
        #
        #     for agent in population:
        #         # Genetic.calculate_fitness(agent, zero_stress)
        #         Genetic.calculate_fitness_by_params(zero_stress,agent[1],agent[0].size,agent[0].x_amount*agent[0].y_amount)
        #
        #     fitness = []
        #     for agent in population:
        #         fitness.append(agent[2])
        #
        #     a = enumerate(fitness)
        #     for i, j in list(a):
        #         result_table.setItem(i, ResultTableHeaders.FITNESS, QTableWidgetItem(str(round(j, 3))))
        self.update_table(result_table)

    def calculate_current_research(self, result_table, app):
        # # recoding to a Exel file
        # file_path = self.root_folder + os.sep + "researches.csv"
        # with open(file_path, mode="w", newline="") as researches_csv:
        #     writer = csv.writer(researches_csv)
        #     research_result_data = ["research_id", "angle_num", "rotate_angle", "vol_part", "cells_ox", "cells_oy",
        #                             "research_Status"]
        #     writer.writerow(research_result_data)
        range_start = 2 if constants.SAVE_PARENTS and self.generation_counter > 0 else 0

        if self.generation_counter > 0:
            app.increment_cb_generation()

        # Backup every 5 generation in case of some breaks
        if (self.generation_counter + 1) % 2 == 0:
            self.app.save_csv("last_research.csv")

        self.generation_counter += 1
        for row_index in range(range_start, constants.POPULATION_SIZE):
            param = self.__build_calculate_params(result_table, row_index)
            body_params = self.__build_body_params(result_table, row_index)
            cells = self.__calculate_cells(body_params, param)

            result_table.setItem(row_index, ResultTableHeaders.STATUS, QTableWidgetItem('Solving'))
            self.update_table(result_table)

            try:
                self.researchFromDetailModel(body_params, param, cells, self.root_folder,
                                             result_table, row_index)
                if constants.SAVE_TEMP_FILES:
                    self.save_db_and_rst_files(row_index)

            except Exception as e:
                result_table.setItem(row_index, ResultTableHeaders.STATUS, QTableWidgetItem('ERROR!'))
                self.update_table(result_table)
                # app.force_start_ansys() # TODO: ???
                print(e)

            # self.__write_row_in_csv_results(row_index, param)
            # count += 1

        # Change stress label to current min stress
        all_stress = [i[1] for i in self.get_all_finished_id_and_stress(result_table)]
        min_stress = min(all_stress)
        self.min_stress_for_all_time.append(min_stress)
        self.current_stress_signal.emit(str(min_stress))
        app.add_generation_stress_in_plot(self.min_stress_for_all_time)

    def save_db_and_rst_files(self, row_index):
        # Copy '.db' files
        original = self.root_folder + os.sep + 'file.db'
        target = self.root_folder + os.sep + f'{row_index + 1}.db'
        shutil.copyfile(original, target)

        # Copy '.rst' files
        original = self.root_folder + os.sep + 'file.rst'
        target = self.root_folder + os.sep + f'{row_index + 1}.rst'
        shutil.copyfile(original, target)

    def get_all_finished_id_and_stress(self, result_table):
        # TODO: (maybe) REMAKE IT IN UI.py
        finished = []
        for i in range(constants.POPULATION_SIZE):
            status = result_table.item(i, ResultTableHeaders.STATUS).text()
            if status == "Finished" or status == "Parent 1" or status == "Parent 2":
                stress = float(result_table.item(i, ResultTableHeaders.MAX_PRESS).text())
                finished.append((i, stress))
        return finished

    def import_detail_and_load_schema_files(self, detail_fn, load_schema_fn):
        self.detail_fn = detail_fn
        self.load_schema_fn = load_schema_fn

    def create_root_folder_and_move_to_it(self):
        self.root_folder = self.__build_root_folder()
        path = pathlib.Path(self.root_folder)
        path.parent.mkdir(parents=True, exist_ok=True)
        if not os.path.isdir(self.root_folder):  # Create root_folder if not exist
            os.mkdir(self.root_folder)
        return self.root_folder

    def __build_root_folder(self):
        # return str(os.getcwd() + os.sep + 'researches' + os.sep + datetime.now().strftime('%Y-%m-%d %H-%M-%S'))
        return str(os.getcwd() + os.sep + 'researches' + os.sep + 'temp_files')

    def __calculate_cells(self, body_params: BodyParameters, param: CalculationParams):
        if param.angle_num < 3:
            cells = CircleCells(body_params)
        elif param.angle_num == 4:
            cells = RectangleCells(body_params)
        else:
            cells = NAngleCells(body_params)
            cells.angle_num = param.angle_num

        cells.columns = param.cells_ox
        cells.rows = param.cells_oy
        cells.cell_height = body_params.height
        cells.v_cells = body_params.v * param.volume_part / 100
        cells.rotation_angle = param.rotate_angle
        cells.calculation()

        return cells

    def __write_row_in_csv_results(self, research_number: int, param: CalculationParams):
        file_path = self.root_folder + os.sep + "researches.csv"
        try:
            with open(file_path, mode="a", newline="") as researches_csv:
                writer = csv.writer(researches_csv)
                writer.writerow(
                    [research_number, param.angle_num, param.rotate_angle, param.volume_part, param.cells_ox,
                     param.cells_oy, self.results[research_number][ResultIndexes.STATUS]])
        except Exception as e:
            print(e)

    def __build_calculate_params(self, result_table: QtWidgets.QTableWidget, row_index: int) -> CalculationParams:
        return CalculationParams(
            int(result_table.item(row_index, ResultTableHeaders.ROTATE_ANGLE).text()),
            int(result_table.item(row_index, ResultTableHeaders.ANGLE_NUM).text()),
            int(result_table.item(row_index, ResultTableHeaders.VOLUME_PART).text()),
            int(result_table.item(row_index, ResultTableHeaders.CELLS_OX).text()),
            int(result_table.item(row_index, ResultTableHeaders.CELLS_OY).text()))

    def __build_body_params(self, result_table: QtWidgets.QTableWidget, row_index: int) -> BodyParameters:
        return BodyParameters(
            float(result_table.item(row_index, ResultTableHeaders.DETAIL_X0).text()),
            float(result_table.item(row_index, ResultTableHeaders.DETAIL_X1).text()),
            float(result_table.item(row_index, ResultTableHeaders.DETAIL_Y0).text()),
            float(result_table.item(row_index, ResultTableHeaders.DETAIL_Y1).text()),
            float(result_table.item(row_index, ResultTableHeaders.DETAIL_Z0).text()),
            float(result_table.item(row_index, ResultTableHeaders.DETAIL_Z1).text()))

    def __build_body_params_ga(self):
        # TODO: calc body dynamically for different models
        return BodyParameters(float(0), float(250), float(0), float(250), float(0), float(250))

    # def __calc_params(self, context) -> List[CalculationParams]:
    #     list = []
    #
    #     for angle_num in range(context.angle_num_start, context.angle_num_end + 1, context.angle_num_step):
    #         for rotate_angle in range(context.rotate_angle_start, context.rotate_angle_end + 1,
    #                                   context.rotate_angle_step):
    #             for volume_part in range(context.volume_part_start, context.volume_part_end + 1,
    #                                      context.volume_part_step):
    #                 for cells_ox in range(context.cells_ox_start, context.cells_ox_end + 1, context.cells_ox_step):
    #                     for cells_oy in range(context.cells_oy_start, context.cells_oy_end + 1, context.cells_oy_step):
    #                         list.append(CalculationParams(rotate_angle, angle_num, volume_part, cells_ox, cells_oy))
    #
    #     return list

    def update_table(self, table):
        pass
        table.hide()
        table.update()
        # table.resizeColumnsToContents()
        table.show()

    def researchFromDetailModel(self, body_params, calc_param, cells, research_folder, result_table, count):
        try:
            # self.results[count] = [body_params, calc_param, cells, research_folder, 'IN_PROGRESS']
            cells_coordinates = self.__execute_ansys_commands(cells, body_params, calc_param)

            # count stress
            max_press = self.get_max_press()
            if max_press == 0:
                raise ValueError("Max stress is zero. MAPDL failed, there is a hole.")

            # count fitness
            size = calc_param.volume_part
            cells_amount = calc_param.cells_ox * calc_param.cells_oy

            x_0 = float(self.result_table.item(count, ResultTableHeaders.DETAIL_X0).text())
            x_1 = float(self.result_table.item(count, ResultTableHeaders.DETAIL_X1).text())
            y_0 = float(self.result_table.item(count, ResultTableHeaders.DETAIL_Y0).text())
            y_1 = float(self.result_table.item(count, ResultTableHeaders.DETAIL_Y1).text())
            working_zone = ((x_0, x_1), (y_0, y_1))

            fitness = Genetic.calculate_fitness_by_params(self.zero_stress, max_press, size, cells_amount, working_zone)

            try:
                # TODO: See 'TODO' in inner function
                # self.write_all_nodes_coordinates(self.ansys_manager, research_folder)
                pass
            except Exception as e:
                print(e)

            # self.__write_cells_in_json(cells_coordinates, research_folder)
            result_table.setItem(count, ResultTableHeaders.STATUS, QTableWidgetItem('Finished'))
            result_table.setItem(count, ResultTableHeaders.MAX_PRESS, QTableWidgetItem(str(round(max_press, 4))))
            result_table.setItem(count, ResultTableHeaders.FITNESS, QTableWidgetItem(str(round(fitness, 4))))
            self.update_table(result_table)

            self.exit_ansys_experiment()

            # self.results[count] = [body_params, calc_param, cells, research_folder, 'FINISHED']
            return True

        except ValueError:
            result_table.setItem(count, ResultTableHeaders.STATUS, QTableWidgetItem('Bad Cell'))
            self.update_table(result_table)
            # self.results[count] = [body_params, calc_param, cells, research_folder, 'FAILED']

        except Exception as e:
            # TODO: Handle VMESH - "Meshing failure in volume..."
            # TODO: Handle ??? - "Poorly shaped facets in surface mesh..."
            print(traceback.format_exc())

            if result_table:
                result_table.setItem(count, ResultTableHeaders.STATUS, QTableWidgetItem('Failed'))
                self.update_table(result_table)
            # self.results[count] = [body_params, calc_param, cells, research_folder, 'FAILED']

            # restart experiment in case of 'exit'
            try:
                self.exit_ansys_experiment()
            except Exception:
                # TODO: mapdl can exit and all programs crahses ://
                self.ansys_manager = self.force_start_ansys()
                self.clear_and_exit()
                self.quit()
                print("HARD EXIT")
                quit()
                return False

            return False

    def research_zero_stress(self):
        try:
            self.__execute_ansys_start_commands()
            self.__run_load_schema()
            max_press = self.get_max_press()

            self.exit_ansys_experiment()

            return max_press

        except Exception as e:
            print(traceback.format_exc())
            return False

    def exit_ansys_experiment(self):
        if self.ansys_manager is not None:  # or self.ansys_manager == "MAPDL exited":
            self.ansys_manager.save()
            self.ansys_manager.finish()
            self.ansys_manager.clear()

    def clear_and_exit(self):
        # correct closing ANSYS manager
        if self.ansys_manager is not None:
            self.exit_ansys_experiment()
            self.ansys_manager.exit()

    def force_start_ansys(self):
        root_folder = self.create_root_folder_and_move_to_it()
        ansys_manager = None
        while ansys_manager is None:
            ansys_manager = self.init_ansys(root_folder)
        return ansys_manager

    def __execute_ansys_commands(self, cells, body_params, calc_param):
        self.__execute_ansys_start_commands()

        drawer = self.create_drawer(cells, body_params, calc_param)
        res = self.ansys_manager.run("*GET, KMax, VOLU,, NUM, MAX")
        start = res.index("VALUE= ") + 7
        volume_id = res[start:]

        drawer.set_cells(cells)
        cells_coordinates = drawer.draw_cells_volumes()

        self.ansys_manager.run("VSBV,%s,ALL,,," % (volume_id))

        self.__run_load_schema()

        return cells_coordinates

    def __execute_ansys_start_commands(self):
        self.ansys_manager.run("/ BATCH")
        self.ansys_manager.run("WPSTYLE,, , , , , , , 0")
        self.ansys_manager.run("/ AUX15")
        self.ansys_manager.run("IOPTN, IGES, SMOOTH")
        self.ansys_manager.run("IOPTN, MERGE, YES")
        self.ansys_manager.run("IOPTN, SOLID, YES")
        self.ansys_manager.run("IOPTN, SMALL, YES")
        self.ansys_manager.run("IOPTN, GTOLER, DEFA")
        self.ansys_manager.run("IGESIN, '%s','IGS','%s' ! import" %
                               (str(pathlib.Path(self.detail_fn).stem),
                                str(pathlib.Path(self.detail_fn).parent.absolute())))
        self.ansys_manager.run("! VPLOT")
        self.ansys_manager.run("FINISH")
        self.ansys_manager.prep7()
        self.ansys_manager.run("NUMCMP, ALL")
        self.ansys_manager.run("/units, mpa")
        self.ansys_manager.k()

    def __run_load_schema(self):
        with open(file=self.load_schema_fn, mode="r", encoding="utf-8") as load_schema_commands:
            for command in load_schema_commands:
                if not command.isspace() and command[0] != '!':
                    self.ansys_manager.run(command)

    def __write_cells_in_json(self, cells_coordinates, research_folder: str):
        json_cells_coordinates = json.dumps(cells_coordinates)
        with open(research_folder + os.sep + "cells.json", "a") as json_cells_file:
            json_cells_file.write(json_cells_coordinates)

    def __is_java_installed(self) -> bool:
        return os.system("java -version") == 0

    def write_all_nodes_coordinates(self, research_folder: str, file: str = "nodes.csv"):
        nodes_data_frame = pd.DataFrame(columns=["node_id", "x", "y", "z"])
        start_node = 1
        page_size = 10000  # TODO: it was '10000'
        end_node = start_node + page_size
        nodes_count = self.get_count_of_nodes()
        # ####
        # is_java_installed = self.__is_java_installed()
        is_java_installed = False  # TODO: update java version //or// boost python
        # ####
        temp_file = research_folder + os.sep + "temp_nodes.txt"

        while start_node < nodes_count:
            get_nodes_command = "NLIST,{},{}, ,XYZ,NODE,,INTERNAL".format(start_node, end_node)
            nodes_str = self.ansys_manager.run(get_nodes_command)

            if is_java_installed:
                with open(file=temp_file, mode="a") as temp_file_writer:
                    temp_file_writer.write(nodes_str)
            else:
                nodes = nodes_str.split("\n")[12:]
                for node in nodes:
                    parsed_node = node.strip().split()
                    node_id = parsed_node[0]
                    node_x = parsed_node[1]
                    node_y = parsed_node[2]
                    node_z = parsed_node[3]
                    nodes_data_frame.at[node_id, "node_id"] = node_id
                    nodes_data_frame.at[node_id, "x"] = node_x
                    nodes_data_frame.at[node_id, "y"] = node_y
                    nodes_data_frame.at[node_id, "z"] = node_z

            start_node += page_size
            end_node = nodes_count if end_node + page_size > nodes_count else end_node + page_size

        if is_java_installed:
            os.system('java -jar %s "%s" "%s"' % (
                os.getenv('PARSER_JAR'),
                str(research_folder + os.sep + file),
                temp_file))
        else:
            nodes_data_frame.to_csv(research_folder + os.sep + file)

    def get_count_of_nodes(self) -> int:
        self.ansys_manager.run("*GET, N_COUNT, NODE,, COUNT")
        status = self.ansys_manager.run("*STATUS, N_COUNT")
        start = status.index("\n N_COUNT")
        max_stress = re.findall('\d+\\.\d+', status[start:])[0]

        return int(float(max_stress))

    def get_max_press(self):
        self.ansys_manager.run("/ POST1")
        self.ansys_manager.run("SET, FIRST")
        self.ansys_manager.run("NSORT, S, EQV")
        self.ansys_manager.run("*GET, STRESS_MAX, SORT,, MAX")
        status = self.ansys_manager.run("*STATUS, STRESS_MAX")
        start = status.index("\n STRESS_MAX")
        # TODO: Да там и до этого 3 командами выше можно вытянуть макс стресс
        max_stress = re.findall('\d+\\.\d+', status[start:])[0]

        return float(max_stress)

    def init_ansys(self, root_folder):
        if not os.path.isdir(root_folder):  # Create root_folder if not exist
            path = pathlib.Path(root_folder)
            path.parent.mkdir(parents=True, exist_ok=True)
            os.mkdir(root_folder)

        return launch_mapdl(
            append=True,
            run_location=root_folder,
            interactive_plotting=True,
            override=True,
            start_timeout=4000,
            nproc=8,
            memory=2,
            loglevel="DEBUG",
            log_apdl="w",
            exec_file=r"D:\Programs\ANSYS Inc\v192\ansys\bin\winx64\ANSYS192.exe")

    def create_drawer(self, cells, body_params, calc_params):
        if issubclass(cells.__class__, NAngleCells):
            return NAngleCellsDrawer(body_params, calc_params.angle_num, self.ansys_manager)
        elif issubclass(cells.__class__, RectangleCells):
            return RectangleCellsDrawer(body_params, cells.rows, self.ansys_manager)
        # elif (issubclass(cells.__class__, CircleCells)):
        #     return Cir #  TODO: add circle cells!

    def show_result(self, index):
        status = self.result_table.item(index, ResultTableHeaders.STATUS).text()
        # if self.results[index][ResultIndexes.STATUS] == 'FINISHED':
        if status in ("Finished", "Parent 1", "Parent 2"):
            # path = self.results[index][ResultIndexes.RESEARCH_FOLDER] + os.sep + "file.rst"
            path = self.root_folder + os.sep + f"{index + 1}.rst"
            os.system("py plot_result.py \"" + path + "\"")
        print("Visualization done!")

    def show_stress_chart(self, index):
        status = self.result_table.item(index, ResultTableHeaders.STATUS).text()
        if status in ("Finished", "Parent 1", "Parent 2"):
            path = self.root_folder + os.sep + f"{index + 1}.rst"
            os.system("py plot_stress_chart.py \"" + path + "\"")

    def show_cluster_analyse(self):
        os.system("py plot_cluster_analyse.py \"" + self.root_folder + "\"")


class ResultIndexes:
    BODY_PARAMS = 0
    CALC_PARAMS = 1
    CELLS = 2
    RESEARCH_FOLDER = 3
    STATUS = 4
