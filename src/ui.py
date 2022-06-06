import sys
import os

from PyQt5.QtWidgets import QTableWidgetItem, QMessageBox, QDesktopWidget
from PyQt5 import QtGui, QtWidgets
import pyqtgraph as pg

from src.Calculation import Calculation
from src.PopulationData import PopulationData
from src.helper_classes.TableHeaders import TableHeaders
from forms import design, parameters  # Это наши конвертированные файлы дизайна
import src.constants as constants


# TODO: disable editing main table if gen_count is more than 0
# TODO(доп.): чстить папку temp_files (она забивается названиями старых экспр.) или во время эспр. удалять свои файлы

class MainApp(QtWidgets.QMainWindow, design.Ui_MainWindow):

    def __init__(self):
        # Это здесь нужно для доступа к переменным, методам и т.д. в файле design.py
        super().__init__()
        os.chdir(os.getcwd() + os.sep + "forms")  # GOTO /forms to get icons
        self.setupUi(self)  # Это нужно для инициализации нашего дизайна
        os.chdir(os.getcwd() + os.sep + "..")  # Go back to main folder

        self.calculation = Calculation(self)  # Объект калькулятора всех экспериментов
        self.population_data = self.calculation.pop_data = PopulationData()  # Объект со всеми данными о популяции

        self.set_window_position()  # Выставить окно в центре сверху
        self.connect_all_buttons()  # Кнопки, тригеры, связки процессов с интерфейсом и т.д.
        self.set_up_plot_and_table()

        if constants.DEBUG:
            self.add_debug_values()

    def connect_all_buttons(self):
        self.button_detail_file.clicked.connect(self.pick_model_file)
        self.button_load_schema_file.clicked.connect(self.pick_schema_load_file)
        self.button_create_researches.clicked.connect(self.fill_researches_list)
        self.button_import_researches.clicked.connect(self.load_research)
        self.button_export.clicked.connect(self.save_research)
        self.button_play.clicked.connect(self.button_play_pressed)
        self.button_next.clicked.connect(self.button_next_pressed)
        self.button_stop.clicked.connect(self.stop_current_research)
        self.button_result.clicked.connect(self.show_result)
        self.button_stress.clicked.connect(self.show_stress_chart)
        self.button_clusterization.clicked.connect(self.analyze_researches)

        self.action_Parameters.triggered.connect(self.open_parameters_window)
        self.cb_generation.currentIndexChanged.connect(self.load_table, self.cb_generation.currentIndex())

    def add_debug_values(self):
        self.input_detail_file.setText(constants.DETAIL_FN)
        self.input_load_schema_file.setText(constants.SCHEMA_FN)
        self.fill_researches_list()

    def open_parameters_window(self):
        if constants.DEBUG:
            Parameters(self).exec_()
            return
        if self.check_research_in_progress(): return
        if self.calculation.zero_stress is None:
            Parameters(self).exec_()  # Объект PyQt5 - Окно для регулировки параметров приложения.exec_()

            # # Instantly remake main table with a new parameters (do it manually in DEBUG mode)
            # if self.result_table.rowCount() > 0 or not constants.DEBUG:
            #     self.create_first_table()
        else:
            self.show_warning("Change parameters access is given only before experiment started.")

    def set_window_position(self):
        ag = QDesktopWidget().availableGeometry()
        widget = self.geometry()
        # x = ag.width() // 2 - widget.width() // 2  # Center
        x = 0  # Left
        self.move(x, 0)  # move window to TOP

    def set_up_plot_and_table(self):
        # PLOT widget customization
        # Add Background colour to system color
        app_color = self.palette().color(QtGui.QPalette.Window)  # Get the default window background
        self.graph_widget.setBackground(app_color)
        # Add Title
        self.graph_widget.setTitle("Population fitness", color="b", size="22px")
        # Add Axis Labels
        styles = {"color": "b", "font-size": "20px"}
        self.graph_widget.setLabel("left", "Fitness", **styles)
        self.graph_widget.setLabel("bottom", "Generation", **styles)
        # Add legend
        self.graph_widget.addLegend()
        # Add grid
        self.graph_widget.showGrid(x=True, y=True)
        # Add custom pen
        pen = pg.mkPen("b", width=2)
        self.data_line = self.graph_widget.plot(pen=pen, symbol='o', symbolSize=8, symbolBrush='b')

        # TABLE widget customization
        self.result_table.resizeColumnsToContents()

    def add_data_on_plot(self, data):
        self.data_line.setData(data)

    def closeEvent(self, event: QtGui.QCloseEvent):
        if self.calculation is not None:
            self.stop_calculation()
            # self.calculation.clear_and_exit()
        # print("Event: " + str(event))

    def load_research(self):
        if self.check_research_in_progress(): return
        if not self.can_start_from_scratch(): return

        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Open file', r'saves', '(*.json)')
        if file_name:
            self.clear_experiment()

            self.calculation.load_data_from_json(file_name)
            self.population_data.change_result_table_by_generation(self.result_table,
                                                                   self.population_data.generation_counter)

            # Update generation ComboBox counter
            [self.increment_cb_generation() for _ in range(len(self.population_data.table_data) - 1)]

            # Update plot data
            self.add_data_on_plot(self.population_data.max_fitness_for_all_time)

            # Update model and schema
            self.input_detail_file.setText(constants.DETAIL_FN)
            self.input_load_schema_file.setText(constants.SCHEMA_FN)

    def save_research(self, auto_save=False):
        if auto_save:
            file_name = "saves" + os.sep + "last_research.json"
        else:
            # if self.check_research_in_progress(): return
            file_name, _ = QtWidgets.QFileDialog.getSaveFileName(self, 'Save file', r'saves', '(*.json)')

        if file_name:
            self.calculation.save_data_as_json(file_name)

    def check_research_in_progress(self):
        if self.calculation.is_research_running():
            self.show_warning("Research is already in progress.")
            return True
        return False

    def check_table_is_empty(self):
        if self.result_table.rowCount() == 0:
            self.show_warning("Research table is empty.")
            return True
        return False

    def increment_cb_generation(self):
        self.cb_generation.addItem("Поколение: " + str(self.cb_generation.count()))
        if self.cb_generation.currentIndex() == self.cb_generation.count() - 2:
            self.cb_generation.setCurrentIndex(self.cb_generation.count() - 1)  # Move user to next generation (table)

    def load_table(self, index):
        self.clear_result_table()
        self.population_data.change_result_table_by_generation(self.result_table, index)

    def analyze_researches(self):
        rows = self.result_table.rowCount()
        processed_researches = 0
        for i in range(rows):
            status = self.result_table.item(i, TableHeaders.STATUS).text()
            if self.calculation.is_research_done(status):
                processed_researches += 1

        proceed = False
        if processed_researches == 0:
            self.show_warning("Не проведено ни одного эксперимента.")  # No experiment has been researched.
        elif processed_researches < rows:
            proceed = self.ask_info_text("Незавершенные эксперименты", "Не все эксперименты проведены.\n\nПродолжить?")

        if processed_researches == rows or proceed:
            self.calculation.show_cluster_analyse()

    def can_start_from_scratch(self):
        ask = False
        if self.calculation.zero_stress:  # Already launched program
            if self.are_you_sure_msg():  # continue if "yes" pressed
                self.clear_experiment()  # clear old experiment
                ask = True  # Make an action in a new experiment
        else:  # Not launched program
            ask = True  # Make an action and don't afraid of anything

        return ask

    def are_you_sure_msg(self):
        return self.ask_info_text("Reset all data", "This will reset ALL the experiments.\n\nAre you sure?")

    def pick_model_file(self):
        if self.check_research_in_progress(): return
        if not self.can_start_from_scratch(): return

        # открыть диалог выбора файла в текущей папке
        # directory, filter = r'D:\DIPLOMA\mechanical WDIR\igs', '3D model.ACIS files (*.sab *.sat)'
        directory, extension = r'models\\', '3D model.IGES files (*.igs *.iges)'
        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Open file', directory, extension)

        if file_name:  # не продолжать выполнение, если пользователь не выбрал файл
            self.input_detail_file.setText(file_name)
            constants.DETAIL_FN = file_name

            # TODO: мб делать это не в импорте?))  или обозначить как нибудь загрузку
            self.calculation.set_model_dimensions()  # Узнать размеры детали
            # self.create_first_table()  # recreate table with new data

    def pick_schema_load_file(self):
        if self.check_research_in_progress(): return
        if not self.can_start_from_scratch(): return

        # открыть диалог выбора файла в текущей папке
        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Open file', r'load_schemas',
                                                             'text files(*.txt)')
        if file_name:  # не продолжать выполнение, если пользователь не выбрал файл
            self.input_load_schema_file.setText(file_name)
            constants.SCHEMA_FN = file_name

    def button_play_pressed(self):
        if self.check_table_is_empty(): return
        else:  # No errors
            # self.population_data.save_first_state_of_table(self.result_table)  # TODO: you can edit table, make some err
            self.button_play.setStyleSheet("background-color: lime")
            self.calculation.research_UI()

    def button_next_pressed(self):
        # Check for errors
        if self.check_research_in_progress(): return
        elif self.check_table_is_empty(): return
        else:  # No errors
            # self.population_data.save_first_state_of_table(self.result_table)  # TODO: you can edit table, make some err
            self.button_next.setStyleSheet("background-color: lime")
            self.calculation.next_generation_research_UI()

    def stop_current_research(self):
        self.stop_calculation()

    def toggle_buttons_on_research(self, state):
        if not state:
            self.button_stop.setStyleSheet("background-color: red")
        else:
            self.button_play.setStyleSheet("")
            self.button_next.setStyleSheet("")
            self.button_stop.setStyleSheet("")

        self.button_play.setEnabled(state)
        self.button_next.setEnabled(state)
        self.button_stop.setEnabled(not state)

    def show_warning(self, err_text):
        qm = QMessageBox()  # TODO: make a sepearte file\class for showing errors (in calc.py can't show them)
        qm.warning(self, 'Warning', err_text, qm.Ok, qm.Ok)

    def ask_info_text(self, title, text):
        qm = QMessageBox()
        reply = qm.information(self, title, text, qm.Yes | qm.No, qm.No)
        return reply == qm.Yes

    def is_current_generation_the_last_one(self):
        return self.cb_generation.currentIndex() == self.cb_generation.count() - 1

    def change_current_stress_label(self, text):
        self.label_current_stress.setText("Нагрузка текущая: " + text)

    def change_zero_stress_label(self, text):
        self.label_zero_stress.setText("Нагрузка нулевая: " + text)

    def change_table_item(self, row, column, text):
        self.result_table.setItem(row, column, QTableWidgetItem(text))

    def fill_researches_list(self):
        if self.check_research_in_progress(): return
        if not self.input_detail_file.text(): return self.show_warning("3D Model file is not selected.")
        if not self.input_load_schema_file.text(): return self.show_warning("Load schema is not selected.")
        if not self.can_start_from_scratch(): return

        self.create_first_table()

    def create_first_table(self):
        population = self.population_data.create_first_population()

        self.add_population_in_result_table(population)

        self.population_data.save_first_state_of_table(self.result_table)

    def stop_calculation(self):
        self.calculation.stopping_calculation = True
        self.button_stop.setStyleSheet("background-color: maroon")

    def clear_experiment(self):
        # Clear calc
        self.calculation.clear()

        # Clear pop_data
        self.population_data.clear()

        # Clear UI
        self.change_current_stress_label("")
        self.change_zero_stress_label("")
        self.cb_generation.clear()  # bug (sometimes) with vertical scroll bar appears (update/repaint - does't work)
        self.increment_cb_generation()
        self.data_line.clear()

    def add_population_in_result_table(self, population):
        self.result_table.setRowCount(constants.POPULATION_SIZE)

        for i, agent in enumerate(population):
            self.result_table.setItem(i, TableHeaders.ANGLE_NUM, QTableWidgetItem(str(agent.angles)))
            self.result_table.setItem(i, TableHeaders.ROTATE_ANGLE, QTableWidgetItem(str(agent.rotation)))
            self.result_table.setItem(i, TableHeaders.VOLUME_PART, QTableWidgetItem(str(agent.size)))
            self.result_table.setItem(i, TableHeaders.CELLS_OX, QTableWidgetItem(str(agent.x_amount)))
            self.result_table.setItem(i, TableHeaders.CELLS_OY, QTableWidgetItem(str(agent.y_amount)))
    
            self.result_table.setItem(i, TableHeaders.DETAIL_X0, QTableWidgetItem(str(agent.working_zone[0][0])))
            self.result_table.setItem(i, TableHeaders.DETAIL_X1, QTableWidgetItem(str(agent.working_zone[0][1])))
            self.result_table.setItem(i, TableHeaders.DETAIL_Y0, QTableWidgetItem(str(agent.working_zone[1][0])))
            self.result_table.setItem(i, TableHeaders.DETAIL_Y1, QTableWidgetItem(str(agent.working_zone[1][1])))
            self.result_table.setItem(i, TableHeaders.DETAIL_Z0, QTableWidgetItem(str(agent.working_zone[2][0])))
            self.result_table.setItem(i, TableHeaders.DETAIL_Z1, QTableWidgetItem(str(agent.working_zone[2][1])))
    
            self.result_table.setItem(i, TableHeaders.STATUS, QTableWidgetItem(str()))
            self.result_table.setItem(i, TableHeaders.STRESS, QTableWidgetItem(str()))
            self.result_table.setItem(i, TableHeaders.FITNESS, QTableWidgetItem(str()))

        self.result_table.resizeColumnsToContents()

    def clear_result_table(self):
        for row in range(self.result_table.rowCount()):
            for column in range(self.result_table.columnCount()):
                self.result_table.setItem(row, column, QTableWidgetItem(str()))

    def show_result(self):
        # Temporary files exist
        if not constants.SAVE_TEMP_FILES:
            return self.show_warning("Temporary files are not saved.")

        # Row is picked
        if self.result_table.currentRow() == -1:
            return self.show_warning("No experiment selected.")

        # No experiment is done  # TODO(!): пересмотреть это, ибо теперь не так работает
        # if self.calculation.result_table is None:  # cause result table is connecting only in 'set_up_research' method
        #     return self.show_error("No experiment has been researched.")

        error_text = self.calculation.show_result(self.result_table.currentRow())
        if error_text:
            self.show_warning(error_text)

    def show_stress_chart(self):
        if self.result_table.currentRow() != -1:
            self.calculation.show_stress_chart(self.result_table.currentRow())
        else:
            self.show_warning("No experiment selected.")


