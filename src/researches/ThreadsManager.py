import sys
import traceback

from PyQt5.QtCore import *


class WorkerSignals(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)

    zero_stress_signal = pyqtSignal(str)
    current_stress_signal = pyqtSignal(str)
    increment_cb = pyqtSignal()
    change_table_signal = pyqtSignal(int, int, str)
    update_plot = pyqtSignal(list)


class Worker(QRunnable):
    """
    Worker thread

    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

    :param callback: The function callback to run on this worker thread. Supplied args and
                     kwargs will be passed through to the runner.
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function

    """

    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()

        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

        # Add the callback to our kwargs
        self.kwargs['zero_stress_callback'] = self.signals.zero_stress_signal
        self.kwargs['curr_stress_callback'] = self.signals.current_stress_signal
        self.kwargs['increment_cb_callback'] = self.signals.increment_cb
        self.kwargs['table_callback'] = self.signals.change_table_signal
        self.kwargs['plot_callback'] = self.signals.update_plot

    @pyqtSlot()
    def run(self):
        """
        Initialise the runner function with passed args, kwargs.
        """

        # Retrieve args/kwargs here; and fire processing using them
        try:
            result = self.fn(*self.args, **self.kwargs)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)  # Return the result of the processing
        finally:
            self.signals.finished.emit()  # Done
