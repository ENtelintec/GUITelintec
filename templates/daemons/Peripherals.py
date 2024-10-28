# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 28/oct/2024  at 11:58 $"

import threading


class SerialPortListener(threading.Thread):
    def __init__(self, port, baudrate, callback):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.callback = callback
        self.stop_event = threading.Event()

    def run(self):
        import serial

        with serial.Serial(self.port, self.baudrate, timeout=1) as ser:
            while not self.stop_event.is_set():
                line = ser.readline().decode("utf-8").strip()
                if line:
                    self.callback(line)

    def stop(self):
        self.stop_event.set()
