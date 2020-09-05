#!/usr/bin/python
#
# ----------------------------------------------------------------------------
# "THE BEER-WARE LICENSE" (Revision 42):
# <phk@FreeBSD.ORG> wrote this file.  As long as you retain this notice you
# can do whatever you want with this stuff. If we meet some day, and you think
# this stuff is worth it, you can buy me a beer in return.   Poul-Henning Kamp
# ----------------------------------------------------------------------------
#
# Created by Matthijs Visser

import logging
import paho.mqtt.client as paho
from logging.handlers import TimedRotatingFileHandler

log = logging.getLogger("log")
log.setLevel(logging.INFO)

class MqqtHandler (object):
    
	def __init__(self, broker_ip, broker_port, client_id, topic_prefix, 
				 authentication=False, user="", password=""):
		self.broker = broker_ip
		self.port = broker_port
		self.client_id = client_id
		self.topic_prefix = topic_prefix
		self.authentication = authentication
		self.user = user
		self.password = password
	
	def connect(self):
		self.mqtt_client = paho.Client(self.client_id, True)

		if self.authentication:
			self.mqtt_client.username_pw_set(self.user, self.password)

		self.mqtt_client.connect(self.broker, self.port, 60)
		self.mqtt_client.loop_start()
		log.info('Connected to MQTT at: {}:{}'.format(self.broker, self.port))
	
	def disconnect(self):
		self.mqtt_client.disconnect()

	def publish(self, topic, message):
		full_topic = self.create_topic(topic.lower())
		try:
			log.info('Publishing \'{}\'\t\'{}\'\tto {}:{}'.format(full_topic, message,
														   	self.broker, 
															self.port))
			mqtt_info = self.mqtt_client.publish(full_topic, message)
			mqtt_info.wait_for_publish()

		except ValueError as e:
			logging.error('Value error: {}'.format(e))
		except TypeError as e:
			logging.error('Type error: {}'.format(e))

	def subscribe(self, topic):
		if self.mqtt_client.subscribe(topic) == 0:
			log.info('Subscribed to topic: {}'.format(self.topic_prefix))
			return True
		else:
			return False

	def create_topic(self, data):
		return "{}/{}".format(self.topic_prefix, data)

	def loop_start(self):
		self.mqtt_client.loop_start()

	def loop_stop(self):
		self.mqtt_client.loop_stop()