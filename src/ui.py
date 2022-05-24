# import _thread as thread
import sys

from PyQt5.QtWidgets import QTableWidgetItem, QMessageBox, QDesktopWidget
from PyQt5 import QtGui, QtWidgets, QtCore
import pyqtgraph as pg

from src.helper_classes.BodyParams import BodyParameters
from src.Calculation import Calculation
from src.PopulationData import PopulationData
from src.helper_classes.TableHeaders import TableHeaders
from src.util import table_utils
from forms import design, parameters  # Это наши конвертированные файлы дизайна
import src.constants as constants


class MainApp(QtWidgets.QMainWindow, design.Ui_MainWindow):
    is_running = False
    stop_calculation = False

    def __init__(self):
        # Это здесь нужно для доступа к переменным, методам и т.д. в файле design.py
        super().__init__()
        self.setupUi(self)  # Это нужно для инициализации нашего дизайна

        self.calculation = Calculation(self)  # Объект калькулятора всех экспериментов
        self.population_data = self.calculation.pop_data = PopulationData(self.result_table)  # Объект со всеми данными

        self.set_window_position()  # Выставить окно в центре сверху
        self.connect_all_buttons()  # Кнопки, тригеры, связки процессов с интерфейсом и т.д.
        self.set_up_plot_and_table()

        if constants.DEBUG:
            self.add_debug_values()

    def connect_all_buttons(self):
        self.button_detail_file.clicked.connect(self.pick_model_file)
        self.button_load_schema_file.clicked.connect(self.pick_schema_load_file)
        self.button_create_researches.clicked.connect(self.fill_researches_list)
        self.button_play_pause.clicked.connect(self.button_play_pause_pressed)
        self.button_next.clicked.connect(self.button_next_pressed)
        self.button_stop.clicked.connect(self.stop_current_research)
        self.button_result.clicked.connect(self.show_result)
        self.button_stress.clicked.connect(self.show_stress_chart)
        self.button_export.clicked.connect(self.save_csv)
        self.button_clusterization.clicked.connect(self.analyze_researches)
        self.button_import_researches.clicked.connect(self.load_csv)

        self.action_Parameters.triggered.connect(self.open_parameters_window)
        self.cb_generation.currentIndexChanged.connect(self.change_cb, self.cb_generation.currentIndex())

    def add_debug_values(self):
        self.input_detail_file.setText(constants.DETAIL_FN)
        self.input_load_schema_file.setText(constants.SCHEMA_FN)
        self.fill_researches_list()

    def open_parameters_window(self):
        params = Parameters(self)
        params.exec_()

    def set_window_position(self):
        ag = QDesktopWidget().availableGeometry()
        widget = self.geometry()
        x = ag.width() // 2 - widget.width() // 2
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
            self.stop_and_clear_calculation()
            # self.calculation.clear_and_exit()
        # print("Event: " + str(event))
        exit()

    def load_csv(self):
        if self.check_research_in_progress(): return

        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Open file', r'..\..', '(*.csv)')
        if file_name:
            # thread.start_new_thread(table_utils.import_research_list_from_csv, (file_name, self.result_table))
            table_utils.import_research_list_from_csv(file_name, self.result_table)
            self.population_data.save_first_state_of_table()

    def save_csv(self, auto_save=False):
        # TODO: save\open ALL generations data and ALL settings
        if auto_save:
            file_name = "last_research.csv"
        else:
            if self.check_research_in_progress(): return
            file_name, _ = QtWidgets.QFileDialog.getSaveFileName(self, 'Save file', r'..\..', '(*.csv)')

        if file_name:
            # TODO: BUG: crashes after save and count next gen
            table_utils.save_csv_to_file(file_name, self.result_table)

    def are_you_sure_msg(self):
        qm = QMessageBox()
        reply = qm.information(self, "Reset all data", "This will reset ALL the experiments. Are you sure?",
                               qm.Yes | qm.No, qm.No)

        return reply == qm.Yes

    def check_research_in_progress(self):
        if self.calculation.is_research_running():
            self.show_error("Research is already in progress.")
            return True
        return False

    def check_table_is_empty(self):
        if self.calculation.is_result_table_empty():
            self.show_error("Research table is empty.")
            return True
        return False

    def increment_cb_generation(self):
        self.cb_generation.addItem("Поколение: " + str(self.cb_generation.count()))
        if self.cb_generation.currentIndex() == self.cb_generation.count() - 2:
            self.cb_generation.setCurrentIndex(self.cb_generation.count() - 1)  # Move user to next generation (table)

    def change_cb(self, index):
        self.load_table(index)

    def load_table(self, index):
        self.clear_result_table()
        self.population_data.change_result_table_by_generation(index)

    def analyze_researches(self):
        rows = self.result_table.rowCount()
        processed_researches = 0
        for i in range(rows):
            status = self.result_table.item(i, TableHeaders.STATUS).text()
            if self.calculation.is_research_done(status):
                processed_researches += 1

        proceed = False
        if processed_researches == 0:
            self.show_error("No experiment has been researched.")
        elif processed_researches < rows:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)

            msg.setText("Не все эксперименты проведены.")
            msg.setInformativeText("Продолжить?")
            msg.setWindowTitle("Warning")
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)

            retval = msg.exec_()
            proceed = retval == QMessageBox.Yes

        if hasattr(self, 'calculation') and (processed_researches == rows or proceed):
            self.calculation.show_cluster_analyse()

        pass

    def __get_body_params_ga(self, agent):
        return BodyParameters(
            int(agent.working_zone[0][0]), int(agent.working_zone[0][1]),
            int(agent.working_zone[1][0]), int(agent.working_zone[1][1]),
            int(0), int(constants.Z_MAX))  # for now Z values is always FULL

    def pick_model_file(self):
        if self.check_research_in_progress(): return

        # открыть диалог выбора файла в текущей папке
        # directory, filter = r'D:\DIPLOMA\mechanical WDIR\igs', '3D model.ACIS files (*.sab *.sat)'
        directory, extension = r'models\\', '3D model.IGES files (*.igs *.iges)'
        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Open file', directory, extension)

        if file_name:  # не продолжать выполнение, если пользователь не выбрал файл
            self.input_detail_file.setText(file_name)

            # TODO: мб делать это не в импорте?))
            # TODO: показывать пользователю, что прога что то грузит и делает (или делать не в потоке а фризить прогу)
            self.calculation.calc_model_dimensions_UI()  # Узнать размеры детали

    def pick_schema_load_file(self):
        if self.check_research_in_progress(): return

        # открыть диалог выбора файла в текущей папке
        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Open file', r'load_schemas',
                                                             'text files(*.txt)')

        if file_name:  # не продолжать выполнение, если пользователь не выбрал файл
            self.input_load_schema_file.setText(file_name)

    def button_play_pause_pressed(self):
        if self.check_table_is_empty(): return
        else:  # No errors
            self.calculation.research_UI()

    def button_next_pressed(self):
        # Check for errors
        if self.check_research_in_progress(): return
        elif self.check_table_is_empty(): return
        else:  # No errors
            if self.population_data.generation_counter == 0:  # Ability to start from user defined params TODO(?): need?
                self.population_data.save_first_state_of_table()
            self.calculation.next_generation_research_UI()

    def stop_current_research(self):
        # TODO(BIG!): (mb) breaks after stop if it was the Last one
        self.stop_and_clear_calculation()

    def show_error(self, err_text):
        qm = QMessageBox()  # TODO: make a sepearte file\class for showing errors (in calc.py can't show them)
        qm.warning(self, 'Warning', err_text, qm.Ok, qm.Ok)

    def is_current_generation_the_last_one(self):
        return self.cb_generation.currentIndex() == self.cb_generation.count() - 1

    def change_current_stress_label(self, text):
        self.label_current_stress.setText("Нагрузка текущая: " + text)

    def change_zero_stress_label(self, text):
        self.label_zero_stress.setText("Нагрузка нулевая: " + text)

    def change_table_item(self, row, column, text):
        self.result_table.setItem(row, column, QTableWidgetItem(text))

    def change_body_size_parameters(self, dimensions):
        constants.X_MAX, constants.Y_MAX, constants.Z_MAX = dimensions
        print("done!", dimensions)

    def fill_researches_list(self):
        if self.check_research_in_progress(): return
        if not self.input_load_schema_file.text(): return self.show_error("Load schema is not selected.")
        if not self.input_detail_file.text(): return self.show_error("3D Model file is not selected.")

        # Not the first generation
        if self.population_data.generation_counter != 0:
            if self.are_you_sure_msg():
                self.clear_ui()  # clear old data
            else:
                return  # Exit if pressed 'No'

        population = self.population_data.create_first_population()  # TODO(?): агенты только для мутации и скрещивания их хранить не нужно, так?

        for i in range(constants.POPULATION_SIZE):
            self.count_body_params_and_add_in_table(population[i], i)

        self.population_data.save_first_state_of_table()

    def stop_and_clear_calculation(self):
        self.stop_calculation = True

    def clear_ui(self):
        self.stop_and_clear_calculation()

        # Wait until all is done
        while self.calculation.threadpool.activeThreadCount() != 0:
            QtCore.QThread.msleep(250)

        # Clear calc
        self.calculation.max_fitness_for_all_time.clear()

        # Clear pop_data
        self.population_data.clear()

        # Clear UI
        self.change_current_stress_label("")
        self.change_zero_stress_label("")
        self.cb_generation.clear()  # T0D0(mb): bug with vertical scroll bar appears (update/repaint - does't work)
        self.increment_cb_generation()
        self.data_line.clear()

    def count_body_params_and_add_in_table(self, agent, i):
        body_params = self.__get_body_params_ga(agent)

        self.result_table.setRowCount(i + 1)
        self.__add_ga_param_in_result_table(agent, body_params, i)

    def clear_result_table(self):
        for row in range(self.result_table.rowCount()):
            for column in range(self.result_table.columnCount()):
                self.result_table.setItem(row, column, QTableWidgetItem(str()))

    def toggle_buttons_on_research(self, state):
        self.button_play_pause.setEnabled(state)

        self.button_stop.setEnabled(not state)

    def __add_ga_param_in_result_table(self, agent, bp, index):
        self.result_table.setItem(index, TableHeaders.ANGLE_NUM, QTableWidgetItem(str(agent.angles)))
        self.result_table.setItem(index, TableHeaders.ROTATE_ANGLE, QTableWidgetItem(str(agent.rotation)))
        self.result_table.setItem(index, TableHeaders.VOLUME_PART, QTableWidgetItem(str(agent.size)))
        self.result_table.setItem(index, TableHeaders.CELLS_OX, QTableWidgetItem(str(agent.x_amount)))
        self.result_table.setItem(index, TableHeaders.CELLS_OY, QTableWidgetItem(str(agent.y_amount)))

        self.result_table.setItem(index, TableHeaders.DETAIL_X0, QTableWidgetItem(str(bp.x0)))
        self.result_table.setItem(index, TableHeaders.DETAIL_X1, QTableWidgetItem(str(bp.x1)))
        self.result_table.setItem(index, TableHeaders.DETAIL_Y0, QTableWidgetItem(str(bp.y0)))
        self.result_table.setItem(index, TableHeaders.DETAIL_Y1, QTableWidgetItem(str(bp.y1)))
        self.result_table.setItem(index, TableHeaders.DETAIL_Z0, QTableWidgetItem(str(bp.z0)))
        self.result_table.setItem(index, TableHeaders.DETAIL_Z1, QTableWidgetItem(str(bp.z1)))

        self.result_table.setItem(index, TableHeaders.STATUS, QTableWidgetItem(str()))
        self.result_table.setItem(index, TableHeaders.STRESS, QTableWidgetItem(str()))
        self.result_table.setItem(index, TableHeaders.FITNESS, QTableWidgetItem(str()))

        self.result_table.resizeColumnsToContents()

    def add_parents_data(self, stress, fitness):
        for i in range(2):
            self.result_table.setItem(i, TableHeaders.STATUS, QTableWidgetItem(f"Parent {i + 1}"))
            self.result_table.setItem(i, TableHeaders.STRESS, QTableWidgetItem(str(round(stress[i], 4))))
            self.result_table.setItem(i, TableHeaders.FITNESS, QTableWidgetItem(str(round(fitness[i], 4))))

    def show_result(self):
        # Temporary files exist
        if not constants.SAVE_TEMP_FILES:
            return self.show_error("Temporary files are not saved.")

        # Row is picked
        if self.result_table.currentRow() == -1:
            return self.show_error("No experiment selected.")

        # No experiment is done  # TODO(!): пересмотреть это, ибо теперь не так работает
        # if self.calculation.result_table is None:  # cause result table is connecting only in 'set_up_research' method
        #     return self.show_error("No experiment has been researched.")

        error_text = self.calculation.show_result(self.result_table.currentRow())
        if error_text:
            self.show_error(error_text)

    def show_stress_chart(self):
        if self.result_table.currentRow() != -1:
            self.calculation.show_stress_chart(self.result_table.currentRow())
        else:
            self.show_error("No experiment selected.")


