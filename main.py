import sys
import numpy as np
import pyvisa as visa
import matplotlib.pyplot as plt
from matplotlib import font_manager, rc
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QMessageBox

# 폰트 경로 설정 (NanumGothic 폰트를 사용하는 경우)
font_path = "NanumGothic.ttf"  # 적절한 경로로 변경
font_prop = font_manager.FontProperties(fname=font_path)

plt.rc('font', family=font_prop.get_name())

class Oscilloscope:
    def __init__(self, visa_address):
        try:
            # VISA 리소스 관리자 초기화 및 오실로스코프 리소스 열기
            self.rm = visa.ResourceManager()
            self.scope = self.rm.open_resource(visa_address)
            self.scope.timeout = 10000  # ms
            self.scope.encoding = 'UTF-8'
            self.scope.read_termination = '\n'
            self.scope.write_termination = None
            self.scope.write('*cls')  # ESR 클리어
            print(self.scope.query('*idn?'))  # 오실로스코프 식별 출력
            self.is_connected = True

            # 오실로스코프 설정 구성
            self.configure_io()
        except Exception as e:
            QMessageBox.critical(None, "연결 오류", f"오실로스코프 연결 실패: {str(e)}")
            self.is_connected = False

    def configure_io(self):
        try:
            # IO 설정
            self.scope.write('header 0')
            self.scope.write('data:encdg SRIBINARY')
            self.scope.write('data:source CH1')  # 채널
            record = int(self.scope.query('horizontal:recordlength?'))
            self.scope.write('data:start 1')  # 첫 샘플
            self.scope.write(f'data:stop {record}')  # 마지막 샘플
            self.scope.write('wfmoutpre:byt_n 1')  # 1 바이트 당 샘플
        except Exception as e:
            QMessageBox.critical(None, "설정 오류", f"오실로스코프 설정 실패: {str(e)}")

    def acquire_data(self):
        if not self.is_connected:
            QMessageBox.warning(None, "경고", "오실로스코프에 연결되지 않았습니다.")
            return
        try:
            # 수집 설정
            self.scope.write('acquire:state 0')  # 정지
            self.scope.write('acquire:state 1')  # 실행

            # 데이터 쿼리
            self.bin_wave = self.scope.query_binary_values('curve?', datatype='b', container=np.array)
            self.retrieve_scaling_factors()

            # 데이터 스케일링
            self.scale_data()

            QMessageBox.information(None, "데이터 수집", "데이터가 성공적으로 수집되었습니다.")
        except Exception as e:
            QMessageBox.critical(None, "데이터 오류", f"데이터 수집 실패: {str(e)}")

    def retrieve_scaling_factors(self):
        try:
            # 스케일링 팩터 가져오기
            self.tscale = float(self.scope.query('wfmoutpre:xincr?'))
            self.tstart = float(self.scope.query('wfmoutpre:xzero?'))
            self.vscale = float(self.scope.query('wfmoutpre:ymult?'))  # 볼트 / 레벨
            self.voff = float(self.scope.query('wfmoutpre:yzero?'))  # 기준 전압
            self.vpos = float(self.scope.query('wfmoutpre:yoff?'))  # 기준 위치 (레벨)
        except Exception as e:
            QMessageBox.critical(None, "스케일링 오류", f"스케일링 팩터 가져오기 실패: {str(e)}")

    def scale_data(self):
        try:
            # 스케일링된 벡터 생성
            record = int(self.scope.query('horizontal:recordlength?'))
            total_time = self.tscale * record
            self.tstop = self.tstart + total_time
            self.scaled_time = np.linspace(self.tstart, self.tstop, num=record, endpoint=False)
            unscaled_wave = np.array(self.bin_wave, dtype='double')  # 데이터 타입 변환
            self.scaled_wave = (unscaled_wave - self.vpos) * self.vscale + self.voff
        except Exception as e:
            QMessageBox.critical(None, "스케일링 오류", f"데이터 스케일링 실패: {str(e)}")

    def perform_fft(self):
        if not hasattr(self, 'scaled_wave'):
            QMessageBox.warning(None, "경고", "먼저 데이터를 수집하세요.")
            return
        try:
            # FFT 수행
            record = int(self.scope.query('horizontal:recordlength?'))
            self.fft_result = np.fft.fft(self.scaled_wave)
            self.fft_freq = np.fft.fftfreq(record, d=self.tscale)

            # 양수 주파수와 해당 FFT 값을 유지
            self.positive_freqs = self.fft_freq[:record // 2]
            self.magnitude = np.abs(self.fft_result)[:record // 2]

            QMessageBox.information(None, "FFT", "FFT가 성공적으로 수행되었습니다.")
        except Exception as e:
            QMessageBox.critical(None, "FFT 오류", f"FFT 수행 실패: {str(e)}")

    def plot_signals(self):
        if not hasattr(self, 'scaled_wave') or not hasattr(self, 'positive_freqs'):
            QMessageBox.warning(None, "경고", "먼저 데이터를 수집하고 FFT를 수행하세요.")
            return
        try:
            # 신호 플로팅
            plt.figure(figsize=(10, 6))

            plt.subplot(2, 1, 1)
            plt.plot(self.scaled_time, self.scaled_wave)
            plt.title('Collected Signal')
            plt.xlabel('Time (s)')
            plt.ylabel('Voltage (V)')

            plt.subplot(2, 1, 2)
            plt.plot(self.positive_freqs, self.magnitude)
            plt.title('FFT Result')
            plt.xlabel('Frequency (Hz)')
            plt.ylabel('Linear RMS (V)')
            plt.tight_layout()
            plt.show()
        except Exception as e:
            QMessageBox.critical(None, "플로팅 오류", f"신호 플로팅 실패: {str(e)}")

    def close(self):
        if self.is_connected:
            self.scope.close()
            self.rm.close()
            self.is_connected = False
            print("연결 종료.")
        super().close()

class OscilloscopeGUI(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('oscilloscope.ui', self)  # UI 파일 로드
        self.oscilloscope = None

        # 버튼 클릭 이벤트 연결
        self.connectButton.clicked.connect(self.connect_device)
        self.acquireButton.clicked.connect(self.acquire_data)
        self.fftButton.clicked.connect(self.perform_fft)
        self.plotButton.clicked.connect(self.plot_signals)
        self.quitButton.clicked.connect(self.close_application)

        # 초기 버튼 상태 설정
        self.acquireButton.setEnabled(False)
        self.fftButton.setEnabled(False)
        self.plotButton.setEnabled(False)

    def populate_visa_addresses(self):
        # VISA 주소 목록을 가져와서 콤보 박스에 추가
        try:
            rm = visa.ResourceManager()
            addresses = rm.list_resources()
            self.visaAddressCombo.addItems(addresses)
        except Exception as e:
            QMessageBox.critical(self, "주소 로딩 오류", str(e))

    def connect_device(self):
        try:
            visa_address = self.visaAddressCombo.currentText()  # 콤보 박스에서 선택한 VISA 주소
            self.oscilloscope = Oscilloscope(visa_address)
            if self.oscilloscope.is_connected:
                self.acquireButton.setEnabled(True)
                self.fftButton.setEnabled(True)
                self.plotButton.setEnabled(True)
                self.statusLabel.setText("상태: 연결됨")
                QMessageBox.information(self, "연결", "오실로스코프에 연결되었습니다.")
            else:
                self.statusLabel.setText("상태: 연결되지 않음")
        except Exception as e:
            QMessageBox.critical(self, "연결 오류", str(e))

    def acquire_data(self):
        try:
            if self.oscilloscope:
                self.oscilloscope.acquire_data()
        except Exception as e:
            QMessageBox.critical(self, "데이터 오류", str(e))

    def perform_fft(self):
        try:
            if self.oscilloscope:
                self.oscilloscope.perform_fft()
        except Exception as e:
            QMessageBox.critical(self, "FFT 오류", str(e))

    def plot_signals(self):
        try:
            if self.oscilloscope:
                self.oscilloscope.plot_signals()
        except Exception as e:
            QMessageBox.critical(self, "플로팅 오류", str(e))

    def close_application(self):
        if self.oscilloscope:
            self.oscilloscope.close()
        QtWidgets.qApp.quit()

    def showEvent(self, event):
        super().showEvent(event)
        self.populate_visa_addresses()  # 창이 처음 표시될 때 VISA 주소 목록을 채움


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = OscilloscopeGUI()
    window.show()
    sys.exit(app.exec_())
