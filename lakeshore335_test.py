from lakeshore import Model335
import serial.tools.list_ports

def find_model335():
    ports = serial.tools.list_ports.comports()
    for port in ports:
        try:
            if 'USB' in port.description:
                return port.device
        except Exception:
            continue
    return None


com_port = find_model335()
if not com_port:
    raise RuntimeError("No Lakeshore device found")

temperature_controller = Model335(com_port=com_port)
print(temperature_controller.query('*IDN?'))