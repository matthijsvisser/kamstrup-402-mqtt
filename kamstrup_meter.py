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
# Modified by Matthijs Visser, refactored and simplified code

import serial
import math
import sys
import datetime
import json
import urllib.request
import logging
import time
from logging.handlers import TimedRotatingFileHandler

log = logging.getLogger("log")
log.setLevel(logging.INFO)

kamstrup_402_params = {
	"energy"	    : 0x3C,
	"power"         : 0x50,
	"temp1"         : 0x56,
	"temp2"         : 0x57,
	"tempdiff"      : 0x59,
	"flow"          : 0x4A,
	"volume"        : 0x44,
	"minflow_m"     : 0x8D,
	"maxflow_m"     : 0x8B,
	"minflowDate_m" : 0x8C,
	"maxflowDate_m" : 0x8A,
	"minpower_m"    : 0x91,
	"maxpower_m"    : 0x8F,
	"avgtemp1_m"    : 0x95,
	"avgtemp2_m"    : 0x96,
	"minpowerdate_m": 0x90,
	"maxpowerdate_m": 0x8E,
	"minflow_y"     : 0x7E,
	"maxflow_y"     : 0x7C,
	"minflowdate_y" : 0x7D,
	"maxflowdate_y" : 0x7B,
	"minpower_y"    : 0x82,
	"maxpower_y"    : 0x80,
	"avgtemp1_y"    : 0x92,
	"avgtemp2_y"    : 0x93,
	"minpowerdate_y": 0x81,
	"maxpowerdate_y": 0x7F,
	"temp1xm3"      : 0x61,
	"temp2xm3"      : 0x6E,
	"infoevent"     : 0x71,
	"hourcounter"   : 0x3EC,
}

# Kamstrup uses the "true" CCITT CRC-16
def crc_1021(message):
	poly = 0x1021
	reg = 0x0000
	for byte in message:
		mask = 0x80
		while (mask > 0):
			reg <<= 1
			if byte & mask:
				reg |= 1
			mask >>= 1
			if reg & 0x10000:
				reg &= 0xffff
				reg ^= poly
	return reg

# Byte values which must be escaped before transmission
escapes = {
	0x06: True,
	0x0d: True,
	0x1b: True,
	0x40: True,
	0x80: True,
}

class kamstrup(object):

	def __init__ (self, port, parameters):
		self.serial_port = port
		self.parameters = parameters

		try:
			self.serial = serial.Serial(
				port = self.serial_port,
				baudrate = 1200,
				parity = serial.PARITY_NONE,
				stopbits = serial.STOPBITS_TWO,
				bytesize = serial.EIGHTBITS,
				timeout = 2.0)
		except serial.SerialException as e:
			log.exception(e)

	def run (self):
		values = {}
		if self.serial.is_open:
			self.close()

		if self.open():
			for parameter in self.parameters:
				value = self.readparameter(int(str(kamstrup_402_params[parameter]), 0))
				if value is not None:
					values[parameter] = value
			self.close()
		return values

	def open (self):
		try:
			self.serial.open()
			log.debug('Opened serial port')
			return True
		except (ValueError, Exception) as e:
			log.error(e)
			return False

	def close (self):
		self.serial.close()
		log.debug('Closed serial port')
		
	def rd (self):
		receivedByte = self.serial.read(size=1)
		if len(receivedByte) == 0:
			log.debug("Rx timeout")
			return None
		byte = bytearray(receivedByte)[0]
		return byte

	def send (self, prefix, msg):
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
			log.exception(e.message)

	def recv (self):
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
					log.warning("Missing Escape %02x" % value)
				filteredMessage.append(value)
				i += 2
			else:
				filteredMessage.append(receivedMessage[i])
				i += 1

		if crc_1021(filteredMessage):
			log.error("CRC error")
			return None

		return filteredMessage[:-2]

	def readparameter (self, parameter):
		self.send(0x80, (0x3f, 0x10, 0x01, parameter >> 8, parameter & 0xff))
		receivedMessage = self.recv()

		if (receivedMessage == None):
			log.warning('No response from meter')
			return None
		elif ((receivedMessage[0] != 0x3f) or
			(receivedMessage[1] != 0x10) or
			(receivedMessage[2] != parameter >> 8) or
			(receivedMessage[3] != parameter & 0xff)):
			log.warning('Message is invalid')
			return None

		# Decode the mantissa
		value = 0
		for i in range(0, receivedMessage[5]):
			value <<= 8
			value |= receivedMessage[i + 7]

		# Decode the exponent
		i = receivedMessage[6] & 0x3f
		if receivedMessage[6] & 0x40:
			i = -i
		i = math.pow(10,i)
		if receivedMessage[6] & 0x80:
			i = -i
		value *= i
		return float(value)