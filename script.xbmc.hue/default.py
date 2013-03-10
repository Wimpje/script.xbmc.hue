import xbmc
import xbmcgui
import xbmcaddon
import time
import sys
import colorsys
import os
import datetime

__addon__      = xbmcaddon.Addon()
__cwd__        = __addon__.getAddonInfo('path')
__resource__   = xbmc.translatePath( os.path.join( __cwd__, 'resources', 'lib' ) )

sys.path.append (__resource__)

from settings import *
from tools import *

SCRIPTNAME = "XBMC Hue"

def log(msg):
  global SCRIPTNAME
  xbmc.log("%s: %s" % (SCRIPTNAME, msg))

log("Service started")

class Hue:
  params = None
  connected = None
  settings = None
  state = {}
  lights = {}
  groups = {}
  used_groups = {}


  def __init__(self, settings):
    self._parse_argv()
    self.settings = settings
    log("Hue: init")
    if self.params == {}:
      log("Normal operations")
      if self.settings.bridge_ip != "-":
        self.test_connection()
    elif self.params['action'] == "discover":
      log("Starting discover")
      notify("Bridge discovery", "starting")
      hue_ip = start_autodisover()
      if hue_ip != None:
        notify("Bridge discovery", "Found bridge at: %s" % hue_ip)
        username = register_user(hue_ip)
        log("Updating settings")
        self.settings.update(bridge_ip = hue_ip)
        self.settings.update(bridge_user = username)
        notify("Bridge discovery", "Finished")
        self.test_connection()
      else:
        notify("Bridge discovery", "Failed. Could not find bridge.")
    elif self.params['action'] == "test_connection":
      self.test_connection()
    else:
      # not yet implemented
      log("unimplemented action call: %s" % self.params['action'])
   

    if self.connected:
      #initialize current state of the Hue (for later)
      self.state = get_state(self.settings.bridge_ip, self.settings.bridge_user)
      log(self.state)
      self.used_groups = self.used_groups()
      if self.settings.misc_initialflash:
        self.flash_lights()
      self.run()

  def _parse_argv( self ):
    try:
        self.params = dict(arg.split("=") for arg in sys.argv[1].split("&"))
    except:
        self.params = {}

  def test_connection(self):
    if not test_connection(self.settings.bridge_ip, self.settings.bridge_user):
      notify("Failed", "Could not connect to bridge")
      self.connected = False
    else:
      notify("XBMC Hue", "Connected")
      self.connected = True

  def dim_lights(self):
    for group in self.used_groups:
        group.dim()

  def undim_lights(self):
    for group in self.used_groups:
        group.undim()

  def flash_lights(self):
    for group in self.used_groups:
        group.flash()    

  def used_groups(self):
    #todo: auto detect groups and add to settings
    #this function can be done nicer ;)
    groups = []
    if self.settings.group_1:
      group_from_state = self.state["groups"]["1"]
      if(group_from_state == None):
        log("Group 1 has no state")
      groups.append(HueGroup(1, "group"))
    if self.settings.group_2:
      group_from_state = self.state["groups"]["2"]
      if(group_from_state == None):
        log("Group 2 has no state")
      groups.append(HueGroup(2, "group"))
    if self.settings.group_3:
      group_from_state = self.state["groups"]["3"]
      if(group_from_state == None):
        log("Group 3 has no state")
      groups.append(HueGroup(3, "group"))
    return groups
  
  def run(self):
    self.settings.readxml()

class HueThing:
  state = {}
  id = None
  type = ""
  brightness_before_dim = None
  
  def __init__(self, id, type = ""):
    self.type = type + "s" #groups or lights, but type is single... a bit iffy ;)
    self.get_current_state()
    self.id = id
    log("init huething %s, %s " % (self.id, json.dumps(self.state)))

  def get_current_state(self): 
    if type == "":
       log("Error, this HueThing doesn't have a type")

    self.state = request("GET",url=settings.bridge_ip, action="/api/%s/%s/%s" % (settings.bridge_user, self.type, self.id))

  def get_brightness(self):
    log("get_brightness called, but not implemented by subclass")
    pass

  def dim(self, transition_time = 4):
    self.get_current_state()
    self.brightness_before_dim = self.get_brightness()
    dim = json.dumps({
      "on":True,
      "bri":min(self.brightness_before_dim - 80, 80),
      "transitiontime":transition_time
      })
    self.action(dim)

  def undim(self, transition_time = 4):
    orig_brightness = 254
    if(self.brightness_before_dim != None):
      orig_brightness = self.brightness_before_dim 
    restore = json.dumps({
        "on":True,
        "bri":orig_brightness ,
        "transitiontime":4
        })
    self.action(restore)

  def flash(self):
    self.dim(2)
    self.undim(2)

class HueLight(HueThing):
  def get_brightness(self):
    return self.state["state"]["bri"]

  def request(self):
    request("GET",settings.bridge_ip, action="/api/%s/lights/%s" % (settings.bridge_user, self.id))
  
  def action(self, data):
    request("PUT",settings.bridge_ip, action="/api/%s/lights/%s/action" % (settings.bridge_user, self.id), data=data)


class HueGroup(HueThing):
  def get_brightness(self):
    log("getbrightness before" + json.dumps(self.state))
    self.get_current_state()
    log("getbrightness after" + json.dumps(self.state))
    return self.state["action"]["bri"]

  def request(self):
    request("GET",settings.bridge_ip, action= "/api/%s/groups/%s" % (settings.bridge_user, self.id))
  
  def action(self, data):
    request("PUT",settings.bridge_ip, action="/api/%s/groups/%s/action" % (settings.bridge_user, self.id), data=data)

class HuePlayer( xbmc.Player ):
  hue = None
  
  def __init__( self):
    log("hueplayer init")
    xbmc.Player.__init__(self)
    self.hue = Hue(settings)

  def onPlayBackStarted( self ):
    # Will be called when xbmc starts playing a file
    log( "Hue Dim - start" )
    self.hue.dim_lights()

  def onPlayBackPaused( self ):
    log( "Hue pause" )
    self.hue.undim_lights()
  
  def onPlayBackResumed( self ):
    log( "Hue resume" )
    self.hue.dim_lights()
  
  def onPlayBackEnded( self ):
    # Will be called when xbmc stops playing a file
    log( "Hue undim - end" )
    self.hue.undim_lights()

  def onPlayBackStopped( self ):
    # Will be called when user stops xbmc playing a file
    log( "Hue undim - stop" )
    self.hue.undim_lights()

if ( __name__ == "__main__" ):
  settings = settings()
  player = HuePlayer()

while(not xbmc.abortRequested):
    xbmc.sleep(100)