# vim: set fileencoding=utf-8 :
from __future__ import print_function
import minimalmodbus

minimalmodbus.TIMEOUT = 0.5


class RD6006(object):
    def __init__(self, port, address=1, baudrate=115200):
        self.port = port
        self.address = address
        self.instrument = minimalmodbus.Instrument(port=port, slaveaddress=address)
        self.instrument.serial.baudrate = baudrate
        regs = self._read_registers(0, 4)
        self.sn = regs[1] << 16 | regs[2]
        self.fw = regs[3] / 100.
        self.type = int(regs[0] / 10)

        if self.type == 6012 or self.type == 6018:
            print("RD6012 or RD6018 detected")
            self.voltres = 100.
            self.ampres = 100.
        else:
            print("RD6006 or other detected")
            self.voltres = 100.
            self.ampres = 1000.

    def __repr__(self):
        return "RD6006 SN:{} FW:{}".format(self.sn, self.fw)

    def _read_register(self, register):
        try:
            return self.instrument.read_register(register)
        except minimalmodbus.NoResponseError:
            return self._read_register(register)

    def _read_registers(self, start, length):
        try:
            return self.instrument.read_registers(start, length)
        except minimalmodbus.NoResponseError:
            return self._read_registers(start, length)
        except minimalmodbus.InvalidResponseError:
            return self._read_registers(start, length)

    def _write_register(self, register, value):
        try:
            return self.instrument.write_register(register, value)
        except minimalmodbus.NoResponseError:
            return self._write_register(register, value)

    def _mem(self, M=0):
        """reads the 4 register of a Memory[0-9] and print on a single line"""
        regs = self._read_registers(M * 4 + 80, 4)
        print(
            "M{}: {:4.1f}V, {:3.3f}A, OVP:{:4.1f}V, OCP:{:3.3f}A".format(M, regs[0] / self.voltres, regs[1] / self.ampres, regs[2] / self.voltres, regs[3] / self.ampres)
        )

    def status(self):
        regs = self._read_registers(0, 84)
        print("== Device")
        print("Model   : {}".format(regs[0]/10.))
        print("SN      : {:08d}".format(regs[1]<<16 | regs[2]))
        print("Firmware: {}".format(regs[3]/100.))
        print("Input   : {}V".format(regs[14] / self.voltres))
        if regs[4]:
            sign = -1
        else:
            sign = +1
        print("Temp    : {}°C".format(sign * regs[5]))
        if regs[34]:
            sign = -1
        else:
            sign = +1
        print("TempProb: {}°C".format(sign * regs[35]))
        print("== Output")
        print("Voltage : {}V".format(regs[10] / self.voltres))
        print("Current : {}A".format(regs[11] / self.ampres))
        print("Energy  : {}Ah".format(regs[12]/1000.))
        print("Power   : {}W".format(regs[13]/100.))
        print("== Settings")
        print("Voltage : {}V".format(regs[8] / self.voltres))
        print("Current : {}A".format(regs[9] / self.ampres))
        print("== Protection")
        print("Voltage : {}V".format(regs[82] / self.voltres))
        print("Current : {}A".format(regs[83] / self.ampres))
        print("== Battery")
        if regs[32]:
            print("Active")
            print("Voltage : {}V".format(regs[33] / self.voltres))
        print(
            "Capacity: {}Ah".format((regs[38] <<16 | regs[39])/1000.)
        )  # TODO check 8 or 16 bits?
        print(
            "Energy  : {}Wh".format((regs[40] <<16 | regs[41])/1000.)
        )  # TODO check 8 or 16 bits?
        print("== Memories")
        for m in range(10):
            self._mem(M=m)

    @property
    def input_voltage(self):
        return self._read_register(14) / self.voltres

    @property
    def voltage(self):
        return self._read_register(8) / self.voltres

    @property
    def meastemp_internal(self):
        if self._read_register(4):
            return -1 * self._read_register(5)
        else:
            return 1 * self._read_register(5)

    @property
    def meastempf_internal(self):
        if self._read_register(6):
            return -1 * self._read_register(7)
        else:
            return 1 * self._read_register(7)

    @property
    def meastemp_external(self):
        if self._read_register(34):
            return -1 * self._read_register(35)
        else:
            return 1 * self._read_register(35)

    @property
    def meastempf_external(self):
        if self._read_register(36):
            return -1 * self._read_register(37)
        else:
            return 1 * self._read_register(37)

    @voltage.setter
    def voltage(self, value):
        self._write_register(8, int(value * self.voltres))

    @property
    def measvoltage(self):
        return self._read_register(10) / self.voltres

    @property
    def meascurrent(self):
        return self._read_register(11) / self.ampres

    @property
    def measpower(self):
        return self._read_register(13) / 100.

    @property
    def measah(self):
        return (
            self._read_register(38) << 16 | self._read_register(39)
        ) / 1000.  # TODO check 16 or 8 bit

    @property
    def measwh(self):
        return (
            self._read_register(40) << 16 | self._read_register(41)
        ) / 1000.  # TODO check 16 or 8 bit

    @property
    def battmode(self):
        return self._read_register(32)

    @property
    def battvoltage(self):
        return self._read_register(33)

    @property
    def current(self):
        return self._read_register(9) / self.ampres

    @current.setter
    def current(self, value):
        self._write_register(9, int(value * self.ampres))

    @property
    def voltage_protection(self):
        return self._read_register(82) / self.voltres

    @voltage_protection.setter
    def voltage_protection(self, value):
        self._write_register(82, int(value * self.voltres))

    @property
    def current_protection(self):
        return self._read_register(83) / self.ampres

    @current_protection.setter
    def current_protection(self, value):
        self._write_register(83, int(value * self.ampres))

    @property
    def enable(self):
        return self._read_register(18)

    @enable.setter
    def enable(self, value):
        self._write_register(18, int(value))

    @property
    def ocpovp(self):
        return self._read_register(16)

    @property
    def CVCC(self):
        return self._read_register(17)

    @property
    def backlight(self):
        return self._read_register(72)

    @backlight.setter
    def backlight(self, value):
        self._write_register(72, value)

    @property
    def date(self):
        """returns the date as tuple: (year, month, day)"""
        regs = self._read_registers(48, 3)
        year = regs[0]
        month = regs[1]
        day = regs[2]
        return (year, month, day)

    @date.setter
    def date(self, value):
        """Sets the date, needs tuple with (year, month, day) as argument"""
        year, month, day = value
        self._write_register(48, year)
        self._write_register(49, month)
        self._write_register(50, day)

    @property
    def time(self):
        """returns the time as tuple: (h, m, s)"""
        regs = self._read_registers(51, 3)
        h = regs[0]
        m = regs[1]
        s = regs[2]
        return (h, m, s)

    @time.setter
    def time(self, value):
        """sets the time, needs time with (h, m, s) as argument"""
        h, m, s = value
        self._write_register(51, h)
        self._write_register(52, m)
        self._write_register(53, s)


if __name__ == "__main__":
    import serial.tools.list_ports

    ports = list(serial.tools.list_ports.comports())
    for p in ports:
        if "VID:PID=1A86:7523" in p[2]:
            print(p)
            r = RD6006(p[0])
            break
    else:
        raise Exception("Port not found")
    r.status()
