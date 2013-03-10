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
  xbmc.log("XBMC Hue: XBMC.Notification(%s, %s, 3, %s)" % (title, msg, __icon__))

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
  loop_check = 0
  response = request(mode='POST', url=hue_ip, action='/api', data=data)
  
  while not(check_succes(response)) and loop_check < 10:
    loop_check = loop_check + 1
    time.sleep(3)
    response = request(mode='POST', url=hue_ip, action='/api', data=data)

  if loop_check > 10:
    notify("not registered", "please try again")
    return ""
  else:
    notify("User registered", username)

  return username

def check_succes(response):
  for line in response:
    for key in line:
      if 'success' in key:
         return True
      if 'error' in key:
         if line['error']['type'] == 101:
            notify('Press bridge button', 'Please press button on bridge to register application and call connect() method')
            return False
         if line['error']['type'] == 7:
            notify('Error', 'Unknown username')
            return False
  return False


def get_state(bridge_ip, bridge_user):
  return request(url=bridge_ip, action = '/api/%s' % bridge_user)

def test_connection(bridge_ip, bridge_user):
  response = request(url=bridge_ip, action='/api/%s/config' % bridge_user)
  if response["name"]:
    return True
  else:
    return False

def request(mode = 'GET', url = "", action = "", data = None):
  xbmc.log("XBMC Hue: Request - mode:%s, url:%s, action:%s, data:%s" % (mode, url, action, json.dumps(data)))
  connection = httplib.HTTPConnection(url)
  if mode == 'GET' or mode == 'DELETE':
      connection.request(mode, action)
  if mode == 'PUT' or mode == 'POST':
      connection.request(mode, action, data)

  result = connection.getresponse()
  connection.close()
  json_response = json.loads(result.read())
  xbmc.log("XBMC Hue: response - " + json.dumps(json_response))
  return json_response


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
    request("GET",url=bridge_ip, action="/api/%s/lights/%s/state" % (bridge_user, light), data=data)

