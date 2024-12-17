# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 28/oct/2024  at 11:58 $"

import threading


class SerialPortListener(threading.Thread):
    def __init__(self, port, baudrate, callback, callback_error):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.callback = callback
        self.stop_event = threading.Event()
        self.error_callback = callback_error

    def run(self):
        import serial
        try:
            with serial.Serial(self.port, self.baudrate, timeout=1) as ser:
                while not self.stop_event.is_set():
                    line = ser.readline().decode("utf-8").strip()
                    if line:
                        self.callback(line)
        except serial.SerialException as e:
            error = f"Error: {str(e)}"
            self.error_callback(error)

    def stop(self):
        self.stop_event.set()
