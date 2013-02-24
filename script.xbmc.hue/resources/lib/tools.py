import httplib
import time
import sys
import os
import socket
import json
import random
import hashlib
import xbmc
import xbmcaddon

__addon__      = xbmcaddon.Addon()
__cwd__        = __addon__.getAddonInfo('path')
__icon__       = os.path.join(__cwd__,"icon.png")
__settings__   = os.path.join(__cwd__,"resources","settings.xml")

def notify(title, msg):
  global __icon__
  xbmc.executebuiltin("XBMC.Notification(%s, %s, 3, %s)" % (title, msg, __icon__))

def start_autodisover():
  port = 1900
  ip = "239.255.255.250"

  address = (ip, port)
  data = """M-SEARCH * HTTP/1.1
  HOST: %s:%s
  MAN: ssdp:discover
  MX: 3
  ST: upnp:rootdevice""" % (ip, port)
  client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

  hue_ip = None
  num_retransmits = 0
  while(num_retransmits < 10) and hue_ip == None:
      num_retransmits += 1
      client_socket.sendto(data, address)
      recv_data, addr = client_socket.recvfrom(2048)
      if "IpBridge" in recv_data and "description.xml" in recv_data:
        hue_ip = recv_data.split("LOCATION: http://")[1].split(":")[0]
      time.sleep(1)
      
  return hue_ip

def register_user(hue_ip):
  username = hashlib.md5(str(random.random())).hexdigest()
  device = "xbmc-player"
  data = '{"username": "%s", "devicetype": "%s"}' % (username, device)

  response = request('GET', 'http://%s/api' % hue_ip, data)
  while "link button not pressed" in response:
    notify("Bridge discovery", "press link button on bridge")
    response = request('GET','http://%s/api' % hue_ip, data)
    time.sleep(3)

  return username

def get_state(bridge_ip, bridge_user):
  return request('GET','http://%s/api/%s' % (bridge_ip, bridge_user))

def test_connection(bridge_ip, bridge_user):
  response = request('GET','http://%s/api/%s/config' % (bridge_ip, bridge_user))
  if response.find("name"):
    return True
  else:
    return False

def request(self,  mode = 'GET', address = None, data = None):
  connection = httplib.HTTPConnection(self.ip)
  if mode == 'GET' or mode == 'DELETE':
      connection.request(mode, address)
  if mode == 'PUT' or mode == 'POST':
      connection.request(mode, address, data)

  result = connection.getresponse()
  connection.close()
  return json.loads(result.read())

def set_light2(bridge_ip, bridge_user, light, hue, sat, bri):
    #this one is not used atm
    data = json.dumps({
        "on": True,
        "hue": hue,
        "sat": sat,
        "bri": bri,
        #"bri": 254,
        #"transitiontime":0
    })
    request("GET","http://%s/api/%s/lights/%s/state" % (bridge_ip, bridge_user, light), data=data)

