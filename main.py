from PyQt6.QtWidgets import QApplication, QWidget, QHBoxLayout, QVBoxLayout
from PyQt6.QtCore import QLocale
from widgets.ocean_spectrometer_widget import OceanSpectrometerWidget
from widgets.lakeshore_model335_widget import LakeShoreModel335Widget
from widgets.temperature_chart_widget import TemperatureChartWidget


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

    spectrometer_widget.setFixedWidth(600)

    layout = QHBoxLayout()
    layout.addWidget(spectrometer_widget)
    sub_layout = QVBoxLayout()
    sub_layout.addWidget(temperature_controller_widget)
    sub_layout.addWidget(temperature_chart_widget)
    layout.addLayout(sub_layout)
    
    win.setLayout(layout)
    win.show()

    app.exec()


if __name__ == "__main__":
    main()
