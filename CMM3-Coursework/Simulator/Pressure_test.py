# -*- coding: utf-8 -*-
"""
Created on Fri Jun 20 23:18:23 2025

@author: grego
"""

from pyModbusTCP.client import ModbusClient
import struct
import time
import matplotlib.pyplot as plt
from collections import deque
import csv


client = ModbusClient(host="10.24.1.22", port=502, auto_open=True)

modbus_map = {
    "P1": 100,
    "P2": 102,
    "P3": 104,
    "P4": 106,
    "P5": 108
}


MAX_POINTS = 60  # Number of points to keep for plotting
data_log = {label: deque(maxlen=MAX_POINTS) for label in modbus_map}
timestamps = deque(maxlen=MAX_POINTS)


csv_log = []


def read_float(register):
    regs = client.read_holding_registers(register, 2)
    if regs:
        packed = struct.pack('>HH', regs[0], regs[1])
        return struct.unpack('>f', packed)[0]
    return None


plt.ion()
fig, ax = plt.subplots()

print("Reading started Press Ctrl+C to stop.\n")

try:
    while True:
        timestamp = time.time()
        timestamps.append(timestamp)
        row = [time.strftime('%H:%M:%S', time.localtime(timestamp))]

        for label, reg in modbus_map.items():
            val = read_float(reg)
            if val is not None:
                data_log[label].append(val)
            else:
                data_log[label].append(0.0)
            row.append(val)

        csv_log.append(row)

        # Plotting
        ax.clear()
        for label in modbus_map:
            ax.plot(
                [t - timestamps[0] for t in timestamps],  # Relative time
                data_log[label],
                label=label
            )

        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Pressure (bar)")
        ax.set_title("Live Pressure Data")
        ax.legend(loc="upper right")
        plt.pause(1)

except KeyboardInterrupt:
    print("Stopped")

finally:
    # -------- Save CSV Log --------
    filename = f"pressure_log_{time.strftime('%Y%m%d_%H%M%S')}.csv"
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Time", "P1", "P2", "P3", "P4", "P5"])
        writer.writerows(csv_log)
    print(f"Logged data saved to: {filename}")
    plt.ioff()
    plt.show()