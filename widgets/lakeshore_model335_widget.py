from PyQt6.QtWidgets import (
    QGroupBox, QPushButton, QLabel, QComboBox, QVBoxLayout, QFormLayout,
    QSpinBox, QDoubleSpinBox, QMessageBox, QWidget
)
from PyQt6.QtCore import pyqtSignal
from lakeshore import Model335
import serial.tools.list_ports
from widgets.base_polling_thread import BasePollingThread
from datetime import datetime
from collections import deque
import numpy as np
import logging

lake_shore_log = logging.getLogger("lakeshore")
lake_shore_log.setLevel(logging.WARNING)


logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')
BAUD_RATE = 57600 # fixed baud rate for Model 335


class LakeShoreModel335Widget(QGroupBox):

    def __init__(self, parent=None, polling_interval=0.5):
        super().__init__("Lake Shore Model335 Control", parent)

        self.controller = None
        self.polling_thread = None
        self._polling_interval = polling_interval
        self._last_temp_A = 0.0
        self._last_temp_B = 0.0
        self._buffer_A = deque(maxlen=60)
        self._buffer_B = deque(maxlen=60)

        # UI Elements
        self.scan_port_btn = QPushButton("Scan COM Port")
        self.scan_port_btn.clicked.connect(self.scan_com_port)
        self.ports_combo = QComboBox()
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.toggle_connect)
        self.serial_number_label = QLabel("Serial Number: -----")

        self.temp_A_label = QLabel("Temperature A: ----- K")
        self.temp_B_label = QLabel("Temperature B: ----- K")
        self.heater_output1_label = QLabel("Heater Output 1: -----%")
        self.heater_output2_label = QLabel("Heater Output 2: -----%")

        self.heater_channel_spin = QSpinBox()
        self.heater_channel_spin.setRange(1, 2)
        self.heater_range_combo = QComboBox()
        self.heater_range_combo.addItems(["HIGH", "MEDIUM", "LOW"])
        self.heater_range_combo.setCurrentText("HIGH")
        self.heater_target_spin = QDoubleSpinBox()
        self.heater_target_spin.setRange(0.0, 350.0)
        self.heater_target_spin.setValue(300.0)
        self.heater_target_spin.setDecimals(2)
        self.heater_target_spin.setSingleStep(5.0)
        self.heater_target_spin.setSuffix(" K")
        self.heater_target_spin.editingFinished.connect(self.change_target)
        self.control_status_label = QLabel("----")

        self.heater_on_btn = QPushButton("Heater ON")
        self.heater_on_btn.clicked.connect(self.heater_on)
        self.heater_off_btn = QPushButton("ALL HEATER OFF")
        self.heater_off_btn.clicked.connect(self.heater_off)

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.scan_port_btn)
        layout.addWidget(self.ports_combo)
        layout.addWidget(self.connect_btn)
        layout.addWidget(self.serial_number_label)
        layout.addWidget(self.temp_A_label)
        layout.addWidget(self.temp_B_label)
        layout.addWidget(self.heater_output1_label)
        layout.addWidget(self.heater_output2_label)
        form_heater_output = QFormLayout()
        form_heater_output.addRow("Target Temperature:", self.heater_target_spin)
        form_heater_output.addRow("Heater Output Channel:", self.heater_channel_spin)
        form_heater_output.addRow("Heater Output Range", self.heater_range_combo)
        form_heater_output.addRow("Temperature Stabilized:", self.control_status_label)
        layout.addLayout(form_heater_output)
        layout.addWidget(self.heater_on_btn)
        layout.addWidget(self.heater_off_btn)
        self.setLayout(layout)
    

    def scan_com_port(self):
        self.ports_combo.clear()
        ports = serial.tools.list_ports.comports()
        for port in ports:
            self.ports_combo.addItem(f"{port.description}", port.device)
    

    def toggle_connect(self):
        if self.controller is None:
            # connect
            port = self.ports_combo.currentData()
            if port is None:
                QMessageBox.warning(self, "Warning", "Please selet a COM port.")
                return
            try:
                self.controller = Model335(com_port=port, baud_rate=BAUD_RATE)
            except Exception as e:
                logging.error(f"Failed to create Lake Shore Model 335 instance: {e}")
                return
            try:
                self.scan_port_btn.setEnabled(False)
                self.ports_combo.setEnabled(False)
                self.connect_btn.setText("Disconnect")
                self.serial_number_label.setText(f"Serial Number: {self.controller.query("*IDN?")}")
            except Exception as e:
                logging.error(e)
                return
            # start polling
            try:
                self.polling_thread = LakeShoreModel335PollingThread(self.controller, self._polling_interval, parent=self)
                self.polling_thread.updated.connect(self.update_values_display)
                self.polling_thread.start()
            except Exception as e:
                logging.error(f"Failed to start polling thread: {e}")
                return
        else:
            # disconnect
            if self.polling_thread is not None:
                self.polling_thread.stop()
                self.polling_thread = None
            try:
                self.controller.disconnect_usb()
                self.controller = None
            except Exception as e:
                logging.error(e)
                return
            self.scan_port_btn.setEnabled(True)
            self.ports_combo.setEnabled(True)
            self.connect_btn.setText("Connect")
    

    def heater_on(self):
        output_channel = self.heater_channel_spin.value()
        range = self.heater_range_combo.currentText()
        if range == "HIGH":
            self.controller.set_heater_range(output=output_channel, heater_range=self.controller.HeaterRange.HIGH)
        elif range == "MEDIUM":
            self.controller.set_heater_range(output=output_channel, heater_range=self.controller.HeaterRange.MEDIUM)
        elif range == "LOW":
            self.controller.set_heater_range(output=output_channel, heater_range=self.controller.HeaterRange.LOW)
    

    def heater_off(self):
        self.controller.all_heaters_off()
    

    def change_target(self):
        target_temperature = self.heater_target_spin.value()
        channel = self.heater_channel_spin.value()
        self.controller.set_control_setpoint(output=channel, value=target_temperature)
    

    def update_values_display(self, data: dict):
        temperatureA = float(data.get("temperature_A", float("nan")))
        temperatureB = float(data.get("temperature_B", float("nan")))
        heater_output_1 = data["heater_output_1"]
        heater_output_2 = data["heater_output_2"]
        self.temp_A_label.setText(f"Temperature A: {temperatureA:.2f} K")
        self.temp_B_label.setText(f"Temperature B: {temperatureB:.2f} K")
        self.heater_output1_label.setText(f"Heater Output: {heater_output_1}%")
        self.heater_output2_label.setText(f"Heater Output: {heater_output_2}%")
        self._last_temp_A = temperatureA
        self._last_temp_B = temperatureB
        self._buffer_A.append(temperatureA)
        self._buffer_B.append(temperatureB)
        self.control_status_label.setText(str(self.is_temperature_stable()))
        
    

    @property
    def temperatures(self) -> tuple[float, float]:
        return self._last_temp_A, self._last_temp_B


    def get_data_dict(self) -> dict:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        temperatures = self.temperatures
        return {"timestamp": timestamp, "temperature_A": temperatures[0], "temperature_B": temperatures[1]}
    

    @property
    def is_temperature_stable(self, tol_A: float = 0.02, std_tol: float = 0.05) -> bool:
        if len(self._buffer_A) < 60: # length of buffer
            return False
        target_A = self.heater_target_spin.value()
        temps_A = np.array(self._buffer_A)
        temps_B = np.array(self._buffer_B)
        mean_A = np.mean(temps_A)
        std_A = np.std(temps_A)
        std_B = np.std(temps_B)
        return (abs(mean_A - target_A) < tol_A) and (std_A < std_tol) and (std_B < std_tol)


    def __del__(self):
        if self.polling_thread is not None:
            self.polling_thread.stop()
            self.polling_thread = None
        try:
            self.controller.disconnect_usb()
            self.controller = None
        except Exception as e:
            return


# polling thread class
class LakeShoreModel335PollingThread(BasePollingThread):
    updated = pyqtSignal(dict)

    def get_data(self) -> dict:
        heater_output1 = self.controller.get_heater_output(1)
        heater_output2 = self.controller.get_heater_output(2)
        temperature_reading = self.controller.get_all_kelvin_reading()
        data = {
            "temperature_A": temperature_reading[0],
            "temperature_B": temperature_reading[1],
            "heater_output_1": heater_output1,
            "heater_output_2": heater_output2 
            # "heater_status": ... ON OFF status (bool)
        }
        return data
    

    def emit_data(self, data: dict) -> None:
        self.updated.emit(data)

            
            