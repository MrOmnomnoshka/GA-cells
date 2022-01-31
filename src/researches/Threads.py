from PyQt5 import QtCore


class ZeroStressThread(QtCore.QThread):
    """ Потоковая задача """
    zero_stress = QtCore.pyqtSignal(int)  # Объявляем сигнал, с аргументом(int)

    def __init__(self, calculation):
        super().__init__()

        self.calculation = calculation

    def run(self, *args, **kwargs):
            self.calculation.calculate_zero_stress()
            print("Thread zero stress")
