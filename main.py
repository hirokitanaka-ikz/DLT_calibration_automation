from PyQt6.QtWidgets import QApplication, QWidget, QHBoxLayout, QTabWidget
from PyQt6.QtCore import QLocale
from widgets.ocean_spectrometer_widget import OceanSpectrometerWidget


def main():
    app = QApplication([])

    QLocale.setDefault(QLocale.c())

    win = QWidget()
    win.setWindowTitle("Laser Cooling App")
    win.resize(1200, 800)
    layout = QHBoxLayout()

    polling_interval = 0.5 # sec

    spectrometer_widget = OceanSpectrometerWidget(polling_interval=polling_interval)
    # temperature_controller_widget = TemperatureControllerWidget(polling_interval=polling_interval)


    layout.addWidget(spectrometer_widget)
    # layout.addWidget(temperature_controller_widget)
    
    win.setLayout(layout)
    win.show()

    app.exec()


if __name__ == "__main__":
    main()
