from PyQt6.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout, QFormLayout, QSpinBox,
    QPushButton, QMessageBox, QGroupBox, QLabel, QFileDialog
)
from PyQt6.QtCore import QLocale, QTimer
from widgets.ocean_spectrometer_widget import OceanSpectrometerWidget
from widgets.lakeshore_model335_widget import LakeShoreModel335Widget
from widgets.temperature_chart_widget import TemperatureChartWidget

import os
from datetime import datetime
from pathlib import Path
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
ENCODING = "utf-8"


def main():
    app = QApplication([])

    QLocale.setDefault(QLocale.c())

    win = QWidget()
    win.setWindowTitle("DLT Calibration App")
    win.resize(1200, 800)

    polling_interval = 0.5 # sec

    spectrometer_widget = OceanSpectrometerWidget(polling_interval=polling_interval)
    temperature_controller_widget = LakeShoreModel335Widget(polling_interval=polling_interval)
    temperature_chart_widget = TemperatureChartWidget(temperature_controller_widget)
    process_widget = MeasurementProcessWidget(spectrometer_widget, temperature_controller_widget)

    spectrometer_widget.setFixedWidth(600)

    layout = QVBoxLayout()
    sub_layout = QHBoxLayout()
    sub_layout.addWidget(spectrometer_widget)
    subsub_layout = QVBoxLayout()
    subsub_layout.addWidget(temperature_controller_widget)
    subsub_layout.addWidget(temperature_chart_widget)
    sub_layout.addLayout(subsub_layout)
    layout.addLayout(sub_layout)
    layout.addWidget(process_widget)
    
    win.setLayout(layout)
    win.show()

    app.exec()



class MeasurementProcessWidget(QGroupBox):
    def __init__(self, spectrometer_widget, temperature_controller_widget, parent=None):
        super().__init__("Process", parent)
        self.spectrometer_widget = spectrometer_widget
        self.temperature_controller_widget = temperature_controller_widget
        self.timer = None
        self.csv_path = None
        self.spectra_path = None

        # UI elements
        self.path_label = QLabel("----------")
        self.path_btn = QPushButton("Select Save Path")
        self.path_btn.clicked.connect(self.set_save_path)
        self.start_temperature_spin = QSpinBox()
        self.start_temperature_spin.setRange(10, 350)
        self.start_temperature_spin.setSingleStep(5)
        self.start_temperature_spin.setSuffix("K")
        self.start_temperature_spin.setValue(50)
        self.stop_temperature_spin = QSpinBox()
        self.stop_temperature_spin.setRange(10, 350)
        self.stop_temperature_spin.setSingleStep(5)
        self.stop_temperature_spin.setSuffix("K")
        self.stop_temperature_spin.setValue(300)
        self.step_temperature_spin = QSpinBox()
        self.step_temperature_spin.setRange(5, 100)
        self.step_temperature_spin.setSingleStep(1)
        self.step_temperature_spin.setSuffix("K")
        self.step_temperature_spin.setValue(10)
        self.record_interval_spin = QSpinBox()
        self.record_interval_spin.setRange(1, 60)
        self.record_interval_spin.setSingleStep(1)
        self.record_interval_spin.setSuffix("min")
        self.record_interval_spin.setValue(10)
        self.start_btn = QPushButton("Start Process")
        self.start_btn.setStyleSheet("background-color: green; color: white; font-weight:bold")
        self.start_btn.clicked.connect(self.toggle_start)

        # layout
        form = QFormLayout()
        form.addRow("Start Temperature:", self.start_temperature_spin)
        form.addRow("Stop Temperature:", self.stop_temperature_spin)
        form.addRow("Step:", self.step_temperature_spin)
        layout = QVBoxLayout()
        layout1 = QHBoxLayout()
        layout1.addWidget(self.path_btn)
        layout1.addWidget(self.path_label)
        layout2 = QHBoxLayout()
        layout2.addWidget(self.record_interval_spin)
        layout2.addWidget(self.start_btn)
        layout.addLayout(form)
        layout.addLayout(layout1)
        layout.addLayout(layout2)
        self.setLayout(layout)


    def set_save_path(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder to Save Data and Spectra")
        if not folder:
            QMessageBox.warning(self, "Warning", "No folder selected.")
            return
        folder_path = Path(folder)
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"{now}_DLT-calibration"
        self.csv_path = folder_path / f"{default_name}.csv"
        try:
            spectra_dir = folder_path / "spectra"
            spectra_dir.mkdir(parents=True, exist_ok=True)
            self.spectra_path = spectra_dir
            self.path_label.setText(str(self.csv_path))
            logging.info(f"Save paths set: csv={self.csv_path}, spectra_dir={self.spectra_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create spectra folder:\n{e}")
            logging.error(f"Failed to create spectra folder: {e}")
            self.csv_path = None
            self.spectra_path = None


    def toggle_start(self):
        if self.timer is None:
            # start
            self.timer = QTimer(self)
            self.timer.timeout.connect(self.record)
            try:
                self.timer.start(int(self.record_interval_spin.value() * 60 * 1000)) # min -> ms
            except (TypeError, Exception) as e:
                logging.error(f"Failed to start process: {e}")
                self.timer = None
                return
            self.start_btn.setText("Stop Process")
            self.start_btn.setStyleSheet("background-color: red; color: white; font-weight:bold")
            self.record_interval_spin.setEnabled(False)
            QMessageBox.information(self, "Information", "Process Start")
            logging.info("Process started")
        else:
            self.timer.stop()
            self.timer = None
            self.start_btn.setText("Start Process")
            self.start_btn.setStyleSheet("background-color: green; color: white; font-weight:bold")
            self.record_interval_spin.setEnabled(True)
            QMessageBox.information(self, "Information", "Process Stop")
            logging.info("Process stopped")
    

    # connected to timer
    def record(self):
        self.save_spectrum()
        self.write_temperatures()


    def get_spectrum(self):
        pass


    def save_spectrum(self):
        pass


    def get_temperatures(self):
        pass


    def write_temperatures(self):
        pass

    
    def __del__(self):
        try:
            self.timer.stop()
        except Exception:
            pass
        


if __name__ == "__main__":
    main()
