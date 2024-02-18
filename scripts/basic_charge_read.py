import sys
import argparse
from datetime import datetime
import pytz
import struct
import asyncio
from bleak import BleakClient
from loguru import logger

logger.add("error.log", rotation="10 MB")

address = "<MAC_ADDRESS_HERE>"
ChargingBasicDataUUID = "fd47416a-95fb-4206-88b5-b4a8045f75cf"
timestamp = pytz.timezone("Europe/Brussels").localize(datetime.now()).strftime("%Y-%m-%dT%H:%M:%S%z")


parser = argparse.ArgumentParser()
parser.add_argument('--output', type=str, default="json")
args = parser.parse_args()


def convert_seconds_to_hhmmss(seconds):
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    return '{:02d}:{:02d}:{:02d}'.format(int(hours), int(minutes), int(seconds))

def is_bytearray_valid(bytearray_obj):
    if bytearray_obj and all(isinstance(byte, int) and 0 <= byte <= 255 for byte in bytearray_obj):
        return True
    else:
        return False

async def main(address):
    async with BleakClient(address) as client:
        await asyncio.sleep(0.5)
        result_ba = await client.read_gatt_char(ChargingBasicDataUUID)
        await client.disconnect()
        #print(f'Bytearray: {result_ba}')

        ## Manueel uitgerekend
        charging_seconds = result_ba[1]*256+result_ba[0]
        charging_discriminator_raw = result_ba[2]
        charging_status_raw = chr(result_ba[3])
        charging_energy = result_ba[11]*16777216+result_ba[10]*65536+result_ba[9]*256+result_ba[8] 
        charging_phases = result_ba[13]

        charging_hhmmss = convert_seconds_to_hhmmss(charging_seconds)

        if charging_discriminator_raw == 1:
            charging_discriminator = "started"
        elif charging_discriminator_raw == 2:
            charging_discriminator = "charging"
        elif charging_discriminator_raw == 3:
            charging_discriminator = "stopped"
        else:
            charging_discriminator_raw = 0
            charging_discriminator = "unknown"

        # IEC 61851 standard for EV charging
        # B: Charger is available, but the EV is not connected.
        # C: Charger is currently being connected to the EV.
        # D: Charger is currently supplying energy to the EV.
        # E: EV is fully charged, but still connected to the charger.
        # F: EV is disconnected from the charger, but the charger is still powered on.

        if charging_status_raw == "B":
            charging_status = "plugged"
        elif charging_status_raw == "C":
            charging_status = "charging"
        elif charging_status_raw == "D":
            charging_status = "charging"
        elif charging_status_raw == "E":
            charging_status = "fault"
        elif charging_status_raw == "F":
            charging_status = "fault"
        else:
            charging_status_raw = "A"
            charging_status = "unplugged"

        charging_energy_human = "%.2f kWh" % (charging_energy / 1000.0)
        charging_energy_kwh = "%.2f" % (charging_energy / 1000.0)

        ## Construct json
        result_json = "{"
        result_json += "\"error\": \"0\","
        result_json += "\"timestamp\": \"" + str(timestamp) + "\","
        result_json += "\"charging_seconds\": \"" + str(charging_seconds) + "\","
        result_json += "\"charging_hhmmss\": \"" + str(charging_hhmmss) + "\","
        result_json += "\"charging_discriminator_raw\": \"" + str(charging_discriminator_raw) + "\","
        result_json += "\"charging_discriminator\": \"" + str(charging_discriminator) + "\","
        result_json += "\"charging_status_raw\": \"" + str(charging_status_raw) + "\","
        result_json += "\"charging_status\": \"" + str(charging_status) + "\","
        result_json += "\"charging_energy\": \"" + str(charging_energy) + "\","
        result_json += "\"charging_energy_kwh\": \"" + str(charging_energy_kwh) + "\","
        result_json += "\"charging_phases\": \"" + str(charging_phases) + "\""
        result_json += "}"

        if args.output == "debug":
            print(f'RAW                      : {result_ba}')
            print(f'Error                    : 0')
            print(f'Timestamp                : {timestamp}')
            print(f'Charging Seconds         : {charging_seconds}')
            print(f'Charging time            : {charging_hhmmss}')
            print(f'Charging Discrimator raw : {charging_discriminator_raw}')
            print(f'Charging Discrimator     : {charging_discriminator}')
            print(f'Charging Status raw      : {charging_status_raw}')
            print(f'Charging Status          : {charging_status}')
            print(f'Charging Energy          : {charging_energy}')
            print(f'Charging Energy kWh      : {charging_energy_kwh}')
            print(f'Charging Phases          : {charging_phases}')
            print(result_json)
        elif args.output == "json":
            print(result_json)

try:
    asyncio.run(main(address))
except BleakError as e:
    print(str(e))
except Exception as e:
    logger.exception(e)
    print("{\"error\": \"1\", \"timestamp\": \"" + timestamp + "\"}")
    sys.exit(1)
