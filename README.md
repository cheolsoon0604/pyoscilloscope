# PyOscilloscope 
Oscilloscope Control and Data Analysis Application

※ This project is still on development ※  
※ 아직 개발중인 프로젝트 입니다. ※

Python based GUI program for Tektronix MDO4024C Oscilloscope

## Table of Contents

- [Introduction](#Introduction)
- [Features](#Features)
- [Requirements](#Requirements)
- [Installation](#Installation)
- [Usage](#Usage)

## Introduction

The **Oscilloscope Control and Data Analysis Application** is a Python-based GUI tool designed to interface with oscilloscopes via VISA (Virtual Instrument Software Architecture). It allows users to connect to their oscilloscope, acquire waveform data from Channel 1, perform Fast Fourier Transform (FFT) analysis, and visualize both time-domain and frequency-domain signals. The application leverages PyQt5 for the user interface, PyVISA for instrument communication, and Matplotlib for plotting.

## Features

Something will be written here

## Requirements

Before installing and running the application, ensure that the following software and hardware requirements are met:

### Hardware Requirements

- **Oscilloscope**: Tektronix MDO4024C Oscilloscope

### Software Requirements

- **OS**: Windows10
- **Python**: Version 3.6+ (tested: 3.11)
- **Packages**:
  - numpy (1.26.4)
  - matplotlib (3.9.0)
  - PyVISA (1.14.1)
  - PyQt5 (5.15.10)
- **VISA Backend**: NI-VISA (2024 Q3)

NI-VISA can be downloaded from [National Instruments Corporation](https://www.ni.com/en/support/downloads/drivers/download.ni-visa.html?srsltid=AfmBOoqtvk6fcF6_a1q-t-BRAPNtnBMvJC90ikrsAYKw32quuOrMsXpn)
  
## Installation

Follow these steps to set up the application on your system:

1. **Clone the Repository**

        git clone https://github.com/yourusername/oscilloscope-app.git
        cd oscilloscope-app

2. Set Up a Virtual Environment (Optional but Recommended)

        python -m venv venv
        source venv/bin/activate  # On Windows: venv\Scripts\activate
    
3. Install Required Python Packages

       pip install -r requirements.txt

    *If you don't have a requirements.txt file, install packages individually:*

        pip install PyQt5 pyvisa numpy matplotlib

4. Ensure VISA Backend is Installed

   - NI-VISA: Download and install from National Instruments.
   - Alternative Backends: If not using NI-VISA, ensure that an appropriate PyVISA backend (like pyvisa-py) is installed.

## Usage
1. Run the Application

        python main.py

   Replace your_script.py with the actual name of your Python script containing the provided code.

2. Connect to the Oscilloscope

   - Upon launching, the application will list available VISA addresses in a dropdown menu.
   - Select the appropriate VISA address corresponding to your oscilloscope.
   - Click the Connect button to establish a connection. A status message will confirm the connection.

3. Acquire Data

   - After a successful connection, the Acquire Data button becomes enabled.
   - Click it to collect waveform data from Channel 1. A confirmation message will appear upon successful acquisition.

4. Perform FFT

   - Once data is acquired, the FFT button becomes enabled.
   - Click it to perform Fast Fourier Transform on the collected data. A confirmation message will indicate success.

5. Plot Signals

   - With both data acquisition and FFT completed, the Plot Signals button is enabled.
   - Click it to visualize the time-domain signal and its FFT result in separate plots.

6. Quit Application

   - Click the Quit button to safely close the connection and exit the application.
