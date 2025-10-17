from lakeshore import Model335
import serial.tools.list_ports

BAUD_RATE = 57600

def find_lakeshore_model335():
    ports = serial.tools.list_ports.comports()
    for port in ports:
        if "Lake Shore Model 335" in port.description:
            return port

port = find_lakeshore_model335()
if port is None:
    raise RuntimeError("No Lakeshore device found")

temperature_controller = Model335(com_port=port.device, baud_rate=BAUD_RATE)
print(temperature_controller.query('*IDN?'))
print(temperature_controller.query('*ESR?'))