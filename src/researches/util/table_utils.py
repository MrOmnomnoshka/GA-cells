import csv

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QTableWidgetItem


def import_research_list_from_csv(csv_file: str, table: QtWidgets.QTableWidget):
    with open(csv_file, "r") as fileInput:
        for row in csv.reader(fileInput):
            if len(row) == 0:
                continue

            column = 0
            index = table.rowCount()
            table.setRowCount(index + 1)

            for field in row:
                table.setItem(index, column, QTableWidgetItem(field))
                column += 1


def save_csv_to_file(csv_file: str, table: QtWidgets.QTableWidget):
    with open(csv_file, "w", newline="") as fileOutput:
        writer = csv.writer(fileOutput)
        for rowNumber in range(table.rowCount()):
            # +
            fields = [
                table.item(rowNumber, columnNumber).text() if table.item(rowNumber, columnNumber) is not None else ""
                for columnNumber in range(table.columnCount())
            ]

            if len(fields) > 0:
                writer.writerow(fields)
