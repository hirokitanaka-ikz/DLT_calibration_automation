from PyQt6.QtWidgets import QApplication, QWidget, QHBoxLayout, QTabWidget
from PyQt6.QtCore import QLocale
from widgets.ocean_spectrometer_widget import OceanSpectrometerWidget
from widgets.lakeshore_model335_widget import LakeShoreModel335Widget


def main():
    app = QApplication([])

    QLocale.setDefault(QLocale.c())

    win = QWidget()
    win.setWindowTitle("DLT Calibration App")
    win.resize(1200, 800)
    layout = QHBoxLayout()

    polling_interval = 0.5 # sec

    spectrometer_widget = OceanSpectrometerWidget(polling_interval=polling_interval)
    temperature_controller_widget = LakeShoreModel335Widget(polling_interval=polling_interval)

    spectrometer_widget.setFixedWidth(600)

    layout.addWidget(spectrometer_widget)
    layout.addWidget(temperature_controller_widget)
    
    win.setLayout(layout)
    win.show()

    app.exec()


if __name__ == "__main__":
    main()
