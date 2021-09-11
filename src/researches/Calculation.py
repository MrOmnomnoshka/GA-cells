import csv
import json
import os
import pathlib
# import ansys.mapdl
import re
import traceback
from datetime import datetime
from typing import List
from time import sleep
from ansys.mapdl.core import launch_mapdl
import pandas as pd
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QTableWidgetItem


from PyQt5.QtCore import QMutex, QObject, QThread, pyqtSignal
import logging


from src.researches.ResultTableHeaders import ResultTableHeaders
from src.researches.BodyParams import BodyParameters
from src.researches.Cells import NAngleCells, CircleCells, RectangleCells
from src.researches.Drawers import NAngleCellsDrawer, RectangleCellsDrawer
from src.researches.GA import Genetic

logging.basicConfig(format="%(message)s", level=logging.INFO)


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


class WorkerThread(QObject):
    finished = pyqtSignal()
    updatedBalance = pyqtSignal()

    def withdraw(self, person, amount, mutex, balance):
        logging.infqo("%s wants to withdraw $%.2f...", person, amount)
        mutex.lock()
        if balance - amount >= 0:
            sleep(1)
            balance -= amount
            logging.info("-$%.2f accepted", amount)
        else:
            logging.info("-$%.2f rejected", amount)
        logging.info("===Balance===: $%.2f", balance)
        self.updatedBalance.emit()
        mutex.unlock()
        self.finished.emit()


