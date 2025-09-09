#!/usr/bin/python
"""
Kamstrup Multical 402 Heat Meter Communication Module

This module handles serial communication with Kamstrup Multical 402 heat meters
using the proprietary Kamstrup protocol. It can read various parameters like
energy consumption, temperatures, flow rates, and volume measurements.

Originally based on work by Poul-Henning Kamp (Beer-ware license)
Modified by Frank Reijn and Paul Bonnemaijers for Kamstrup Multical 402
Further modified and refactored by Matthijs Visser

Protocol Details:
- 1200 baud, 8 data bits, 2 stop bits, no parity
- Uses CCITT CRC-16 for error detection
- Certain bytes must be escaped during transmission
"""

import datetime
import json
import logging
import math
import serial
import sys
import time
import urllib.request
from typing import Dict, List, Optional, Union
from logging.handlers import TimedRotatingFileHandler

log = logging.getLogger("log")
log.setLevel(logging.INFO)

# Kamstrup Multical 402 parameter mapping
# Maps parameter names to their corresponding register addresses
KAMSTRUP_402_PARAMS = {
    "energy": 0x3C,          # Energy consumption in GJ
    "power": 0x50,           # Current power in kW
    "temp1": 0x56,           # Inlet temperature in °C
    "temp2": 0x57,           # Outlet temperature in °C
    "tempdiff": 0x59,        # Temperature difference in °C
    "flow": 0x4A,            # Flow rate in l/h
    "volume": 0x44,          # Volume consumption in m³
    "minflow_m": 0x8D,       # Minimum flow this month
    "maxflow_m": 0x8B,       # Maximum flow this month
    "minflowDate_m": 0x8C,   # Date of minimum flow this month
    "maxflowDate_m": 0x8A,   # Date of maximum flow this month
    "minpower_m": 0x91,      # Minimum power this month
    "maxpower_m": 0x8F,      # Maximum power this month
    "avgtemp1_m": 0x95,      # Average inlet temp this month
    "avgtemp2_m": 0x96,      # Average outlet temp this month
    "minpowerdate_m": 0x90,  # Date of minimum power this month
    "maxpowerdate_m": 0x8E,  # Date of maximum power this month
    "minflow_y": 0x7E,       # Minimum flow this year
    "maxflow_y": 0x7C,       # Maximum flow this year
    "minflowdate_y": 0x7D,   # Date of minimum flow this year
    "maxflowdate_y": 0x7B,   # Date of maximum flow this year
    "minpower_y": 0x82,      # Minimum power this year
    "maxpower_y": 0x80,      # Maximum power this year
    "avgtemp1_y": 0x92,      # Average inlet temp this year
    "avgtemp2_y": 0x93,      # Average outlet temp this year
    "minpowerdate_y": 0x81,  # Date of minimum power this year
    "maxpowerdate_y": 0x7F,  # Date of maximum power this year
    "temp1xm3": 0x61,        # Temperature 1 × volume
    "temp2xm3": 0x6E,        # Temperature 2 × volume
    "infoevent": 0x71,       # Information event register
    "hourcounter": 0x3EC,    # Hour counter
}

def crc_1021(message: bytearray) -> int:
    """
    Calculate CCITT CRC-16 checksum.
    
    Kamstrup uses the "true" CCITT CRC-16 algorithm for error detection
    in their communication protocol.
    
    Args:
        message: The message bytes to calculate checksum for
        
    Returns:
        The calculated CRC-16 checksum
    """
    poly = 0x1021  # CCITT polynomial
    reg = 0x0000   # Initial register value
    
    for byte in message:
        mask = 0x80
        while mask > 0:
            reg <<= 1
            if byte & mask:
                reg |= 1
            mask >>= 1
            if reg & 0x10000:
                reg &= 0xFFFF
                reg ^= poly
    return reg


# Byte values that must be escaped before transmission in Kamstrup protocol
ESCAPE_BYTES = {
    0x06: True,  # ACK
    0x0D: True,  # Carriage return (message terminator)
    0x1B: True,  # Escape character
    0x40: True,  # Message start character
    0x80: True,  # Command prefix
}

