import os
import pathlib
import shutil
from threading import Thread
from copy import copy

from ansys.mapdl.core import launch_mapdl
from PyQt5 import QtCore

import src.constants as constants
import src.util.ansys_parser as ansys_parser
import src.util.plot_result as plot_result
import src.util.plot_stress_chart as plot_stress_chart
from src.helper_classes.TableHeaders import TableHeaders
from src.helper_classes.BodyParams import BodyParameters
from src.helper_classes.CalculationParams import CalculationParams
from src.helper_classes.Cells import NAngleCells, CircleCells, RectangleCells
from src.helper_classes.Drawers import NAngleCellsDrawer, RectangleCellsDrawer, CircleCellsDrawer
from src.GA import Genetic
from src.ThreadsManager import Worker


# TODO(доп.): Сдлеать доп кнопку для выбора сохранять ли все резы, что бы можно было показывать из любого поколения
# TODO(доп.): Добавить скрин рядом\в\где-то в строке, что бы было видно сразу, не заходя в "Результат"
# TODO(доп.): Многопоточность и сразу пару экспреиментов? https://mapdldocs.pyansys.com/user_guide/pool.html
# TODO(доп.): При нажатии на паузу стопить всё на текущем экспр. не идти до конца. и потом начинать от сюда же


class Calculation:
    root_folder = zero_stress = stopped_id = ansys_manager = pop_data = None
    max_fitness_for_all_time = list()
    threadpool = QtCore.QThreadPool()  # for multithreading

    def __init__(self, app):
        # Prepare arguments for methods in class
        self.app = app

    def connect_worker_to_signals(self, worker):
        worker.signals.zero_stress_signal.connect(self.app.change_zero_stress_label)
        worker.signals.current_stress_signal.connect(self.app.change_current_stress_label)
        worker.signals.increment_cb.connect(self.app.increment_cb_generation)
        worker.signals.change_table_signal.connect(self.app.change_table_item)
        worker.signals.update_plot.connect(self.app.add_data_on_plot)
        worker.signals.calc_dimension.connect(self.app.change_body_size_parameters)

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

    def calc_model_dimensions_UI(self):
        worker = Worker(self.calc_model_dimensions)
        self.connect_worker_to_signals(worker)
        self.threadpool.start(worker)

    def calc_model_dimensions(self, **kwargs):
        # Start ANSYS if this is the first research
        if self.ansys_manager is None:
            self.ansys_manager = self.force_start_ansys()

        self.__ansys_import_model_IGS()

        self.dimensions = ansys_parser.get_dimensions(self.ansys_manager)
        # print(self.dimensions)

        self.clear_ansys_experiment()

        kwargs.get("dimension_callback").emit(self.dimensions)

        return

    def calculate_zero_stress(self, **kwargs):
        # Emulation of loading something
        kwargs.get("zero_stress_callback").emit(" *****")

        if constants.DEBUG:
            max_stress, mass = 46808.6826, 0.25631
        else:
            max_stress, mass = self.research_zero_stress()  # Count zero_stress

        if max_stress:
            self.zero_stress = max_stress
            self.zero_mass = mass

            kwargs.get("zero_stress_callback").emit(str(self.zero_stress))

    def research_zero_stress(self):
        try:
            self.__ansys_import_model_IGS()
            self.__ansys_run_load_schema()
            self.__ansys_solve()
            max_press = ansys_parser.get_max_press(self.ansys_manager)
            mass = ansys_parser.get_model_mass(self.ansys_manager)

            self.clear_ansys_experiment()

            return max_press, mass

        except Exception as e:
            print(e)
            return False

    def calculate_next_iteration(self, **kwargs):
        # Start ANSYS if this is the first research
        if self.ansys_manager is None:
            self.ansys_manager = self.force_start_ansys()

        if self.zero_stress is None:
            self.calculate_zero_stress(**kwargs)

        # Backup to excel file every N generation in case of some breaks
        if constants.BACKUP_TO_CSV and (self.pop_data.generation_counter + 1) % constants.SAVE_TO_CSV_EVERY_N == 0:
            self.app.save_csv(auto_save=True)

        # Count current generation
        self.calculate_current_research(**kwargs)

        if self.stopped_id is not None: return

        # TODO: if stopped on the last one - crashes

        # Count finished data
        full_table = self.pop_data.get_current_table_data()
        finished = self.get_all_finished(full_table)
        min_stress = min(float(s[TableHeaders.STRESS]) for s in finished)
        max_fitness = max(float(s[TableHeaders.FITNESS]) for s in finished)

        self.max_fitness_for_all_time.append(max_fitness)

        # Change stress label to current min stress
        kwargs.get("curr_stress_callback").emit(str(min_stress))

        # Update plot data
        kwargs.get("plot_callback").emit(self.max_fitness_for_all_time)

        # If button is turned off and research is stopped - turn it on
        if not self.app.is_running:
            self.app.button_play_pause.setEnabled(True)

        # Increment generation
        self.pop_data.generation_counter += 1

        # STOP
        # Stop if limit exceeded
        if self.pop_data.generation_counter >= constants.GENERATION_LIMIT:
            self.app.is_running = False
        # time_limit = None # TODO: add time limit (don't forget about pause)
        # if time_limit >= constants.TIME_LIMIT:
        #     self.app.is_running = False
        #     return

        # Crossover parents
        self.crossover_parents(finished, full_table)

        # Increase combo_box text of generations
        kwargs.get("increment_cb_callback").emit()

    def crossover_parents(self, finished, full_table):
        if len(finished) >= 2:
            new_data, index1, index2 = Genetic.start_new_generation(finished, full_table)
            self.pop_data.table_data.append(new_data)

            # Make possible to read Parents files in a new generation
            if constants.SAVE_PARENTS:
                path = self.root_folder + os.sep
                if index1 + 1 != 1:
                    shutil.copyfile(path + f'{index1 + 1}.db', path + '1.db')
                    shutil.copyfile(path + f'{index1 + 1}.rst', path + '1.rst')

                if index2 + 1 != 2:
                    shutil.copyfile(path + f'{index2 + 1}.db', path + '2.db')
                    shutil.copyfile(path + f'{index2 + 1}.rst', path + '2.rst')
        else:
            # TODO: ??create and recalculate new generation??
            print("Bad News: Not enough parents.")
            pass

    def get_all_finished(self, table_data):
        finished = []
        for i in range(len(table_data)):
            status = table_data[i][TableHeaders.STATUS]
            if self.is_research_done(status):
                finished.append(table_data[i])
        return finished

    def research(self, **kwargs):
        # Stop or pause calculating
        if self.app.is_running:  # if stopped while research isn't complete - disable button
            self.app.button_play_pause.setEnabled(False)

        self.app.is_running = not self.app.is_running
        self.app.button_play_pause.setDefault(self.app.is_running)

        # An infinite cycle
        while self.app.is_running:  # Continue the experiment
            self.calculate_next_iteration(**kwargs)

    def toggle_buttons_on_research(self, state):
        self.app.button_play_pause.setEnabled(state)

        self.app.button_stop.setEnabled(not state)

    def next_generation_research(self, **kwargs):
        self.toggle_buttons_on_research(False)

        self.calculate_next_iteration(**kwargs)

        self.toggle_buttons_on_research(True)

    def count_start_id(self):
        # Start from the last stop
        if self.stopped_id:
            range_start = self.stopped_id
            self.stopped_id = None
        # Start from 2-rd agent; skip researching parents(0,1) if exists
        elif constants.SAVE_PARENTS and self.pop_data.generation_counter > 0:
            range_start = 2
        # Start from the beginning
        else:
            range_start = 0
        return range_start

    def calculate_current_research(self, **kwargs):
        range_start = self.count_start_id()
        for row_index in range(range_start, constants.POPULATION_SIZE):
            # Stop if 'stop' button is pressed or a new experiment is loaded
            if self.app.stop_calculation:
                self.clear_and_exit()  # TODO(?): Does it needs to close ANSYS?
                self.stopped_id = row_index
                return None

            param = self.__build_calculate_params(row_index)
            body_params = self.__build_body_params(row_index)
            cells = self.__calculate_cells(body_params, param)
            if constants.SYMMETRY_OX:
                body_params2 = copy(body_params)

                mirror = (constants.Y_MAX - constants.Y_MIN) / 2
                body_params2.make_ox_symmetry(mirror)
                cells2 = self.__calculate_cells(body_params2, param)

                self.researchFromDetailModel(param, [body_params, body_params2], [cells, cells2], row_index,
                                             kwargs.get("table_callback"))
            else:
                self.researchFromDetailModel(param, [body_params], [cells], row_index, kwargs.get("table_callback"))

            # row = self.pop_data.get_current_table_row_data(row_index)
            # done = self.is_research_done(row[TableHeaders.STATUS])

    def save_db_and_rst_files(self, row_index):
        # Copy '.db, .rst' files
        for ext in (".db", ".rst"):
            original = self.root_folder + os.sep + 'file' + ext
            target = self.root_folder + os.sep + f'{row_index + 1}' + ext
            if os.path.exists(original):
                shutil.copyfile(original, target)

    def create_root_folder_and_move_to_it(self):
        self.root_folder = self.__build_root_folder()
        path = pathlib.Path(self.root_folder)
        path.parent.mkdir(parents=True, exist_ok=True)
        if not os.path.isdir(self.root_folder):  # Create root_folder if not exist
            os.mkdir(self.root_folder)
        return self.root_folder

    def __build_root_folder(self):
        # return str(os.getcwd() + os.sep + 'researches' + os.sep + datetime.now().strftime('%Y-%m-%d %H-%M-%S'))
        return str(os.getcwd() + os.sep + 'temp_files')

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

    def __build_calculate_params(self, row_index):
        table_data = self.pop_data.get_current_table_data()[row_index]
        return CalculationParams(
            int(table_data[TableHeaders.ROTATE_ANGLE]),
            int(table_data[TableHeaders.ANGLE_NUM]),
            int(table_data[TableHeaders.VOLUME_PART]),
            int(table_data[TableHeaders.CELLS_OX]),
            int(table_data[TableHeaders.CELLS_OY]))

    def __build_body_params(self, row_index):
        table_data = self.pop_data.get_current_table_data()[row_index]
        return BodyParameters(
            float(table_data[TableHeaders.DETAIL_X0]),
            float(table_data[TableHeaders.DETAIL_X1]),
            float(table_data[TableHeaders.DETAIL_Y0]),
            float(table_data[TableHeaders.DETAIL_Y1]),
            float(table_data[TableHeaders.DETAIL_Z0]),
            float(table_data[TableHeaders.DETAIL_Z1]))

    def researchFromDetailModel(self, param, body_params, cells, count, table_callback, first_try=True):
        try:
            # ================ STATUS SHOWING ================
            self.save_and_show_current_state(count, "Solving", "", "", table_callback)

            cells_coordinates = self.__execute_ansys_commands(param, body_params, cells, count, table_callback)

            # calculate stress, mass, fitness
            max_press = ansys_parser.get_max_press(self.ansys_manager)
            mass = ansys_parser.get_model_mass(self.ansys_manager)

            if max_press == 0:
                raise ValueError("Max stress is zero. MAPDL failed, there is a hole.")
            elif max_press > constants.MAX_STRESS:
                raise ValueError("Stress limit error. Stress value is grater than maximum allowed")

            fitness = self.calculate_fitness_value(param, body_params[0], max_press, mass)
            status, stress, fitness = "Finished", str(round(max_press, 4)), str(round(fitness, 4))

        except Exception as e:
            error_msg = ""
            if len(e.args) == 6:
                if 'Low-level communication error -15: Connection was closed' in e.args[1]:
                    error_msg = "Restart"
                    # ================ STATUS SHOWING ================
                    self.save_and_show_current_state(count, error_msg, "", "", table_callback)

                    self.ansys_manager.exit()  # TODO: No need in exit, but need some time to create lock file .___. add timeout

                    del self.ansys_manager
                    self.ansys_manager = self.force_start_ansys()
                    # If error is caused by user, try to restart one time
                    if first_try and constants.RESTART_AFTER_ERROR:
                        self.researchFromDetailModel(param, [body_params], [cells], count, table_callback, False)
            elif "Poorly shaped facets in surface mesh." in e.args[0]:
                error_msg = "Face ERR"
            elif "VMESH failure" in e.args[0] or "Volume mesh failure" in e.args[0]:
                error_msg = "VMESH ERR"
            elif "Meshing failure in volume" in e.args[0]:
                error_msg = "MESH ERR"
            elif "Max stress is zero. MAPDL failed, there is a hole." in e.args[0]:
                error_msg = "Cell ERR"
            elif "One or more of pressing area is corrupted or destroyed." in e.args[0]:
                error_msg = "Press ERR"
            elif "One or more of supporting area is corrupted or destroyed." in e.args[0]:
                error_msg = "DOF ERR"
            elif "Stress limit error. Stress value is grater than maximum allowed" in e.args[0]:
                error_msg = "Max Stress"
            elif "Output entity is identical to the first input entity for VSBV command." in e.args[0]:
                error_msg = "No Cells"
            elif "Area list could contain multiple volumes" in e.args[0]:
                error_msg = "2+ Volum"
            else:  # TODO: check all unknown errors         For EXP: e.args[1] - 'COMPLETED_NO'
                error_msg = "Unkn ERR"

            status, stress, fitness = error_msg, "", ""

        # ================ STATUS SHOWING ================
        self.save_and_show_current_state(count, status, stress, fitness, table_callback)

        self.clear_ansys_experiment()

        # Save temp files if needed
        if constants.SAVE_TEMP_FILES:
            self.save_db_and_rst_files(count)

    def save_and_show_current_state(self, count, status, stress, fitness, table_callback):
        # Save table state in Pop class
        self.pop_data.add_status_stress_fitness_data(count, status, stress, fitness)

        if self.app.is_current_generation_the_last_one():  # Change data only when table is active
            table_callback.emit(count, TableHeaders.STATUS, status)
            table_callback.emit(count, TableHeaders.STRESS, stress)
            table_callback.emit(count, TableHeaders.FITNESS, fitness)

    def save_all_for_debug(self, count):
        self.ansys_manager.save()
        self.ansys_manager.finish()
        self.save_db_and_rst_files(count)

    def calculate_fitness_value(self, calc_param, body_params, press, mass):
        fitness = Genetic.calculate_fitness_by_params(self.zero_stress, self.zero_mass, press, mass, calc_param,
                                                      body_params)
        return fitness

    def is_research_running(self):
        return self.threadpool.activeThreadCount() > 0

    def is_result_table_empty(self):
        return self.app.result_table.rowCount() == 0

    # #######################################################
    def print_output(self, s):
        print("Thread result:", s)

    def thread_complete(self):
        print("THREAD COMPLETE!")

    # #######################################################

    def clear_ansys_experiment(self):
        if self.ansys_manager is not None:  # or self.ansys_manager == "MAPDL exited":
            self.ansys_manager.save()
            self.ansys_manager.finish()
            self.ansys_manager.clear()

    def clear_and_exit(self):
        self.app.is_running = False
        self.app.stop_calculation = False

        # correct closing ANSYS manager
        if self.ansys_manager is not None:
            self.clear_ansys_experiment()
            self.ansys_manager.exit()
            self.ansys_manager = None

    def force_start_ansys(self):
        root_folder = self.create_root_folder_and_move_to_it()
        ansys_manager = None
        while ansys_manager is None:
            ansys_manager = self.init_ansys(root_folder)
        return ansys_manager

    def __execute_ansys_commands(self, calc_param, body_params, cells, count, table_callback):
        # ================ STATUS SHOWING ================
        self.save_and_show_current_state(count, "Importing...", "", "", table_callback)

        self.__ansys_import_model_IGS()

        # ================ STATUS SHOWING ================
        self.save_and_show_current_state(count, "Modeling...", "", "", table_callback)

        for i in range(len(body_params)):
            volume_id = ansys_parser.get_max_element_id_from_command(self.ansys_manager, "VOLU")

            drawer = self.create_drawer(cells[i], body_params[i], calc_param)
            drawer.set_cells(cells[i])
            cells_coordinates = drawer.draw_cells_volumes()

            output = self.ansys_manager.run("VSBV,%s,ALL,,," % str(volume_id))

            if not constants.SYMMETRY_OX or i == 1:  # Save not symmetry or only second version
                self.save_all_for_debug(count)  # TODO: for debug delete this later
                self.ansys_manager.run("/PREP7")

            if "Output entity is identical to the first input entity for VSBV command." in output:
                raise ValueError("Output entity is identical to the first input entity for VSBV command.")

            # Running this ti check if there is more than 1 VOLUME or getting an Error
            self.ansys_manager.run("VA, ALL")

        # ================ STATUS SHOWING ================
        self.save_and_show_current_state(count, "Loading...", "", "", table_callback)

        self.__ansys_run_load_schema()

        self.check_for_loading_errors()

        # ================ STATUS SHOWING ================
        self.save_and_show_current_state(count, "Solving...", "", "", table_callback)
        self.__ansys_solve()  # Run solve command and calculate all data

        return cells_coordinates

    def check_for_loading_errors(self):
        # Do not waste time on solving if experiment is broken
        pressed_areas = ansys_parser.get_pressed_areas(self.ansys_manager)
        support_areas = ansys_parser.get_supported_areas(self.ansys_manager)
        with open(self.app.input_load_schema_file.text()) as file:
            load_schema = file.read()
        needed_loads = ansys_parser.analyze_load_schema(load_schema)

        # One or more of pressing area is corrupted or destroyed
        if pressed_areas != needed_loads["DA"]:  # DA - [D]isplacement support on some amount of [A]reas
            raise ValueError("One or more of pressing area is corrupted or destroyed. Can't SOLVE.")
        # One or more of supporting area is corrupted or destroyed
        if support_areas != needed_loads["SFA"]:  # SFA - [S]tructural [F]orce pressure on some amount of [A]reas
            raise ValueError("One or more of supporting area is corrupted or destroyed. Can't SOLVE.")

    def __ansys_import_model_SATIN(self):
        self.ansys_manager.run("~SATIN,'%s','sat','%s',SOLIDS,0" % (
            str(pathlib.Path(self.app.input_detail_file.text()).stem),
            str(pathlib.Path(self.app.input_detail_file.text()).parent.absolute())))
        self.ansys_manager.run("FINISH")
        self.ansys_manager.prep7()
        self.ansys_manager.run("NUMCMP, ALL")
        self.ansys_manager.run("/UNITS, mpa")

    def __ansys_import_model_IGS(self):
        self.ansys_manager.run("/AUX15")
        self.ansys_manager.run("IOPTN,IGES,SMOOTH")
        self.ansys_manager.run("IOPTN,MERGE,NO")
        self.ansys_manager.run("IOPTN,SOLID,NO")
        self.ansys_manager.run("IOPTN,SMALL,NO")
        self.ansys_manager.run("IOPTN,GTOLER, DEFA  ")
        self.ansys_manager.run("IGESIN,'%s','IGS','%s'" % (
            str(pathlib.Path(self.app.input_detail_file.text()).stem),
            str(pathlib.Path(self.app.input_detail_file.text()).parent.absolute())))

        self.ansys_manager.run("/PREP7")
        self.ansys_manager.run("NUMMRG, ALL")
        self.ansys_manager.run("NUMCMP, ALL")
        self.ansys_manager.run("/UNITS, mpa")
        self.ansys_manager.run("VA, ALL")

    def __ansys_run_load_schema(self):
        with open(file=self.app.input_load_schema_file.text(), mode="r", encoding="utf-8") as load_schema_commands:
            for command in load_schema_commands:
                # if 'smart meshing' is ON, create mesh with suitable quality [1-10]
                if "SMRT" in command and constants.SMART_MESHING:
                    command = command.replace("!SMRT,10", f"SMRT,{constants.MESH_QUALITY}")

                if not command.isspace() and command[0] != '!':
                    self.ansys_manager.run(command)

    def __ansys_solve(self):
        # calc all experimental data
        self.ansys_manager.run("FINISH")
        self.ansys_manager.run("/SOL")
        self.ansys_manager.run("SOLVE")

    def init_ansys(self, root_folder):
        return launch_mapdl(
            nproc=4,  # Number of processors.
            # ram=1,  # Fixed amount of memory to request for MAPDL.
            loglevel="DEBUG",  # Sets which messages are printed to the console.
            start_timeout=4000,  # Maximum allowable time to connect to the MAPDL server.
            override=True,  # Attempts to delete the lock file at the run_location.
            # log_apdl="w",  # Enables logging every APDL command to the local disk.
            remove_temp_files=True,  # Removes temporary files on exit.
            run_location=root_folder,  # MAPDL working directory.
            exec_file=r"D:\Programs\ANSYS Inc\v192\ansys\bin\winx64\ANSYS192.exe",  # The location of the MAPDL exec.
            # For jupyter (...I suppose)
            # memory=4,
            append=True,
            # interactive_plotting=True
        )

        # mapdl GPU acess: https://www.cfd-online.com/Forums/ansys/185213-unknown-error.html

    def create_drawer(self, cells, body_params, calc_params):
        if issubclass(cells.__class__, NAngleCells):
            return NAngleCellsDrawer(body_params, calc_params.angle_num, self.ansys_manager)
        elif issubclass(cells.__class__, RectangleCells):
            return RectangleCellsDrawer(body_params, cells.rows, self.ansys_manager)
        elif issubclass(cells.__class__, CircleCells):
            return CircleCellsDrawer(body_params, cells.rows, self.ansys_manager)

    def is_research_done(self, status):
        return status in ("Finished", "Parent 1", "Parent 2")

    def show_result(self, index):
        # TODO: open in new py window
        status = self.app.result_table.item(index, TableHeaders.STATUS).text()
        if constants.DEBUG or self.is_research_done(status):
            # self.root_folder = 'D:\\DIPLOMA\\app\\researcher\\temp_files'
            path = self.root_folder + os.sep + f"{index + 1}.rst"
            Thread(target=plot_result.show_principal_nodal_stress, args=(path,)).start()
        else:
            return "This research failed or unfinished."

    def show_stress_chart(self, index):
        status = self.app.result_table.item(index, TableHeaders.STATUS).text()
        if constants.DEBUG or self.is_research_done(status):
            path = self.root_folder + os.sep + f"{index + 1}.rst"
            Thread(target=plot_stress_chart.show_stress_chart, args=(path,)).start()
            plot_stress_chart.show_stress_chart(path)
        else:
            return "This research failed or unfinished."

    def show_cluster_analyse(self):
        os.system("py src\\clusterization\\plot_cluster_analyse.py \"" + self.root_folder + "\"")
