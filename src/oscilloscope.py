import numpy as np
import pyvisa as visa
from PyQt5.QtWidgets import QMessageBox
import time


# Data Acquisition Class
class Oscilloscope:
    def __init__(self):
        super().__init__()
        self.scope_idn = None
        self.is_connected = False
        self.scaled_time = {}
        self.scaled_wave = {}
        self.is_channel_on = {
            1: False,
            2: False,
            3: False,
            4: False
        }

    def connect_device(self, visa_address):
        try:
            self.rm = visa.ResourceManager()
            self.scope = self.rm.open_resource(visa_address)
            self.scope.timeout = 10000  # ms
            self.scope.encoding = 'UTF-8'
            self.scope.read_termination = '\n'
            self.scope.write_termination = None
            self.scope.write('*cls')  # Clear ESR
            self.scope_idn = self.scope.query('*IDN?')  # Identify the oscilloscope
            print(self.scope_idn)
            self.is_connected = True
        except Exception as e:
            QMessageBox.critical(None, "Connection Error", f"Failed to connect to oscilloscope: {str(e)}")

    def configure_io(self, channel):
        try:
            self.scope.write('HEAder 0')
            self.scope.write('DATa:ENCdg SRIBINARY')
            self.scope.write(f'DATa:SOUrce CH{channel}')
            record = int(self.scope.query('HORizontal:RECOrdlength?'))
            self.scope.write('DATa:START 1')
            self.scope.write(f'DATa:STOP {record}')
            self.scope.write('WFMOutpre:BYT_Nr 1')
        except Exception as e:
            QMessageBox.critical(None, "Configuration Error", f"Oscilloscope configuration failed: {str(e)}")

    def check_channel_on(self, channels):
        for channel in range(1, 5):
            self.is_channel_on[channel] = self.scope.query(f":SELECT:CH{channel}?") == "1"
            # print(f"{channel}, want {channels[channel]}, real {self.is_channel_on[channel]}") # for debug

            if channels[channel]:
                if not self.is_channel_on[channel]:
                    QMessageBox.critical(None, "Acquisition Error", f"Check Channel{channel}")
                    return False
        return True

    def acquire_data(self, channels):
        if not self.is_connected:
            QMessageBox.critical(None, "Connection Error", "Data cannot be acquired before the oscilloscope is connected")
            return  # Return if the oscilloscope is not connected
        try:
            # Start acquisition
            for channel in channels:
                if channels[channel]:
                    self.configure_io(channel)
                    self.scope.write('ACQuire:STAte 1')  # Start acquisition
                    self.bin_wave = self.scope.query_binary_values('CURve?', datatype='b', container=np.array)
                    self.retrieve_scaling_factors()
                    self.scale_data(channel)
        except visa.VisaIOError as e:
            QMessageBox.critical(None, "VISA Error", f"Error during acquisition: {str(e)}")
        except Exception as e:
            QMessageBox.critical(None, "Acquisition Error", f"Data acquisition failed: {str(e)}")

    def retrieve_scaling_factors(self):
        try:
            self.tscale = float(self.scope.query('WFMoutpre:XINcr?'))
            self.tstart = float(self.scope.query('WFMoutpre:XZEro?'))
            self.vscale = float(self.scope.query('WFMoutpre:YMUlt?'))
            self.vzero = float(self.scope.query('WFMoutpre:YZEro?'))
            self.voff = float(self.scope.query('WFMoutpre:YOFf?'))
        except visa.VisaIOError as e:
            QMessageBox.critical(None, "Scaling Error", f"Error retrieving scaling factors: {str(e)}")
        except Exception as e:
            QMessageBox.critical(None, "Scaling Error", f"Failed to retrieve scaling factors: {str(e)}")

    def scale_data(self, channel):
        try:
            record = int(self.scope.query('HORizontal:RECOrdlength?'))
            total_time = self.tscale * record
            self.tstop = self.tstart + total_time
            self.scaled_time[channel] = np.linspace(self.tstart*1000, self.tstop*1000, num=record, endpoint=False)
            unscaled_wave = np.array(self.bin_wave, dtype='double')
            self.scaled_wave[channel] = (unscaled_wave - self.voff) * self.vscale + self.vzero
        except Exception as e:
            QMessageBox.critical(None, "Scaling Error", f"Data scaling failed: {str(e)}")


    def close(self):
        self.scope.close()
        self.is_connected = False
