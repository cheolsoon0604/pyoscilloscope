import numpy as np
import pyvisa as visa
from PyQt5.QtWidgets import QMessageBox
import time

# Data Acquisition Class
class Oscilloscope:
    def __init__(self, visa_address):
        try:
            self.rm = visa.ResourceManager()
            self.scope = self.rm.open_resource(visa_address)
            self.scope.timeout = 10000  # ms
            self.scope.encoding = 'UTF-8'
            self.scope.read_termination = '\n'
            self.scope.write_termination = None
            self.scope.write('*cls')  # Clear ESR
            print(self.scope.query('*idn?'))  # Identify the oscilloscope
            self.is_connected = True

            self.configure_io()
        except Exception as e:
            QMessageBox.critical(None, "Connection Error", f"Failed to connect to oscilloscope: {str(e)}")
            self.is_connected = False

    def configure_io(self):
        try:
            self.scope.write('header 0')
            self.scope.write('data:encdg SRIBINARY')
            self.scope.write('data:source CH1')
            record = int(self.scope.query('horizontal:recordlength?'))
            self.scope.write('data:start 1')
            self.scope.write(f'data:stop {record}')
            self.scope.write('wfmoutpre:byt_n 1')
        except Exception as e:
            QMessageBox.critical(None, "Configuration Error", f"Oscilloscope configuration failed: {str(e)}")

    def acquire_data(self):
        if not self.is_connected:
            return  # Return if the oscilloscope is not connected

        try:
            # Start acquisition
            self.scope.write('acquire:state 1')  # Start acquisition
            self.bin_wave = self.scope.query_binary_values('curve?', datatype='b', container=np.array)
            self.retrieve_scaling_factors()
            self.scale_data()
        except visa.VisaIOError as e:
            QMessageBox.critical(None, "VISA Error", f"Error during acquisition: {str(e)}")
        except Exception as e:
            QMessageBox.critical(None, "Acquisition Error", f"Data acquisition failed: {str(e)}")

    def retrieve_scaling_factors(self):
        try:
            self.tscale = float(self.scope.query('wfmoutpre:xincr?'))
            self.tstart = float(self.scope.query('wfmoutpre:xzero?'))
            self.vscale = float(self.scope.query('wfmoutpre:ymult?'))
            self.voff = float(self.scope.query('wfmoutpre:yzero?'))
            self.vpos = float(self.scope.query('wfmoutpre:yoff?'))
        except visa.VisaIOError as e:
            QMessageBox.critical(None, "Scaling Error", f"Error retrieving scaling factors: {str(e)}")
        except Exception as e:
            QMessageBox.critical(None, "Scaling Error", f"Failed to retrieve scaling factors: {str(e)}")

    def scale_data(self):
        try:
            record = int(self.scope.query('horizontal:recordlength?'))
            total_time = self.tscale * record
            self.tstop = self.tstart + total_time
            self.scaled_time = np.linspace(self.tstart, self.tstop, num=record, endpoint=False)
            unscaled_wave = np.array(self.bin_wave, dtype='double')
            self.scaled_wave = (unscaled_wave - self.vpos) * self.vscale + self.voff
        except Exception as e:
            QMessageBox.critical(None, "Scaling Error", f"Data scaling failed: {str(e)}")

    def close(self):
        if self.is_connected:
            self.scope.close()
            self.rm.close()
            self.is_connected = False
            print("Connection closed.")

    def run_acquisition_loop(self, interval=0.1):
        """ Continuously acquire data in a loop. """
        while self.is_connected:
            self.acquire_data()
            time.sleep(interval)  # Pause for a specified interval before the next acquisition
