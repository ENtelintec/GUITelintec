# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 25/oct/2024  at 15:22 $"

import serial
import serial.tools.list_ports


def serial_ports():
    """Lists serial port names
    :returns:
        A list of the serial ports available on the system
    """
    ports = list(serial.tools.list_ports.comports())
    ports.sort()
    ports_names = [port.device for port in ports]
    ports_descriptions = [port.description for port in ports]
    # result = []
    # result_d = []
    # for port, description in zip(ports_names, ports_descriptions):
    #     try:
    #         s = serial.Serial(port)
    #         s.close()
    #         result.append(port)
    #         result_d.append(description)
    #     except serial.SerialException:
    #         print("Puerto no disponible: ", port)

    return ports_names, ports_descriptions
