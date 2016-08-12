### Author: EMF Badge team
### Description: Handles connecting to a wifi access point based on a valid wifi.json file
### License: MIT

import network
import os
import json
import pyb


class NICState:
    NOT_CONNECTED = 1
    NO_VISIBLE_SSIDS = 2
    CONNECTING = 3
    CONNECTED = 3

_nic = None
_network = None
_state = NICState.NOT_CONNECTED


def nic():
    global _nic
    if not _nic:
        _nic = network.CC3100()
    return _nic

def create_default_config():
    with open("wifi.json", "wt") as file:
        file.write(json.dumps([{"ssid": "emfcamp-insecure"}]))
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

def rssi():
    v = 0
    if is_connected():
        v = nic().get_rssi()
    return v

def update():
    nic().update()

def disconnect():
    nic().disconnect()

def connect(wait = True, timeout = 10):
    
    print( "wifi.connect(wait=%r)" % (wait) )
    
    global _network, _state

    if is_connected():
        print( "-> already connected.")
        return
    _state = NICState.CONNECTING
    
    networks = connection_details()
    visible_ssids = [ ap['ssid'] for ap in nic().list_aps() ]
    print( "-> visible_ssids: %r" % visible_ssids )

    known_ssids = [ ap['ssid'] for ap in networks ]
    print( "-> known_ssids: %r" % known_ssids )

    if len(set(known_ssids).intersection(visible_ssids)) < 1:
        print( "--> no known ssids visible!" )
        _state = NICState.NO_VISIBLE_SSIDS
        return

    exc = None
    for details in networks:

        if details["ssid"] in visible_ssids:

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
            except OSError as e:
                # hold OSErrors and if we fail to connect to anything, throw the most recent
                exc = e

            # found an AP to connect to, don't bother trying any more
            break

    if exc is not None:
        raise exc

def wait_for_connection():
    print( "wifi.py: wait_for_connection()" )
    global _state
    while not nic().is_connected():
        nic().update()
        pyb.delay(100)
    _state = NICState.CONNECTED

def is_connected():
    global _state
    c = nic().is_connected()
    if c: 
        _state = NICState.CONNECTED
    return c

def connection_text():
    global _state
    text = ""
    
    if (_state == NICState.NOT_CONNECTED) or (_state == NICState.CONNECTING):
        text = "Connecting to wifi"
        if _network is not None:
            text += " %s" % (ssid()) 
        text += ". If this doesn't work, please check your wifi.json."

    elif _state == NICState.NO_VISIBLE_SSIDS:
        text = "No visible wifi networks have details in your wifi.json."

    elif _state == NICState.CONNECTED:
        text = "Wifi connnected to %." % (ssid())        
    
    text += " More information: badge.emfcamp.org/TiLDA_MK3/wifi"
    return text
