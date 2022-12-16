# Kamstrup multical 402 MQTT library
This project provides a Python library that enables communication with the Kamstrup Multical 402 heat meter. The configured parameters will be read from the meter at a certain interval and published in MQTT messages.

## Contents
  * [Requirements](#Requirements)
  * [Installation](#Installation)
  * [Configuration file](#Configuration-file)
    * [Kamstrup meter parameters](#Kamstrup-meter-parameters)
  * [Running the script](#Running-the-script)
    * [on the command line](#Running-on-the-commandline)
    * [as a service with systemd](#Running-as-a-systemd-service)
  * [Meter setup](#Meter-setup)
  * [Troubleshooting](#Troubleshooting)
    * [Read the log file](#Read-the-log-file)
    * [Reading values](#Reading-values)
    * [Finding the correct com port](#Finding-the-correct-com-port)
  * [Add sensors to Home Assistant](#Add-sensors-to-home-assistant)

## Requirements
* Python 3
  * [Pyserial](https://pypi.org/project/pyserial/)
  * [Paho MQTT](https://pypi.org/project/paho-mqtt/)
  * [PyYaml](https://pypi.org/project/PyYAML/)
* MQTT broker e.g.: [Mosquitto](https://mosquitto.org/)
* Infrared read/write USB cable e.g.: IR Schreib/Lesekopf USB (Optokopf) from [shop](https://shop.weidmann-elektronik.de/index.php?page=product&info=24) or [ebay](https://www.ebay.de/itm/274962288487)
* Hardware such as a (Raspberry Zero W)[https://www.raspberrypi.com/products/raspberry-pi-zero-2-w/] with (USB cable)[https://www.raspberrypi.com/products/micro-usb-male-to-usb-a-female-cable/]

## Installation
Following the instructions by [Pieter Brinkman](https://www.pieterbrinkman.com/about-me/) in [this blog post](https://www.pieterbrinkman.com/2022/02/01/make-your-city-heating-stadsverwarming-smart-and-connect-it-home-assistant-energy-dashboard/)

On a Raspberry Zero W, run the following commands to install Python3 and the required packages.
```
sudo su
apt-get update
apt-get install python3-pip
pip3 install pyserial, paho-mqtt, PyAML
```

Install git and clone this repository by
```
apt-get install git
git clone https://github.com/matthijsvisser/kamstrup-402-mqtt.git
```

Configure the script as explained below
```
nano config.yaml
```

Depending on your setup, [add sensors to Home Assistant](#Add-sensors-to-home-assistant).

## Configuration file
The library can be configured to fit your needs using the config.yaml file. The parameters of this file are described below.
| parameter name | description |
| - | - |
| host | MQTT broker host domain name or IP address |
| port | MQTT broker port number |
| client | Client name to identify this MQTT client e.g. Kamstrup |
| topic | MQTT topic where the values are published on |
| retain | If set to true, the message will be set as the "last known good"/retained message for the topic |
| qos | The quality of service level to use for the message. Cane be any value between 0 and 2 |
| authentication | Set this to true if your MQTT broker requires authentication |
| username | Username to connect to broker |
| password | Password to connect to broker |
| com_port | port of serial communication device |
| parameters | List of parameters that are read and published to the configured MQTT topic. See [Meter parameters](#Kamstrup-meter-parameters) table. |
| poll_interval | Meter readout interval in minutes (value should be less than 30 to prevent the meter from going in standby mode|

### Kamstrup meter parameters
These parameters can be added to the config.yaml file. Atleast one parameter must be present in the configuration file.
| parameter name | description |
| - | - |
| energy | consumed energy in GJ |
| power |   |
| temp1 | incoming temperature in degrees |  
| temp2 | outgoing temperature in degrees|
| tempdiff | difference between temp1 and temp2 in degrees |  
| flow | water flow in l/h |
| volume | consumed water in m3 |      
| minflow_m | minimum water flow |
| maxflow_m | minimum water flow  |
| minflowDate_m | |
| maxflowDate_m | |
| minpower_m | |
| maxpower_m | |
| avgtemp1_m | |
| avgtemp2_m | |
| minpowerdate_m | |
| maxpowerdate_m | |
| minflow_y | |
| maxflow_y | |
| minflowdate_y | |
| maxflowdate_y | |
| minpower_y | |
| maxpower_y |  |
| avgtemp1_y |  |
| avgtemp2_y |  |
| minpowerdate_y | |
| maxpowerdate_y | |
| temp1xm3 | |
| temp2xm3 |   |
| infoevent |   |
| hourcounter | |


## Running the script

### Running on the commandline
The script can be started by simply starting the daemon file with Python 3.
``` bash
python3 daemon.py &
```

### Running as a systemd service
Edit the kamstrup_meter.service file and adjust the path accordingly. The working directory in this example is /opt/kamstrup/.
``` bash kamstrup_meter.service
[Unit]
Description=Kamstrup2mqtt Service
After=multi-user.target

[Service]
Type=simple
WorkingDirectory=/opt/kamstrup
ExecStart=/usr/bin/python3 /opt/kamstrup/daemon.py
StandardOutput=null
StandardError=journal
Restart=always

[Install]
WantedBy=multi-user.target
```
Check if the service has the required permissions after copying, if not, change it with chmod and chown.
``` bash
cp /opt/kamstrup/kamstrup_meter.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable kamstrup_meter.service
sudo service kamstrup_meter start
```

## Meter setup
It can be hard to find the correct position of the meter head. It might differ if you are using an other model. I positioned the infrared head as follows:

<img src="images/meter_setup.jpg" alt="meter setup" width="200"/>

## Troubleshooting
This section includes some tips to solve some issues.

### Read the log file
The log file will, in most cases, spoil what going on if something's not working.
``` bash
tail -f debug.log
```
### Reading values
If you have any troubles with retrieving the values from the meter, make sure that the meter is 'awake', you can do so by pressing any button on the meter. The meter will stay awake for at most 30 minutes when there is no IR activities nor any buttons pressed. It is also important that you've positioned the meter head correctly. I may take a while to find the sweet spot. For some reason the position for the meter head that I've got is a little bit higher than what the distance keepers on the meter suggest.

In order to find the right spot on the meter, it helps to set the ```poll_interval``` interval to 0 and [run the daemon from the command line](#Running-on-the-commandline) so that the daemon keeps trying to read out values. [Watch the log file](#Read-the-log-file) until you see values reported back.  

### Finding the correct com port
Unplug the usb connector from the computer/raspberry pi and plug it back in. Use dmesg to find the com port reported as one of the last few messages.
``` bash
dmesg
```

### Restarting the daemon
Use
```
ps -aef | grep python
```
to list all python3 processes. You can kill the daemon with
```
kill -9 [process id]
```
where ```[process id]``` is the id displayed by the ```ps``` command above.

## Add sensors to Home Assistant
Adapted from the instructions by [Pieter Brinkman](https://www.pieterbrinkman.com/about-me/) in [this blog post](https://www.pieterbrinkman.com/2022/02/01/make-your-city-heating-stadsverwarming-smart-and-connect-it-home-assistant-energy-dashboard/), updated according to the [MQTT integration in Home Assistant](https://www.home-assistant.io/integrations/sensor.mqtt/).

1. Install and configure the Mosquitto MQTT broker addon in Home Assistant, following [these instructions](https://github.com/home-assistant/addons/blob/master/mosquitto/DOCS.md). In the process, you create [a new Home Assistant user](http://homeassistant.local:8123/config/users).

2. In the ```config.yaml``` of this script, set ```authentication: True``` and add the username and password of the Home Assistant user you created in step 1.

3. If the daemon is working correctly, you can listen to the ```kamstrup/values``` in the [MQTT settings](http://homeassistant.local:8123/config/mqtt)

4. Edit ```configuration.yaml``` in Home Assistant and add the following sensors:

```
mqtt:
  sensor:
    - name: "CH_Consumed_Energy"
      unique_id: "CH_Consumed_Energy"
      state_topic: "kamstrup/values"
      value_template: "{{ value_json.energy }}"
      unit_of_measurement: "GJ"
    - name: "CH_Consumed_Water"
      state_topic: "kamstrup/values"
      value_template: "{{ value_json.volume }}"
      unit_of_measurement: "m³"
    - name: "CH_Temperature_in"
      state_topic: "kamstrup/values"
      value_template: "{{ value_json.temp1 }}"
      unit_of_measurement: "°C"
    - name: "CH_Temperature_out"
      state_topic: "kamstrup/values"
      value_template: "{{ value_json.temp2 }}"
      unit_of_measurement: "°C"
    - name: "CH_Temperature_diff"
      state_topic: "kamstrup/values"
      value_template: "{{ value_json.tempdiff }}"
      unit_of_measurement: "°C"
    - name: "CH_Current_flow"
      state_topic: "kamstrup/values"
      value_template: "{{ value_json.flow }}"
      unit_of_measurement: "l/uur"
    - name: "CH_to_Gas"
      state_topic: "kamstrup/values"
      # apply formula to value to translate to gas
      value_template: "{{ value_json.energy | float * 32 }}"
      unit_of_measurement: "m³"
      state_class: 'total_increasing'
      # Set device class to gas so we can use the sensor in the energy dashboard
      device_class: 'gas'
```
