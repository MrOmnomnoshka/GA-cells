import _thread as thread
import sys
# import random

from PyQt5 import QtCore, QtGui, QtWidgets

# from PyQt5.QtCore import QMutex, QObject, QThread, pyqtSignal

from PyQt5.QtWidgets import QTableWidgetItem, QMessageBox
import pyqtgraph as pg

# from src.researches.BodyParams import BodyParameters
from src.researches.Calculation import *
from src.researches.ResultTableHeaders import ResultTableHeaders
from src.researches.util import table_utils
from src.researches.GA.Chromosome import Chromosome
from forms import design  # Это наш конвертированный файл дизайна
import src.researches.constants as constants


class MainApp(QtWidgets.QMainWindow, design.Ui_MainWindow):

    def __init__(self):
        # Это здесь нужно для доступа к переменным, методам и т.д. в файле design.py
        super().__init__()
        self.setupUi(self)  # Это нужно для инициализации нашего дизайна

        # self.mutex = QMutex()  # lock class that allows to manage mutual exclusion
        self.calculation = Calculation()
        self.is_running = False

        self.connect_all_buttons()
        self.set_up_threads()

    def connect_all_buttons(self):
        self.button_detail_file.clicked.connect(self.pick_model_file)
        self.button_load_schema_file.clicked.connect(self.pick_schema_load_file)
        self.button_create_researches.clicked.connect(self.fill_researches_list)
        self.button_play_pause.clicked.connect(self.research)
        self.button_next.clicked.connect(self.next_generation_research)
        # self.button_stop.clicked.connect()
        self.button_result.clicked.connect(self.show_result)
        self.button_stress.clicked.connect(self.show_stress_chart)
        self.button_export.clicked.connect(self.save_csv)
        self.button_clusterization.clicked.connect(self.analyze_researches)
        self.button_import_researches.clicked.connect(self.load_csv)

        self.set_up_plot()

    def set_up_plot(self):
        # Customize plot widget
        app_color = self.palette().color(QtGui.QPalette.Window)
        self.graph_widget.setBackground(app_color)
        self.graph_widget.showGrid(x=True, y=True)
        # TODO: что бы было видно первую точку, сделать точки жирными и ставить их на график
        # plot(x, y, color='green', linestyle='dashed', linewidth=3,
        #       marker='o', markerfacecolor='blue', markersize=12)
        self.plot_widget = self.graph_widget.plotItem.plot(pen=pg.mkPen("b", width=2, marker="o", markersize=25))

    def set_up_threads(self):
        # --- Подключаем сигналы к слоту, слот будет вызываться с параметрами сигнала в нужное время.
        self.calculation.threadFinish.connect(self.threadFinished)
        self.calculation.current_stress_signal.connect(self.change_current_stress_label)
        self.calculation.zero_stress_signal.connect(self.change_zero_stress_label)

    def increment_cb_generation(self):
        self.cb_generation.addItem("Поколение: " + str(self.cb_generation.count()))
        self.cb_generation.setCurrentIndex(self.cb_generation.count() - 1)

    def add_generation_stress_in_plot(self, data):
        self.plot_widget.setData(data)
        # self.graph_widget.plotItem.plot([generation], [stress], pen=pg.mkPen("b", width=2))

    def closeEvent(self, event: QtGui.QCloseEvent):
        if self.calculation is not None:
            self.calculation.clear_and_exit()
        # print("Event: " + str(event))

    def load_csv(self):
        file_name = QtWidgets.QFileDialog.getOpenFileName(self, 'Open file', r'..\..', '(*.csv)')
        thread.start_new_thread(table_utils.import_research_list_from_csv, (file_name[0], self.result_table))

    def save_csv(self, default=None):
        # TODO: BUG: crashes after save and count next gen
        if default:
            file_name = default
        else:
            file_name, _ = QtWidgets.QFileDialog.getSaveFileName(self, 'Open file', r'..\..', '(*.csv)')

        if file_name:
            table_utils.save_csv_to_file(file_name, self.result_table)

    def analyze_researches(self):
        rows = self.result_table.rowCount()
        processed_researches = 0
        for i in range(rows):
            if self.result_table.item(i, ResultTableHeaders.STATUS) \
                    and self.result_table.item(i, ResultTableHeaders.STATUS).text() == "Finished":
                processed_researches += 1

        proceed = False
        if processed_researches == 0:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)

            msg.setText("Ни один эксперимент не проведен.")
            msg.setWindowTitle("Warning")
            msg.setStandardButtons(QMessageBox.Ok)

            msg.exec_()
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
            float(min(agent.working_zone[0][0], agent.working_zone[0][1])),
            float(max(agent.working_zone[0][0], agent.working_zone[0][1])),
            float(min(agent.working_zone[1][0], agent.working_zone[1][1])),
            float(max(agent.working_zone[1][0], agent.working_zone[1][1])),
            # Z values:
            float(0),
            float(250))

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

    def set_up_research(self):
        self.calculation.import_detail_and_load_schema_files(self.input_detail_file.text(),
                                                             self.input_load_schema_file.text())

        # Prepare arguments for methods in Calculation class
        self.calculation.result_table = self.result_table
        self.calculation.app = self

        # Count zero_stress
        self.calculation.current_task = 0
        self.calculation.start()

        # Wait until it finishes
        while self.calculation.isRunning():
            QtCore.QThread.msleep(250)

        # Start the experiment
        if self.is_running:
            # calculate infinity
            self.calculation.current_task = 2
            self.calculation.start()
        else:
            # calculate next iteration
            self.calculation.current_task = 1
            self.calculation.start()

    def next_generation_research(self):
        if self.calculation.ansys_manager is None:
            thread.start_new_thread(self.set_up_research, ())
        else:
            # calculate next iteration
            self.calculation.current_task = 1
            self.calculation.start()  # TODO: Бесконечно генерятся потоки, мб есть на них ограничение и все полетит
            # thread.start_new_thread(self.calculation.calculate_next_iteration, (self.result_table, self))

    def on_threadSignal(self, value):
        # функция вывода чисел
        """ Визуализация потоковых данных-WorkThread.  """
        self.label_current_stress.setNum(value)

    def threadFinished(self):
        self.label_current_stress.setText("{} - Финиш!".format(self.label_current_stress.text()))
        # print("FINISHED!")

    def change_current_stress_label(self, text):
        self.label_current_stress.setText("Нагрузка текущая: " + text)

    def change_zero_stress_label(self, text):
        self.label_zero_stress.setText("Нагрузка нулевая: " + text)

    def research(self):
        # Stop or pause calculating
        self.is_running = not self.is_running
        self.button_play_pause.setDefault(self.is_running)

        if self.calculation.ansys_manager is None:
            # TODO: thread? or PyQt Thread?! xD
            thread.start_new_thread(self.set_up_research, ())
        else:
            # calculate infinity
            if self.is_running:
                self.calculation.current_task = 2
                self.calculation.start()
            # thread.start_new_thread(self.calculation.calculate_infinity, (self.result_table, self))

        # !!NOTE!!: the line below is for profiler ONLY
        # self.set_up_research()

    def fill_researches_list(self):
        for i in range(constants.POPULATION_SIZE):
            agent = Chromosome()
            agent.generate_all_params()
            self.count_body_params_and_add_in_table(agent, i)
            del agent

    def count_body_params_and_add_in_table(self, agent, i):
        body_params = self.__get_body_params_ga(agent)

        self.result_table.setRowCount(i + 1)
        self.__add_ga_param_in_result_table(agent, body_params, i)

    def clear_result_table(self):
        self.result_table.setRowCount(1)

        # TODO: redo it in designer.ui
        self.result_table.setItem(0, ResultTableHeaders.ANGLE_NUM, QTableWidgetItem(str()))
        self.result_table.setItem(0, ResultTableHeaders.ROTATE_ANGLE, QTableWidgetItem(str()))
        self.result_table.setItem(0, ResultTableHeaders.VOLUME_PART, QTableWidgetItem(str()))
        self.result_table.setItem(0, ResultTableHeaders.CELLS_OX, QTableWidgetItem(str()))
        self.result_table.setItem(0, ResultTableHeaders.CELLS_OY, QTableWidgetItem(str()))
        self.result_table.setItem(0, ResultTableHeaders.DETAIL_X0, QTableWidgetItem(str()))
        self.result_table.setItem(0, ResultTableHeaders.DETAIL_X1, QTableWidgetItem(str()))
        self.result_table.setItem(0, ResultTableHeaders.DETAIL_Y0, QTableWidgetItem(str()))
        self.result_table.setItem(0, ResultTableHeaders.DETAIL_Y1, QTableWidgetItem(str()))
        self.result_table.setItem(0, ResultTableHeaders.DETAIL_Z0, QTableWidgetItem(str()))
        self.result_table.setItem(0, ResultTableHeaders.DETAIL_Z1, QTableWidgetItem(str()))
        self.result_table.setItem(0, ResultTableHeaders.STATUS, QTableWidgetItem(str()))
        self.result_table.setItem(0, ResultTableHeaders.MAX_PRESS, QTableWidgetItem(str()))
        self.result_table.setItem(0, ResultTableHeaders.FITNESS, QTableWidgetItem(str()))

    def __add_ga_param_in_result_table(self, agent, bp, index):
        # TODO: redo it in designer.ui
        self.result_table.setItem(index, ResultTableHeaders.ANGLE_NUM, QTableWidgetItem(str(agent.angles)))
        self.result_table.setItem(index, ResultTableHeaders.ROTATE_ANGLE, QTableWidgetItem(str(agent.rotation)))
        self.result_table.setItem(index, ResultTableHeaders.VOLUME_PART, QTableWidgetItem(str(agent.size)))
        self.result_table.setItem(index, ResultTableHeaders.CELLS_OX, QTableWidgetItem(str(agent.x_amount)))
        self.result_table.setItem(index, ResultTableHeaders.CELLS_OY, QTableWidgetItem(str(agent.y_amount)))

        self.result_table.setItem(index, ResultTableHeaders.DETAIL_X0, QTableWidgetItem(str(bp.get_x0_body())))
        self.result_table.setItem(index, ResultTableHeaders.DETAIL_X1, QTableWidgetItem(str(bp.get_xend_body())))
        self.result_table.setItem(index, ResultTableHeaders.DETAIL_Y0, QTableWidgetItem(str(bp.get_y0_body())))
        self.result_table.setItem(index, ResultTableHeaders.DETAIL_Y1, QTableWidgetItem(str(bp.get_yend_body())))
        self.result_table.setItem(index, ResultTableHeaders.DETAIL_Z0, QTableWidgetItem(str(bp.get_z0_body())))
        self.result_table.setItem(index, ResultTableHeaders.DETAIL_Z1, QTableWidgetItem(str(bp.get_zend_body())))

        self.result_table.setItem(index, ResultTableHeaders.STATUS, QTableWidgetItem(str()))
        self.result_table.setItem(index, ResultTableHeaders.MAX_PRESS, QTableWidgetItem(str()))

        self.result_table.resizeColumnsToContents()

    def __add_calc_param_and_body_param_in_result_table(self, calculation_param: CalculationParams,
                                                        body_param: BodyParameters, index: int):
        self.result_table.setItem(index, ResultTableHeaders.ANGLE_NUM,
                                  QTableWidgetItem(str(calculation_param.angle_num)))
        self.result_table.setItem(index, ResultTableHeaders.ROTATE_ANGLE,
                                  QTableWidgetItem(str(calculation_param.rotate_angle)))
        self.result_table.setItem(index, ResultTableHeaders.VOLUME_PART,
                                  QTableWidgetItem(str(calculation_param.volume_part)))
        self.result_table.setItem(index, ResultTableHeaders.CELLS_OX,
                                  QTableWidgetItem(str(calculation_param.cells_ox)))
        self.result_table.setItem(index, ResultTableHeaders.CELLS_OY,
                                  QTableWidgetItem(str(calculation_param.cells_oy)))
        self.result_table.setItem(index, ResultTableHeaders.DETAIL_X0,
                                  QTableWidgetItem(str(body_param.get_x0_body())))
        self.result_table.setItem(index, ResultTableHeaders.DETAIL_X1,
                                  QTableWidgetItem(str(body_param.get_xend_body())))
        self.result_table.setItem(index, ResultTableHeaders.DETAIL_Y0,
                                  QTableWidgetItem(str(body_param.get_y0_body())))
        self.result_table.setItem(index, ResultTableHeaders.DETAIL_Y1,
                                  QTableWidgetItem(str(body_param.get_yend_body())))
        self.result_table.setItem(index, ResultTableHeaders.DETAIL_Z0,
                                  QTableWidgetItem(str(body_param.get_z0_body())))
        self.result_table.setItem(index, ResultTableHeaders.DETAIL_Z1,
                                  QTableWidgetItem(str(body_param.get_zend_body())))

    def add_parents_data(self, stress, fitness):
        for i in range(2):
            self.result_table.setItem(i, ResultTableHeaders.STATUS, QTableWidgetItem(f"Parent {i + 1}"))
            self.result_table.setItem(i, ResultTableHeaders.MAX_PRESS, QTableWidgetItem(str(round(stress[i], 4))))
            self.result_table.setItem(i, ResultTableHeaders.FITNESS, QTableWidgetItem(str(round(fitness[i], 4))))

    def show_result(self):
        # if row is picked
        if self.result_table.currentRow() != -1:
            self.calculation.show_result(self.result_table.currentRow())

    def show_stress_chart(self):
        if self.result_table.currentRow() != -1:
            self.calculation.show_stress_chart(self.result_table.currentRow())


def main():
    # os.environ["PARSER_JAR"] = r"..\..\nodes_parser.jar"
    app = QtWidgets.QApplication(sys.argv)  # Новый экземпляр QApplication
    window = MainApp()  # Создаём объект класса ExampleApp
    window.show()  # Показываем окно
    app.exec_()  # и запускаем приложение


if __name__ == '__main__':  # Если мы запускаем файл напрямую, а не импортируем
    main()  # то запускаем функцию main()
