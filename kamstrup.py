#!/usr/bin/python
#
# ----------------------------------------------------------------------------
# "THE BEER-WARE LICENSE" (Revision 42):
# <phk@FreeBSD.ORG> wrote this file.  As long as you retain this notice you
# can do whatever you want with this stuff. If we meet some day, and you think
# this stuff is worth it, you can buy me a beer in return.   Poul-Henning Kamp
# ----------------------------------------------------------------------------
#
# Modified by Frank Reijn and Paul Bonnemaijers for Kamstrup Multical 402
#
# Modified by Matthijs Visser 2020
# * refactored code
# * added mqtt support

import serial
import math
import sys
import datetime
import json
import urllib.request

kamstrup_402_var = {                # Decimal Number in Command
 0x003C: "Heat Energy (E1)",        #60
 0x0050: "Power",                   #80
 0x0056: "Temp1",                   #86
 0x0057: "Temp2",                   #87
 0x0059: "Tempdiff",                #89
 0x004A: "Flow",                    #74
 0x0044: "Volume",                  #68
 0x008D: "MinFlow_M",               #141
 0x008B: "MaxFlow_M",               #139
 0x008C: "MinFlowDate_M",           #140
 0x008A: "MaxFlowDate_M",           #138
 0x0091: "MinPower_M",              #145
 0x008F: "MaxPower_M",              #143
 0x0095: "AvgTemp1_M",              #149
 0x0096: "AvgTemp2_M",              #150
 0x0090: "MinPowerDate_M",          #144
 0x008E: "MaxPowerDate_M",          #142
 0x007E: "MinFlow_Y",               #126
 0x007C: "MaxFlow_Y",               #124
 0x007D: "MinFlowDate_Y",           #125
 0x007B: "MaxFlowDate_Y",           #123
 0x0082: "MinPower_Y",              #130
 0x0080: "MaxPower_Y",              #128
 0x0092: "AvgTemp1_Y",              #146
 0x0093: "AvgTemp2_Y",              #147
 0x0081: "MinPowerDate_Y",          #129
 0x007F: "MaxPowerDate_Y",          #127
 0x0061: "Temp1xm3",                #97
 0x006E: "Temp2xm3",                #110
 0x0071: "Infoevent",               #113
 0x03EC: "HourCounter",             #1004
}

#######################################################################
# Kamstrup uses the "true" CCITT CRC-16
#

def crc_1021(message):
    poly = 0x1021
    reg = 0x0000
    for byte in message:
        mask = 0x80
        while(mask > 0):
            reg<<=1
            if byte & mask:
                reg |= 1
            mask>>=1
            if reg & 0x10000:
                reg &= 0xffff
                reg ^= poly
    return reg

#######################################################################
# Byte values which must be escaped before transmission
#

escapes = {
    0x06: True,
    0x0d: True,
    0x1b: True,
    0x40: True,
    0x80: True,
}

class kamstrup(object):

    def __init__(self, serial_port):
        
        try:
            self.serial = serial.Serial(
                port = serial_port,
                baudrate = 1200,
                parity = serial.PARITY_NONE,
                stopbits = serial.STOPBITS_TWO,
                bytesize = serial.EIGHTBITS,
                timeout = 2.0)
        except serial.SerialException as e:
            print(e.message)

    def rd(self):
        receivedByte = self.serial.read(size=1)
        if len(receivedByte) == 0:
            print("Rx timeout")
            return None
        byte = bytearray(receivedByte)[0]
        return byte

    def send(self, prefix, msg):
        message = bytearray(msg)
        command = bytearray()
        
        message.append(0)
        message.append(0)
        
        checksum = crc_1021(message)
        
        message[-2] = checksum >> 8
        message[-1] = checksum & 0xff
        
        command.append(prefix)
        for byte in message:
            if byte in escapes:
                command.append(0x1b)
                command.append(byte ^ 0xff)
            else:
                command.append(byte)
        command.append(0x0d)
        try:
            self.serial.write(command)
        except serial.SerialTimeoutException as e:
            pass
        

    def recv(self):
        receivedMessage = bytearray()
        filteredMessage = bytearray()

        while True:
            receivedByte = self.rd()
            if receivedByte == None:
                return None
            if receivedByte == 0x40:
                receivedMessage = bytearray()
            receivedMessage.append(receivedByte)
            if receivedByte == 0x0d:
                break
        
        i = 1;
        while i < len(receivedMessage) - 1:
            if receivedMessage[i] == 0x1b:
                value = receivedMessage[i + 1] ^ 0xff
                if value not in escapes:
                    print("Missing Escape %02x" % value)
                filteredMessage.append(value)
                i += 2
            else:
                filteredMessage.append(receivedMessage[i])
                i += 1

        if crc_1021(filteredMessage):
            print("CRC error")
            return None

        return filteredMessage[:-2]

    def readvar(self, parameter):

        self.send(0x80, (0x3f, 0x10, 0x01, parameter >> 8, parameter & 0xff))
        receivedMessage = self.recv()

        if ((receivedMessage == None) or
            (receivedMessage[0] != 0x3f) or
            (receivedMessage[1] != 0x10) or
            (receivedMessage[2] != parameter >> 8) or
            (receivedMessage[3] != parameter & 0xff)):
            return None

        # Decode the mantissa
        value = 0
        for i in range(0, receivedMessage[5]):
            value <<= 8
            value |= receivedMessage[i + 7]

        # Decode the exponent
        i = receivedMessage[6] & 0x3f
        if receivedMessage[6] & 0x40:
            receivedMessage = -i
        i = math.pow(10, i)
        if receivedMessage[6] & 0x80:
            i = -i
        value *= i

        return "{:.2f}".format(value)
            

if __name__ == "__main__":

    import time

    comport = "/dev/ttyUSB1"
    commands = [60, 68, 86, 87]
    meter = kamstrup(comport)

    for command in commands:
        print(str(meter.readvar(command)))