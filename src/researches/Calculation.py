import csv
import json
import os
import pathlib
import shutil
import ansys.mapdl
import re
import traceback

# from datetime import datetime
# from time import sleep, strftime, localtime
import pandas as pd
from ansys.mapdl.core import launch_mapdl
from PyQt5 import QtWidgets, QtCore

import src.researches.constants as constants
from src.researches.TableHeaders import TableHeaders
from src.researches.BodyParams import BodyParameters
from src.researches.Cells import NAngleCells, CircleCells, RectangleCells
from src.researches.Drawers import NAngleCellsDrawer, RectangleCellsDrawer
from src.researches.GA import Genetic
from src.researches.ThreadsManager import Worker


class CalculationParams:
    def __init__(self, rotate_angle: int, angle_num: int, volume_part: int, cells_ox: int, cells_oy: int):
        self.rotate_angle = rotate_angle
        self.angle_num = angle_num
        self.volume_part = volume_part
        self.cells_ox = cells_ox
        self.cells_oy = cells_oy


# class Calculation(QtCore.QThread):
class Calculation:
    load_schema_fn = root_folder = detail_fn = zero_stress = stopped_id = ansys_manager = result_table = None
    max_fitness_for_all_time = list()
    pop_data = None  # TODO: all generations data in 'pop_data'
    threadpool = QtCore.QThreadPool()  # for multithreading

    def __init__(self, app):
        self.app = app

    def connect_worker_to_signals(self, worker):
        worker.signals.zero_stress_signal.connect(self.app.change_zero_stress_label)
        worker.signals.current_stress_signal.connect(self.app.change_current_stress_label)
        worker.signals.increment_cb.connect(self.app.increment_cb_generation)
        worker.signals.change_table_signal.connect(self.app.change_table_item)
        worker.signals.update_plot.connect(self.app.add_data_on_plot)

        worker.signals.result.connect(self.print_output)
        worker.signals.finished.connect(self.thread_complete)

    def research_UI(self):
        worker = Worker(self.research)
        self.connect_worker_to_signals(worker)

        self.threadpool.start(worker)

    def next_generation_research_UI(self):
        worker = Worker(self.next_generation_research)
        self.connect_worker_to_signals(worker)
        self.threadpool.start(worker)

    def set_up_research(self, **kwargs):
        # Prepare arguments for methods in class
        self.import_detail_and_load_schema_files(self.app.input_detail_file.text(),
                                                 self.app.input_load_schema_file.text())
        self.result_table = self.app.result_table

        # Start ansys
        if self.ansys_manager is None:
            self.ansys_manager = self.force_start_ansys()

        # Count zero_stress
        kwargs.get("zero_stress_callback").emit(" *****")
        self.calculate_zero_stress()
        kwargs.get("zero_stress_callback").emit(str(self.zero_stress))

    def calculate_zero_stress(self):
            # NOTE: Uncomment in release version
        # max_stress = self.research_zero_stress()
        max_stress = 1061.04292

        if max_stress:
            self.zero_stress = max_stress

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

    def calculate_next_iteration(self, **kwargs):
        # Check if this is the first research
        if self.zero_stress is None:
            self.set_up_research(**kwargs)

        # Increase combo_box text of generations
        if self.pop_data.generation_counter > 0:
            kwargs.get("increment_cb_callback").emit()

        # Backup to excel file every N generation in case of some breaks
        if (self.pop_data.generation_counter + 1) % constants.SAVE_TO_CSV_EVERY_N == 0:
            self.app.save_csv("last_research.csv")

        # Count current generation
        self.calculate_current_research(**kwargs)

        # Count finished data
        finished = self.get_all_finished_id_stress_fitness(self.result_table)
        min_stress = min([i[1] for i in finished])
        max_fitness = max([i[2] for i in finished])
        self.max_fitness_for_all_time.append(max_fitness)

        # Change stress label to current min stress
        kwargs.get("curr_stress_callback").emit(str(min_stress))

        # Update plot data
        kwargs.get("plot_callback").emit(self.max_fitness_for_all_time)

        # Save table state in Pop class
        self.pop_data.save_result_table_state()

        # If button is turned off and research is stopped - turn it on
        if not self.app.is_running:
            self.app.button_play_pause.setEnabled(True)

        # Increment generation
        self.pop_data.generation_counter += 1

        # STOP
        # Stop if limit exceeded
        if self.pop_data.generation_counter >= constants.GENERATION_LIMIT:
            self.app.is_running = False
            return  # TODO: add time limit (don't forget about pause)

    def crossover_parents(self):
        finished = self.get_all_finished_id_stress_fitness(self.result_table)

        if len(finished) >= 2:
            Genetic.start_new_generation(finished, self.zero_stress, self.result_table, self.app)
        else:
            # TODO: ??create and recalculate new generation??
            print("Bad News: Not enough parents.")
            pass

        self.update_table(self.result_table)  # TODO: ??update needed??

    def research(self, **kwargs):
        # Stop or pause calculating
        if self.app.is_running:  # if stopped while research isn't complete - disable button
            self.app.button_play_pause.setEnabled(False)

        self.app.is_running = not self.app.is_running
        self.app.button_play_pause.setDefault(self.app.is_running)

        # An infinite cycle
        while self.app.is_running:  # Continue the experiment
            self.calculate_next_iteration(**kwargs)
        print('infinity thread finishes.')

    def next_generation_research(self,  **kwargs):
        self.app.button_play_pause.setEnabled(False)

        self.calculate_next_iteration(**kwargs)

        self.app.button_play_pause.setEnabled(True)

    def calculate_current_research(self, **kwargs):
        # Start from the last stop
        if self.stopped_id:
            range_start = self.stopped_id
            self.stopped_id = None
        # Start from 3-rd agent; skip researching parents(0,1) if exists
        elif constants.SAVE_PARENTS and self.pop_data.generation_counter > 0:
            range_start = 2
        # Start from the beginning
        else:
            range_start = 0

        for row_index in range(range_start, constants.POPULATION_SIZE):
            # Stop if 'stop' button is pressed or a new experiment is loaded
            if self.app.stop_calculation:  # todo: тут после сброса тру и не едет дальше
                self.clear_and_exit()
                self.stopped_id = row_index
                return None

            param = self.__build_calculate_params(self.result_table, row_index)
            body_params = self.__build_body_params(self.result_table, row_index)
            cells = self.__calculate_cells(body_params, param)

            self.researchFromDetailModel(body_params, param, cells, row_index, kwargs.get("table_callback"))

    def save_db_and_rst_files(self, row_index):
        # Copy '.db' files
        original = self.root_folder + os.sep + 'file.db'
        target = self.root_folder + os.sep + f'{row_index + 1}.db'
        shutil.copyfile(original, target)

        # Copy '.rst' files
        original = self.root_folder + os.sep + 'file.rst'
        target = self.root_folder + os.sep + f'{row_index + 1}.rst'
        shutil.copyfile(original, target)

    def get_all_finished_id_stress_fitness(self, result_table):
        # TODO: mb ID isn't using anywhere
        finished = []
        for i in range(constants.POPULATION_SIZE):
            status = result_table.item(i, TableHeaders.STATUS).text()
            if status == "Finished" or status == "Parent 1" or status == "Parent 2":
                stress = float(result_table.item(i, TableHeaders.MAX_PRESS).text())
                fitness = float(result_table.item(i, TableHeaders.FITNESS).text())
                finished.append((i, stress, fitness))
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
        pass
        # file_path = self.root_folder + os.sep + "researches.csv"
        # try:
        #     with open(file_path, mode="a", newline="") as researches_csv:
        #         writer = csv.writer(researches_csv)
                # writer.writerow(
                #     [research_number, param.angle_num, param.rotate_angle, param.volume_part, param.cells_ox,
                #      param.cells_oy, self.results[research_number][ResultIndexes.STATUS]])
        # except Exception as e:
        #     print(e)

    def __build_calculate_params(self, result_table: QtWidgets.QTableWidget, row_index: int) -> CalculationParams:
        return CalculationParams(
            int(result_table.item(row_index, TableHeaders.ROTATE_ANGLE).text()),
            int(result_table.item(row_index, TableHeaders.ANGLE_NUM).text()),
            int(result_table.item(row_index, TableHeaders.VOLUME_PART).text()),
            int(result_table.item(row_index, TableHeaders.CELLS_OX).text()),
            int(result_table.item(row_index, TableHeaders.CELLS_OY).text()))

    def __build_body_params(self, result_table: QtWidgets.QTableWidget, row_index: int) -> BodyParameters:
        return BodyParameters(
            float(result_table.item(row_index, TableHeaders.DETAIL_X0).text()),
            float(result_table.item(row_index, TableHeaders.DETAIL_X1).text()),
            float(result_table.item(row_index, TableHeaders.DETAIL_Y0).text()),
            float(result_table.item(row_index, TableHeaders.DETAIL_Y1).text()),
            float(result_table.item(row_index, TableHeaders.DETAIL_Z0).text()),
            float(result_table.item(row_index, TableHeaders.DETAIL_Z1).text()))

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
        table.hide()
        table.update()
        # table.resizeColumnsToContents()
        table.show()

    def researchFromDetailModel(self, body_params, calc_param, cells, count, table_callback, first_try=True):
        try:
            table_callback.emit(count, TableHeaders.STATUS, "Solving")

            cells_coordinates = self.__execute_ansys_commands(cells, body_params, calc_param)

            # count stress
            max_press = self.get_max_press()
            if max_press == 0:
                raise ValueError("Max stress is zero. MAPDL failed, there is a hole.")

            # count fitness
            fitness = self.calculate_fitness_value(calc_param, count, max_press)

            # try:
            #     # TODO: See 'TODO' in inner function
            #     # self.write_all_nodes_coordinates(self.ansys_manager, research_folder)
            #     pass
            # except Exception as e:
            #     print(e)

            # self.__write_cells_in_json(cells_coordinates, research_folder)
            table_callback.emit(count, TableHeaders.STATUS, "Finished")
            table_callback.emit(count, TableHeaders.MAX_PRESS, str(round(max_press, 4)))
            table_callback.emit(count, TableHeaders.FITNESS, str(round(fitness, 4)))

            self.exit_ansys_experiment()

            # Save temp files if needed
            if constants.SAVE_TEMP_FILES:
                self.save_db_and_rst_files(count)

            return True

        except Exception as e:
            # print(traceback.format_exc())

            if len(e.args) == 6:  # breaks in load schema im 'solve' command -- understand why
                if 'Low-level communication error -15: Connection was closed' in e.args[1]:
                    table_callback.emit(count, TableHeaders.STATUS, "Restart")
                    # QtCore.QThread.msleep(500)  # Wait some time for OS to delete lock file

                    self.ansys_manager.exit()
                    del self.ansys_manager
                    # self.exit_ansys_experiment()
                    self.ansys_manager = self.force_start_ansys()
                    # If error is caused by user, try to restart one time
                    if first_try and constants.RESTART_AFTER_ERROR:
                        self.researchFromDetailModel(body_params, calc_param, cells, count, table_callback, False)
                    return False

            elif "Poorly shaped facets in surface mesh." in e.args[0]:
                table_callback.emit(count, TableHeaders.STATUS, "Face ERR")
            elif "VMESH failure, perhaps due to:" in e.args[0]:
                table_callback.emit(count, TableHeaders.STATUS, "VMESH ERR")
            elif "Meshing failure in volume" in e.args[0]:
                table_callback.emit(count, TableHeaders.STATUS, "MESH ERR")
            elif "Max stress is zero. MAPDL failed, there is a hole." in e.args[0]:
                table_callback.emit(count, TableHeaders.STATUS, "Cell ERR")
            else:  # TODO: check all unknown errors             e.args[1] - 'COMPLETED_NO'
                table_callback.emit(count, TableHeaders.STATUS, "Unkn ERR")

            # if "No volumes were meshed by the VMESH operation" in e.args[0]:
            #     table_callback.emit(count, TableHeaders.STATUS, "VMESH ERR")

            # restart experiment in case of 'exit'
            try:
                self.exit_ansys_experiment()
            except Exception:
                self.ansys_manager = self.force_start_ansys()
                return False

            return False

    def calculate_fitness_value(self, calc_param, count, max_press):
        size = calc_param.volume_part
        cells_amount = calc_param.cells_ox * calc_param.cells_oy
        x_0 = float(self.result_table.item(count, TableHeaders.DETAIL_X0).text())
        x_1 = float(self.result_table.item(count, TableHeaders.DETAIL_X1).text())
        y_0 = float(self.result_table.item(count, TableHeaders.DETAIL_Y0).text())
        y_1 = float(self.result_table.item(count, TableHeaders.DETAIL_Y1).text())
        working_zone = ((x_0, x_1), (y_0, y_1))
        fitness = Genetic.calculate_fitness_by_params(self.zero_stress, max_press, size, cells_amount, working_zone)
        return fitness

    def check_for_errors_basic(self):
        if self.app.result_table.rowCount() <= 0:
            return "Research table is empty."

    def check_for_errors_next(self):
        if self.threadpool.activeThreadCount() > 0:  # Exit if research is not complete
            return "Research is already in progress."
        return self.check_for_errors_basic()

    # #######################################################
    def print_output(self, s):
        print("Thread result:", s)

    def thread_complete(self):
        print("THREAD COMPLETE!")
    # #######################################################

    def exit_ansys_experiment(self):
        if self.ansys_manager is not None:  # or self.ansys_manager == "MAPDL exited":
            self.ansys_manager.save()
            self.ansys_manager.finish()
            self.ansys_manager.clear()

    def clear_and_exit(self):
        self.app.is_running = False
        self.app.stop_calculation = False

        # correct closing ANSYS manager
        if self.ansys_manager is not None:
            self.exit_ansys_experiment()
            self.ansys_manager.exit()
            self.ansys_manager = None

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
        page_size = 10000  # basic: 10000
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
            nproc=4,
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
        status = self.result_table.item(index, TableHeaders.STATUS).text()

        if status in ("Finished", "Parent 1", "Parent 2"):
            path = self.root_folder + os.sep + f"{index + 1}.rst"
            os.system("py plot_result.py \"" + path + "\"")
        else:
            return "This research failed or unfinished."

    def show_stress_chart(self, index):
        status = self.result_table.item(index, TableHeaders.STATUS).text()
        if status in ("Finished", "Parent 1", "Parent 2"):
            path = self.root_folder + os.sep + f"{index + 1}.rst"
            os.system("py plot_stress_chart.py \"" + path + "\"")

    def show_cluster_analyse(self):
        os.system("py plot_cluster_analyse.py \"" + self.root_folder + "\"")

