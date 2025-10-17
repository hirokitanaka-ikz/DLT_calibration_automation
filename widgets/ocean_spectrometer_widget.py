from PyQt6.QtWidgets import (
    QGroupBox, QPushButton, QLabel, QVBoxLayout,
    QSpinBox, QFormLayout
)
from PyQt6.QtCore import QThread, pyqtSignal
import pyqtgraph as pg
import numpy as np
import seabreeze
seabreeze.use('cseabreeze')
from seabreeze.spectrometers import Spectrometer
import logging
from typing import Optional
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class OceanSpectrometerWidget(QGroupBox):

    def __init__(self, parent=None, polling_interval=0.5):
        super().__init__("Ocean Optics Spectrometer Control", parent)

        self.spectrometer = None
        self.polling_thread = None
        self._polling_interval = polling_interval
        self.wavelength = np.array([])
        self.intensity = np.array([])
        self.dark = np.array([])

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground("w")
        self.plot_widget.setLabel("left", "Intensity", units="counts")
        self.plot_widget.setLabel("bottom", "Wavelength", units="nm")
        self.plot = self.plot_widget.plot(self.wavelength, self.intensity, pen="b")

        # UI Elements
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.toggle_connect)

        self.model_type_label = QLabel("---")
        self.serial_number_label = QLabel("---")

        self.integration_time_spin = QSpinBox()
        self.integration_time_spin.setSuffix(" us")
        self.integration_time_spin.setSingleStep(10)
        self.integration_time_spin.valueChanged.connect(self.set_integration_time)
        self.integration_time_spin.setEnabled(False)

        self.start_btn = QPushButton("Start")
        self.start_btn.clicked.connect(self.start)
        self.start_btn.setEnabled(False)

        self.dark_btn = QPushButton("Capture Dark")
        self.dark_btn.clicked.connect(self.capture_dark)
        self.dark_btn.setEnabled(False)

        self.peak_wavelength_label = QLabel("---")
        self.mean_wavelength_label = QLabel("---")

        # layout
        layout = QVBoxLayout()

        layout.addWidget(self.connect_btn)

        info_form = QFormLayout()
        info_form.addRow("Model Type:", self.model_type_label)
        info_form.addRow("Serial Number:", self.serial_number_label)
        layout.addLayout(info_form)

        parameter_from = QFormLayout()
        parameter_from.addRow("Integration Time:", self.integration_time_spin)
        layout.addLayout(parameter_from)

        layout.addWidget(self.start_btn)
        layout.addWidget(self.dark_btn)

        wavelength_form = QFormLayout()
        wavelength_form.addRow("Peak Wavelength", self.peak_wavelength_label)
        wavelength_form.addRow("Mean Wavelength", self.mean_wavelength_label)
        layout.addLayout(wavelength_form)

        layout.addWidget(self.plot_widget)

        self.setLayout(layout)


    def toggle_connect(self):
        if self.spectrometer is None:
            try:
                self.spectrometer = Spectrometer.from_first_available()
                # self.spectrometer.from_first_available()
                logging.info("Spectrometer connected")
            except (seabreeze.cseabreeze._wrapper.SeaBreezeError, TypeError, TimeoutError, RuntimeError, OSError) as e:
                logging.error(f"Failed to connect spectrometer: {e}")
                return
            try: # initialize spectrometer
                self.model_type_label.setText(self.spectrometer.model)
                self.serial_number_label.setText(self.spectrometer.serial_number)
                min_integration_time, max_integration_time = self.spectrometer.integration_time_micros_limits
                self.integration_time_spin.setRange(min_integration_time, max_integration_time)
                self.connect_btn.setText("Disconnect")
                self.integration_time_spin.setEnabled(True)
                self.start_btn.setEnabled(True)
                self.dark_btn.setEnabled(True)
                self.wavelength = self.spectrometer.wavelengths()
                self.intensity = np.zeros_like(self.wavelength)
                self.dark = np.zeros_like(self.wavelength)
            except (TypeError, TimeoutError, RuntimeError, OSError, Exception) as e:
                logging.error(f"Failed to initialize spectrometer: {e}")
        else:
            if not self.polling_thread is None:
                self.polling_thread.stop()
                self.polling_thread = None
            self.spectrometer = None
            self.model_type_label.setText("---")
            self.serial_number_label.setText("---")
            self.connect_btn.setText("Connect")
            self.integration_time_spin.setEnabled(False)
            self.start_btn.setEnabled(False)
            self.dark_btn.setEnabled(False)
            self.start_btn.setText("Start")
            logging.info("Spectrometer disconnected")
    

    def set_integration_time(self, new_value:int):
        self.spectrometer.integration_time_micros(new_value)
        logging.info(f"Integration Time changed to {new_value} us")
    

    def capture_dark(self):
        if self.spectrometer is None:
            return
        self.dark = self.intensity
        logging.info(f"Capture current spectrum as dark")
    

    def start(self):
        if self.spectrometer is None:
            return
        if self.polling_thread is None:
            self.polling_thread = SpectrometerPollingThread(self.spectrometer, interval=self._polling_interval)
            self.polling_thread.updated.connect(self.update_spectrum)
            self.polling_thread.start()
            self.start_btn.setText("Stop")
        else:
            self.polling_thread.stop()
            self.polling_thread = None
            self.start_btn.setText("Start")
    

    def update_spectrum(self, intensity_array):
        self.intensity = intensity_array
        intensity_corrected = self.intensity - self.dark
        self.plot.setData(self.wavelength, intensity_corrected)
        self.update_wavelength(intensity_corrected)


    def update_wavelength(self, intensity_array):
        peak_wavelength = self.wavelength[np.argmax(intensity_array)]
        mean_wavelength = np.sum(self.wavelength * intensity_array) / np.sum(intensity_array)
        self.peak_wavelength_label.setText(f"{peak_wavelength:.2f} nm")
        self.mean_wavelength_label.setText(f"{mean_wavelength:.2f} nm")

    
    def __del__(self):
        if not self.spectrometer is None:
            self.spectrometer.close()
    

    @property
    def peak_wavelength(self) -> Optional[float]:
        try:
            text = self.peak_wavelength_label.text()
            return float(text[:-len("nm")].strip())
        except (TypeError, Exception) as e:
            # logging.error(f"Failed to read peak wavelength for data export: {e}")
            return None

    
    @property
    def mean_wavelength(self) -> Optional[float]:
        try:
            text = self.mean_wavelength_label.text()
            return float(text[:-len("nm")].strip())
        except (TypeError, Exception) as e:
            # logging.error(f"Failed to read mean wavelength for data export: {e}")
            return None


class SpectrometerPollingThread(QThread):
    
    updated = pyqtSignal(np.ndarray)

    def __init__(self, spectrometer, interval, parent=None):
        super().__init__(parent)
        self.spectrometer = spectrometer
        self.interval = interval
        self._running = True

    
    def run(self):
        while self._running:
            try:
                intensity_array = self.spectrometer.intensities()
                self.updated.emit(intensity_array)
            except Exception as e:
                logging.error(f"Polling spectrum failed: {e}")
            time.sleep(self.interval)


    def stop(self):
        self._running = False
        self.wait()