#!/usr/bin/python3

# *************************************************************************
# A Rest API for Tuya Smart Bulbs 
# Allows JSON requests to be sent over a network to control bulb colour,
#   brightness, and more, using FastAPI, uvicorn, and TinyTuya
# See https://github.com/TimboFimbo/TuyaSmartBulbs_API for more information

# *************************************************************************

import json
import tinytuya
from time import sleep
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# Start by setting all the bulbs from the included snapshot.json file
# File can be obtained by running 'python3 -m tinytuya scan'
# File will only be generated correctly if 'python3 -m tinytuya wizard'
#   has previously been run successfully, and device keys obtained
# See https://pypi.org/project/tinytuya/#description for more information

CON_TIMEOUT = 2
RETRY_LIMIT = 1

class BulbObject:
    def __init__(self, name_in, dev_id_in, address_in, local_key_in, version_in):
        self.name = name_in
        self.bulb = tinytuya.BulbDevice(
            dev_id = dev_id_in,
            address = address_in,
            local_key = local_key_in,
            connection_timeout = CON_TIMEOUT,
            version = version_in
        )

bulbs : BulbObject = []

# set path of snapshot file here, or place a copy into this folder
with open('./snapshot.json', 'r') as infile:
    bulb_json = json.load(infile)

for bulb in bulb_json['devices']:
    bulbs.append(BulbObject(
    name_in=bulb['name'],
    dev_id_in=bulb['id'],
    address_in=bulb['ip'],
    local_key_in=bulb['key'],
    version_in=bulb['ver']
))
    
for this_bulb in bulbs:
    this_bulb.bulb.set_socketPersistent(True)
    this_bulb.bulb.set_socketRetryLimit(RETRY_LIMIT)

# Compile all the bulbs into a list with a true or false toggle
# This list will be added to the JSON classes below

class BulbToggle(BaseModel):
    name: str = ""
    toggle: bool = True

bulb_toggles : BulbToggle = []

for this_bulb in bulbs:
    bulb_toggles.append(BulbToggle(
        name=this_bulb.name,
        toggle=True
    ))

# TODO add 'no_wait'
class PowerClass(BaseModel):
    global bulb_toggles
    power: bool = True
    toggles: list = bulb_toggles

class RgbClass(BaseModel):
    global bulb_toggles
    red: int
    green: int
    blue: int
    toggles: list = bulb_toggles

class BrightnessClass(BaseModel):
    global bulb_toggles
    brightness: int
    toggles: list = bulb_toggles

# API endpoints

# TODO add 'no_wait'
@app.put("/set_power")
def set_bulb_power(power_in: PowerClass):
    for this_bulb in bulbs:
        for this_toggle in power_in.toggles:
            if this_toggle['name'] == this_bulb.name and this_toggle['toggle'] == True:
                if power_in.power == True: this_bulb.bulb.turn_on()
                else: this_bulb.bulb.turn_off()

    return "Power On" if power_in.power == True else "Power Off"

@app.put("/set_colour")
def set_bulb_colour(rgb: RgbClass):
    for this_bulb in bulbs:
        for this_toggle in rgb.toggles:
            if this_toggle['name'] == this_bulb.name and this_toggle['toggle'] == True:
                this_bulb.bulb.set_colour(rgb.red, rgb.green, rgb.blue)

    return "Colour changed to ({}, {}, {})".format(rgb.red, rgb.green, rgb.blue)

@app.put("/set_brightness")
def set_bulb_brightness(brightness_in: BrightnessClass):
    for this_bulb in bulbs:
        for this_toggle in brightness_in.toggles:
            if this_toggle['name'] == this_bulb.name and this_toggle['toggle'] == True:
                this_bulb.bulb.set_brightness(brightness_in.brightness)

    return "Brightness changed to {}".format(brightness_in.brightness)