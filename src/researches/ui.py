import _thread as thread
import sys

from PyQt5.QtWidgets import QTableWidgetItem, QMessageBox, QDesktopWidget
from PyQt5 import QtGui, QtWidgets, QtCore
import pyqtgraph as pg

from src.researches.BodyParams import BodyParameters
from src.researches.Calculation import Calculation
from src.researches.PopulationData import PopulationData
from src.researches.TableHeaders import TableHeaders
from src.researches.util import table_utils
from forms import design, parameters  # Это наш конвертированный файл дизайна
import src.researches.constants as constants


class MainApp(QtWidgets.QMainWindow, design.Ui_MainWindow):
    is_running = False
    table_changed_by_program = False
    stop_calculation = False

    def __init__(self):
        # Это здесь нужно для доступа к переменным, методам и т.д. в файле design.py
        super().__init__()
        self.setupUi(self)  # Это нужно для инициализации нашего дизайна
        self.set_window_position()  # Выставить окно в центре сверху

        self.calculation = Calculation(self)
        self.population_data = self.calculation.pop_data = PopulationData(self.result_table)

        self.connect_all_buttons()
        self.set_up_plot_and_table()

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
        self.cb_generation.currentIndexChanged.connect(self.load_table, self.cb_generation.currentIndex())

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
        # self.result_table.setRowCount(constants.POPULATION_SIZE)
        self.result_table.resizeColumnsToContents()  # TODO: resize it in 'untiled.ui'

    def add_data_on_plot(self, data):
        self.data_line.setData(data)

    def closeEvent(self, event: QtGui.QCloseEvent):
        if self.calculation is not None:
            self.stop_and_clear_calculation()
            # self.calculation.clear_and_exit()
        # print("Event: " + str(event))

    def load_csv(self):
        file_name = QtWidgets.QFileDialog.getOpenFileName(self, 'Open file', r'..\..', '(*.csv)')
        thread.start_new_thread(table_utils.import_research_list_from_csv, (file_name[0], self.result_table))

    def save_csv(self, default=None):
        if default:
            file_name = default
        else:
            # TODO: BUG: crashes after save and count next gen
            file_name, _ = QtWidgets.QFileDialog.getSaveFileName(self, 'Open file', r'..\..', '(*.csv)')

        if file_name:
            table_utils.save_csv_to_file(file_name, self.result_table)

    def are_you_sure_msg(self):
        qm = QMessageBox()
        reply = qm.information(self, "Reset all data", "This will reset ALL the experiments. Are you sure?",
                               qm.Yes | qm.No, qm.No)

        return reply == qm.Yes

    def load_table(self, index):
        if self.table_changed_by_program:
            self.table_changed_by_program = False
        else:
            self.clear_result_table()
            self.population_data.change_result_table_by_generation(index)

    def analyze_researches(self):
        rows = self.result_table.rowCount()
        processed_researches = 0
        for i in range(rows):
            if self.result_table.item(i, TableHeaders.STATUS) \
                    and self.result_table.item(i, TableHeaders.STATUS).text() == "Finished":
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
            float(agent.working_zone[0][0]), float(agent.working_zone[0][1]),
            float(agent.working_zone[1][0]), float(agent.working_zone[1][1]),
            float(0), float(250))  # for now Z values is always 250

    def pick_model_file(self):
        # открыть диалог выбора файла в текущей папке
        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Open file', '..\\..', '3D model.igs files (*.igs)')

        if file_name:  # не продолжать выполнение, если пользователь не выбрал файл
            self.input_detail_file.setText(file_name)

    def pick_schema_load_file(self):
        # открыть диалог выбора файла в текущей папке
        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Open file', '..\\..', '(*.txt)')

        if file_name:  # не продолжать выполнение, если пользователь не выбрал файл
            self.input_load_schema_file.setText(file_name)

    def button_play_pause_pressed(self):
        error_text = self.calculation.check_for_errors_basic()
        if error_text:
            self.show_error(error_text)
        else:  # No errors
            self.calculation.research_UI()

    def button_next_pressed(self):
        error_text = self.calculation.check_for_errors_next()
        if error_text:
            self.show_error(error_text)
        else:  # No errors
            self.calculation.next_generation_research_UI()

    def stop_current_research(self):
        self.stop_and_clear_calculation()

    def show_error(self, text):
        qm = QMessageBox()
        qm.warning(self, 'Warning', text, qm.Ok, qm.Ok)

    def increment_cb_generation(self):
        self.table_changed_by_program = True
        self.cb_generation.addItem("Поколение: " + str(self.cb_generation.count()))
        self.cb_generation.setCurrentIndex(self.cb_generation.count() - 1)

    def change_current_stress_label(self, text):
        self.label_current_stress.setText("Нагрузка текущая: " + text)

    def change_zero_stress_label(self, text):
        self.label_zero_stress.setText("Нагрузка нулевая: " + text)

    def change_table_item(self, row, column, text):
        self.result_table.setItem(row, column, QTableWidgetItem(text))

    def fill_researches_list(self):
        # Not the first generation
        if self.population_data.generation_counter != 0:
            if self.are_you_sure_msg():
                self.clear_ui()  # clear old data
            else:
                return None  # Exit if pressed 'No'

        self.population_data.create_first_population()

        for i in range(constants.POPULATION_SIZE):
            self.count_body_params_and_add_in_table(self.population_data.population[0][i], i)

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

    def __add_ga_param_in_result_table(self, agent, bp, index):
        self.result_table.setItem(index, TableHeaders.ANGLE_NUM, QTableWidgetItem(str(agent.angles)))
        self.result_table.setItem(index, TableHeaders.ROTATE_ANGLE, QTableWidgetItem(str(agent.rotation)))
        self.result_table.setItem(index, TableHeaders.VOLUME_PART, QTableWidgetItem(str(agent.size)))
        self.result_table.setItem(index, TableHeaders.CELLS_OX, QTableWidgetItem(str(agent.x_amount)))
        self.result_table.setItem(index, TableHeaders.CELLS_OY, QTableWidgetItem(str(agent.y_amount)))

        self.result_table.setItem(index, TableHeaders.DETAIL_X0, QTableWidgetItem(str(bp.get_x0_body())))
        self.result_table.setItem(index, TableHeaders.DETAIL_X1, QTableWidgetItem(str(bp.get_xend_body())))
        self.result_table.setItem(index, TableHeaders.DETAIL_Y0, QTableWidgetItem(str(bp.get_y0_body())))
        self.result_table.setItem(index, TableHeaders.DETAIL_Y1, QTableWidgetItem(str(bp.get_yend_body())))
        self.result_table.setItem(index, TableHeaders.DETAIL_Z0, QTableWidgetItem(str(bp.get_z0_body())))
        self.result_table.setItem(index, TableHeaders.DETAIL_Z1, QTableWidgetItem(str(bp.get_zend_body())))

        self.result_table.setItem(index, TableHeaders.STATUS, QTableWidgetItem(str()))
        self.result_table.setItem(index, TableHeaders.MAX_PRESS, QTableWidgetItem(str()))
        self.result_table.setItem(index, TableHeaders.FITNESS, QTableWidgetItem(str()))

        self.result_table.resizeColumnsToContents()

    def __add_calc_param_and_body_param_in_result_table(self, calculation_param, body_param, index):
        self.result_table.setItem(index, TableHeaders.ANGLE_NUM,
                                  QTableWidgetItem(str(calculation_param.angle_num)))
        self.result_table.setItem(index, TableHeaders.ROTATE_ANGLE,
                                  QTableWidgetItem(str(calculation_param.rotate_angle)))
        self.result_table.setItem(index, TableHeaders.VOLUME_PART,
                                  QTableWidgetItem(str(calculation_param.volume_part)))
        self.result_table.setItem(index, TableHeaders.CELLS_OX,
                                  QTableWidgetItem(str(calculation_param.cells_ox)))
        self.result_table.setItem(index, TableHeaders.CELLS_OY,
                                  QTableWidgetItem(str(calculation_param.cells_oy)))
        self.result_table.setItem(index, TableHeaders.DETAIL_X0,
                                  QTableWidgetItem(str(body_param.get_x0_body())))
        self.result_table.setItem(index, TableHeaders.DETAIL_X1,
                                  QTableWidgetItem(str(body_param.get_xend_body())))
        self.result_table.setItem(index, TableHeaders.DETAIL_Y0,
                                  QTableWidgetItem(str(body_param.get_y0_body())))
        self.result_table.setItem(index, TableHeaders.DETAIL_Y1,
                                  QTableWidgetItem(str(body_param.get_yend_body())))
        self.result_table.setItem(index, TableHeaders.DETAIL_Z0,
                                  QTableWidgetItem(str(body_param.get_z0_body())))
        self.result_table.setItem(index, TableHeaders.DETAIL_Z1,
                                  QTableWidgetItem(str(body_param.get_zend_body())))

    def add_parents_data(self, stress, fitness):
        for i in range(2):
            self.result_table.setItem(i, TableHeaders.STATUS, QTableWidgetItem(f"Parent {i + 1}"))
            self.result_table.setItem(i, TableHeaders.MAX_PRESS, QTableWidgetItem(str(round(stress[i], 4))))
            self.result_table.setItem(i, TableHeaders.FITNESS, QTableWidgetItem(str(round(fitness[i], 4))))

    def show_result(self):
        # Temporary files exist
        if not constants.SAVE_TEMP_FILES:
            return self.show_error("Temporary files are not saved.")

        # Row is picked
        if self.result_table.currentRow() == -1:
            return self.show_error("No experiment selected.")

        # No experiment is done
        if self.calculation.result_table is None:  # cause result table is connecting only in 'set_up_research' method
            return self.show_error("No experiment has been researched.")

        answer = self.calculation.show_result(self.result_table.currentRow())
        if answer:
            self.show_error(answer)

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
        self.sb_pop_size.setValue(constants.POPULATION_SIZE)
        self.sb_max_stress.setValue(constants.MAX_STRESS)
        self.sb_every_exel.setValue(constants.SAVE_TO_CSV_EVERY_N)
        self.sb_time_limit.setValue(constants.TIME_LIMIT)
        self.sb_gen_limit.setValue(constants.GENERATION_LIMIT)

        self.cb_save_parents.setChecked(constants.SAVE_PARENTS)
        self.cb_save_temp.setChecked(constants.SAVE_TEMP_FILES)
        self.cb_save_to_exel.setChecked(constants.BACKUP_TO_CSV)
        self.cb_restart_ansys.setChecked(constants.RESTART_AFTER_ERROR)

    def save_and_exit(self):
        constants.POPULATION_SIZE = int(self.sb_pop_size.value())
        constants.MAX_STRESS = int(self.sb_max_stress.value())
        constants.SAVE_TO_CSV_EVERY_N = int(self.sb_every_exel.value())
        constants.TIME_LIMIT = int(self.sb_time_limit.value())
        constants.GENERATION_LIMIT = int(self.sb_gen_limit.value())

        constants.SAVE_PARENTS = self.cb_save_parents.checkState()
        constants.SAVE_TEMP_FILES = self.cb_save_temp.checkState()
        constants.BACKUP_TO_CSV = self.cb_save_to_exel.checkState()
        constants.RESTART_AFTER_ERROR = self.cb_restart_ansys.checkState()

        self.close()


def main():
    # os.environ["PARSER_JAR"] = r"..\..\nodes_parser.jar"
    app = QtWidgets.QApplication(sys.argv)  # Новый экземпляр QApplication
    window = MainApp()  # Создаём объект класса ExampleApp
    window.show()  # Показываем окно
    app.exec_()  # и запускаем приложение


if __name__ == '__main__':  # Если мы запускаем файл напрямую, а не импортируем
    main()  # то запускаем функцию main()
