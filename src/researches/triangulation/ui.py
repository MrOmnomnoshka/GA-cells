import _thread as thread
import json
import time

import matplotlib as mpl
import matplotlib.pyplot as plt
import mpl_toolkits.mplot3d as a3
import scipy as sp
import numpy as np
import os
from PyQt5 import QtCore, QtGui, QtWidgets, Qt
from PyQt5.QtWidgets import QTableWidgetItem

from researches.triangulation import triangulation


class NodesTableHeaders:
    NODE_ID = 0
    NODE_X = 1
    NODE_Y = 2
    NODE_Z = 3


class Ui_Dialog(object):



    def __init__(self, research_folder: str):
        self.__research_folder = research_folder
        self.__nodes = np.genfromtxt(fname=research_folder + os.sep + "nodes.csv", skip_header=1, delimiter=",",
                                     usecols=(0, 1, 2, 3))
        super().__init__()


    def setupUi(self, Dialog):
        self.__dialog = Dialog
        Dialog.setObjectName("Dialog")
        Dialog.resize(695, 605)
        Dialog.setModal(False)

        self.all_nodes_table = QtWidgets.QTableWidget(Dialog)
        self.all_nodes_table.setColumnCount(4)
        self.all_nodes_table.horizontalHeader().setDefaultAlignment(QtCore.Qt.AlignLeft)
        self.all_nodes_table.setHorizontalHeaderLabels(["Node #","X","Y","Z"])
        self.all_nodes_table.setColumnWidth(NodesTableHeaders.NODE_ID, 70)
        self.all_nodes_table.setColumnWidth(NodesTableHeaders.NODE_X, 70)
        self.all_nodes_table.setColumnWidth(NodesTableHeaders.NODE_Y, 70)
        self.all_nodes_table.setColumnWidth(NodesTableHeaders.NODE_Z, 70)
        self.all_nodes_table.setGeometry(QtCore.QRect(10, 100, 285, 400))
        self.all_nodes_table.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
        self.all_nodes_table.doubleClicked.connect(self.add_node)

        self.build_model_btn = QtWidgets.QPushButton(Dialog)
        self.build_model_btn.setGeometry(QtCore.QRect(400, 50, 285, 40))
        self.build_model_btn.setObjectName("build_model_btn")
        self.build_model_btn.clicked.connect(self.build_model_handler)

        self.picked_nodes_table = QtWidgets.QTableWidget(Dialog)
        self.picked_nodes_table.setColumnCount(4)
        self.picked_nodes_table.horizontalHeader().setDefaultAlignment(QtCore.Qt.AlignLeft)
        self.picked_nodes_table.setHorizontalHeaderLabels(["Node #", "X", "Y", "Z"])
        self.picked_nodes_table.setColumnWidth(NodesTableHeaders.NODE_ID, 70)
        self.picked_nodes_table.setColumnWidth(NodesTableHeaders.NODE_X, 70)
        self.picked_nodes_table.setColumnWidth(NodesTableHeaders.NODE_Y, 70)
        self.picked_nodes_table.setColumnWidth(NodesTableHeaders.NODE_Z, 70)
        self.picked_nodes_table.setGeometry(QtCore.QRect(400, 100, 285, 400))
        self.picked_nodes_table.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
        self.picked_nodes_table.doubleClicked.connect(self.remove_node)

        self.add_btn = QtWidgets.QPushButton(Dialog)
        self.add_btn.setGeometry(QtCore.QRect(10, 510, 285, 40))
        self.add_btn.setObjectName("add_all_btn")
        self.add_btn.clicked.connect(self.add_node)
        self.add_all_btn = QtWidgets.QPushButton(Dialog)
        self.add_all_btn.setGeometry(QtCore.QRect(10, 555, 285, 40))
        self.add_all_btn.setObjectName("add_all_btn")
        self.add_all_btn.clicked.connect(self.add_all_nodes)

        self.remove_btn = QtWidgets.QPushButton(Dialog)
        self.remove_btn.setGeometry(QtCore.QRect(400, 510, 285, 40))
        self.remove_btn.setObjectName("remove_all_btn")
        self.remove_btn.clicked.connect(self.remove_node)
        self.remove_all_btn = QtWidgets.QPushButton(Dialog)
        self.remove_all_btn.setGeometry(QtCore.QRect(400, 555, 285, 40))
        self.remove_all_btn.setObjectName("remove_all_btn")
        self.remove_all_btn.clicked.connect(self.remove_all_nodes)


        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

        thread.start_new_thread(self.init_table, tuple())


    def build_model_handler(self):
        # cmd = 'triangulation.py "%s" "%s"' % (self.__research_folder, json.dumps(self.__get_picked_nodes_ids()))
        # print("cmd: ", cmd)
        # os.system(cmd)
        thread.start_new(self.__build_model, tuple())

    def __build_model(self):
        json_nodes_ids = json.dumps(list(self.get_picked_nodes_ids()))
        cmd = 'python triangulation.py "%s" "%s"' % (self.__research_folder, json_nodes_ids)
        print("cmd: ", cmd)
        os.system(cmd)
        # fig = plt.figure()
        # ax = fig.add_subplot(111, projection='3d')
        # ax.dist = 20
        # ax.azim = 0
        # ax.set_xlim([0, 100])
        # ax.set_ylim([0, 100])
        # ax.set_zlim([0, 100])
        # ax.set_xlabel('x')
        # ax.set_ylabel('y')
        # ax.set_zlabel('z')
        #
        # faces = triangulation.calculate_faces(self.__get_picked_nodes_ids(), self.__research_folder)
        #
        # for f in faces:
        #     face = a3.art3d.Poly3DCollection([f])
        #     face.set_color(mpl.colors.rgb2hex(sp.rand(3)))
        #     face.set_edgecolor('k')
        #     face.set_alpha(0.5)
        #     ax.add_collection3d(face)
        #     break
        #
        # plt.show()

    def add_node(self):
        current_row = self.all_nodes_table.currentRow()
        if (current_row != -1) and not self.picked_list_contains_el(current_row):
            picked_table_rows = self.picked_nodes_table.rowCount()
            self.picked_nodes_table.setRowCount(picked_table_rows + 1)

            node_id = self.all_nodes_table.item(current_row, NodesTableHeaders.NODE_ID).text()
            node_x = self.all_nodes_table.item(current_row, NodesTableHeaders.NODE_X).text()
            node_y = self.all_nodes_table.item(current_row, NodesTableHeaders.NODE_Y).text()
            node_z = self.all_nodes_table.item(current_row, NodesTableHeaders.NODE_Z).text()

            self.picked_nodes_table.setItem(picked_table_rows, NodesTableHeaders.NODE_ID, QTableWidgetItem(node_id))
            self.picked_nodes_table.setItem(picked_table_rows, NodesTableHeaders.NODE_X, QTableWidgetItem(node_x))
            self.picked_nodes_table.setItem(picked_table_rows, NodesTableHeaders.NODE_Y, QTableWidgetItem(node_y))
            self.picked_nodes_table.setItem(picked_table_rows, NodesTableHeaders.NODE_Z, QTableWidgetItem(node_z))

    def picked_list_contains_el(self, row_number: int):
        picked_nodes = list(self.get_picked_nodes_ids())
        picked_node_id = int(self.all_nodes_table.item(row_number, NodesTableHeaders.NODE_ID).text())
        return picked_node_id in picked_nodes

    def remove_node(self):
        if self.picked_nodes_table.currentRow() > -1:
            self.picked_nodes_table.removeRow(self.picked_nodes_table.currentRow())

    def add_all_nodes(self):
        pass

    def remove_all_nodes(self):
        pass

    def get_picked_nodes_ids(self) -> set:
        rows = self.picked_nodes_table.rowCount()
        return set(int(self.picked_nodes_table.item(row, NodesTableHeaders.NODE_ID).text()) for row in range(rows))


    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        self.build_model_btn.setText(_translate("Dialog", "Построить"))
        Dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        self.add_btn.setText(_translate("Dialog", "Добавить"))
        self.add_all_btn.setText(_translate("Dialog", "Добавить все"))
        self.remove_btn.setText(_translate("Dialog", "Удалить"))
        self.remove_all_btn.setText(_translate("Dialog", "Удалить все"))

    def init_table(self):
        for node in self.__nodes:
            row_count = self.all_nodes_table.rowCount()
            self.all_nodes_table.setRowCount(row_count + 1)
            self.all_nodes_table.setItem(row_count,
                                         NodesTableHeaders.NODE_ID,
                                         QTableWidgetItem(str(int(node[NodesTableHeaders.NODE_ID]))))
            self.all_nodes_table.setItem(row_count,
                                         NodesTableHeaders.NODE_X,
                                         QTableWidgetItem(str(round(node[NodesTableHeaders.NODE_X],2))))
            self.all_nodes_table.setItem(row_count,
                                         NodesTableHeaders.NODE_Y,
                                         QTableWidgetItem(str(round(node[NodesTableHeaders.NODE_Y], 2))))
            self.all_nodes_table.setItem(row_count,
                                         NodesTableHeaders.NODE_Z,
                                         QTableWidgetItem(str(round(node[NodesTableHeaders.NODE_Z], 2))))
            row_count += 1


class MyDialog(QtWidgets.QDialog):

    def __init__(self, parent = None):
        super().__init__(parent)

    def closeEvent(self, event: QtGui.QCloseEvent):
        super(MyDialog, self).closeEvent(event)


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Dialog = MyDialog()
    research_folder = sys.argv[1]
    ui = Ui_Dialog(research_folder)
    ui.setupUi(Dialog)
    Dialog.show()
    sys.exit(app.exec_())
