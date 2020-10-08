# Kamstrup multical 402 MQTT library
This project provides a Python library that enables communication with the Kamstrup Multical 402 heat meter. The configured parameters will be read from the meter at a certain interval and published in MQTT messages.

# Contents
  * [Requirements](#Requirements)
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

## Requirements
* Python 3
  * [Pyserial](https://pypi.org/project/pyserial/)
  * [Paho MQTT](https://pypi.org/project/paho-mqtt/)
  * [Yaml](https://pypi.org/project/yaml-1.3/)
* MQTT broker e.g.: [Mosquitto](https://mosquitto.org/)
* Infrared read/write USB cable e.g.: [IR Schreib/Lesekopf USB (Optokopf)](https://shop.weidmann-elektronik.de/index.php?page=product&info=24)

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


  * [Running the script](#Running-the-script)
    * [on the command line](#Running-on-the-commandline)
    * [as a service with systemd](#Running-as-a-systemd-service)

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
If you have any troubles with retrieving the values from the meter, make sure that the meter is 'awake', you can do so by pressing any button on the meter. It is also important that you've positioned the meter head correctly. I may take a while to find the sweet spot. For some reason the position for the meter head that I've got is a little bit higher than what the distance keepers on the meter suggest.

### Finding the correct com port
Unplug the usb connector from the computer and plug it back in. Use dmesg to find the com port.
``` bash
dmesg
```
