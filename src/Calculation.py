import json
import os
import pathlib
import shutil
from datetime import datetime

from ansys.mapdl.core import launch_mapdl
from PyQt5 import QtCore

import src.constants as constants
import src.util.ansys_parser as ansys_parser
from src.PopulationData import PopulationData
from src.helper_classes.TableHeaders import TableHeaders
from src.helper_classes.CellParams import CellParams
from src.helper_classes.Drawers import PerfectCellsDrawer
from src.GA import Genetic
from src.ThreadsManager import Worker


# TODO(доп.): Сдлеать доп кнопку для выбора сохранять ли все резы, что бы можно было показывать из любого поколения
# TODO(доп.): Добавить скрин рядом\в\где-то в строке, что бы было видно сразу, не заходя в "Результат" (наводя мышкой?)
# TODO(доп.): Многопоточность и сразу пару экспреиментов? https://mapdldocs.pyansys.com/user_guide/pool.html
# TODO(доп.): Генериовать ячейки в пределах главной площади детали (кривая форма (как банан например)), UI выбор?
# TODO(доп.): Разбивать модель на воксели? Проходить ГА пару раз по уже сделанным ГА?
# TODO(доп.): После загрузки данных, возможность пересчитать и показать любую выбранную хромосому
# TODO(доп.): Сохранять скрины всех особей и родителей, и скидывать в папку, после из этого сделать видео\анимацию с плавным переходом скринов от поколения к поколению, визуально продемонстрировать работу ГА и поиск оптимума(?)


