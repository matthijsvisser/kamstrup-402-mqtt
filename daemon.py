#!/usr/bin/python
"""
Kamstrup Multical 402 MQTT Daemon

This daemon reads data from a Kamstrup Multical 402 heat meter at regular
intervals and publishes the data to an MQTT broker. It supports various
meter parameters like energy consumption, temperatures, flow rates, etc.

The daemon runs as a multiprocessing service and handles graceful shutdown
on SIGINT signals.

Created by Matthijs Visser
"""

import datetime
import json
import logging
import multiprocessing
import signal
import subprocess
import sys
import time
import yaml
from typing import Dict, List, Any, Optional
from logging.handlers import TimedRotatingFileHandler

from kamstrup_meter import Kamstrup
from mqtt_handler import MqqtHandler

# Configuration defaults
DEFAULT_POLL_INTERVAL = 28  # minutes
DEFAULT_QOS = 0
DEFAULT_MQTT_PORT = 1883
DEFAULT_SERIAL_TIMEOUT = 2.0

# Validation constants
MIN_POLL_INTERVAL = 1
MAX_POLL_INTERVAL_WARNING = 30
REQUIRED_CONFIG_SECTIONS = ["mqtt", "serial_device", "kamstrup"]
REQUIRED_MQTT_SETTINGS = ["host", "port", "client", "topic"]

# Configure logging
log = logging.getLogger("log")
log.setLevel(logging.DEBUG)

# Create logs directory if it doesn't exist
import os
if not os.path.exists("logs"):
    os.makedirs("logs")

handler = TimedRotatingFileHandler(
    "logs/debug.log", when="d", interval=1, backupCount=5
)
formatter = logging.Formatter(
    "[%(asctime)s %(filename)s %(funcName)s:%(lineno)4s - %(levelname)s - %(message)s]",
    "%Y-%m-%d %H:%M:%S",
)
handler.setFormatter(formatter)
log.addHandler(handler)

def load_config() -> Dict[str, Any]:
    """
    Load and validate configuration from config.yaml.
    
    Returns:
        Parsed configuration dictionary
        
    Raises:
        FileNotFoundError: If config.yaml is not found
        yaml.YAMLError: If configuration file is invalid
        ValueError: If required configuration sections are missing
    """
    try:
        with open("config.yaml", "r") as ymlfile:
            cfg = yaml.load(ymlfile, Loader=yaml.SafeLoader)
        
        # Validate required sections
        for section in REQUIRED_CONFIG_SECTIONS:
            if section not in cfg:
                raise ValueError(f"Missing required configuration section: {section}")
        
        # Validate required MQTT settings
        for setting in REQUIRED_MQTT_SETTINGS:
            if setting not in cfg["mqtt"]:
                raise ValueError(f"Missing required MQTT setting: {setting}")
        
        log.info("Configuration loaded successfully")
        return cfg
        
    except FileNotFoundError:
        log.error("Configuration file config.yaml not found")
        raise
    except yaml.YAMLError as e:
        log.error(f"Invalid YAML configuration: {e}")
        raise
    except Exception as e:
        log.error(f"Error loading configuration: {e}")
        raise


