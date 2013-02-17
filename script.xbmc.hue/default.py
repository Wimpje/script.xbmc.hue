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
  last_state = None
  settings = None

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
    else:
      # not yet implemented
      log("unimplemented action call: %s" % self.params['action'])

    if self.connected:
      if self.settings.misc_initialflash:
        self.flash_lights()
      self.run()

  def flash_lights(self):
    for light in self.used_lights():
        flash_light(self.settings.bridge_ip, self.settings.bridge_user, light)
    
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
    for light in self.used_lights():
        dim_light(self.settings.bridge_ip, self.settings.bridge_user, light)

  def brighter_lights(self):
    for light in self.used_lights():
        brighter_light(self.settings.bridge_ip, self.settings.bridge_user, light)

  def used_lights(self):
    lights = []
    if self.settings.light_1:
      lights.append(1)
    if self.settings.light_2:
      lights.append(2)
    if self.settings.light_3:
      lights.append(3)    
    if self.settings.light_4:
      lights.append(4)
    if self.settings.light_5:
      lights.append(5)
    return lights
  
  def run(self):
    self.settings.readxml()

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
    self.hue.brighter_lights()
  
  def onPlayBackResumed( self ):
    log( "Hue resume" )
    self.hue.dim_lights()
  
  def onPlayBackEnded( self ):
    # Will be called when xbmc stops playing a file
    log( "Hue undim - end" )
    self.hue.brighter_lights()

  def onPlayBackStopped( self ):
    # Will be called when user stops xbmc playing a file
    log( "Hue undim - stop" )
    self.hue.brighter_lights()

if ( __name__ == "__main__" ):
  settings = settings()
  player = HuePlayer()

while(not xbmc.abortRequested):
    xbmc.sleep(100)