class Calculation:
    root_folder = zero_stress = zero_mass = stopped_id = ansys_manager = table_callback = None
    pop_data: PopulationData = None
    threadpool = QtCore.QThreadPool()  # for multithreading
    stopping_calculation = False

    def clear(self):
        self.zero_stress = self.zero_mass = self.stopped_id = None
        self.stopping_calculation = False

    def __init__(self, app):
        # Prepare arguments for methods in class
        self.app = app

    def connect_worker_to_signals(self, worker):
        worker.signals.zero_stress_signal.connect(self.app.change_zero_stress_label)
        worker.signals.current_stress_signal.connect(self.app.change_current_stress_label)
        worker.signals.increment_cb.connect(self.app.increment_cb_generation)
        worker.signals.change_table_signal.connect(self.app.change_table_item)
        worker.signals.update_plot.connect(self.app.add_data_on_plot)
        worker.signals.toggle_buttons.connect(self.app.toggle_buttons_on_research)

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

    def set_model_dimensions(self):
        # Start ANSYS if this is the first research
        if self.ansys_manager is None:
            self.ansys_manager = self.force_start_ansys()

        self.__ansys_import_model_IGS()

        xd, yd, zd = ansys_parser.get_dimensions(self.ansys_manager)
        # xd, yd, zd = list(map(int, xd)), list(map(int, yd)), list(map(int, zd))
        constants.X_MIN, constants.X_MAX = xd[0] + constants.OFFSET, xd[1] - constants.OFFSET
        constants.Y_MIN, constants.Y_MAX = yd[0] + constants.OFFSET, yd[1] - constants.OFFSET
        # No offset on Z axis in this version
        constants.Z_MIN, constants.Z_MAX = zd
        print("Model size:", xd, yd, zd)

        self.clear_ansys_experiment()

    def calculate_zero_stress(self, **kwargs):
        # Emulation of loading something
        kwargs.get("zero_stress_callback").emit(" *****")

        if constants.DEBUG:
            max_stress, mass = 10702218.18, 69.96
        else:
            max_stress, mass = self.research_zero_stress()  # Count zero_stress

        self.zero_stress = max_stress
        self.zero_mass = mass

        kwargs.get("zero_stress_callback").emit(str(self.zero_stress))

    def research_zero_stress(self):
        try:
            self.__ansys_import_model_IGS()
            self.__ansys_generate_mesh()
            self.__ansys_run_load_schema()
            self.__ansys_solve()

            max_press = ansys_parser.get_max_press(self.ansys_manager)
            mass = ansys_parser.get_model_mass(self.ansys_manager)

            self.clear_ansys_experiment()

            return max_press, mass

        except Exception as e:
            print(e)
            return 0, 0

    def calculate_next_iteration(self, **kwargs):
        # Start ANSYS if this is the first research
        if self.ansys_manager is None:
            self.ansys_manager = self.force_start_ansys()

        if self.zero_stress is None:  # NOTE: It used as a marker of a started experiment. Make marker if want delete zs
            self.calculate_zero_stress(**kwargs)

        # Backup to excel file every N generation in case of some breaks
        if constants.BACKUP_TO_CSV and (self.pop_data.generation_counter + 1) % constants.SAVE_TO_CSV_EVERY_N == 0:
            self.app.save_research(auto_save=True)

        # Count current generation
        self.calculate_current_generation(**kwargs)

        if self.stopping_calculation:
            return

        # Count finished data
        full_table = self.pop_data.get_current_table_data()
        finished = self.get_finished_data(full_table)

        if len(finished) >= 2:
            # Change stress label to current min stress
            min_stress = min(float(s[TableHeaders.STRESS]) for s in finished)
            kwargs.get("curr_stress_callback").emit(str(min_stress))
            # Update plot data
            max_fitness = max(float(s[TableHeaders.FITNESS]) for s in finished)  # Elites\Parents counts too
            self.pop_data.max_fitness_for_all_time.append(max_fitness)
            kwargs.get("plot_callback").emit(self.pop_data.max_fitness_for_all_time)

            # Increment generation
            self.pop_data.generation_counter += 1

            # Crossover parents
            self.crossover_parents(finished)

            # Increase combo_box text of generations; !! NOTE: it automatically will change result table
            kwargs.get("increment_cb_callback").emit()

            # checking exit conditions
            self.check_for_limits()

        else:
            print("Recalculating generation -", self.pop_data.generation_counter)

            # Get table with values
            if self.pop_data.generation_counter == 0:
                # create new table from scratch
                self.app.create_first_table()
            else:  # recalculate last table
                # Count finished data
                full_table = self.pop_data.get_previous_table_data()
                finished = self.get_finished_data(full_table)

                new_data = Genetic.start_new_generation(finished, self.pop_data.elite_list)
                curr_index = self.pop_data.generation_counter
                self.pop_data.table_data[curr_index] = new_data

                self.pop_data.change_result_table_by_generation(self.app.result_table, curr_index)  # not threading safe, mb add callback to ui

            self.calculate_next_iteration(**kwargs)  # Start new iteration

    def crossover_parents(self, finished):
        new_data = Genetic.start_new_generation(finished, self.pop_data.elite_list)
        self.pop_data.table_data.append(new_data)

    def check_for_limits(self):
        # Stop if generation limit exceeded
        if self.pop_data.generation_counter >= constants.GENERATION_LIMIT:
            self.stopping_calculation = True
            print("Stop due to generation limit.")
        # elif time_limit >= constants.TIME_LIMIT:   # TODO: add time limit (don't forget about pause)
        #     self.stopping_calculation = True

        if self.stopping_calculation:
            save_file = datetime.now().strftime("%d-%m-%y %H-%M-%S") + " gen-" + str(self.pop_data.generation_counter)
            print("Experiment completed! All data was saved to JSON file:", save_file)

            save_file_path = os.getcwd() + os.sep + "saves" + os.sep + save_file + ".json"
            self.save_data_as_json(save_file_path)

    def save_data_as_json(self, save_file):
        settings_name = ["constants", "self.pop_data"]
        json_settings = {}
        for s in settings_name:
            module = getattr(self, s[5:]) if "self" in s else globals().get(s)
            if module:
                data = self.get_all_variables(module)
                json_settings.update({s: json.dumps(data)})

        json_string = json.dumps(json_settings)

        with open(save_file, "w") as outfile:
            outfile.write(json_string)

    def load_data_from_json(self, save_file):
        is_debug = constants.DEBUG

        with open(save_file) as json_file:
            data = json.load(json_file)
            for s in data:
                module = getattr(self, s[5:]) if "self" in s else globals().get(s)
                if module:
                    for name, value in json.loads(data[s]).items():
                        setattr(module, name, value)

        # If current mode is Debug, load in debug mode too
        constants.DEBUG = is_debug

    def get_all_variables(self, module):
        return {key: value for key, value in vars(module).items() if not (key.startswith('__') or key.startswith('_'))}

    def get_finished_data(self, full_table):
        finished = self.get_all_finished(full_table)

        # Find best elem in this research
        max_fit_from_finished = None
        if finished:  # Get best element from finished if exist
            max_fit_from_finished = Genetic.find_elem_with_max_fitness(finished)

        # Add elite to a finished list AFTER finding the best one
        if constants.ELITE_STRATEGY:
            finished.extend(self.pop_data.elite_list)

        # Add best in this generation to elite AFTER extending 'finished'
        if max_fit_from_finished and len(finished) >= 2:  # try to add best to elite
            self.add_to_elite(max_fit_from_finished, full_table)
        return finished

    def add_to_elite(self, elem_to_add, full_table):
        # TODO: Plz redo this!, my eyes are burning x_x
        elite = self.pop_data.elite_list
        append = False
        if not elite:  # if elite list empty (first generation)
            append = True
        else:  # Not empty
            if len(elite) < constants.ELITE_AMOUNT:  # If elite isn't full
                append = True
            else:  # elite FULL. Need to find and replace for a better one
                min_elite = Genetic.find_elem_with_min_fitness(elite)
                if float(elem_to_add[TableHeaders.FITNESS]) > float(min_elite[TableHeaders.FITNESS]):
                    if elem_to_add not in elite:
                        old_index = elite.index(min_elite)
                        elem_to_add_index = full_table.index(elem_to_add)
                        self.save_db_and_rst_files(str(elem_to_add_index + 1), str(old_index + 1))
                        elite[old_index] = elem_to_add  # if new one is better - replace as Queue(LIFO).

        if append and elem_to_add not in elite:
            elite.append(elem_to_add)

            elem_to_add_index = full_table.index(elem_to_add)

            self.save_db_and_rst_files(str(elem_to_add_index + 1), str(len(elite)))

    def get_all_finished(self, table_data):
        finished = []
        for i in range(len(table_data)):
            status = table_data[i][TableHeaders.STATUS]
            if self.is_research_finished(status):
                finished.append(table_data[i])
        return finished

    def research(self, **kwargs):
        kwargs.get("ui_buttons_callback").emit(False)

        # An infinite cycle
        while not self.stopping_calculation:  # Continue the experiment
            self.calculate_next_iteration(**kwargs)
        self.stopping_calculation = False

        kwargs.get("ui_buttons_callback").emit(True)

    def next_generation_research(self, **kwargs):
        kwargs.get("ui_buttons_callback").emit(False)

        self.calculate_next_iteration(**kwargs)
        self.stopping_calculation = False

        kwargs.get("ui_buttons_callback").emit(True)

    def count_start_id(self):
        # Start from the last stop
        if self.stopped_id:
            range_start = self.stopped_id
            self.stopped_id = None
        # Start from 2 agent; skip researching agents(0,1) if exists
        elif constants.SAVE_PARENTS and self.pop_data.generation_counter > 0:
            range_start = 2
        # Start from N agent; skip researching agents(0..N-1) if exists
        elif constants.SAVE_ELITE and self.pop_data.generation_counter > 0:
            range_start = len(self.pop_data.elite_list)
        # Start from the beginning
        else:
            range_start = 0
        return range_start

    def calculate_current_generation(self, **kwargs):
        self.table_callback = kwargs.get("table_callback")  # create individual variable for simplicity

        range_start = self.count_start_id()  # TODO: just skip all where 'status' is not null
        for row_index in range(range_start, constants.POPULATION_SIZE):
            # Stop if 'stop' button is pressed or a new experiment is loaded
            if self.stopping_calculation:
                self.clear_ansys_experiment()
                self.stopped_id = row_index
                return None

            cells_params = self.build_cells_params(row_index)
            self.calculate_one_research(cells_params, row_index)

    def save_db_and_rst_files(self, orig_name, new_name):
        # Copy '.db, .rst' files
        for ext in (".db", ".rst"):
            original = self.root_folder + os.sep + orig_name + ext
            target = self.root_folder + os.sep + new_name + ext
            if os.path.exists(original) and original != target:
                shutil.copyfile(original, target)

    def create_root_folder(self):
        self.root_folder = self.build_root_folder()
        path = pathlib.Path(self.root_folder)
        path.parent.mkdir(parents=True, exist_ok=True)
        if not os.path.isdir(self.root_folder):  # Create root_folder if not exist
            os.mkdir(self.root_folder)
        return self.root_folder

    def build_root_folder(self):
        return str(os.getcwd() + os.sep + "temp_files")

    def build_cells_params(self, row_index):
        table_data = self.pop_data.get_current_table_data()[row_index]
        cell = CellParams(table_data)
        cell.calculate_all()
        return cell

    def calculate_one_research(self, cells_params, row_index, first_try=True):
        self.save_table_and_show_current_state(row_index, "Solving", "", "")

        self.build_and_load_model(cells_params, row_index, first_try)

        # Save temp files if needed
        if constants.SAVE_TEMP_FILES:
            self.save_row_by_index(row_index)

        self.clear_ansys_experiment()

    def build_and_load_model(self, cells_params, row_index, first_try):
        try:
            self.__execute_ansys_commands(cells_params, row_index)

            # calculate stress, mass
            max_press = ansys_parser.get_max_press(self.ansys_manager)  # TODO: count it faster (get data from solve?)
            mass = ansys_parser.get_model_mass(self.ansys_manager)

            if max_press == 0:
                raise ValueError("Max stress is zero. MAPDL failed, there is a hole.")
            elif max_press > constants.MAX_STRESS:
                raise ValueError("Stress limit error. Stress value is grater than maximum allowed")

            # calculate fitness
            fitness = self.calculate_fitness_value(cells_params, max_press, mass)

            self.save_table_and_show_current_state(row_index, "Finished", str(round(max_press, 4)), str(round(fitness, 4)))

        except Exception as e:
            err_text = str(e.args[1]) if len(e.args) > 1 else e.args[0]  # if len(e.args) == 6 or 2

            user_error_msg = self.create_error_message_from_output(err_text)

            self.save_table_and_show_current_state(row_index, user_error_msg, "", "")

            if user_error_msg == "Restart":
                self.save_table_and_show_current_state(row_index, user_error_msg, "", "")

                self.restart_ansys(cells_params, row_index, first_try)

    def create_error_message_from_output(self, err_text):
        if "Connection was closed" in err_text or "COMPLETED_NO" in err_text:
            error_msg = "Restart"
        elif "Poorly shaped facets in surface mesh." in err_text:
            error_msg = "Face ERR"
        elif "VMESH failure" in err_text or "Volume mesh failure" in err_text:
            error_msg = "VMESH ERR"
        elif "Meshing failure in volume" in err_text:
            error_msg = "MESH ERR"
        elif "Max stress is zero. MAPDL failed, there is a hole." in err_text:
            error_msg = "Cell ERR"
        elif "One or more of pressing area is corrupted or destroyed." in err_text:
            error_msg = "Press ERR"
        elif "One or more of supporting area is corrupted or destroyed." in err_text:
            error_msg = "DOF ERR"
        elif "One or more of loading areas is corrupted or destroyed." in err_text:
            error_msg = "AREAS ERR"
        elif "Stress limit error. Stress value is grater than maximum allowed" in err_text:
            error_msg = "Max Stress"
        elif "Output entity is identical to the first input entity for VSBV command." in err_text:
            error_msg = "Cells AIR"
        elif "Area list could contain multiple volumes" in err_text or "More than 1 VOLUME." in err_text:
            error_msg = "2+ Volume"
        else:  # TODO: check all unknown errors     EXAMPL: Unkn ERR Boolean operation failed.  Try adjusting the tolerance value on the BTOL command to some fraction of the minimum keypoint distance.Model Size (current problem) 6.941378e+01, current BTOL setting 1.000000e-05, minimum KPT distance 3.852823e-01.
                                                    # TODO: COMPLETED_MAYBE
            error_msg = "Unkn ERR"
            print(error_msg, err_text)
        return error_msg

    def restart_ansys(self, cells_params, row_index, first_try):
        lockfile = self.root_folder + os.sep + "file.lock"
        for i in range(5):  # try 5 time to delete lock file
            QtCore.QThread.msleep(500)  # If exited already - need to give some time to create lock file
            try:
                if os.path.exists(lockfile):
                    os.remove(lockfile)  # Bug with removing 'lock' file via ansys, removing it manually here
                    break
            except PermissionError:
                continue

        # del self.ansys_manager
        self.ansys_manager.exit()

        QtCore.QThread.msleep(500)

        self.ansys_manager = self.force_start_ansys()  # Restarting ANSYS

        # If error is caused ansys closing - try to restart experiment once
        if first_try and constants.RESTART_AFTER_ERROR:
            self.calculate_one_research(cells_params, row_index, False)

    def save_table_and_show_current_state(self, row_index, status, stress, fitness):
        # Save table state in Pop class
        self.pop_data.add_status_stress_fitness_data(row_index, status, stress, fitness)

        if self.app.is_current_generation_the_last_one():  # Change data only when table is active
            self.table_callback.emit(row_index, TableHeaders.STATUS, status)
            self.table_callback.emit(row_index, TableHeaders.STRESS, stress)
            self.table_callback.emit(row_index, TableHeaders.FITNESS, fitness)

    def save_row_by_index(self, row_index):
        if self.ansys_manager and not str(self.ansys_manager) == "MAPDL exited":
            self.ansys_manager.save()
            self.save_db_and_rst_files("file", str(row_index + 1))

    def calculate_fitness_value(self, cells_params, press, mass):
        fitness = Genetic.calculate_fitness_by_params(self.zero_stress, self.zero_mass, press, mass, cells_params)
        return fitness

    def is_research_running(self):
        return self.threadpool.activeThreadCount() > 0

    # #######################################################
    def print_output(self, s):
        print("Thread result:", s)

    def thread_complete(self):
        print("THREAD COMPLETE!")

    # #######################################################

    def clear_ansys_experiment(self):
        if self.ansys_manager and not str(self.ansys_manager) == "MAPDL exited":
            # self.ansys_manager.save()  # TODO: do i need save here?
            self.ansys_manager.finish()
            self.ansys_manager.clear()

    def force_start_ansys(self):
        root_folder = self.create_root_folder()
        ansys_manager = None
        while ansys_manager is None:
            ansys_manager = self.init_ansys(root_folder)
        return ansys_manager

    def check_for_loading_errors(self):
        pressed_areas = ansys_parser.get_pressed_areas(self.ansys_manager)
        support_areas = ansys_parser.get_supported_areas(self.ansys_manager)
        needed_loads = ansys_parser.analyze_load_schema_on_actions(self.read_load_schema())

        # One or more of pressing area is corrupted or destroyed
        if pressed_areas != needed_loads["DA"]:  # DA - [D]isplacement support on some amount of [A]reas
            raise ValueError("One or more of pressing area is corrupted or destroyed. Can't SOLVE.")
        # One or more of supporting area is corrupted or destroyed
        if support_areas != needed_loads["SFA"]:  # SFA - [S]tructural [F]orce pressure on some amount of [A]reas
            raise ValueError("One or more of supporting area is corrupted or destroyed. Can't SOLVE.")

    def check_for_modeling_errors(self, subtract_output):
        # No new elements created (cells in air)
        if "Output entity is identical to the first input entity for VSBV command." in subtract_output:
            raise ValueError("Output entity is identical to the first input entity for VSBV command.")

        # Cells created but they divides model on more than 1 VOLUME
        volumes = ansys_parser.get_element_ids(subtract_output)
        if len(volumes) > 1:
            raise ValueError("More than 1 VOLUME. Can't SOLVE.")

        # Check if delete some of crucial areas
        areas_exists = ansys_parser.get_all_areas(self.ansys_manager)
        areas_in_load = ansys_parser.analyze_load_schema_on_items(self.read_load_schema())
        for area in areas_in_load:
            if area not in areas_exists:
                raise ValueError("One or more of loading areas is corrupted or destroyed. Can't SOLVE.")

    def __execute_ansys_commands(self, cells_params, row_index):
        self.save_table_and_show_current_state(row_index, "Importing...", "", "")
        self.__ansys_import_model_IGS()

        self.save_table_and_show_current_state(row_index, "Modeling...", "", "")
        self.__ansys_add_cells_to_model(cells_params, row_index)

        self.save_table_and_show_current_state(row_index, "Meshing...", "", "")
        self.__ansys_generate_mesh(row_index)

        self.save_table_and_show_current_state(row_index, "Loading...", "", "")
        self.__ansys_run_load_schema(row_index)

        self.save_table_and_show_current_state(row_index, "Solving...", "", "")
        self.__ansys_solve(row_index)

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

    def __ansys_add_cells_to_model(self, cells_params, row_index):
        volume_id = ansys_parser.get_max_element_id_from_command(self.ansys_manager, "VOLU")

        drawer = PerfectCellsDrawer(cells_params, self.ansys_manager)
        drawer.draw_cells_volumes()

        # Subtract volumes of cells from main model
        self.save_table_and_show_current_state(row_index, "Cutting...", "", "")
        subtract_output = self.ansys_manager.run(f"VSBV,{volume_id},ALL,,,")

        if constants.DEBUG: self.save_row_by_index(row_index)  # Save before checking errors

        # Do not waste time on solving if experiment is broken
        self.check_for_modeling_errors(subtract_output)

    def __ansys_generate_mesh(self, row_index=0, first_try=True):
        # ADD PARAMETERS
        self.ansys_manager.run("/PREP7")
        self.ansys_manager.run("DENSITY   = 7.85e-6")
        self.ansys_manager.run("YOUNG     = 210000.0")
        self.ansys_manager.run("MP,EX,1,YOUNG")
        self.ansys_manager.run("MP,NUXY,1,0.3")
        self.ansys_manager.run("MP,DENS,1,DENSITY")
        self.ansys_manager.run("et,1,solid186")

        # GENERATE MESH
        if constants.SMART_SIZING:  # if 'smart meshing' is ON, create mesh with suitable quality [1-10] [good-bad]
            self.ansys_manager.run(f"SMRT,{constants.MESH_QUALITY}")
        else:  # if smart meshing is turns off in UI, while experiment restarting with opened ansys
            self.ansys_manager.run("SMRT,OFF")
        self.ansys_manager.run("MSHKEY,0")
        self.ansys_manager.run("MSHAPE,1,3d")

        self.ansys_manager.run("VMESH,all")
        # TOOD(?): make remeshing if error, it takes +-20 min to mesh at SmartSize=2?
        # # try to mesh and retry if fails
        # try:
        #     self.ansys_manager.run("VMESH,all")
        # except Exception as e:
        #     print(e)
        #     if "turn on SmartSizing" in e.args[0] and first_try:
        #         constants.SMART_SIZING = True
        #         self.__ansys_generate_mesh(row_index, first_try=False)
        #         constants.SMART_SIZING = False
        #     else:
        #         raise ValueError("Meshing failure in volume")

        # self.ansys_manager.run("ASEL,ALL")  # TODO: need this?

        if constants.DEBUG: self.save_row_by_index(row_index)  # Save mesh

    def __ansys_run_load_schema(self, row_index=0):
        load_schema_commands = self.read_load_schema().split("\n")
        for command in load_schema_commands:
            if command and not command.isspace() and command[0] != "!":
                self.ansys_manager.run(command)

        if constants.DEBUG: self.save_row_by_index(row_index)  # Save before checking errors

        # Do not waste time on solving if experiment is broken
        self.check_for_loading_errors()

    def __ansys_solve(self, row_index=0):
        # run solve command and calculate all experiment data
        self.ansys_manager.run("FINISH")
        self.ansys_manager.run("/SOL")
        self.ansys_manager.run("SOLVE")

        if constants.DEBUG: self.save_row_by_index(row_index)

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

    def is_research_done(self, status):
        # return status in ("Finished", "Parent 1", "Parent 2")
        return "Finished" in status or "Parent" in status or "Elite" in status

    def is_research_finished(self, status):
        return status == "Finished"

    def read_load_schema(self):
        with open(self.app.input_load_schema_file.text()) as file:
            return file.read()

    def show_result(self, index):
        self._show_info_with_new_py_win(index, "plot_result.py")

    def show_stress_chart(self, index):
        self._show_info_with_new_py_win(index, "plot_stress_chart.py")

    def _show_info_with_new_py_win(self, index, script_name):
        status = self.app.result_table.item(index, TableHeaders.STATUS).text()
        if self.is_research_done(status):
            path_to_script = os.getcwd() + os.sep + "src" + os.sep + "util" + os.sep + script_name
            path_to_rst = self.root_folder + os.sep + f"{index + 1}.rst"
            os.system("py " + path_to_script + " " + path_to_rst)  # TODO(mb): On other devices 'py3', 'python', etc; remake
        else:
            return "This research failed or unfinished."

    def show_cluster_analyse(self):
        os.system("py src\\clusterization\\plot_cluster_analyse.py \"" + self.root_folder + "\"")