class KamstrupDaemon(multiprocessing.Process):
    """
    Main daemon process for reading Kamstrup meter data and publishing to MQTT.
    
    This process runs continuously, reading meter data at configured intervals
    and publishing the results to an MQTT broker. It handles graceful shutdown
    on SIGINT signals.
    """

    def __init__(self) -> None:
        """
        Initialize the Kamstrup daemon.
        
        Loads configuration, sets up MQTT and meter connections, and configures
        signal handlers for graceful shutdown.
        
        Raises:
            ConnectionError: If MQTT or meter connection fails
            ValueError: If configuration is invalid
        """
        super().__init__()
        log.info("Initializing Kamstrup daemon")

        self.running = True
        self.event_finished = multiprocessing.Event()
        self.receive_queue = multiprocessing.Queue()
        
        # Load and validate configuration
        cfg = load_config()
        mqtt_cfg = cfg["mqtt"]
        serial_cfg = cfg["serial_device"]
        kamstrup_cfg = cfg["kamstrup"]

        self.poll_interval = int(kamstrup_cfg.get("poll_interval", DEFAULT_POLL_INTERVAL))
        if self.poll_interval < MIN_POLL_INTERVAL:
            raise ValueError(f"Poll interval must be at least {MIN_POLL_INTERVAL} minute")
        if self.poll_interval >= MAX_POLL_INTERVAL_WARNING:
            log.warning(
                f"Poll interval >= {MAX_POLL_INTERVAL_WARNING} minutes may cause meter to enter standby mode"
            )

        # Set up signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)

        # Initialize MQTT handler
        self._setup_mqtt_handler(mqtt_cfg)
        
        # Initialize Kamstrup meter interface
        self._setup_meter_interface(serial_cfg, kamstrup_cfg)

    def _setup_mqtt_handler(self, mqtt_cfg: Dict[str, Any]) -> None:
        """Set up MQTT handler with configuration."""
        # Convert string boolean values to actual booleans
        retain = mqtt_cfg.get("retain", "false").lower() == "true"
        authentication = mqtt_cfg.get("authentication", "false").lower() == "true"
        tls_enabled = mqtt_cfg.get("tls_enabled", "false").lower() == "true"
        tls_insecure = mqtt_cfg.get("tls_insecure", "true").lower() == "true"

        if authentication:
            self.mqtt_handler = MqqtHandler(
                mqtt_cfg["host"],
                int(mqtt_cfg.get("port", DEFAULT_MQTT_PORT)),
                mqtt_cfg["client"],
                mqtt_cfg["topic"],
                retain,
                int(mqtt_cfg.get("qos", DEFAULT_QOS)),
                True,
                mqtt_cfg.get("username", ""),
                mqtt_cfg.get("password", ""),
                tls_enabled,
                mqtt_cfg.get("tls_ca_cert", ""),
                mqtt_cfg.get("tls_cert", ""),
                mqtt_cfg.get("tls_key", ""),
                tls_insecure,
            )
        else:
            self.mqtt_handler = MqqtHandler(
                mqtt_cfg["host"],
                int(mqtt_cfg.get("port", DEFAULT_MQTT_PORT)),
                mqtt_cfg["client"],
                mqtt_cfg["topic"],
                retain,
                int(mqtt_cfg.get("qos", DEFAULT_QOS)),
            )
        
        # Connect to MQTT broker
        self.mqtt_handler.connect()
        self.mqtt_handler.loop_start()

    def _setup_meter_interface(
        self, serial_cfg: Dict[str, Any], kamstrup_cfg: Dict[str, Any]
    ) -> None:
        """Set up Kamstrup meter interface."""
        com_port = serial_cfg.get("com_port")
        if not com_port:
            raise ValueError("Serial com_port not specified in configuration")
            
        parameters = kamstrup_cfg.get("parameters", [])
        if not parameters:
            raise ValueError("No parameters specified in configuration")
            
        self.heat_meter = Kamstrup(com_port, parameters)
	
    def _signal_handler(self, signal_num: int, frame) -> None:
        """
        Handle SIGINT signal for graceful shutdown.
        
        Args:
            signal_num: The signal number received
            frame: The current stack frame
        """
        log.info("Received shutdown signal, stopping daemon")
        self.running = False
        
        # Clean up connections
        try:
            if hasattr(self, 'heat_meter'):
                self.heat_meter.close()
        except Exception as e:
            log.error(f"Error closing meter connection: {e}")
            
        try:
            if hasattr(self, 'mqtt_handler'):
                self.mqtt_handler.loop_stop()
                self.mqtt_handler.disconnect()
        except Exception as e:
            log.error(f"Error closing MQTT connection: {e}")
            
        log.info("Daemon stopped")
        sys.exit(0)

    def run(self) -> None:
        """
        Main daemon loop.
        
        Continuously reads meter data and publishes to MQTT at the configured
        interval until shutdown is requested.
        """
        log.info("Starting Kamstrup daemon main loop")
        
        while self.running:
            try:
                # Read meter values
                log.debug("Reading meter data")
                values = self.heat_meter.run()
                
                if values:
                    # Convert to JSON and publish
                    json_values = json.dumps(values)
                    self.mqtt_handler.publish("values", json_values)
                    log.info(f"Published meter data: {json_values}")
                else:
                    log.warning("No values received from meter")
                
            except Exception as e:
                log.error(f"Error reading meter or publishing data: {e}")
                
            # Wait for next poll interval
            log.info(f"Waiting {self.poll_interval} minute(s) for next meter readout")
            time.sleep(self.poll_interval * 60)


def main() -> None:
    """
    Main entry point for the Kamstrup daemon.
    
    Creates and starts the daemon process.
    """
    try:
        daemon = KamstrupDaemon()
        daemon.run()
    except KeyboardInterrupt:
        log.info("Received keyboard interrupt, shutting down")
        sys.exit(0)
    except Exception as e:
        log.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
