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
heater_output1 = temperature_controller.get_heater_output(1)
heater_output2 = temperature_controller.get_heater_output(2)
temperature_reading = temperature_controller.get_all_kelvin_reading()
print(f"A: {temperature_reading[0]:.2f}")
print(f"B: {temperature_reading[0]:.2f}")
print(f"Heater Ouput 1: {heater_output1}")
print(f"Heater Ouput 2: {heater_output2}")
