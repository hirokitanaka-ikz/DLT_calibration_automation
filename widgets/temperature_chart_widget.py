from PyQt6.QtWidgets import (
    QGroupBox, QPushButton, QFileDialog, QMessageBox, QVBoxLayout, QFormLayout, QSpinBox
)
from PyQt6.QtCore import QTimer
import os
import pyqtgraph as pg
from pathlib import Path
import logging
from datetime import datetime
import csv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

ENCODING = "utf-8"


def default_filename() -> str:
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{now}_temperature"


class TemperatureChartWidget(QGroupBox):
    def __init__(self, temperature_control_widget, parent=None):
        super().__init__("Temperature Chart", parent)
        self.temperature_control_widget = temperature_control_widget
        self.record_timer = None
        self.data_dict = None

        # UI elements
        self.record_interval_spin = QSpinBox()
        self.record_interval_spin.setRange(1, 600) # sec
        self.record_interval_spin.setSingleStep(1)
        self.record_interval_spin.setSuffix("sec")
        self.record_btn = QPushButton("Start Record")
        self.record_btn.clicked.connect(self.toggle_record)

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground("w")
        self.plot_widget.showGrid(x=True, y=True)
        self.plot_widget.setLabel("left", "T", units="K")
        self.plot_widget.setLabel("bottom", "Time", units="min")

        # layout
        layout = QVBoxLayout()
        record_form = QFormLayout()
        record_form.addRow("Record Interval", self.record_interval_spin)
        record_form.addRow("", self.record_btn)
        layout.addLayout(record_form)
        layout.addWidget(self.plot_widget)
        self.setLayout(layout)


    def initialize_chart(self):
        self.plot_widget.clear()
        self.t_data = []
        self.Ta_data = []
        self.Tb_data = []
        self.start_timestamp = None
        self.plot_Ta = self.plot_widget.plot(self.t_data, self.Ta_data, pen="r", name="Temperature A")
        self.plot_Tb = self.plot_widget.plot(self.t_data, self.Tb_data, pen="b", name="Temperature B")
        self.plot_widget.enableAutoRange()
    

    def __del__(self):
        try:
            self.record_timer.stop()
        except Exception:
            pass
    

    def update_data(self) -> None:
        try:
            self.data_dict = self.temperature_control_widget.get_data_dict()
        except Exception as e:
            logging.error(f"Failed to load data from controller widget: {e}")
            return
        self.update_chart()
        self.write_data()
    

    def update_chart(self) -> None:
        try:
            timestamp = datetime.fromisoformat(self.data_dict["timestamp"])
            Ta = self.data_dict["temperature_A"]
            Tb = self.data_dict["temperature_B"]
            if self.start_timestamp is None:
                self.start_timestamp = timestamp
            elapsed_min = (timestamp - self.start_timestamp).total_seconds() / 60.0
            self.t_data.append(elapsed_min)
            self.Ta_data.append(Ta)
            self.Tb_data.append(Tb)
            self.plot_Ta.setData(self.t_data, self.Ta_data)
            self.plot_Tb.setData(self.t_data, self.Tb_data)
            # print(self.t_data, self.Ta_data, self.Tb_data)
        except Exception as e:
            logging.error(f"Fail to plot data: {e}")
            return
    

    def write_data(self) -> None:
        try:
            # write header if file not existing
            if not os.path.exists(self.csv_path):
                with open(self.csv_path, "w", newline="", encoding=ENCODING) as f_csv:
                    writer = csv.DictWriter(f_csv, fieldnames=self.data_dict.keys())
                    writer.writeheader()
            # add data
            with open(self.csv_path, "a", newline="", encoding=ENCODING) as f_csv:
                writer = csv.DictWriter(f_csv, fieldnames=self.data_dict.keys())
                writer.writerow(self.data_dict)
        except Exception as e:
            logging.error(f"Fail to write data to csv: {e}")
            return


    def toggle_record(self):
        if self.record_timer is None:
            folder = QFileDialog.getExistingDirectory(self, "Select Folder to Save Data")
            if not folder:
                QMessageBox.warning(self, "Warning", "No folder selected.")
                return
            folder_path = Path(folder)
            default_name = default_filename()
            self.csv_path = folder_path / f"{default_name}.csv"
            # plot and write first data
            self.initialize_chart()
            self.update_chart()
            self.write_data()
            self.record_timer = QTimer(self)
            self.record_timer.timeout.connect(self.update_data)
            try:
                self.record_timer.start(int(self.record_interval_spin.value() * 1000)) # sec -> millisec
            except TypeError as e:
                logging.error(f"Failed to start timer: {e}")
                self.record_timer = None
                return
            self.record_btn.setText("Stop Record")
            QMessageBox.information(self, "Recording Start", f"save path: \n{self.csv_path}\nRecording start")
            logging.info("Data recording started")
        else:
            self.record_timer.stop()
            self.record_timer = None
            self.start_timestamp = None
            QMessageBox.information(self, "Recording Stop", f"save path: \n{self.csv_path}\nRecording stop")
            logging.info("Data recording stopped")
            self.record_btn.setText("Start Record")