class Parameters(QtWidgets.QDialog, parameters.Ui_Dialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)  # Это нужно для инициализации нашего дизайна
        self.init_parameters()  # Init const values

        self.btn_save.clicked.connect(self.save_and_exit)  # Save const values

    def init_parameters(self):
        """ Load ui parameters from constants file """
        # Хотел сделать красиво(одной функцией считывать и менять константы), но намудрил, упроситить или допилить
        self.ui_elements_to_set = (
            # == PARAMS ==
            self.sb_pop_size, constants.POPULATION_SIZE, self.sb_mut_chanse, constants.MUT_CHANSE,
            self.sb_mut_size, constants.MUT_SIZE, self.sb_max_stress, constants.MAX_STRESS,
            self.sb_every_exel, constants.SAVE_TO_CSV_EVERY_N, self.sb_time_limit, constants.TIME_LIMIT,
            self.sb_gen_limit, constants.GENERATION_LIMIT, self.sb_elite_amount, constants.ELITE_AMOUNT,
            # == GA ==
            self.sb_an_min, constants.AN_MIN, self.sb_an_max, constants.AN_MAX, self.sb_rt_min, constants.RT_MIN,
            self.sb_rt_max, constants.RT_MAX, self.sb_sz_min, constants.SZ_MIN, self.sb_sz_max, constants.SZ_MAX,
            self.sb_xa_min, constants.XA_MIN, self.sb_xa_max, constants.XA_MAX, self.sb_ya_min, constants.YA_MIN,
            self.sb_ya_max, constants.YA_MAX)
        self.ui_elements_to_check = (
            # == PARAMS ==
            self.cb_save_parents, constants.SAVE_PARENTS, self.cb_save_temp, constants.SAVE_TEMP_FILES,
            self.cb_save_to_exel, constants.BACKUP_TO_CSV, self.cb_restart_ansys, constants.RESTART_AFTER_ERROR,
            self.cb_oy_symm, constants.SYMMETRY_OY, self.cb_elite, constants.ELITE_STRATEGY,
            self.cb_save_elite, constants.SAVE_ELITE, self.cb_cells_depth, constants.CELLS_DEPTH,
            # == FITNESS (GroupBoxes) ==
            self.gb_volume, bool(constants.FIT_VOLUME), self.gb_size, bool(constants.FIT_SIZE),
            self.gb_amount, bool(constants.FIT_AMOUNT), self.gb_mass, bool(constants.FIT_MASS),
            self.gb_stress, bool(constants.FIT_STRESS),
            # == FITNESS (RadioButtons) ==
            self.rb_vol_max, constants.FIT_VOLUME == 1, self.rb_size_max, constants.FIT_SIZE == 1,
            self.rb_amount_max, constants.FIT_AMOUNT == 1, self.rb_mass_max, constants.FIT_MASS == 1,
            self.rb_stress_max, constants.FIT_STRESS == 1)

        self.init_ui_by_func(self.ui_elements_to_set, "setValue")
        self.init_ui_by_func(self.ui_elements_to_check, "setChecked")

    def save_to_constants(self):
        # -- Params --
        constants.POPULATION_SIZE = int(self.sb_pop_size.value())
        constants.MUT_CHANSE = int(self.sb_mut_chanse.value())
        constants.MUT_SIZE = int(self.sb_mut_size.value())
        constants.MAX_STRESS = int(self.sb_max_stress.value())
        constants.SAVE_TO_CSV_EVERY_N = int(self.sb_every_exel.value())
        constants.TIME_LIMIT = int(self.sb_time_limit.value())
        constants.GENERATION_LIMIT = int(self.sb_gen_limit.value())
        constants.ELITE_AMOUNT = int(self.sb_elite_amount.value())
        constants.SAVE_PARENTS = self.cb_save_parents.checkState()
        constants.SAVE_TEMP_FILES = self.cb_save_temp.checkState()
        constants.BACKUP_TO_CSV = self.cb_save_to_exel.checkState()
        constants.RESTART_AFTER_ERROR = self.cb_restart_ansys.checkState()
        constants.SYMMETRY_OY = self.cb_oy_symm.checkState()
        constants.ELITE_STRATEGY = self.cb_elite.checkState()
        constants.SAVE_ELITE = self.cb_save_elite.checkState()
        constants.CELLS_DEPTH = self.cb_cells_depth.checkState()
        # -- Ga --
        constants.AN_MIN, constants.AN_MAX = int(self.sb_an_min.value()), int(self.sb_an_max.value())
        constants.RT_MIN, constants.RT_MAX = int(self.sb_rt_min.value()), int(self.sb_rt_max.value())
        constants.SZ_MIN, constants.SZ_MAX = int(self.sb_sz_min.value()), int(self.sb_sz_max.value())
        constants.XA_MIN, constants.XA_MAX = int(self.sb_xa_min.value()), int(self.sb_xa_max.value())
        constants.YA_MIN, constants.YA_MAX = int(self.sb_ya_min.value()), int(self.sb_ya_max.value())
        # -- Fitness --
        # If set - change min\max value. if not - turn off
        constants.FIT_VOLUME = 0 if not self.gb_volume.isChecked() else 1 if self.rb_vol_max.isChecked() else -1
        constants.FIT_SIZE = 0 if not self.gb_size.isChecked() else 1 if self.rb_size_max.isChecked() else -1
        constants.FIT_AMOUNT = 0 if not self.gb_amount.isChecked() else 1 if self.rb_amount_max.isChecked() else -1
        constants.FIT_MASS = 0 if not self.gb_mass.isChecked() else 1 if self.rb_mass_max.isChecked() else -1
        constants.FIT_STRESS = 0 if not self.gb_stress.isChecked() else 1 if self.rb_stress_max.isChecked() else -1
        constants.FIT_STRESS = 0 if not self.gb_stress.isChecked() else 1 if self.rb_stress_max.isChecked() else -1

    def init_ui_by_func(self, elements, function_str):
        for element, const in zip(elements[::2], elements[1::2]):
            el_func = getattr(element, function_str)
            el_func(const)

    def change_const_from_ui(self, elements, function_str):
        # didn't work :(
        for element, const in zip(elements[::2], elements[1::2]):
            el_func = getattr(element, function_str)
            const = int(el_func())

    def save_and_exit(self):
        valid_text = self.validation()
        if valid_text == "OK":
            self.save_to_constants()
            self.close()
        else:
            # show error
            qm = QMessageBox()
            qm.warning(self, 'Внимание!', valid_text, qm.Ok, qm.Ok)

    def validation(self):
        err_msg = "OK"
        min_ui_elements = (self.sb_an_min, self.sb_rt_min, self.sb_sz_min, self.sb_xa_min, self.sb_ya_min)
        max_ui_elements = (self.sb_an_max, self.sb_rt_max, self.sb_sz_max, self.sb_xa_max, self.sb_ya_max)
        min_value_int = [int(el.value()) for el in min_ui_elements]
        max_value_int = [int(el.value()) for el in max_ui_elements]

        for start, end in zip(min_value_int, max_value_int):
            if start > end:
                err_msg = "Начальная позиция не может быть больше конечной."
        if int(self.sb_elite_amount.value()) >= int(self.sb_pop_size.value()):
            err_msg = "Количество элитарных особей должно быть меньше, чем общее количество особей."
        return err_msg


def start_main_app():
    app = QtWidgets.QApplication(sys.argv)  # Новый экземпляр QApplication
    window = MainApp()  # Создаём объект класса ExampleApp
    window.show()  # Показываем окно
    app.exec_()  # и запускаем приложение
