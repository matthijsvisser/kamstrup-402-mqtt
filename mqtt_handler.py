#!/usr/bin/python
"""
MQTT Handler for Kamstrup Meter Data Publishing

This module provides an MQTT client handler for publishing Kamstrup meter
data to an MQTT broker with support for authentication and TLS.

Created by Matthijs Visser
"""

import logging
import ssl
from typing import Optional
import paho.mqtt.client as paho
from logging.handlers import TimedRotatingFileHandler

log = logging.getLogger("log")
log.setLevel(logging.INFO)


class MqqtHandler:
    """
    MQTT Handler for publishing Kamstrup meter data.
    
    This class manages MQTT connections, authentication, and message publishing
    for Kamstrup meter data. It supports both authenticated and non-authenticated
    connections, as well as TLS encryption.
    """
    
    def __init__(
        self,
        broker_ip: str,
        broker_port: int,
        client_id: str,
        topic_prefix: str,
        retain: bool = False,
        qos: int = 0,
        authentication: bool = False,
        user: str = "",
        password: str = "",
        tls_enabled: bool = False,
        tls_ca_cert: str = "",
        tls_cert: str = "",
        tls_key: str = "",
        tls_insecure: bool = True,
    ) -> None:
        """
        Initialize the MQTT Handler.

        Args:
            broker_ip: MQTT broker IP address or hostname
            broker_port: MQTT broker port number
            client_id: Unique client identifier for the MQTT connection
            topic_prefix: Prefix for all MQTT topics
            retain: Whether to set the retain flag on published messages
            qos: Quality of Service level (0, 1, or 2)
            authentication: Whether to use username/password authentication
            user: Username for authentication
            password: Password for authentication
            tls_enabled: Whether to enable TLS encryption
            tls_ca_cert: Path to CA certificate file
            tls_cert: Path to client certificate file
            tls_key: Path to client private key file
            tls_insecure: Whether to allow insecure TLS connections
        """
        self.broker = broker_ip
        self.port = broker_port
        self.client_id = client_id
        self.topic_prefix = topic_prefix
        self.retain = retain
        self.qos = qos
        self.authentication = authentication
        self.user = user
        self.password = password
        self.tls_enabled = tls_enabled
        self.tls_ca_cert = tls_ca_cert
        self.tls_cert = tls_cert
        self.tls_key = tls_key
        self.tls_insecure = tls_insecure
        self.mqtt_client: Optional[paho.Client] = None
	
    def connect(self) -> None:
        """
        Establish connection to the MQTT broker.
        
        Configures authentication and TLS if enabled, then connects to the broker.
        
        Raises:
            ConnectionError: If connection to the broker fails
        """
        settings_message = ""
        self.mqtt_client = paho.Client(
            paho.CallbackAPIVersion.VERSION1, self.client_id, True
        )

        if self.authentication:
            self.mqtt_client.username_pw_set(self.user, self.password)
            settings_message = f"with username {self.user}, "
            
        if self.tls_enabled:
            self.mqtt_client.tls_set(
                self.tls_ca_cert, tls_version=ssl.PROTOCOL_TLSv1_2
            )
            self.mqtt_client.tls_insecure_set(self.tls_insecure)

        try:
            self.mqtt_client.connect(self.broker, self.port, 60)
            self.mqtt_client.loop_start()
            log.info(f"Connected to MQTT at: {self.broker}:{self.port}")
            settings_message += f"QoS level = {self.qos} and retain = {self.retain}"
            log.info(settings_message)
        except Exception as e:
            log.error(f"Failed to connect to MQTT broker: {e}")
            raise ConnectionError(f"MQTT connection failed: {e}") from e
		
    def disconnect(self) -> None:
        """Disconnect from the MQTT broker."""
        if self.mqtt_client:
            self.mqtt_client.disconnect()
            log.info("Disconnected from MQTT broker")

    def publish(self, topic: str, message: str) -> None:
        """
        Publish a message to the specified MQTT topic.

        Args:
            topic: The topic suffix to publish to (will be prefixed)
            message: The message payload to publish

        Raises:
            ValueError: If message format is invalid
            TypeError: If topic or message are not strings
        """
        if not self.mqtt_client:
            log.error("MQTT client not connected. Call connect() first.")
            return

        full_topic = self.create_topic(topic.lower())
        try:
            log.info(
                f"Publishing '{full_topic}'\t'{message}'\tto {self.broker}:{self.port}"
            )
            mqtt_info = self.mqtt_client.publish(
                full_topic, message, self.qos, self.retain
            )
            mqtt_info.wait_for_publish()

        except ValueError as e:
            log.error(f"Value error during publish: {e}")
            raise
        except TypeError as e:
            log.error(f"Type error during publish: {e}")
            raise

    def subscribe(self, topic: str) -> bool:
        """
        Subscribe to an MQTT topic.

        Args:
            topic: The topic to subscribe to

        Returns:
            True if subscription was successful, False otherwise
        """
        if not self.mqtt_client:
            log.error("MQTT client not connected. Call connect() first.")
            return False

        result = self.mqtt_client.subscribe(topic)
        if result[0] == 0:
            log.info(f"Subscribed to topic: {topic}")
            return True
        else:
            log.error(f"Failed to subscribe to topic: {topic}")
            return False

    def create_topic(self, data: str) -> str:
        """
        Create a full topic name by prefixing with the configured topic prefix.

        Args:
            data: The topic suffix

        Returns:
            The full topic name
        """
        return f"{self.topic_prefix}/{data}"

    def is_connected(self) -> bool:
        """
        Check if the MQTT client is connected.
        
        Returns:
            True if connected, False otherwise
        """
        return self.mqtt_client is not None and self.mqtt_client.is_connected()

    def loop_start(self) -> None:
        """Start the MQTT client network loop in a separate thread."""
        if self.mqtt_client:
            self.mqtt_client.loop_start()

    def loop_stop(self) -> None:
        """Stop the MQTT client network loop."""
        if self.mqtt_client:
            self.mqtt_client.loop_stop()