class Kamstrup:
    """
    Kamstrup Multical 402 Heat Meter Communication Interface.
    
    This class handles serial communication with Kamstrup Multical 402 heat meters
    using the proprietary Kamstrup protocol. It can read various meter parameters
    such as energy consumption, temperatures, flow rates, and volume measurements.
    
    The communication uses:
    - 1200 baud serial communication
    - 8 data bits, 2 stop bits, no parity
    - CCITT CRC-16 for error detection
    - Specific escape sequences for certain byte values
    """

    def __init__(self, port: str, parameters: List[str]) -> None:
        """
        Initialize the Kamstrup meter interface.
        
        Args:
            port: Serial port device path (e.g., '/dev/ttyUSB0')
            parameters: List of parameter names to read from the meter
            
        Raises:
            serial.SerialException: If serial port cannot be configured
            ValueError: If invalid parameters are specified
        """
        self.serial_port = port
        self.parameters = parameters
        self._validate_parameters()

        try:
            self.serial = serial.Serial(
                port=self.serial_port,
                baudrate=1200,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_TWO,
                bytesize=serial.EIGHTBITS,
                timeout=2.0,
            )
            log.info(f"Initialized Kamstrup interface on {port}")
        except serial.SerialException as e:
            log.error(f"Failed to initialize serial port {port}: {e}")
            raise

    def _validate_parameters(self) -> None:
        """Validate that all requested parameters are supported."""
        invalid_params = [p for p in self.parameters if p not in KAMSTRUP_402_PARAMS]
        if invalid_params:
            raise ValueError(f"Invalid parameters: {invalid_params}")
            
    def run(self) -> Dict[str, float]:
        """
        Read all configured parameters from the meter.
        
        Returns:
            Dictionary mapping parameter names to their values
            
        Raises:
            serial.SerialException: If communication with meter fails
        """
        values = {}
        
        # Close port if already open to ensure clean connection
        if self.serial.is_open:
            self.close()

        if self.open():
            try:
                for parameter in self.parameters:
                    param_code = KAMSTRUP_402_PARAMS[parameter]
                    value = self.readparameter(param_code)
                    if value is not None:
                        values[parameter] = value
                    else:
                        log.warning(f"Failed to read parameter: {parameter}")
            finally:
                self.close()
        else:
            log.error("Failed to open serial connection to meter")
            
        return values

    def open(self) -> bool:
        """
        Open the serial connection to the meter.
        
        Returns:
            True if connection opened successfully, False otherwise
        """
        try:
            self.serial.open()
            log.debug("Opened serial port")
            return True
        except (ValueError, Exception) as e:
            log.error(f"Failed to open serial port: {e}")
            return False

    def close(self) -> None:
        """Close the serial connection to the meter."""
        if self.serial.is_open:
            self.serial.close()
            log.debug("Closed serial port")

    def _read_byte(self) -> Optional[int]:
        """
        Read a single byte from the serial port.
        
        Returns:
            The byte value, or None if timeout occurred
        """
        received_byte = self.serial.read(size=1)
        if len(received_byte) == 0:
            log.debug("Serial read timeout")
            return None
        return bytearray(received_byte)[0]

    def send(self, prefix: int, msg: tuple) -> None:
        """
        Send a command message to the meter.
        
        Args:
            prefix: Command prefix byte
            msg: Message bytes as a tuple
            
        Raises:
            serial.SerialTimeoutException: If send operation times out
        """
        message = bytearray(msg)
        command = bytearray()

        # Add space for CRC
        message.extend([0, 0])

        # Calculate and append CRC
        checksum = crc_1021(message)
        message[-2] = checksum >> 8
        message[-1] = checksum & 0xFF

        # Build command with prefix and escape sequences
        command.append(prefix)
        for byte in message:
            if byte in ESCAPE_BYTES:
                command.append(0x1B)  # Escape character
                command.append(byte ^ 0xFF)  # Escaped byte
            else:
                command.append(byte)
        command.append(0x0D)  # Message terminator

        try:
            self.serial.write(command)
        except serial.SerialTimeoutException as e:
            log.error(f"Serial write timeout: {e}")
            raise

    def recv(self) -> Optional[bytearray]:
        """
        Receive and decode a response message from the meter.
        
        Returns:
            The decoded message bytes, or None if receive failed
        """
        received_message = bytearray()
        filtered_message = bytearray()

        # Read message until terminator
        while True:
            received_byte = self._read_byte()
            if received_byte is None:
                return None
            if received_byte == 0x40:  # Message start, reset buffer
                received_message = bytearray()
            received_message.append(received_byte)
            if received_byte == 0x0D:  # Message terminator
                break

        # Decode escaped bytes
        i = 1
        while i < len(received_message) - 1:
            if received_message[i] == 0x1B:  # Escape character
                if i + 1 >= len(received_message):
                    log.error("Incomplete escape sequence")
                    return None
                value = received_message[i + 1] ^ 0xFF
                if value not in ESCAPE_BYTES:
                    log.warning(f"Unexpected escaped byte: 0x{value:02x}")
                filtered_message.append(value)
                i += 2
            else:
                filtered_message.append(received_message[i])
                i += 1

        # Verify CRC
        if crc_1021(filtered_message):
            log.error("CRC error in received message")
            return None

        # Return message without CRC bytes
        return filtered_message[:-2]

    def readparameter(self, parameter: int) -> Optional[float]:
        """
        Read a specific parameter from the meter.
        
        Args:
            parameter: The parameter register address to read
            
        Returns:
            The parameter value as a float, or None if read failed
        """
        # Send read parameter command
        self.send(0x80, (0x3F, 0x10, 0x01, parameter >> 8, parameter & 0xFF))
        received_message = self.recv()

        if received_message is None:
            log.warning("No response from meter")
            return None
            
        # Validate response format
        if (
            len(received_message) < 4
            or received_message[0] != 0x3F
            or received_message[1] != 0x10
            or received_message[2] != parameter >> 8
            or received_message[3] != parameter & 0xFF
        ):
            log.warning("Invalid response format from meter")
            return None

        if len(received_message) < 7:
            log.warning("Response too short")
            return None

        # Decode the mantissa (variable length)
        mantissa_length = received_message[5]
        if len(received_message) < 7 + mantissa_length:
            log.warning("Incomplete mantissa in response")
            return None
            
        value = 0
        for i in range(mantissa_length):
            value <<= 8
            value |= received_message[i + 7]

        # Decode the exponent
        exponent_byte = received_message[6]
        exponent = exponent_byte & 0x3F
        if exponent_byte & 0x40:  # Negative exponent
            exponent = -exponent
        scale_factor = math.pow(10, exponent)
        if exponent_byte & 0x80:  # Negative value
            scale_factor = -scale_factor
            
        return float(value * scale_factor)