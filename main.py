import sys
from src.oscilloscope_gui import OscilloscopeGUI
from PyQt5 import QtWidgets


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = OscilloscopeGUI()
    window.connection_populate_visa_addresses()
    window.setWindowTitle("Oscilloscope GUI")  # 창 제목 설정
    window.show()
    sys.exit(app.exec_())



