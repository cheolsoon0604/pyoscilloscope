import numpy as np
from PyQt5.QtWidgets import QMessageBox


class FFTProcessor:
    def __init__(self):
        self.fft_result = None
        self.positive_freqs = None
        self.magnitude = None

    def perform_fft(self, time_scale, wave_data, use_dBV=False):
        """FFT를 수행하고 결과를 저장합니다.

        Parameters:
            time_scale: 데이터의 시간 간격
            wave_data: 시간 도메인에서의 데이터
            use_dBV: dBV RMS를 사용할지 여부
        """
        try:
            record = len(wave_data)

            # FFT 계산
            self.fft_result = np.fft.fft(wave_data)
            self.fft_freq = np.fft.fftfreq(record, d=time_scale)

            # 양의 주파수와 크기 계산
            self.positive_freqs = self.fft_freq[:record // 2]

            if use_dBV:
                # dBV RMS 계산
                self.magnitude = 20 * np.log10(np.abs(self.fft_result/10)[:record // 2])
            else:
                # Linear RMS 계산
                self.magnitude = np.abs(self.fft_result/10)[:record // 2]  # FFT의 크기

        except Exception as e:
            QMessageBox.critical(None, "FFT Error", f"FFT computation failed: {str(e)}")

    def get_results(self):
        """계산된 FFT 결과를 반환합니다."""
        if self.positive_freqs is None or self.magnitude is None:
            raise ValueError("FFT has not been performed yet.")
        return self.positive_freqs, self.magnitude
