# Kamstrup Multical 402 MQTT Library

![GitHub](https://img.shields.io/github/license/matthijsvisser/kamstrup-402-mqtt?style=flat-square)
![GitHub Issues](https://img.shields.io/github/issues/matthijsvisser/kamstrup-402-mqtt?style=flat-square)
![GitHub Closed Issues](https://img.shields.io/github/issues-closed/matthijsvisser/kamstrup-402-mqtt?style=flat-square)
![Python Version](https://img.shields.io/badge/python-3.8%2B-blue?style=flat-square)

A Python library that enables communication with Kamstrup Multical heat meters via serial communication and publishes the data to MQTT brokers. This project provides a robust, well-documented solution for integrating Kamstrup heat meters into home automation systems.

## 🏠 Supported Devices

- **Kamstrup Multical 402** (primary support)
- **Kamstrup Multical 603** (confirmed by [seranoo](https://github.com/seranoo))
- **Kamstrup Multical 403** (confirmed by [WobwobRt](https://github.com/WobwobRt) and [spaya1](https://github.com/spaya1))

## ✨ Features

- **Real-time Data Reading**: Continuous monitoring of heat meter parameters
- **MQTT Publishing**: Publishes data to any MQTT broker with configurable QoS and retain settings
- **Flexible Configuration**: YAML-based configuration with validation
- **Multiple Parameters**: Support for energy, temperature, flow, volume, and statistical data
- **Robust Error Handling**: Comprehensive error handling and logging
- **Docker Support**: Ready-to-use Docker container and docker-compose setup
- **Systemd Integration**: Service file for Linux systems
- **TLS/SSL Support**: Secure MQTT connections with certificate authentication

# Contents

- [📋 Requirements](#-requirements)
- [⚙️ Configuration](#️-configuration)
  - [📊 Available Meter Parameters](#-available-meter-parameters)
- [🚀 Installation & Usage](#-installation--usage)
  - [📦 Standard Installation](#-standard-installation)
  - [🔧 Command Line Usage](#-command-line-usage)
  - [🔄 Systemd Service](#-systemd-service)
  - [🐳 Docker Container](#-docker-container)
- [🔌 Hardware Setup](#-hardware-setup)
- [🐛 Troubleshooting](#-troubleshooting)
- [🤝 Contributing](#-contributing)

## 📋 Requirements

### Software Requirements
- **Python 3.8+** with pip package manager
- **MQTT Broker** (e.g., [Mosquitto](https://mosquitto.org/), Home Assistant, etc.)

### Hardware Requirements
- **Infrared USB Cable**: Compatible IR read/write head such as:
  - [IR Schreib/Lesekopf USB (Optokopf)](https://shop.weidmann-elektronik.de/index.php?page=product&info=24)
  - Any compatible infrared optical reader for Kamstrup meters

### Python Dependencies
Core dependencies are automatically installed:
- `paho-mqtt` - MQTT client library
- `pyserial` - Serial communication
- `PyYAML` - Configuration file parsing

## ⚙️ Configuration

The library uses a `config.yaml` file for all settings. Here's a complete example:

```yaml
mqtt:
  host: 192.168.1.100          # MQTT broker IP or hostname
  port: 1883                    # MQTT broker port
  client: kamstrup             # Unique client identifier
  topic: kamstrup              # Base topic for publishing
  qos: 0                       # Quality of Service (0, 1, or 2)
  retain: false                # Retain messages on broker
  authentication: false        # Enable username/password auth
  username: user               # MQTT username (if auth enabled)
  password: password           # MQTT password (if auth enabled)
  tls_enabled: false          # Enable TLS/SSL encryption
  tls_ca_cert: ""             # Path to CA certificate
  tls_cert: ""                # Path to client certificate  
  tls_key: ""                 # Path to client private key
  tls_insecure: true          # Allow insecure TLS connections

serial_device:
  com_port: /dev/ttyUSB0       # Serial port for meter communication

kamstrup:
  parameters:                  # List of parameters to read
    - energy
    - volume
    - temp1
    - temp2
    - flow
  poll_interval: 28            # Reading interval in minutes (< 30 recommended)
```

### 📊 Available Meter Parameters

| Parameter | Description | Unit |
|-----------|-------------|------|
| `energy` | Total energy consumption | GJ |
| `power` | Current power consumption | kW |
| `temp1` | Inlet temperature | °C |
| `temp2` | Outlet temperature | °C |
| `tempdiff` | Temperature difference | °C |
| `flow` | Current flow rate | l/h |
| `volume` | Total volume consumption | m³ |
| `minflow_m` | Minimum flow this month | l/h |
| `maxflow_m` | Maximum flow this month | l/h |
| `minpower_m` | Minimum power this month | kW |
| `maxpower_m` | Maximum power this month | kW |
| `avgtemp1_m` | Average inlet temp this month | °C |
| `avgtemp2_m` | Average outlet temp this month | °C |
| `*_y` | Yearly statistics | Various |
| `temp1xm3` | Temperature 1 × volume | °C×m³ |
| `temp2xm3` | Temperature 2 × volume | °C×m³ |
| `infoevent` | Information events | - |
| `hourcounter` | Operating hours | h |

> **Note**: Add at least one parameter to your configuration. Poll intervals ≥30 minutes may cause the meter to enter standby mode.

## 🚀 Installation & Usage

### 📦 Standard Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/matthijsvisser/kamstrup-402-mqtt.git
   cd kamstrup-402-mqtt
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure the application:**
   ```bash
   cp config.yaml config.yaml.backup
   # Edit config.yaml with your settings
   nano config.yaml
   ```

### 🔧 Command Line Usage

Run the daemon directly from the command line:

```bash
python3 daemon.py
```

Run as a background process:
```bash
python3 daemon.py &
```

**Example Output:**
```
[2024-01-15 10:30:15 mqtt_handler.py publish:56 - INFO - Publishing 'kamstrup/values' '{"energy": 227.445, "volume": 2131.935, "temp1": 52.81, "temp2": 39.94}' to 192.168.1.100:1883]
```

You can monitor the published data using [MQTT Explorer](https://mqtt-explorer.com/) or subscribe to the topic:
```bash
mosquitto_sub -h your-mqtt-broker -t "kamstrup/values"
```

### 🔄 Systemd Service

For automatic startup and better process management on Linux systems:

1. **Edit the service file:**
   ```bash
   sudo cp kamstrup2mqtt.service /etc/systemd/system/
   sudo nano /etc/systemd/system/kamstrup2mqtt.service
   ```
   
   Update the paths in the service file:
   ```ini
   [Unit]
   Description=Kamstrup2mqtt Service
   After=multi-user.target

   [Service]
   Type=simple
   WorkingDirectory=/opt/kamstrup  # Update this path
   ExecStart=/usr/bin/python3 /opt/kamstrup/daemon.py  # Update this path
   StandardOutput=null
   StandardError=journal
   Restart=always
   User=kamstrup  # Optional: run as specific user

   [Install]
   WantedBy=multi-user.target
   ```

2. **Enable and start the service:**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable kamstrup2mqtt.service
   sudo systemctl start kamstrup2mqtt.service
   ```

3. **Monitor the service:**
   ```bash
   sudo systemctl status kamstrup2mqtt.service
   sudo journalctl -u kamstrup2mqtt.service -f
   ```

### 🐳 Docker Container

Docker provides an isolated environment and easy deployment.

#### Prerequisites
- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/) (recommended)

#### Quick Start with Docker Compose

1. **Edit docker-compose.yml:**
   ```yaml
   version: '3.8'
   services:
     kamstrup:
       build: .
       container_name: kamstrup-mqtt
       devices:
         - /dev/ttyUSB0:/dev/ttyUSB0  # Update device path
       volumes:
         - ./config.yaml:/opt/kamstrup/config.yaml:ro
         - ./logs:/opt/kamstrup/logs
       restart: unless-stopped
   ```

2. **Start the container:**
   ```bash
   docker-compose up -d
   ```

#### Manual Docker Usage

1. **Build the image:**
   ```bash
   docker build -t kamstrup-mqtt .
   ```

2. **Run the container:**
   ```bash
   docker run -d \
     --name kamstrup-mqtt \
     --device=/dev/ttyUSB0:/dev/ttyUSB0 \
     -v $(pwd)/config.yaml:/opt/kamstrup/config.yaml:ro \
     -v $(pwd)/logs:/opt/kamstrup/logs \
     --restart unless-stopped \
     kamstrup-mqtt
   ```

#### Container Management

```bash
# View logs
docker logs -f kamstrup-mqtt

# Stop container
docker stop kamstrup-mqtt

# Start container
docker start kamstrup-mqtt

# Restart container
docker restart kamstrup-mqtt

# Remove container
docker rm kamstrup-mqtt
```

## 🔌 Hardware Setup

Proper positioning of the infrared head is crucial for reliable communication.

<img src="images/meter_setup.jpg" alt="Kamstrup meter setup showing IR head placement" width="300"/>

**Setup Tips:**
- Position the IR head as shown in the image above
- The optimal position may vary between meter models
- You might need to position the head slightly higher than the meter's distance guides suggest
- Ensure the IR head makes good contact with the meter's optical interface
- Test different positions if you experience communication issues

## 🐛 Troubleshooting

### Check the Logs

The application creates detailed logs in the `logs/` directory:

```bash
# View current log in real-time
tail -f logs/debug.log

# View recent errors
grep ERROR logs/debug.log

# View MQTT publishing activity
grep "Publishing" logs/debug.log
```

### Common Issues

#### 🔄 **Meter Communication Issues**

**Problem:** No response from meter or timeout errors

**Solutions:**
1. **Wake up the meter** - Press any button on the meter display
2. **Check IR head positioning** - Try slightly different positions
3. **Verify serial port** - Ensure correct device path in config
4. **Check permissions** - User must have access to serial port:
   ```bash
   sudo usermod -a -G dialout $USER
   # Log out and back in
   ```

#### 📶 **MQTT Connection Issues**

**Problem:** Failed to connect to MQTT broker

**Solutions:**
1. **Test broker connectivity:**
   ```bash
   mosquitto_pub -h your-broker-ip -t test -m "hello"
   ```
2. **Check authentication settings** in config.yaml
3. **Verify network connectivity** and firewall rules
4. **Check broker logs** for connection attempts

#### 🔍 **Finding the Serial Port**

**Linux:**
```bash
# Before plugging in the IR cable
ls /dev/tty*

# After plugging in the IR cable
ls /dev/tty*
# Look for new device, usually /dev/ttyUSB0

# Alternative: check dmesg
dmesg | grep tty
```

**Windows:**
- Check Device Manager under "Ports (COM & LPT)"
- Look for "USB Serial Port" or similar

#### ⚙️ **Configuration Validation**

**Problem:** Configuration errors or validation failures

**Solutions:**
1. **Validate YAML syntax:**
   ```bash
   python3 -c "import yaml; yaml.safe_load(open('config.yaml'))"
   ```
2. **Check required sections** are present
3. **Verify parameter names** against the supported list
4. **Ensure numeric values** are properly formatted

#### 🐳 **Docker Issues**

**Problem:** Container cannot access serial device

**Solutions:**
1. **Check device mapping** in docker-compose.yml
2. **Verify device permissions:**
   ```bash
   ls -l /dev/ttyUSB0
   ```
3. **Run container with privileged mode** (for testing):
   ```bash
   docker run --privileged --device=/dev/ttyUSB0 kamstrup-mqtt
   ```

### Performance Optimization

- **Poll Interval:** Keep under 30 minutes to prevent meter standby
- **MQTT QoS:** Use QoS 0 for better performance, QoS 1 for reliability
- **Logging Level:** Set to INFO in production to reduce log size

### Getting Help

1. **Enable debug logging** by setting log level to DEBUG
2. **Check existing issues** on GitHub
3. **Provide complete error logs** when reporting issues
4. **Include configuration** (remove sensitive data like passwords)
5. **Specify hardware details** (meter model, IR cable, OS)

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

**Quick Start for Contributors:**
1. Fork the repository
2. Create a feature branch
3. Make your changes with proper documentation
4. Add type hints and docstrings
5. Test thoroughly
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Original Kamstrup protocol implementation by Poul-Henning Kamp
- Protocol modifications by Frank Reijn and Paul Bonnemaijers
- Community contributions for additional meter model support

---

**Need help?** Open an issue on GitHub or check the troubleshooting section above.
