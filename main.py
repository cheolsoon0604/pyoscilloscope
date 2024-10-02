import sys
from oscilloscope_gui import OscilloscopeGUI
from PyQt5 import QtWidgets


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = OscilloscopeGUI()
    window.show()
    sys.exit(app.exec_())


