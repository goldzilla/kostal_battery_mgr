#!/usr/bin/env python

import pymodbus
from datetime import datetime
from pymodbus.client import ModbusTcpClient
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.payload import BinaryPayloadBuilder
import time
import os

INVERTER_IP = "192.168.1.30"
INVERTER_PORT = "1502"

# Define the path to the file
STATE_FILE_PATH = "kostal_battery_state"

# Charging power (percentage of inverter nominal power, enter a negative a number)
# For example:
# Kostal Plenticore Plus 7.0, nominal power is 7 kW. CHARGE_POWER -0.85 means that
# battery will be charged with 7kW * 0.85 = 5.95 kW power.
CHARGE_POWER = -85.0

# Forced discharging power (percentage of inverter nominal power, enter a positive number)
DISCHARGE_POWER = 85.0

# time between operations
SLEEP_TIME = 60

# Minimum SoC
MINIMUM_SOC = 10.0

############################################

STATE_BLOCKED = 0
STATE_CHARGING = 1
STATE_NORMAL = 2
STATE_FORCED_DISCHARGE = 3
STATE_UNDEFINED = 255

state = STATE_UNDEFINED

#-----------------------------------------
# Routine to read a float
def readfloat(client,myadr_dec,unitid):
    r1=client.read_holding_registers(myadr_dec,2,slave=unitid)
    FloatRegister = BinaryPayloadDecoder.fromRegisters(r1.registers, byteorder=Endian.BIG, wordorder=Endian.LITTLE)
    result_FloatRegister =round(FloatRegister.decode_32bit_float(),2)
    return(result_FloatRegister)

# Routine to write a float
def writefloat(client,myadr_dec,unitid,myfloat):
    builder = BinaryPayloadBuilder(byteorder=Endian.BIG, wordorder=Endian.LITTLE)
    builder.reset()
    builder.add_32bit_float(myfloat)
    payload = builder.build()
    result_write = client.write_registers(myadr_dec, payload, skip_encode=True, slave=unitid)
    return result_write

def block_discharge():
    global state

    try:
        # connection Kostal
        client = ModbusTcpClient(INVERTER_IP,port=INVERTER_PORT)
        client.connect()

        # stop charging if we were previously charging
        if state == STATE_CHARGING:
            writefloat(client, 1034, 71, 0.0)

        batteryminimumsoc = readfloat(client,1042,71)

        # Battery discharge is blocked by setting minimum SoC to 100%
        if batteryminimumsoc < 99:
            writefloat(client, 1042, 71, 100.0)
            batteryminimumsoc = readfloat(client,1042,71)

        state = STATE_BLOCKED

        print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " minimum SoC (%): ", batteryminimumsoc)
    except Exception as ex:
        print ("ERROR: ", ex)
    finally:
        client.close()

def permit_normal_discharge():
    global state

    if state != STATE_NORMAL:
        try:
            #connection Kostal
            client = ModbusTcpClient(INVERTER_IP,port=INVERTER_PORT)
            client.connect()

            # stop charging if we were previously charging
            if state == STATE_CHARGING:
                writefloat(client, 1034, 71, 0.0)

            batteryminimumsoc = readfloat(client,1042,71)

            # reduce minimum SoC in case it was set to a higher number
            # (discharge was blocked)
            if batteryminimumsoc != MINIMUM_SOC:
                print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " modifying SoC to ", MINIMUM_SOC)
                writefloat(client, 1042, 71, MINIMUM_SOC)
                batteryminimumsoc = readfloat(client,1042,71)

            state = STATE_NORMAL

            print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " minimum SoC (%): ", batteryminimumsoc)

        except Exception as ex:
            print ("ERROR: ", ex)
        finally:
            client.close()


def charge_battery():
    global state

    try:

        #connection Kostal
        client = ModbusTcpClient(INVERTER_IP,port=INVERTER_PORT)
        client.connect()

        batterypercent = readfloat(client,210,71)
        print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " battery (%): ", batterypercent)

        writefloat(client, 1036, 71, CHARGE_POWER)

        state = STATE_CHARGING

    except Exception as ex:
        print ("ERROR Kostal: ", ex)
    finally:
        client.close()

def force_discharge():
    global state

    try:

        #connection Kostal
        client = ModbusTcpClient(INVERTER_IP,port=INVERTER_PORT)
        client.connect()

        batterypercent = readfloat(client,210,71)
        print (datetime.now().strftime("%d/%m/%Y %H:%M:%S") + " battery (%): ", batterypercent)

        writefloat(client, 1036, 71, DISCHARGE_POWER)

        state = STATE_FORCED_DISCHARGE

    except Exception as ex:
        print ("ERROR Kostal: ", ex)
    finally:
        client.close()

while True:
    try:
        # Check if the file exists and get its modification time
        if os.path.exists(STATE_FILE_PATH):
            file_mod_time = os.path.getmtime(STATE_FILE_PATH)
            current_time = time.time()

            # Check if the file is older than one hour (3600 seconds + 60 seconds to make sure we don't toggle unnecessarily)
            if current_time - file_mod_time < 3660:
                # Open and read the file
                with open(STATE_FILE_PATH, "r") as file:
                    content = file.read()

                # Perform actions based on the content of the file
                if "0" in content:
                    print("Blocking battery discharge.")
                    block_discharge()
                elif "1" in content:
                    print("Charging battery from grid.")
                    charge_battery()
                elif "2" in content:
                    print("Permit normal discharge.")
                    permit_normal_discharge()
                elif "3" in content:
                    print("Force discharge (to grid, if no local consumption).")
                    force_discharge()
            else:
                print(f"File {STATE_FILE_PATH} is older than one hour, continue with inverter-controlled battery management.")
                permit_normal_discharge()

        else:
            print(f"The file {STATE_FILE_PATH} does not exist, continue with inverter-controlled battery management.")
            permit_normal_discharge()


        # Wait for a specified time before the next check
        time.sleep(SLEEP_TIME)  # Check the file periodically

    except KeyboardInterrupt:
        print("Loop interrupted by user.")
        break

