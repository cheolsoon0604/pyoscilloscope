import sys
import pyvisa as visa
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from oscilloscope import Oscilloscope
from fft_processor import FFTProcessor
import pyqtgraph as pg
import numpy as np
from datetime import datetime


class OscilloscopeGUI(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        uic.loadUi('oscilloscope.ui', self)
        # uic.loadUi('test.ui', self)

        self.oscilloscope = None
        self.fft_processor = FFTProcessor()

        # UI 요소 설정
        # Connect
        self.is_connected = False
        self.connection_connect_button.clicked.connect(self.connection_connect_device)

        # Time Update
        self.time_update_timer = QTimer()
        self.time_update_timer.start(1000)
        self.time_update_timer.timeout.connect(self.connection_update_current_time)
        self.current_time = None

        # Control
        self.is_acquiring = False
        self.channel_selected = {
            1: False,
            2: False,
            3: False,
            4: False
        }

        self.control_select_channel_ch1.stateChanged.connect(
            lambda: self.control_channel_select(1, self.control_select_channel_ch1.isChecked()))
        self.control_select_channel_ch2.stateChanged.connect(
            lambda: self.control_channel_select(2, self.control_select_channel_ch2.isChecked()))
        self.control_select_channel_ch3.stateChanged.connect(
            lambda: self.control_channel_select(3, self.control_select_channel_ch3.isChecked()))
        self.control_select_channel_ch4.stateChanged.connect(
            lambda: self.control_channel_select(4, self.control_select_channel_ch4.isChecked()))

        self.control_single.clicked.connect(self.control_single_aquire_data)
        self.control_run_stop.clicked.connect(self.control_run_stop_aquire_data)

        self.control_run_stop_timer = QTimer()
        self.control_run_stop_timer.timeout.connect(self.control_run_stop_aquire_data_loop)

        # Math
        self.math_source1 = None
        self.math_source2 = None

        self.math_is_running = {
            'add': False,
            'subtract': False,
            'multiply': False,
            'divide': False
        }

        self.math_function_add.stateChanged.connect(lambda: self.math_operation_function('add', self.math_function_add.isChecked()))
        self.math_function_subtract.stateChanged.connect(lambda: self.math_operation_function('subtract', self.math_function_subtract.isChecked()))
        self.math_function_multiply.stateChanged.connect(lambda: self.math_operation_function('multiply', self.math_function_multiply.isChecked()))
        self.math_function_divide.stateChanged.connect(lambda: self.math_operation_function('divide', self.math_function_divide.isChecked()))

        # Plots
        self.time_domain_data_graphics_view = pg.PlotWidget()
        self.timeLayout = QVBoxLayout(self.time_domain_data_graphics_widget)
        self.timeLayout.addWidget(self.time_domain_data_graphics_view)

        '''
        self.result_graphics_view = pg.PlotWidget()
        self.resultLayout = QVBoxLayout(self.results_graphics_widget)
        self.resultLayout.addWidget(self.result_graphics_view)'''

        self.plots_initialize()

        self.color_dictionary = {
            1: "y",
            2: "b",
            3: "r",
            4: "g"
        }

        self.math_plot = {
            'add': None,
            'subtract': None,
            'multiply': None,
            'divide': None
        }

        # Toolbar

    # --------------------------------------------------- Connection ------------------------------------------------- #
    def connection_populate_visa_addresses(self):  # 사용 가능한 VISA 주소 콤보 상자를 채우는 함수
        try:
            rm = visa.ResourceManager()
            address = rm.list_resources()
            self.connection_combobox.addItems(address)
        except Exception as e:
            QMessageBox.critical(self, "Address Loading Error", str(e))

    def connection_connect_device(self):  # 선택한 VISA 주소로 연결하는 함수
        try:
            visa_address = self.connection_combobox.currentText()
            self.oscilloscope = Oscilloscope()
            self.oscilloscope.connect_device(visa_address)
            if self.oscilloscope.is_connected:
                self.control_set_btn_on()
                self.connection_status_label.setText("Status: Connected")
                QMessageBox.information(self, "Connection", f"Connected to {self.oscilloscope.scope_idn}")
                self.connect_device_name_label.setText(f"Device: {self.oscilloscope.scope_idn}")
            else:
                self.connection_status_label.setText("Status: Not Connected")
        except Exception as e:
            QMessageBox.critical(self, "Connection Error", str(e))

    def connection_disconnect_device(self):
        try:
            if self.oscilloscope.is_connected:
                self.oscilloscope.close()
                self.is_connected = False
                self.control_set_btn_off()
                self.connection_device_name_label.setText("Device:")

        except Exception as e:
            QMessageBox.critical(self, "Disconnect Error", str(e))

    def connection_update_current_time(self):  # 현재 시간을 QLabel에 업데이트하는 함수
        self.current_time = QTime.currentTime().toString("HH:mm:ss")
        self.connection_current_time_label.setText("Current Time: " + str(self.current_time))

    # ----------------------------------------------------- Control -------------------------------------------------- #

    def control_set_btn_on(self):
        try:
            self.control_single.setEnabled(True)
            self.control_run_stop.setEnabled(True)
        except Exception as e:
            QMessageBox.critical(self, "Button Setting Error", str(e))

    def control_set_btn_off(self):
        try:
            self.control_single.setEnabled(False)
            self.control_run_stop.setEnabled(False)
        except Exception as e:
            QMessageBox.critical(self, "Button Setting Error", str(e))

    def control_channel_select(self, channel_num, checked):
        try:
            self.channel_selected[channel_num] = checked
        except Exception as e:
            QMessageBox.critical(self, "Channel Selecting Error", str(e))

    def control_single_aquire_data(self):
        try:
            if not self.is_acquiring:
                if self.oscilloscope:
                    if self.oscilloscope.check_channel_on(self.channel_selected):
                        self.oscilloscope.acquire_data(self.channel_selected)
                        self.plot_time_domain_signals()
                    else:
                        return
        except Exception as e:
            QMessageBox.critical(self, "Data Aquiration Error", str(e))

    def control_run_stop_aquire_data(self):
        try:
            if self.is_acquiring:
                self.control_run_stop_timer.stop()
                self.is_acquiring = False
            else:
                if self.oscilloscope.check_channel_on(self.channel_selected):
                    self.is_acquiring = True
                    self.control_run_stop_timer.start(30)
                else:
                    return
        except Exception as e:
            QMessageBox.critical(self, "Data Aquiration Error", str(e))

    def control_run_stop_aquire_data_loop(self):
        if self.is_acquiring:
            try:
                self.oscilloscope.acquire_data(self.channel_selected)
                self.plot_time_domain_signals()
                print(self.return_time_stamp())
            except Exception as e:
                self.is_acquiring = False
                QMessageBox.critical(self, "Data Aquiration Error", str(e))

    # ------------------------------------------------------ Math ---------------------------------------------------- #
    def math_select_channel(self):
        self.math_source1 = self.math_channel_select_source1_combobox.currentIndex() + 1
        self.math_source2 = self.math_channel_select_source2_combobox.currentIndex() + 1

    def math_operation_function(self, operation_type, checked):
        try:
            if checked:
                if self.oscilloscope:
                    self.math_is_running[operation_type] = True
                    self.math_select_channel()
                    self.plot_math_operation(operation_type)
                else:
                    QMessageBox.critical(self, "Math Error", "Data is not collected")
            else:
                self.plot_math_operation_remove(operation_type)
                self.math_is_running[operation_type] = False

        except Exception as e:
            QMessageBox.critical(self, "Math Error", str(e))

    # ------------------------------------------------------ Plots --------------------------------------------------- #

    def plots_initialize(self):
        """그래프에 기본 제목과 레이블을 설정합니다."""
        # 시간 도메인 그래프 초기 설정
        self.time_domain_data_graphics_view.clear()
        self.time_domain_data_graphics_view.setTitle("Time Domain Signal")
        self.time_domain_data_graphics_view.setLabel('left', 'Voltage (V)')
        self.time_domain_data_graphics_view.setLabel('bottom', 'Time (ms)')
        self.time_domain_data_graphics_view.showGrid(x=True, y=True)

        view_box = self.time_domain_data_graphics_view.getViewBox()
        view_box.setMouseMode(view_box.PanMode)
        # self.time_domain_data_graphics_view.enableAutoRange()
        self.time_domain_data_graphics_view.addLegend()

        '''
        # 결과 그래프 초기 설정
        self.result_graphics_view.setTitle("Result")
        self.result_graphics_view.setLabel('left', '')
        self.result_graphics_view.setLabel('bottom', '')
        self.result_graphics_view.showGrid(x=True, y=True)

        self.result_graphics_view.plot([], [], pen='r')
'''
    def plot_time_domain_signals(self):  # 수집된 신호 플로팅 함수
        try:
            if self.oscilloscope:
                self.time_domain_data_graphics_view.clear()
                for channel in self.channel_selected:
                    if self.channel_selected[channel]:
                        self.time_domain_data_graphics_view.plot(self.oscilloscope.scaled_time[channel],
                                                                 self.oscilloscope.scaled_wave[channel],
                                                                 pen=self.color_dictionary[channel],
                                                                 name=f"Channel{channel}")

                for func in self.math_is_running:
                    if self.math_is_running[func]:
                        self.math_operation_function(func, True)

        except Exception as e:
            QMessageBox.critical(self, "Plotting Error", str(e))

    def plot_math_operation(self, operation_type):
        try:
            if self.oscilloscope and self.oscilloscope.is_channel_on[self.math_source1] and self.oscilloscope.is_channel_on[self.math_source2]:

                # 연산에 따른 결과 계산
                operations = {
                    'add': {'func': np.add, 'label': '+'},
                    'subtract': {'func': np.subtract, 'label': '-'},
                    'multiply': {'func': np.multiply, 'label': '*'},
                    'divide': {'func': np.divide, 'label': '/'}
                }

                if operation_type in operations:
                    result_wave = operations[operation_type]['func'](self.oscilloscope.scaled_wave[self.math_source1], self.oscilloscope.scaled_wave[self.math_source2])
                    plot_name = f"Source{self.math_source1} {operations[operation_type]['label']} Source{self.math_source2}"
                    time_data = self.oscilloscope.scaled_time[self.math_source1]
                    self.math_plot[operation_type] = self.time_domain_data_graphics_view.plot(time_data, result_wave, pen='r', name=plot_name)

        except Exception as e:
            QMessageBox.critical(self, "Plotting Error", str(e))

    def plot_math_operation_remove(self, operation_type):
        try:
            self.time_domain_data_graphics_view.removeItem(self.math_plot[operation_type])
        except Exception as e:
            QMessageBox.critical(self, "Plotting Error", str(e))

    '''def update_measurement_results(self, measurement_type, result):
        """측정 결과를 테이블에 업데이트합니다."""
        row_position = self.resultsTable.rowCount()
        self.resultsTable.insertRow(row_position)
        self.resultsTable.setItem(row_position, 0, QtWidgets.QTableWidgetItem(measurement_type))
        self.resultsTable.setItem(row_position, 1, QtWidgets.QTableWidgetItem(str(result)))'''

    '''
                    self.time_domain_data_graphics_view.setTitle("Time Domain Signal")
                    self.time_domain_data_graphics_view.setLabel('left', 'Voltage (V)')
                    self.time_domain_data_graphics_view.setLabel('bottom', 'Time (ms)')'''
    '''
    use_dbv = self.dBVRadio.isChecked()
    self.fft_processor.perform_fft(self.oscilloscope.tscale, self.oscilloscope.scaled_wave, use_dbv)
    freq_domain, magnitude = self.fft_processor.get_results()

    self.freqPlotWidget.clear()
    self.freqPlotWidget.plot(freq_domain, magnitude, pen='r', name='FFT')
    self.freqPlotWidget.addLegend()
    self.freqPlotWidget.setTitle("Frequency Domain Signal")
    self.freqPlotWidget.setLabel('left', 'dBV RMS (mV)' if use_dbv else 'Linear RMS (mV)')
    self.freqPlotWidget.setLabel('bottom', 'Frequency (Hz)')'''

    # ---------------------------------------------------- Tool bar -------------------------------------------------- #
    def close(self):
        if self.is_connected:
            self.oscilloscope.close()
            self.rm.close()
            self.is_connected = False
            print("Connection closed.")

    # --------------------------------------------------- Time stamp ------------------------------------------------- #
    def return_time_stamp(self):
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = OscilloscopeGUI()
    window.connection_populate_visa_addresses()
    window.setWindowTitle("Oscilloscope GUI")  # 창 제목 설정
    window.show()
    sys.exit(app.exec_())
