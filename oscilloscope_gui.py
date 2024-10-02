import sys
import pyvisa as visa
import numpy as np
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QMessageBox, QVBoxLayout
from PyQt5.QtCore import QTimer, QTime, Qt
from oscilloscope import Oscilloscope
from fft_processor import FFTProcessor
import pyqtgraph as pg

class OscilloscopeGUI(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('oscilloscope.ui', self)
        self.oscilloscope = None
        self.fft_processor = FFTProcessor()  # FFTProcessor 객체 초기화

        # UI 요소 설정
        self.connectButton.clicked.connect(self.connect_device)
        self.acquireButton.clicked.connect(self.toggle_acquire_data)
        self.quitButton.clicked.connect(self.close_application)

        # 플롯을 PyQtGraph로 설정
        self.timePlotWidget = pg.PlotWidget()
        self.freqPlotWidget = pg.PlotWidget()

        self.timeLayout = QVBoxLayout(self.timeDomainPlot)
        self.freqLayout = QVBoxLayout(self.frequencyDomainPlot)

        self.timeLayout.addWidget(self.timePlotWidget)
        self.freqLayout.addWidget(self.freqPlotWidget)

        # 버튼 비활성화 초기화
        self.acquireButton.setEnabled(False)

        # 토글 상태 변수
        self.is_acquiring = False

        # QTimer 초기화
        self.timer = QTimer()
        self.timer.timeout.connect(self.start_acquisition_loop)

        # 시간 업데이트용 QTimer
        self.timeUpdateTimer = QTimer()
        self.timeUpdateTimer.timeout.connect(self.update_current_time)
        self.timeUpdateTimer.start(1000)  # 1초마다 시간 업데이트

    def update_current_time(self):
        """현재 시간을 QLabel에 업데이트합니다."""
        current_time = QTime.currentTime().toString("HH:mm:ss")
        self.currentTimeLabel.setText(current_time)

    def populate_visa_addresses(self):
        """사용 가능한 리소스로 VISA 주소 콤보 상자를 채웁니다."""
        try:
            rm = visa.ResourceManager()
            addresses = rm.list_resources()
            self.visaAddressCombo.addItems(addresses)
        except Exception as e:
            QMessageBox.critical(self, "주소 로딩 오류", str(e))

    def connect_device(self):
        """선택한 VISA 주소를 사용하여 오실로스코프에 연결합니다."""
        try:
            visa_address = self.visaAddressCombo.currentText()
            self.oscilloscope = Oscilloscope(visa_address)
            if self.oscilloscope.is_connected:
                self.acquireButton.setEnabled(True)
                self.statusLabel.setText("상태: 연결됨")
                QMessageBox.information(self, "연결", "오실로스코프에 연결되었습니다.")
            else:
                self.statusLabel.setText("상태: 연결되지 않음")
        except Exception as e:
            QMessageBox.critical(self, "연결 오류", str(e))

    def toggle_acquire_data(self):
        """오실로스코프에서 데이터 수집을 토글합니다."""
        if not self.is_acquiring:
            # 데이터 수집 시작
            if self.oscilloscope:
                self.statusLabel.setText("상태: 데이터 수집 중...")
                self.acquireButton.setText("수집 중지")
                self.is_acquiring = True
                self.timer.start(1000)  # 1초마다 데이터 수집을 시작합니다.
        else:
            # 데이터 수집 정지
            self.statusLabel.setText("상태: 수집 중지")
            self.acquireButton.setText("데이터 수집 시작")
            self.is_acquiring = False
            self.timer.stop()  # 타이머 정지

    def start_acquisition_loop(self):
        """데이터 수집을 위한 루프를 시작합니다."""
        if self.is_acquiring:
            try:
                self.oscilloscope.acquire_data()  # 데이터 수집
                self.plot_signals()  # 플로팅
            except Exception as e:
                QMessageBox.critical(self, "수집 오류", str(e))

    def plot_signals(self):
        """수집된 신호와 FFT 결과를 플로팅합니다."""
        try:
            if self.oscilloscope:
                # 시간 영역 신호 플로팅
                self.timePlotWidget.clear()
                self.timePlotWidget.plot(self.oscilloscope.scaled_time, self.oscilloscope.scaled_wave, pen='y')
                self.timePlotWidget.setTitle("Time Domain Signal")
                self.timePlotWidget.setLabel('left', 'Voltage (V)')
                self.timePlotWidget.setLabel('bottom', 'Time (s)')

                # RMS 선택
                use_dBV = self.dBVRadio.isChecked()  # dBV RMS가 선택된 경우 True

                # 주파수 영역 신호 플로팅
                self.fft_processor.perform_fft(self.oscilloscope.tscale, self.oscilloscope.scaled_wave,
                                               use_dBV)  # FFT 계산
                freq_domain, magnitude = self.fft_processor.get_results()  # 결과 가져오기

                self.freqPlotWidget.clear()
                self.freqPlotWidget.plot(freq_domain, magnitude, pen='r')
                self.freqPlotWidget.setTitle("Frequency Domain Signal")
                if use_dBV:
                    self.freqPlotWidget.setLabel('left', 'Magnitude (dBV RMS)')
                else:
                    self.freqPlotWidget.setLabel('left', 'Magnitude (Linear RMS)')
                self.freqPlotWidget.setLabel('bottom', 'Frequency (Hz)')
        except Exception as e:
            QMessageBox.critical(self, "플로팅 오류", str(e))

    def close_application(self):
        """어플리케이션 종료 시 호출됩니다."""
        if self.oscilloscope:
            self.oscilloscope.close()
        self.close()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = OscilloscopeGUI()
    window.populate_visa_addresses()  # VISA 주소 로드
    window.show()
    sys.exit(app.exec_())
