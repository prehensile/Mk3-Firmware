### Author: EMF Badge team
### Description: Handles connecting to a wifi access point based on a valid wifi.json file
### License: MIT

import network
import os
import json
import pyb

_nic = None
_network = None

def nic():
    global _nic
    if not _nic:
        _nic = network.CC3100()
    return _nic

def create_default_config():
    with open("wifi.json", "wt") as file:
        file.write(json.dumps({"ssid": "emfcamp-insecure"}))
        file.flush()
    os.sync()

def connection_details():
    data = {}
    try:
        if "wifi.json" in os.listdir():
            with open("wifi.json") as f:
                data = json.loads(f.read())
    except ValueError as e:
        print(e)

    if type(data) is dict:
        # convert original format data (dict, one network) to new (list, many networks)
        data = [data]

    if not all( [ ("ssid" in config) for config in data ] ):
        raise OSError("Couldn't find a valid wifi.json. See https://badge.emf.camp for more information")

    return data

def ssid():
    global _network
    if _network is None:
        return "Not connected"
    return _network["ssid"]

def connect(wait = True, timeout = 10):
    global _network
    if nic().is_connected():
        return
    networks = connection_details()

    exc = None
    for details in networks:
        _network = details
        
        try:
            if "pw" in details and details["pw"]:
                if wait:
                    nic().connect(details["ssid"], details["pw"], timeout=timeout)
                    wait_for_connection()
                else:
                    nic().connect(details["ssid"], details["pw"], timeout=None)
            else:
                if wait:
                    nic().connect(details["ssid"], timeout=timeout)
                    wait_for_connection()
                else:
                    nic().connect(details["ssid"], timeout=None)
        except Exception as e:
            exc = e

        if nic().is_connected():
            # successful connection, we don't need to try any more
            break

    if (not nic().is_connected()) and (exc is not None):
        raise exc

def wait_for_connection():
    while not nic().is_connected():
        nic().update()
        pyb.delay(100)

def is_connected():
    return nic().is_connected()

def connection_text():
    return "Connecting to wifi. If this doesn't work, please check your wifi.json. More information: badge.emfcamp.org/TiLDA_MK3/wifi" 
