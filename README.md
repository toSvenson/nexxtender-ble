# Nexxtender Home Bluetooth Controller

Control your Nexxtender Home EV charger locally over bluetooth. 

Automate, schedule and control your EV charging with Home Assistant.

## What you'll need

- A Raspberry Pi Zero W within BLE range of the charger and Wi-Fi connected.
- An MQTT Broker (e.g., Mosquitto) for send instructions and receive status updates.
- Home Assistant for controlling the charger.
- (optional) HACS "Nexxtmove for Home Assistant" component

## How it works

The Raspberry Pi subscribes to the MQTT Broker to receive instruction from Home Assistant.
When connected to the Nexxtender Home charger it can start/stop charging and read charging details.

## Possible actions

- Enable / Disable Bluetooth connection
- Start charging with profiles: Default, Max, Auto, Eco
- Stop charging
- Read Basic Charge information

## Setup on Raspberry Pi

Install [Raspberry Pi OS](https://www.raspberrypi.com/software/) or [DietPi](https://dietpi.com/) on a Raspberry Pi (Zero W).

(Optional) Install Python with [pyenv](https://github.com/pyenv/pyenv) to have full control in a very easy to manage way. Update 

```
$ curl https://pyenv.run | bash
$ pyenv install 3.9
$ pyenv global 3.9
```

The working dir is `/opt/nexxtender`

Python packages are installed globally since the device will serve no other purpose, use venv if needed.

### First time bluetooth pairing

Manually pair the Raspberry Pi once to enable the scripts to connect in subsequent steps.

#### Retrieve the Bluetooth 6 digit PIN code to pair with the charger

Each Nexxtender Home charger has a unique predefined PIN code.

1. **Easy way** - install the Home Assistant HACS component "Nexxtmove for Home Assistant" 

    [![Open your Home Assistant instance and open the repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg?style=flat-square)](https://my.home-assistant.io/redirect/hacs_repository/?owner=geertmeersman&repository=nexxtmove&category=integration)

    This HA component will log in on the Nexxtmove portal to retrieve information, including the PIN code. This component is also very useful to visualise charging history.

    The 6 digit PIN code will be visible as a sensor of the nexxtmove device:
    `sensor.nexxtmove_<emailaddress>_charging_device_<deviceid>_pin` 

2. **Hard(er) way** - if you don't have portal access or don't use Home Assistant

    This process requires an Android device with Developer Mode enabled and ADB (Android Debug Bridge)
    ``` 
    $ adb root
    $ adb shell
    $ adb pull /data/data/com.powerdale.nexxtender/shared_prefs/prefs_volley.xml
    ```
    Search for `"pin"` in the XML file to get the 6 digit PIN code.

#### Find the Bluetooth Device Address (aka Bluetooth MAC Address) and Pair:

Make sure the bluetooth service is "Active (running)":
```
$ service bluetooth status
```

If needed, enable and start the service:
```
$ sudo systemctl enable bluetooth.service
$ sudo service bluetooth start
```

Scan for BLE devices in range and pair with PIN code:
```
[BT]# power on
[BT]# agent on
[BT]# default-agent
[BT]# discoverable on
[BT]# pairable on
[BT]# scan on

Look for response like this:
[CHG] Device FB:XX:XX:XX:XX:XX RSSI: -70
[CHG] Device FB:XX:XX:XX:XX:XX Name: HOME
[CHG] Device FB:XX:XX:XX:XX:XX Alias: HOME

[BT]# pair <MAC_ADDRESS_HERE>
[BT]# exit
```

### Install scripts on Raspberry Pi

``` 
$ sudo mkdir /opt/nexxtender/scripts
``` 

Deploy scripts to the following locations:
```
 /etc/systemd/system/mqtt-launcher.service
 /opt/nexxtender/launcher.conf
 /opt/nexxtender/mqtt-launcher.py
 /opt/nexxtender/requirements.txt
 /opt/nexxtender/scripts/ble_on.py
 /opt/nexxtender/scripts/ble_off.py
 /opt/nexxtender/scripts/charge.py
 /opt/nexxtender/scripts/basic_charge_read.py
```

Update the following scripts with the Bluetooth Device Address:
```
## /opt/nexxtender/scripts/basic_charge_read.py
address = "<MAC_ADDRESS_HERE>"

## /opt/nexxtender/scripts/charge.py
address = "<MAC_ADDRESS_HERE>"
```

Install the Python packages
``` 
$ cd /opt/nexxtender/
$ sudo pip install -r requirements.txt
$ cd /opt/nexxtender/scripts
$ sudo pip install -r requirements.txt
```

#### mqtt-launcher config 

Edit launcher.conf, enter IP, username and password to connect to the MQTT Broker:
```
mqtt_broker     = '<IP_ADDRESS_HERE>' 
mqtt_username   = '<USERNAME_HERE>'
mqtt_password   = '<PASSWORD_HERE>'
```

#### install systemd service

make sure to deploy `/etc/systemd/system/mqtt-launcher.service` 

```
$ sudo systemctl daemon-reload

$ sudo systemctl start mqtt-launcher.service
$ sudo systemctl restart mqtt-launcher.service

Enable service to automatically start on startup
$ sudo systemctl enable mqtt-launcher

Check status
$ sudo systemctl status mqtt-launcher

Check logs
$ sudo journalctl -S today -u mqtt-launcher.service
```

### Disable swap to lower SD usage (optional)

```
$ sudo dphys-swapfile swapoff
$ sudo dphys-swapfile uninstall
$ sudo update-rc.d dphys-swapfile remove
$ sudo apt purge dphys-swapfile
```

## Home Assistant Setup

Add the following sensors, scripts and automations to Home Assistant.


### MQTT Sensors

Add [MQTT Sensors](https://www.home-assistant.io/integrations/sensor.mqtt/) to the HA configuration.


Add the following to `/homeassistant/configuration.yaml` to load separate mqtt sensors file:
```
mqtt:
  sensor: !include_dir_merge_list mqtt/sensor/
```

Create `/homeassistant/mqtt/sensor/powerdale_home.yaml` with the sensors :

```
- state_topic: "powerdale/data/report"
  name: "Powerdale Charger Timestamp"
  unique_id: "powerdale_timestamp"
  value_template: "{{ value_json.timestamp }}"
  device_class: timestamp
- state_topic: "powerdale/data/report"
  name: "Powerdale Charger Status"
  unique_id: "powerdale_status"
  value_template: "{{ value_json.charging_status }}"
- state_topic: "powerdale/data/report"
  name: "Powerdale Charger Status Raw"
  unique_id: "powerdale_status_raw"
  value_template: "{{ value_json.charging_status_raw }}"
- state_topic: "powerdale/data/report"
  name: "Powerdale Charging Seconds"
  unique_id: "powerdale_seconds"
  value_template: "{{ value_json.charging_seconds }}"
  unit_of_measurement: 's'
  device_class: duration
- state_topic: "powerdale/data/report"
  name: "Powerdale Charging Time"
  unique_id: "powerdale_time"
  value_template: "{{ value_json.charging_hhmmss }}"
- state_topic: "powerdale/data/report"
  name: "Powerdale Charging Discriminator Raw"
  unique_id: "powerdale_discriminator_raw"
  value_template: "{{ value_json.charging_discriminator_raw }}"  
- state_topic: "powerdale/data/report"
  name: "Powerdale Charging Discriminator"
  unique_id: "powerdale_discriminator"
  value_template: "{{ value_json.charging_discriminator }}"  
- state_topic: "powerdale/data/report"
  name: "Powerdale Charging Energy"
  unique_id: "powerdale_energy"
  value_template: "{{ value_json.charging_energy | float }}"
  unit_of_measurement: 'Wh'
  device_class: energy
  state_class: total_increasing
- state_topic: "powerdale/data/report"
  name: "Powerdale Charging Energy kWh"
  unique_id: "powerdale_energy_kwh"
  value_template: "{{ value_json.charging_energy_kwh | float }}"
  unit_of_measurement: 'kWh'
  device_class: energy
  state_class: total_increasing
- state_topic: "powerdale/data/report"
  name: "Powerdale Charging Phases"
  unique_id: "powerdale_phases"
  value_template: "{{ value_json.charging_phases | int }}"  

```

### Script - Nexxtender - Bluetooth On
```
alias: Nexxtender - Bluetooth On
sequence:
  - service: mqtt.publish
    data:
      qos: "0"
      retain: false
      topic: powerdale/ble
      payload: "on"
  - delay:
      hours: 0
      minutes: 0
      seconds: 5
      milliseconds: 0
mode: single
```

### Script - Nexxtender - Bluetooth Off
```
alias: Nexxtender - Bluetooth Off
sequence:
  - service: mqtt.publish
    data:
      qos: "0"
      retain: false
      topic: powerdale/ble
      payload: "off"
  - delay:
      hours: 0
      minutes: 0
      seconds: 5
      milliseconds: 0
mode: single
```

### Script - Nexxtender - Start Charging
```
alias: Nexxtender - Start Charging
sequence:
  - service: mqtt.publish
    data:
      qos: "0"
      retain: false
      topic: powerdale/start
      payload: default
  - delay:
      hours: 0
      minutes: 1
      seconds: 0
      milliseconds: 0
mode: single
```

### Script - Nexxtender - Stop Charging
```
alias: Nexxtender - Stop Charging
sequence:
  - service: mqtt.publish
    data:
      qos: 0
      retain: false
      topic: powerdale/stop
  - delay:
      hours: 0
      minutes: 1
      seconds: 0
      milliseconds: 0
mode: single
```

### Script - Nexxtender - Trigger Read Basic Data
```
alias: Nexxtender - Trigger Read Basic Data
sequence:
  - service: mqtt.publish
    data:
      qos: "0"
      retain: false
      topic: powerdale/data
      payload: basic
mode: single
```

### Automation - Nexxtender - Set bluetooth on/off
``` 
alias: Nexxtender - Set bluetooth on/off
description: Set carport bluetooth on/off based on helper powerdale_ble toggle
trigger:
  - platform: state
    entity_id:
      - input_boolean.powerdale_ble
condition: []
action:
  - if:
      - condition: state
        entity_id: input_boolean.powerdale_ble
        state: "on"
    then:
      - service: script.nexxtender_bluetooth_on
        data: {}
    else:
      - service: script.nexxtender_bluetooth_off
        data: {}
mode: single
```

### Automation - Nexxtender - Get basic charging data
```
alias: Nexxtender - Get basic charging data
description: Request basic charging data through MQTT
trigger:
  - platform: time_pattern
    minutes: "10"
condition:
  - condition: state
    entity_id: input_boolean.powerdale_ble
    state: "on"
action:
  - service: mqtt.publish
    data:
      qos: 0
      retain: false
      topic: powerdale/data
      payload: basic
mode: single
```
### Automation - Nexxtender - Auto-charge off peak
```
alias: Nexxtender - Auto-charge off peak
description: When boolean is set to charge off peak
trigger:
  - platform: time
    at: "22:01:00"
condition:
  - condition: and
    conditions:
      - condition: state
        entity_id: input_boolean.powerdale_autocharge_offpeak
        state: "on"
      - condition: state
        entity_id: sensor.XXXXXXXXX_range_electric
        attribute: chargingstatus
        state: "2"
action:
  - service: script.nexxtender_start_charging
    data: {}
mode: single
```

### Entities Card with the Nexxtender readings

```
type: entities
entities:
  - entity: sensor.powerdale_charger_timestamp
  - entity: sensor.powerdale_charger_status
  - entity: sensor.powerdale_charging_discriminator
  - entity: sensor.powerdale_charging_time
  - entity: sensor.powerdale_charging_energy_kwh
  - entity: sensor.powerdale_charging_phases
  - entity: script.nexxtender_trigger_read_basic_data
  - entity: input_boolean.powerdale_ble
title: 'Nexxtender Home BLE Charging Data'
```

### Horizontal stack Card with Start / Stop buttons
```
type: horizontal-stack
cards:
  - show_name: true
    show_icon: true
    type: button
    tap_action:
      action: call-service
      service: script.nexxtender_start_charging
      target: {}
    icon: mdi:ev-plug-type2
    name: Start Charging
    show_state: false
    icon_height: 50px
  - show_name: true
    show_icon: true
    type: button
    tap_action:
      action: call-service
      service: script.nexxtender_stop_charging
      target: {}
    icon: mdi:battery-off
    name: Stop Charging
    show_state: false
    icon_height: 50px
```

### Toggle to enable / disable automatic charging (off peak)
```
type: entities
entities:
  - entity: input_boolean.powerdale_autocharge_offpeak
    secondary_info: none
    name: Auto charge off-peak
title: EV Charge
```

## Disclaimer

This repository is for research purposes only, the use of this code is your responsibility.

I take NO responsibility and/or liability for how you choose to use any of the source code available here. By using any of the files available in this repository, you understand that you are AGREEING TO USE AT YOUR OWN RISK. Once again, ALL files available here are for EDUCATION and/or RESEARCH purposes ONLY.


## Credits

[mqtt-launcher](https://github.com/jpmens/mqtt-launcher)

[Nexxtmove for Home Assistant](https://github.com/geertmeersman/nexxtmove)