class Calculation:
    detail_fn = str
    load_schema_fn = str
    root_folder = str
    zero_stress = int
    generation_counter = 0
    min_stress_for_all_time = list()

    def __init__(self):
        self.results = {}

    def calculate_zero_stress(self, label, ansys_manager):
        # label.setText(label.text() + " ****")
        # TODO: uncomment
        # max_stress = self.research_zero_stress(ansys_manager)
        max_stress = 1061.04292

        if max_stress:
            # max_stress_label.setText(max_stress_label.text() + " " + str(max_stress))
            # label.setText("Нагрузка нулевая: " + str(max_stress))
            self.zero_stress = max_stress

    def calculate_infinity(self, result_table, ansys_manager, app):
        # An infinite cycle
        while app.is_running:  # Continue the experiment
            # self.calculate_next_iteration(result_table, ansys_manager, app)

            app.mutex.lock()
            t0 = "Нагрузка текущая:"
            t1 = "Нагрузка текущая: " + str(11111)
            t2 = "Нагрузка текущая: " + str(22222)
            t3 = "Нагрузка текущая: Жопа"
            t4 = "Нагрузка текущая: " + "Жопа2"
            t5 = "Нагрузка текущая: " + str(33333)

            if app.label_current_stress.text() == t0:
                app.change_stress_label(t1)
            elif app.label_current_stress.text() == t1:
                app.change_stress_label(t2)
            elif app.label_current_stress.text() == t2:
                app.change_stress_label(t3)
            elif app.label_current_stress.text() == t3:
                app.change_stress_label(t4)
            elif app.label_current_stress.text() == t4:
                app.change_stress_label(t5)
            elif app.label_current_stress.text() == t5:
                app.change_stress_label(t1)

            # app.mutex.unlock()
            sleep(1)

        else:
            sleep(1)  # not overload CPU on pause

    def calculate_next_iteration(self, result_table, ansys_manager, app):
        if self.generation_counter > 0:  # Not the first generation
            # Create new generation
            self.create_new_generation(result_table, app)

        # Count current generation
        self.calculate_current_research(result_table, ansys_manager, app)

    def create_new_generation(self, result_table, app):
        finished = self.get_all_finished_id_and_stress(result_table)

        if len(finished) >= 2:
            Genetic.start_new_generation(finished, self.zero_stress, result_table, app)
        else:
            # TODO: ??create and recalculate new generation??
            print("Bad News: Not enough parents.")
            pass

    def calculate_current_research(self, result_table, ansys_manager, app):
        # # recoding to a Exel file
        # file_path = self.root_folder + os.sep + "researches.csv"
        # with open(file_path, mode="w", newline="") as researches_csv:
        #     writer = csv.writer(researches_csv)
        #     research_result_data = ["research_id", "angle_num", "rotate_angle", "vol_part", "cells_ox", "cells_oy",
        #                             "research_Status"]
        #     writer.writerow(research_result_data)

        # TODO: вылетает тут, азобраться че каво, мб из за паралелльности
        # TODO: мб "pg.QtGui.QApplication.processEvents()"
        # app.change_stress_label("Нагрузка текущая: " + str(1))
        # app.change_stress_label("Нагрузка текущая: " + str(2))
        # app.change_stress_label("Нагрузка текущая: Жопа")
        # app.change_stress_label("Нагрузка текущая: " + "Жопа")
        # app.change_stress_label("Нагрузка текущая: " + str(3))

        if self.generation_counter > 0:
            app.increment_cb_generation()

        self.generation_counter += 1
        count = 0
        for row_index in range(result_table.rowCount()):
            param = self.__build_calculate_params(result_table, row_index)
            body_params = self.__build_body_params(result_table, row_index)
            cells = self.__calculate_cells(body_params, param)

            result_table.setItem(count, ResultTableHeaders.STATUS, QTableWidgetItem('In progress'))
            self.update_table(result_table)

            try:
                self.researchFromDetailModel(body_params, param, cells, self.root_folder,
                                             result_table, count, ansys_manager)
            except Exception as e:
                result_table.setItem(count, ResultTableHeaders.STATUS, QTableWidgetItem('Bad cell size'))
                self.update_table(result_table)
                print(e)

            # self.__write_row_in_csv_results(count, param)
            count += 1

        # Change stress label to current min stress
        all_stress = [i[1] for i in self.get_all_finished_id_and_stress(result_table)]
        min_stress = min(all_stress)
        self.min_stress_for_all_time.append(min_stress)
        # TODO: ВОТ ТУТ ВТОРОЙ РАЗ УМЕР!
        # app.change_stress_label("Нагрузка текущая: " + str(min_stress))
        app.add_generation_stress_in_plot(self.min_stress_for_all_time)

    def get_all_finished_id_and_stress(self, result_table):
        # TODO: (maybe) REMAKE IT IN UI.py
        finished = []
        for i in range(result_table.rowCount()):
            if result_table.item(i, ResultTableHeaders.STATUS).text() == "Finished":
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

    def __calc_params(self, context) -> List[CalculationParams]:
        list = []

        for angle_num in range(context.angle_num_start, context.angle_num_end + 1, context.angle_num_step):
            for rotate_angle in range(context.rotate_angle_start, context.rotate_angle_end + 1,
                                      context.rotate_angle_step):
                for volume_part in range(context.volume_part_start, context.volume_part_end + 1,
                                         context.volume_part_step):
                    for cells_ox in range(context.cells_ox_start, context.cells_ox_end + 1, context.cells_ox_step):
                        for cells_oy in range(context.cells_oy_start, context.cells_oy_end + 1, context.cells_oy_step):
                            list.append(CalculationParams(rotate_angle, angle_num, volume_part, cells_ox, cells_oy))

        return list

    def update_table(self, table):
        table.hide()
        table.update()
        table.show()

    def exit_ansys_experiment(self, ansys):
        ansys.save()
        ansys.run("FINISH")
        ansys.run("/CLEAR")
        # ansys.run("/INPUT FILE+ D:\\Programs\\ANSYS Inc\\v192\\ANSYS\\apdl\\start.ans")

    def researchFromDetailModel(self, body_params, calc_param, cells, research_folder, result_table, count, ansys):
        try:
            self.results[count] = [body_params, calc_param, cells, research_folder, 'IN_PROGRESS']
            cells_coordinates = self.__execute_ansys_commands(ansys, cells, body_params, calc_param)

            max_press = self.get_max_press(ansys)

            # TODO: add all 'file.db' aka model in folder like: (1,2,3...8) and read data from them by clicking 'result'
            try:
                # TODO: See 'TODO' in inner function
                # self.write_all_nodes_coordinates(ansys, research_folder)
                pass
            except Exception as e:
                print(e)

            # self.__write_cells_in_json(cells_coordinates, research_folder)
            result_table.setItem(count, ResultTableHeaders.STATUS, QTableWidgetItem('Finished'))
            result_table.setItem(count, ResultTableHeaders.MAX_PRESS, QTableWidgetItem(str(max_press)))
            self.update_table(result_table)

            self.exit_ansys_experiment(ansys)

            self.results[count] = [body_params, calc_param, cells, research_folder, 'FINISHED']
            return True

        except Exception as e:
            print(traceback.format_exc())
            if result_table:
                result_table.setItem(count, ResultTableHeaders.STATUS, QTableWidgetItem('Failed'))
                self.update_table(result_table)
            self.results[count] = [body_params, calc_param, cells, research_folder, 'FAILED']

            self.exit_ansys_experiment(ansys)
            return False

    def research_zero_stress(self, ansys):
        try:
            self.__execute_ansys_start_commands(ansys)
            self.__run_load_schema(ansys)
            max_press = self.get_max_press(ansys)

            self.exit_ansys_experiment(ansys)

            return max_press

        except Exception as e:
            print(traceback.format_exc())
            return False

    def __execute_ansys_commands(self, ansys, cells, body_params, calc_param):
        self.__execute_ansys_start_commands(ansys)

        drawer = self.create_drawer(ansys, cells, body_params, calc_param)
        res = ansys.run("*GET, KMax, VOLU,, NUM, MAX")
        start = res.index("VALUE= ") + 7
        volume_id = res[start:]

        drawer.set_cells(cells)
        cells_coordinates = drawer.draw_cells_volumes()

        ansys.run("VSBV,%s,ALL,,," % (volume_id))

        with open(file=self.load_schema_fn, mode="r", encoding="utf-8") as load_schema_commands:
            for command in load_schema_commands:
                if not command.isspace() and command[0] != '!':
                    ansys.run(command)

        return cells_coordinates

    def __execute_ansys_start_commands(self, ansys):
        ansys.run("/ BATCH")
        ansys.run("WPSTYLE,, , , , , , , 0")
        ansys.run("/ AUX15")
        ansys.run("IOPTN, IGES, SMOOTH")
        ansys.run("IOPTN, MERGE, YES")
        ansys.run("IOPTN, SOLID, YES")
        ansys.run("IOPTN, SMALL, YES")
        ansys.run("IOPTN, GTOLER, DEFA")
        ansys.run("IGESIN, '%s','IGS','%s' ! import" %
                  (str(pathlib.Path(self.detail_fn).stem), str(pathlib.Path(self.detail_fn).parent.absolute())))
        ansys.run("! VPLOT")
        ansys.run("FINISH")
        ansys.prep7()
        ansys.run("NUMCMP, ALL")
        ansys.run("/units, mpa")
        ansys.k()

    def __run_load_schema(self, ansys):
        with open(file=self.load_schema_fn, mode="r", encoding="utf-8") as load_schema_commands:
            for command in load_schema_commands:
                if not command.isspace() and command[0] != '!':
                    ansys.run(command)

    def __write_cells_in_json(self, cells_coordinates, research_folder: str):
        json_cells_coordinates = json.dumps(cells_coordinates)
        with open(research_folder + os.sep + "cells.json", "a") as json_cells_file:
            json_cells_file.write(json_cells_coordinates)

    def __is_java_installed(self) -> bool:
        return os.system("java -version") == 0

    def write_all_nodes_coordinates(self, ansys, research_folder: str, file: str = "nodes.csv"):
        nodes_data_frame = pd.DataFrame(columns=["node_id", "x", "y", "z"])
        start_node = 1
        page_size = 7000  # TODO: it was '10000'
        end_node = start_node + page_size
        nodes_count = self.get_count_of_nodes(ansys)
        # ####
        # is_java_installed = self.__is_java_installed()
        is_java_installed = False  # TODO: update java version //or// boost python
        # ####
        temp_file = research_folder + os.sep + "temp_nodes.txt"

        while start_node < nodes_count:
            get_nodes_command = "NLIST,{},{}, ,XYZ,NODE,,INTERNAL".format(start_node, end_node)
            nodes_str = ansys.run(get_nodes_command)

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

    def get_count_of_nodes(self, ansys) -> int:
        ansys.run("*GET, N_COUNT, NODE,, COUNT")
        status = ansys.run("*STATUS, N_COUNT")
        start = status.index("\n N_COUNT")
        max_stress = re.findall('\d+\\.\d+', status[start:])[0]

        return int(float(max_stress))

    def get_max_press(self, ansys):
        ansys.run("/ POST1")
        ansys.run("SET, FIRST")
        ansys.run("NSORT, S, EQV")
        ansys.run("*GET, STRESS_MAX, SORT,, MAX")
        status = ansys.run("*STATUS, STRESS_MAX")
        start = status.index("\n STRESS_MAX")
        # TODO: Да там и до этого 3 командами выше можно вытянуть макс стресс
        max_stress = re.findall('\d+\\.\d+', status[start:])[0]
        # TODO: ногда бывает Finished stress = 0, просто сделать из него FAILED

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
            start_timeout=2000,
            nproc=8,
            loglevel="DEBUG",
            log_apdl="w",
            exec_file=r"D:\Programs\ANSYS Inc\v192\ansys\bin\winx64\ANSYS192.exe")

    def create_drawer(self, ansys, cells, body_params, calc_params):
        if issubclass(cells.__class__, NAngleCells):
            return NAngleCellsDrawer(body_params, calc_params.angle_num, ansys)
        elif issubclass(cells.__class__, RectangleCells):
            return RectangleCellsDrawer(body_params, cells.rows, ansys)
        # elif (issubclass(cells.__class__, CircleCells)):
        #     return Cir

    def show_result(self, index):
        if self.results[index][ResultIndexes.STATUS] == 'FINISHED':
            path = self.results[index][ResultIndexes.RESEARCH_FOLDER] + os.sep + "file.rst"
            os.system("py plot_result.py \"" + path + "\"")

    def show_stress_chart(self, index):
        if self.results[index][ResultIndexes.STATUS] == 'FINISHED':
            path = self.results[index][ResultIndexes.RESEARCH_FOLDER] + os.sep + "file.rst"
            os.system("py plot_stress_chart.py \"" + path + "\"")

    def show_cluster_analyse(self):
        os.system("py plot_cluster_analyse.py \"" + self.root_folder + "\"")


class ResultIndexes:
    BODY_PARAMS = 0
    CALC_PARAMS = 1
    CELLS = 2
    RESEARCH_FOLDER = 3
    STATUS = 4
