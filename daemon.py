#!/usr/bin/env python

import datetime
import time
import sys
import signal
import subprocess
import logging
import paho.mqtt.client as paho
import multiprocessing
import yaml
from kamstrup_meter import kamstrup
from mqtt_handler import MqqtHandler
from logging.handlers import TimedRotatingFileHandler


log = logging.getLogger("log")
log.setLevel(logging.INFO)

handler = TimedRotatingFileHandler('debug.log', when="d", interval=1, backupCount=5)

formatter = logging.Formatter("[%(asctime)s %(filename)s %(funcName)s:%(lineno)4s - %(levelname)s - %(message)s]",
							  "%Y-%m-%d %H:%M:%S")
handler.setFormatter(formatter)
log.addHandler(handler)

with open("config.yaml", "r") as ymlfile:
	cfg = yaml.load(ymlfile, Loader=yaml.BaseLoader)

class KamstrupDaemon(multiprocessing.Process):
	def __init__(self):
		log.info('initializing daemon')

		self.running = True
		self.event_finished = multiprocessing.Event()
		self.receive_queue = multiprocessing.Queue()
		mqtt_cfg = cfg["mqtt"]
		serial_cfg = cfg["serial_device"]
		kamstrup_cfg = cfg["kamstrup"]

		self.poll_interval = kamstrup_cfg["poll_interval"]

		signal.signal(signal.SIGINT, self.signal_handler)

		self.mqtt_handler = MqqtHandler(mqtt_cfg["host"], int(mqtt_cfg["port"]), 
			mqtt_cfg["client"], mqtt_cfg["topic"])
		self.mqtt_handler.connect()
		self.mqtt_handler.loop_start()

		self.heat_meter = kamstrup(serial_cfg["com_port"], kamstrup_cfg["parameters"])
	
	def signal_handler(self, signal, handler):
		self.running = False
		self.heat_meter.close()
		self.mqtt_handler.loop_stop()
		self.mqtt_handler.disconnect()
		log.info('stopping daemon')
		sys.exit(0)

	def run(self):
		while self.running:
			values = self.heat_meter.run()

			print(values)
			for value in values:
				self.mqtt_handler.publish(value, str(values[value]))
				# self.mqtt_handler.publish(self.mqtt_handler.topic_prefix + "/" + value, values[value])
			log.info("Waiting {} minute(s) for the next meter readout".format(self.poll_interval))
			time.sleep(int(self.poll_interval) * 60)
			

def main():
	daemon = KamstrupDaemon()
	daemon.run()

if  __name__ == '__main__':
	main()