class Parameters(QtWidgets.QDialog, parameters.Ui_Dialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)  # Это нужно для инициализации нашего дизайна
        self.init_parameters()  # Init const values
        self.btn_save.clicked.connect(self.save_and_exit)  # Save const values

    def init_parameters(self):
        # -- Params --
        self.sb_pop_size.setValue(constants.POPULATION_SIZE)
        self.dsb_mut_per.setValue(constants.MUT_SIZE)
        self.sb_max_stress.setValue(constants.MAX_STRESS)
        self.sb_every_exel.setValue(constants.SAVE_TO_CSV_EVERY_N)
        self.sb_time_limit.setValue(constants.TIME_LIMIT)
        self.sb_gen_limit.setValue(constants.GENERATION_LIMIT)
        self.cb_save_parents.setChecked(constants.SAVE_PARENTS)
        self.cb_save_temp.setChecked(constants.SAVE_TEMP_FILES)
        self.cb_save_to_exel.setChecked(constants.BACKUP_TO_CSV)
        self.cb_restart_ansys.setChecked(constants.RESTART_AFTER_ERROR)
        # -- Ga --
        self.sb_an_min.setValue(constants.AN_MIN)
        self.sb_an_max.setValue(constants.AN_MAX)
        self.sb_rt_min.setValue(constants.RT_MIN)
        self.sb_rt_max.setValue(constants.RT_MAX)
        self.sb_sz_min.setValue(constants.SZ_MIN)
        self.sb_sz_max.setValue(constants.SZ_MAX)
        self.sb_xa_min.setValue(constants.XA_MIN)
        self.sb_xa_max.setValue(constants.XA_MAX)
        self.sb_ya_min.setValue(constants.YA_MIN)
        self.sb_ya_max.setValue(constants.YA_MAX)

    def save_and_exit(self):
        if self.validation():
            self.save_to_constants()
            self.close()
        else:
            # show error
            qm = QMessageBox()
            qm.warning(self, 'Внимание!', "Начальная позиция не может быть больше конечной.", qm.Ok, qm.Ok)

    def validation(self):
        min_ui_elements = (self.sb_an_min, self.sb_rt_min, self.sb_sz_min, self.sb_xa_min, self.sb_ya_min)
        max_ui_elements = (self.sb_an_max, self.sb_rt_max, self.sb_sz_max, self.sb_xa_max, self.sb_ya_max)
        min_value_int = [int(el.value()) for el in min_ui_elements]
        max_value_int = [int(el.value()) for el in max_ui_elements]

        for start, end in zip(min_value_int, max_value_int):
            if start > end:
                return False
        return True

    def save_to_constants(self):
        # -- Params --
        constants.POPULATION_SIZE = int(self.sb_pop_size.value())
        constants.MUT_SIZE = float(self.dsb_mut_per.value())
        constants.MAX_STRESS = int(self.sb_max_stress.value())
        constants.SAVE_TO_CSV_EVERY_N = int(self.sb_every_exel.value())
        constants.TIME_LIMIT = int(self.sb_time_limit.value())
        constants.GENERATION_LIMIT = int(self.sb_gen_limit.value())
        constants.SAVE_PARENTS = self.cb_save_parents.checkState()
        constants.SAVE_TEMP_FILES = self.cb_save_temp.checkState()
        constants.BACKUP_TO_CSV = self.cb_save_to_exel.checkState()
        constants.RESTART_AFTER_ERROR = self.cb_restart_ansys.checkState()
        # -- Ga --
        constants.AN_MIN, constants.AN_MAX = int(self.sb_an_min.value()), int(self.sb_an_max.value())
        constants.RT_MIN, constants.RT_MAX = int(self.sb_rt_min.value()), int(self.sb_rt_max.value())
        constants.SZ_MIN, constants.SZ_MAX = int(self.sb_sz_min.value()), int(self.sb_sz_max.value())
        constants.XA_MIN, constants.XA_MAX = int(self.sb_xa_min.value()), int(self.sb_xa_max.value())
        constants.YA_MIN, constants.YA_MAX = int(self.sb_ya_min.value()), int(self.sb_ya_max.value())


def start_main_app():
    # os.environ["PARSER_JAR"] = r"..\..\nodes_parser.jar"
    app = QtWidgets.QApplication(sys.argv)  # Новый экземпляр QApplication
    window = MainApp()  # Создаём объект класса ExampleApp
    window.show()  # Показываем окно
    app.exec_()  # и запускаем приложение
