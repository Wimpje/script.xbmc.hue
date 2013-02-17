import sys
import xbmcaddon

ADDON_ID = 'script.xbmc.hue'
__addon__      = sys.modules[ "__main__" ].__addon__

class settings():
  def __init__( self, *args, **kwargs ):
    self.readxml()
    self.addon = xbmcaddon.Addon(id=ADDON_ID)

  def readxml(self):
    #self.log("Hue: reading settings")
    self.bridge_ip             = __addon__.getSetting("bridge_ip")
    self.bridge_user           = __addon__.getSetting("bridge_user")
    self.light_1               = __addon__.getSetting("light_1") == "true"
    self.light_2               = __addon__.getSetting("light_2") == "true"
    self.light_3               = __addon__.getSetting("light_3") == "true"
    self.light_4               = __addon__.getSetting("light_4") == "true"
    self.light_5               = __addon__.getSetting("light_5") == "true"
    self.mode                  = int(__addon__.getSetting("mode"))
    self.misc_initialflash     = __addon__.getSetting("misc_initialflash") == "true"

  def update(self, **kwargs):
    self.__dict__.update(**kwargs)
    for k, v in kwargs.iteritems():
      self.addon.setSetting(k, v)
