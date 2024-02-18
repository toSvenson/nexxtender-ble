import sys
import argparse
from datetime import datetime
import pytz
import asyncio
from bleak import BleakClient
from loguru import logger

logger.add("error.log", rotation="10MB")

address = "<MAC_ADDRESS_HERE>"
timestamp = pytz.timezone("Europe/Brussels").localize(datetime.now()).strftime("%Y-%m-%dT%H:%M:%S%z")

parser = argparse.ArgumentParser()
parser.add_argument('--charge', type=str, default="default")
args = parser.parse_args()

async def charge():
    if args.charge.lower() == "default":
        ba = bytearray(b'\x01\x00')
        print("{\"Timestamp\":\"", timestamp, "\",\"charge\":\"default\",\"error\":0\}")
    elif args.charge.lower() == "max":
        ba = bytearray(b'\x02\x00')
        print("{\"Timestamp\":\"", timestamp, "\",\"charge\":\"max\",\"error\":0}")
    elif args.charge.lower() == "auto":
        ba = bytearray(b'\x03\x00')
        print("{\"Timestamp\":\"", timestamp, "\",\"charge\":\"auto\",\"error\":0}")
    elif args.charge.lower() == "eco":
        ba = bytearray(b'\x04\x00')
        print("{\"Timestamp\":\"", timestamp, "\",\"charge\":\"eco\",\"error\":0}")
    elif args.charge.lower() == "stop":
        ba = bytearray(b'\x06\x00')
        print("{\"Timestamp\":\"", timestamp, "\",\"charge\":\"stop\",\"error\":0}")
    else:
        print("{\"Timestamp\":\"", timestamp, "\",\"charge\":\"unknown\",\"error\":1}")
        return
    
    async with BleakClient(address) as client:
        await asyncio.sleep(0.5)
        result = await client.write_gatt_char(("fd47416a-95fb-4206-88b5-b4a8045f75dd"), ba)
        await client.disconnect()
try:
    asyncio.run(charge())
except Exception as e:
    logger.exception(e)
    print("{\"error\": 1, \"timestamp\": \"" + timestamp + "\"}")

    sys.exit(1)