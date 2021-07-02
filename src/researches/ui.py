# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '../untitled.ui'
#
# Created by: PyQt5 UI code generator 5.13.0
#
# WARNING! All changes made in this file will be lost!

import _thread as thread
import os
from typing import List, Tuple

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QMutex
from PyQt5.QtWidgets import QTableWidgetItem, QMessageBox

from src.researches.BodyParams import BodyParameters
from src.researches.Calculation import CalculationContext, Calculation, CalculationParams
from src.researches.ResultTableHeaders import ResultTableHeaders
from src.researches.util import table_utils

DEBUG = True

# noinspection PyAttributeOutsideInit
class Ui_Dialog(object):

    __schema_load_file_name: Tuple[str, str]

    def __init__(self):
        self.__mutex = QMutex()
        super().__init__()

    def setupUi(self, Dialog):
        self.__dialog = Dialog
        Dialog.setObjectName("Dialog")
        Dialog.resize(810, 540)
        Dialog.setModal(False)

        # Cells configuration form
        self.label_angle_number = QtWidgets.QLabel(Dialog)
        self.label_angle_number.setGeometry(QtCore.QRect(10, 40, 91, 16))
        self.label_angle_number.setObjectName("label_angle_number")
        self.label_rotate_angle = QtWidgets.QLabel(Dialog)
        self.label_rotate_angle.setGeometry(QtCore.QRect(10, 80, 81, 20))
        self.label_rotate_angle.setObjectName("label_rotate_angle")
        self.label_volume_part = QtWidgets.QLabel(Dialog)
        self.label_volume_part.setGeometry(QtCore.QRect(10, 120, 111, 20))
        self.label_volume_part.setObjectName("label_volume_part")
        self.label_start = QtWidgets.QLabel(Dialog)
        self.label_start.setGeometry(QtCore.QRect(120, 20, 47, 13))
        self.label_start.setObjectName("label_start")
        self.label_end = QtWidgets.QLabel(Dialog)
        self.label_end.setGeometry(QtCore.QRect(270, 20, 47, 13))
        self.label_end.setObjectName("label_end")
        self.label_step = QtWidgets.QLabel(Dialog)
        self.label_step.setGeometry(QtCore.QRect(420, 20, 47, 13))
        self.label_step.setObjectName("label_step")
        self.label_cells_ox = QtWidgets.QLabel(Dialog)
        self.label_cells_ox.setGeometry(QtCore.QRect(10, 160, 111, 20))
        self.label_cells_ox.setObjectName("label_cells_ox_start")
        self.label_cells_oy = QtWidgets.QLabel(Dialog)
        self.label_cells_oy.setGeometry(QtCore.QRect(10, 200, 111, 20))
        self.label_cells_oy.setObjectName("label_cells_oy")

        self.input_angle_num_start = QtWidgets.QLineEdit(Dialog)
        self.input_angle_num_start.setGeometry(QtCore.QRect(120, 40, 113, 20))
        self.input_angle_num_start.setObjectName("input_angle_num_start")
        self.input_angle_num_end = QtWidgets.QLineEdit(Dialog)
        self.input_angle_num_end.setGeometry(QtCore.QRect(270, 40, 113, 20))
        self.input_angle_num_end.setObjectName("input_angle_num_end")
        self.input_angle_num_step = QtWidgets.QLineEdit(Dialog)
        self.input_angle_num_step.setGeometry(QtCore.QRect(420, 40, 113, 20))
        self.input_angle_num_step.setObjectName("input_angle_num_step")

        self.input_rotate_angle_start = QtWidgets.QLineEdit(Dialog)
        self.input_rotate_angle_start.setGeometry(QtCore.QRect(120, 80, 113, 20))
        self.input_rotate_angle_start.setObjectName("input_rotate_angle_start")
        self.input_rotate_angle_end = QtWidgets.QLineEdit(Dialog)
        self.input_rotate_angle_end.setGeometry(QtCore.QRect(270, 80, 113, 20))
        self.input_rotate_angle_end.setObjectName("input_rotate_angle_end")
        self.input_rotate_angle_step = QtWidgets.QLineEdit(Dialog)
        self.input_rotate_angle_step.setGeometry(QtCore.QRect(420, 80, 113, 20))
        self.input_rotate_angle_step.setObjectName("input_rotate_angle_step")

        self.input_volume_part_start = QtWidgets.QLineEdit(Dialog)
        self.input_volume_part_start.setGeometry(QtCore.QRect(120, 120, 113, 20))
        self.input_volume_part_start.setObjectName("input_volume_part_start")
        self.input_volume_part_end = QtWidgets.QLineEdit(Dialog)
        self.input_volume_part_end.setGeometry(QtCore.QRect(270, 120, 113, 20))
        self.input_volume_part_end.setObjectName("input_volume_part_end")
        self.input_volume_part_step = QtWidgets.QLineEdit(Dialog)
        self.input_volume_part_step.setGeometry(QtCore.QRect(420, 120, 113, 20))
        self.input_volume_part_step.setObjectName("input_volume_part_step")

        self.input_cells_ox_start = QtWidgets.QLineEdit(Dialog)
        self.input_cells_ox_start.setGeometry(QtCore.QRect(120, 160, 113, 20))
        self.input_cells_ox_start.setObjectName("input_cells_ox_start")
        self.input_cells_ox_end = QtWidgets.QLineEdit(Dialog)
        self.input_cells_ox_end.setGeometry(QtCore.QRect(270, 160, 113, 20))
        self.input_cells_ox_end.setObjectName("input_cells_ox_end")
        self.input_cells_ox_step = QtWidgets.QLineEdit(Dialog)
        self.input_cells_ox_step.setGeometry(QtCore.QRect(420, 160, 113, 20))
        self.input_cells_ox_step.setObjectName("input_cells_ox_step")

        self.input_cells_oy_start = QtWidgets.QLineEdit(Dialog)
        self.input_cells_oy_start.setGeometry(QtCore.QRect(120, 200, 113, 20))
        self.input_cells_oy_start.setObjectName("input_cells_oy_start")
        self.input_cells_oy_end = QtWidgets.QLineEdit(Dialog)
        self.input_cells_oy_end.setGeometry(QtCore.QRect(270, 200, 113, 20))
        self.input_cells_oy_end.setObjectName("input_cells_oy_end")
        self.input_cells_oy_step = QtWidgets.QLineEdit(Dialog)
        self.input_cells_oy_step.setGeometry(QtCore.QRect(420, 200, 113, 20))
        self.input_cells_oy_step.setObjectName("input_cells_oy_step")

        # Area for cells configuration
        self.label_body_z0 = QtWidgets.QLabel(Dialog)
        self.label_body_z0.setGeometry(QtCore.QRect(620, 40, 15, 20))
        self.label_body_z0.setObjectName("label_body_z0")
        self.input_body_z0 = QtWidgets.QLineEdit(Dialog)
        self.input_body_z0.setGeometry(QtCore.QRect(640, 40, 50, 20))
        self.input_body_z0.setObjectName("input_body_z0")
        self.label_body_z1 = QtWidgets.QLabel(Dialog)
        self.label_body_z1.setGeometry(QtCore.QRect(710, 40, 15, 20))
        self.label_body_z1.setObjectName("label_body_z1")
        self.input_body_z1 = QtWidgets.QLineEdit(Dialog)
        self.input_body_z1.setGeometry(QtCore.QRect(730, 40, 50, 20))
        self.input_body_z1.setObjectName("input_body_z1")

        self.label_body_y0 = QtWidgets.QLabel(Dialog)
        self.label_body_y0.setGeometry(QtCore.QRect(620, 80, 15, 20))
        self.label_body_y0.setObjectName("label_body_y0")
        self.input_body_y0 = QtWidgets.QLineEdit(Dialog)
        self.input_body_y0.setGeometry(QtCore.QRect(640, 80, 50, 20))
        self.input_body_y0.setObjectName("input_body_y0")
        self.label_body_y1 = QtWidgets.QLabel(Dialog)
        self.label_body_y1.setGeometry(QtCore.QRect(710, 80, 15, 20))
        self.label_body_y1.setObjectName("label_body_y1")
        self.input_body_y1 = QtWidgets.QLineEdit(Dialog)
        self.input_body_y1.setGeometry(QtCore.QRect(730, 80, 50, 20))
        self.input_body_y1.setObjectName("input_body_y1")

        self.label_body_x0 = QtWidgets.QLabel(Dialog)
        self.label_body_x0.setGeometry(QtCore.QRect(620, 120, 15, 16))
        self.label_body_x0.setObjectName("label_body_x0")
        self.input_body_x0 = QtWidgets.QLineEdit(Dialog)
        self.input_body_x0.setGeometry(QtCore.QRect(640, 120, 50, 20))
        self.input_body_x0.setObjectName("input_body_x0")
        self.label_body_x1 = QtWidgets.QLabel(Dialog)
        self.label_body_x1.setGeometry(QtCore.QRect(710, 120, 15, 16))
        self.label_body_x1.setObjectName("label_body_x1")
        self.input_body_x1 = QtWidgets.QLineEdit(Dialog)
        self.input_body_x1.setGeometry(QtCore.QRect(730, 120, 50, 20))
        self.input_body_x1.setObjectName("input_body_x1")

        self.create_researches_btn = QtWidgets.QPushButton(Dialog)
        self.create_researches_btn.setGeometry(QtCore.QRect(600, 160, 200, 30))
        self.create_researches_btn.setObjectName("create_researches_btn")
        self.create_researches_btn.clicked.connect(self.fill_researches_list)
        self.import_researches_btn = QtWidgets.QPushButton(Dialog)
        self.import_researches_btn.setGeometry(QtCore.QRect(600, 200, 200, 30))
        self.import_researches_btn.setObjectName("import_researches_btn")
        self.import_researches_btn.clicked.connect(self.load_csv)

        # Research form
        self.button_research = QtWidgets.QPushButton(Dialog)
        self.button_research.setGeometry(QtCore.QRect(600, 315, 200, 30))
        self.button_research.setObjectName("button_research")
        self.button_research.clicked.connect(self.research)
        self.result_table = QtWidgets.QTableWidget(Dialog)
        self.result_table.setColumnCount(13)
        self.result_table.horizontalHeader().setDefaultAlignment(QtCore.Qt.AlignLeft)
        self.result_table.setHorizontalHeaderLabels(
            ["Angle #", "Rotate Angle", "Volume part, %", "Cells Ox", "Cells Oy", "X start", "X end", "Y start",
             "Y end", "Z start", "Z end", "Status", "Max pressure"])
        self.result_table.setColumnWidth(ResultTableHeaders.ANGLE_NUM, 70)
        self.result_table.setColumnWidth(ResultTableHeaders.ROTATE_ANGLE, 70)
        self.result_table.setColumnWidth(ResultTableHeaders.VOLUME_PART, 70)
        self.result_table.setColumnWidth(ResultTableHeaders.CELLS_OX, 70)
        self.result_table.setColumnWidth(ResultTableHeaders.CELLS_OY, 70)
        self.result_table.setColumnWidth(ResultTableHeaders.STATUS, 70)
        self.result_table.setColumnWidth(ResultTableHeaders.MAX_PRESS, 70)
        self.result_table.setGeometry(QtCore.QRect(10, 315, 525, 200))
        self.result_table.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
        self.button_result = QtWidgets.QPushButton(Dialog)
        self.button_result.setGeometry(QtCore.QRect(600, 355, 200, 30))
        self.button_result.setObjectName("button_retry")
        self.button_result.clicked.connect(self.show_result)
        self.button_stress = QtWidgets.QPushButton(Dialog)
        self.button_stress.setGeometry(QtCore.QRect(600, 395, 200, 30))
        self.button_stress.setObjectName("button_stress")
        self.button_stress.clicked.connect(self.show_stress_chart)
        self.button_export = QtWidgets.QPushButton(Dialog)
        self.button_export.setGeometry(QtCore.QRect(600, 435, 200, 30))
        self.button_export.setText("Экспорт")
        self.button_export.clicked.connect(self.save_csv)
        self.button_clusterization = QtWidgets.QPushButton(Dialog)
        self.button_clusterization.setGeometry(QtCore.QRect(600, 475, 200, 30))
        self.button_clusterization.setText("Анализ экспериментов")
        self.button_clusterization.clicked.connect(self.analyze_researches)

        # Input files form
        self.button_detail_file = QtWidgets.QPushButton(Dialog)
        self.button_detail_file.setGeometry(QtCore.QRect(10, 240, 200, 25))
        self.button_detail_file.setObjectName("detail_file")
        self.button_detail_file.clicked.connect(self.pick_model_file)
        self.input_detail_file = QtWidgets.QLineEdit(Dialog)
        self.input_detail_file.setGeometry(QtCore.QRect(220, 240, 315, 25))
        self.input_detail_file.setObjectName("input_detail_file")
        self.input_detail_file.setEnabled(False)

        self.button_load_schema_file = QtWidgets.QPushButton(Dialog)
        self.button_load_schema_file.setGeometry(QtCore.QRect(10, 270, 200, 25))
        self.button_load_schema_file.setObjectName("detail_file")
        self.button_load_schema_file.clicked.connect(self.pick_schema_load_file)
        self.input_load_schema_file = QtWidgets.QLineEdit(Dialog)
        self.input_load_schema_file.setGeometry(QtCore.QRect(220, 270, 315, 25))
        self.input_load_schema_file.setObjectName("input_load_schema_file")
        self.input_load_schema_file.setEnabled(False)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def load_csv(self):
        file_name = QtWidgets.QFileDialog.getOpenFileName(self.__dialog, 'Open file', r'..\..', '(*.csv)')
        thread.start_new_thread(table_utils.import_research_list_from_csv, (file_name[0], self.result_table))

    def save_csv(self):
        file_name = QtWidgets.QFileDialog.getSaveFileName(self.__dialog, 'Open file', r'..\..', '(*.csv)')
        thread.start_new_thread(table_utils.save_csv_to_file, (file_name[0], self.result_table))

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

    def __get_body_params(self) -> BodyParameters:
        return BodyParameters(
            float(self.input_body_x0.text()),
            float(self.input_body_x1.text()),
            float(self.input_body_y0.text()),
            float(self.input_body_y1.text()),
            float(self.input_body_z0.text()),
            float(self.input_body_z1.text()))

    def __get_calculation_context(self) -> CalculationContext:
        return CalculationContext(
            int(self.input_rotate_angle_start.text()),
            int(self.input_rotate_angle_end.text()),
            int(self.input_rotate_angle_step.text()),
            int(self.input_angle_num_start.text()),
            int(self.input_angle_num_end.text()),
            int(self.input_angle_num_step.text()),
            int(self.input_volume_part_start.text()),
            int(self.input_volume_part_end.text()),
            int(self.input_volume_part_step.text()),
            int(self.input_cells_ox_start.text()),
            int(self.input_cells_ox_end.text()),
            int(self.input_cells_ox_step.text()),
            int(self.input_cells_oy_start.text()),
            int(self.input_cells_oy_end.text()),
            int(self.input_cells_oy_step.text()))

    def pick_model_file(self):
        if DEBUG:
            self.__detail_file_name = ['D:/DIPLOMA/app/researcher/model_250x250x250mm.igs', ]
        else:
            # открыть диалог выбора файла в текущей папке
            self.__detail_file_name = QtWidgets.QFileDialog.getOpenFileName(self.__dialog, 'Open file', '..\\..',
                                                                            '3D model.igs files (*.igs)')

        if self.__detail_file_name:  # не продолжать выполнение, если пользователь не выбрал файл
            self.input_detail_file.setText(self.__detail_file_name[0])

    def pick_schema_load_file(self):
        if DEBUG:
            self.__schema_load_file_name = [r'D:\DIPLOMA\app\researcher\load_schema2.txt', ]
        else:
            self.__schema_load_file_name = QtWidgets.QFileDialog.getOpenFileName(self.__dialog, 'Open file', '..\\..',
                                                                                 '(*.*)')
        if self.__schema_load_file_name:  # не продолжать выполнение, если пользователь не выбрал файл
            self.input_load_schema_file.setText(self.__schema_load_file_name[0])

    def research(self):
        self.calculation = Calculation()

        # TODO: the line below is for profiler ONLY
        # self.calculation.calculate(self.__detail_file_name[0], self.__schema_load_file_name[0], self.result_table)
        #

        thread.start_new_thread(self.calculation.calculate,
                                (self.__detail_file_name[0], self.__schema_load_file_name[0], self.result_table))

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        self.input_angle_num_start.setText(_translate("Dialog", "3"))
        self.input_rotate_angle_start.setText(_translate("Dialog", "0"))
        self.input_volume_part_start.setText(_translate("Dialog", "50"))
        self.input_volume_part_end.setText(_translate("Dialog", "50"))
        self.input_cells_ox_start.setText(_translate("Dialog", "4"))
        self.input_cells_ox_step.setText(_translate("Dialog", "1"))
        self.input_cells_ox_end.setText(_translate("Dialog", "4"))
        self.input_cells_oy_start.setText(_translate("Dialog", "4"))
        self.input_cells_oy_step.setText(_translate("Dialog", "1"))
        self.input_cells_oy_end.setText(_translate("Dialog", "4"))
        self.label_angle_number.setText(_translate("Dialog", "Количество углов"))
        self.label_rotate_angle.setText(_translate("Dialog", "Угол поворота"))
        self.label_volume_part.setText(_translate("Dialog", "Часть от объёма (%)"))
        self.label_start.setText(_translate("Dialog", "Начало"))
        self.label_end.setText(_translate("Dialog", "Конец"))
        self.label_step.setText(_translate("Dialog", "Шаг"))
        self.input_rotate_angle_end.setText(_translate("Dialog", "0"))
        self.input_angle_num_end.setText(_translate("Dialog", "3"))
        self.label_cells_ox.setText(_translate("Dialog", "Ячеек Ox"))
        self.label_cells_oy.setText(_translate("Dialog", "Ячеек Oy"))
        self.input_volume_part_step.setText(_translate("Dialog", "1"))
        self.input_rotate_angle_step.setText(_translate("Dialog", "1"))
        self.input_angle_num_step.setText(_translate("Dialog", "1"))
        self.button_research.setText(_translate("Dialog", "Исследовать"))
        self.button_result.setText(_translate("Dialog", "Результат"))
        self.button_stress.setText(_translate("Dialog", "Стресс"))
        self.create_researches_btn.setText(_translate("Dialog", "Создать эксперименты"))
        self.import_researches_btn.setText(_translate("Dialog", "Импортировать эксперименты"))

        self.label_body_z0.setText(_translate("Dialog", "Z0"))
        self.input_body_z0.setText(_translate("Dialog", "0"))
        self.label_body_x0.setText(_translate("Dialog", "X0"))
        self.input_body_x0.setText(_translate("Dialog", "0"))
        self.label_body_y0.setText(_translate("Dialog", "Y0"))
        self.input_body_y0.setText(_translate("Dialog", "0"))
        self.label_body_z1.setText(_translate("Dialog", "Z1"))
        self.input_body_z1.setText(_translate("Dialog", "250"))
        self.label_body_x1.setText(_translate("Dialog", "X1"))
        self.input_body_x1.setText(_translate("Dialog", "250"))
        self.label_body_y1.setText(_translate("Dialog", "Y1"))
        self.input_body_y1.setText(_translate("Dialog", "250"))

        self.button_detail_file.setText(_translate("Dialog", "Файл детали"))
        self.button_load_schema_file.setText(_translate("Dialog", "Файл схемы нагрузки"))

    def fill_researches_list(self):
        # Clear the old table if exists
        self.result_table.setRowCount(0)

        context = self.__get_calculation_context()
        body_params = self.__get_body_params()
        calculation_params: List = self.__calc_params(context)

        index = self.result_table.rowCount()

        for calculation_param in calculation_params:
            self.result_table.setRowCount(index + 1)
            self.__add_calc_param_and_body_param_in_result_table(calculation_param, body_params, index)
            index += 1

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

    def __calc_params(self, context) -> List[CalculationParams]:
        params = []

        for angle_num in range(context.angle_num_start, context.angle_num_end + 1, context.angle_num_step):
            for rotate_angle in range(context.rotate_angle_start, context.rotate_angle_end + 1,
                                      context.rotate_angle_step):
                for volume_part in range(context.volume_part_start, context.volume_part_end + 1,
                                         context.volume_part_step):
                    for cells_ox in range(context.cells_ox_start, context.cells_ox_end + 1, context.cells_ox_step):
                        for cells_oy in range(context.cells_oy_start, context.cells_oy_end + 1, context.cells_oy_step):
                            params.append(CalculationParams(rotate_angle, angle_num, volume_part, cells_ox, cells_oy))

        return params

    def show_result(self):
        # if row is picked
        if (self.result_table.currentRow() != -1):
            self.calculation.show_result(self.result_table.currentRow())
            pass

    def show_stress_chart(self):
        if (self.result_table.currentRow() != -1):
            self.calculation.show_stress_chart(self.result_table.currentRow())


class MyDialog(QtWidgets.QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)

    def closeEvent(self, event: QtGui.QCloseEvent):
        print("Event: " + str(event))
        super(MyDialog, self).closeEvent(event)


if __name__ == "__main__":
    import sys
    os.environ["PARSER_JAR"] = r"..\..\nodes_parser.jar"
    app = QtWidgets.QApplication(sys.argv)
    Dialog = MyDialog()
    ui = Ui_Dialog()
    ui.setupUi(Dialog)
    Dialog.show()
    sys.exit(app.exec_())
