#!/usr/bin/env python3

import time, random, subprocess
from sys import exit
import ledshim

try:
    import psutil
except ImportError:
    exit('This script requires the psutil module\nInstall with: sudo pip install psutil')

class LEDRange:
    def __init__(self, lower, upper):
        self.lower = lower
        self.upper = upper
        self.width = upper - lower
        self.range = range(lower, upper + 1)

    def toLEDIndex(self, fraction):
        # print("fraction ", fraction)
        return self.lower + int(round(self.width * fraction))

class Lights:
    def __init__(self):
        ledshim.set_clear_on_exit()
        ledshim.set_brightness(1)
        self.array = [(0,0,0)] * ledshim.NUM_PIXELS
    
    def set(self, index, r, g, b):
        self.array[index] = (r,g,b)

    def drawAndReset(self):
        for i in range(ledshim.NUM_PIXELS):
            j = ledshim.NUM_PIXELS - i - 1
            ledshim.set_pixel(
                i, 
                self.array[j][0], 
                self.array[j][1], 
                self.array[j][2]
            )
            self.array[j] = (0,0,0)

        ledshim.show()

batLEDRange = LEDRange(0, 6) 
hddLEDRange = LEDRange(7, 8)
cpuLEDRange = LEDRange(9, 27)

def doCPU(lights):
    cpu = psutil.cpu_times_percent()

    s = cpu.system + cpu.steal + cpu.guest_nice + cpu.guest
    w = cpu.irq + cpu.iowait +  cpu.softirq
    u = cpu.user + cpu.nice
    i = cpu.idle

    # Cumulative
    ac = s
    bc = ac + w
    cc = bc + u
    tot = cc + i

    aIdx = cpuLEDRange.toLEDIndex(ac / 100)
    bIdx = cpuLEDRange.toLEDIndex(bc / 100)
    cIdx = cpuLEDRange.toLEDIndex(cc / 100)

    for x in cpuLEDRange.range:
        if x <= aIdx:
            lights.set(x, 150, 0, 0)
        elif x <= bIdx:
            lights.set(x, 0, 0, 250)
        elif x <= cIdx:
            lights.set(x, 40, 130, 0)
        else:
            lights.set(x, 0, 0, 0)



def DiskIOMeter(prevBytes = 0):
    def isActive():
        nonlocal prevBytes
        old = prevBytes

        counters = psutil.disk_io_counters()
        prevBytes = counters.read_bytes + counters.write_bytes

        diff = prevBytes - old

        return diff > 0

    return isActive


def doIO(lights, diskActive):
    if(diskActive() > 0):
        for i in hddLEDRange.range:
            lights.set(i, 100, 100, 100)


def doBat(lights):
    out = subprocess.Popen(["lifepo4wered-cli","get","vbat"], stdout=subprocess.PIPE).communicate()[0]
    vbat = int(out.splitlines()[0].decode('ascii'))

    vmax = 3300
    vmin = 3100
    range = vmax - vmin
    frac = min((vbat - vmin) / range, 1)
    batPctIdx = batLEDRange.toLEDIndex(frac)

    if(vbat > vmax):
        for i in batLEDRange.range:
            lights.set(i, 0, 50, 40)
    else:
        for i in batLEDRange.range:
            if i <= batPctIdx:
                lights.set(i, 0, 0, 250)
            else:
                lights.set(i, 250, 0, 100)

lights = Lights()
diskMeter = DiskIOMeter()

while True:
    doCPU(lights)
    doIO(lights, diskMeter)
    doBat(lights)
    
    lights.drawAndReset()
    
    time.sleep(1)
