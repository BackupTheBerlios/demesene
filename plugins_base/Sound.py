# -*- coding: utf-8 -*-

#   This file is part of emesene.
#
#    Emesene is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    emesene is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with emesene; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import os
import gtk

if os.name == 'nt':
    import winsound
    
import Plugin
from emesenecommon import PATH

try: 
    import gst
    GSTREAMER = True
except:
    GSTREAMER = False
   
class Sound:
    '''A plugin to play sounds using the available modules on the system'''

    def __init__(self, theme):
        '''class constructor'''
    
        self.theme = theme
        self.beep = False
        self.command = ''
        self.canPlay = False
        self.canGstreamer = False
        
        if os.name == "posix":
            self.checkAvailability()
            if self.canGstreamer:
                self.player = gst.element_factory_make("playbin", "player")
                bus = self.player.get_bus()
                bus.enable_sync_message_emission()
                bus.add_signal_watch()
                bus.connect('message', self.gst_on_message)
        else:
            self.canPlay = True

    def gst_on_message(self, bus, message):
        t = message.type
        if t == gst.MESSAGE_EOS:
            self.player.set_state(gst.STATE_NULL)

    def checkAvailability(self):
        if self.beep:
            self.canPlay = True
        elif GSTREAMER:
            self.canPlay = True
            self.canGstreamer = True
        elif self.is_on_path('aplay'):
            self.canPlay = True
            self.command = 'aplay'
        elif self.is_on_path('play'):
            self.canPlay = True
            self.command = 'play'
        
    def play(self, sound_theme,  sound):
        if self.beep:
            gtk.gdk.beep()
            return
        
        for theme in (sound_theme, 'default'):
            soundPath = PATH.SOUNDS_PATH + os.sep + sound_theme + os.sep + \
                sound + ".wav"
            
            if os.path.exists(soundPath):
                break
            else:
                soundPath = ''

        if not soundPath:
            return
        
        if os.name == "nt":
            winsound.PlaySound(soundPath, 
                winsound.SND_FILENAME | winsound.SND_ASYNC)
        elif os.name == "posix":
            if self.canGstreamer:
                loc = "file://" + soundPath
                self.player.set_property('uri', loc)
                self.player.set_state(gst.STATE_PLAYING)    
            else:
                os.popen4(self.command + " " + soundPath)
            
    def getCommand(self):
        return self.command
        
    def setCommand(self, string):
        self.command = string
        
    def is_on_path(self, fname):
        for p in os.environ['PATH'].split(os.pathsep):
            if os.path.isfile(os.path.join(p, fname)):
                return True

class MainClass(Plugin.Plugin):
    '''Main plugin class'''
    
    def __init__(self, controller, msn):
        '''Contructor'''
        Plugin.Plugin.__init__(self, controller, msn)
        self.theme = controller.theme
        
        self.description = _('Play sounds for common events.')
        self.authors = { 'Mark Baas' : 'mark.baas123 at gmail dot com' }
        self.website = 'http://www.emesene.org'
        self.displayName = _('Sound')
        self.name = 'Sound'
        
        self.sound = Sound(self.theme)
        
        self.config = controller.config
        self.config.readPluginConfig(self.name)
        self.playOnline = int(self.config.getPluginValue(self.name, 
            'playOnline', '1'))
        self.playMessage = int(self.config.getPluginValue(self.name, 
            'playMessage', '1') )
        self.playNudge = int(self.config.getPluginValue(self.name, 
            'playNudge', '1'))
        self.playInactive = int(self.config.getPluginValue(self.name, 
            'playInactive', '1'))
        self.playSend = int(self.config.getPluginValue(self.name, 
            'playSend', '0'))
        self.disableBusy = int(self.config.getPluginValue(self.name, 
            'disableBusy', '0'))
        
        self.sound_theme = self.config.getPluginValue(self.name, 
            'theme', 'default')
        self.sound.beep = int(self.config.getPluginValue(self.name, 
            'beep', '0'))
        
        self.onlineId = None
        self.messageId = None
        self.nudgeId = None

    def start(self):
        '''start the plugin'''

        self.enabled = True
        self.onlineId = self.msn.connect('user-online', self.online)
        self.messageId = self.msn.connect('message-received', self.message)
        self.nudgeId = self.msn.connect('nudge-received', self.nudge)
        self.sendMessageId = self.controller.conversationManager.connect(
            'send-message', self.send)
        
    def stop(self):    
        '''stop the plugin'''
        self.msn.disconnect(self.onlineId)
        self.msn.disconnect(self.messageId)
        self.msn.disconnect(self.nudgeId)
        self.msn.disconnect(self.sendMessageId)
        
        self.enabled = False
        
    def action(self):
        pass        
    
    def check(self):
        '''
        check if everything is OK to start the plugin
        return a tuple whith a boolean and a message
        if OK -> (True, 'some message')
        else -> (False, 'error message')
        '''
        
        if not self.sound.canPlay:
            return (False, _('gstreamer, play and aplay not found.'))
        
        return (True, 'Ok')

    def online(self, msnp, email, oldStatus):
        self.playOnline = int(self.config.getPluginValue(self.name, 
            'playOnline', '1'))
        self.sound_theme = self.config.getPluginValue(self.name, 'theme', 
            'default')
        if oldStatus == 'FLN' and self.playOnline and self.soundsEnabled():
            self.sound.play(self.sound_theme, 'online')

    def message(self, msnp, email):
        self.playMessage = int(self.config.getPluginValue(self.name, 
            'playMessage', '1') )
        self.sound_theme = self.config.getPluginValue(self.name, 'theme', 
            'default')
        
        if self.playMessage and self.soundsEnabled():
            result = self.controller.conversationManager\
                .getOpenConversation(email)
            if self.playInactive and result != None:
                window, conversation = result
                windowFocus = window.is_active()
                tabFocus = (window.conversation == conversation)
                
                if not (windowFocus and tabFocus):
                    self.sound.play(self.sound_theme, 'type')
            else:
                self.sound.play(self.sound_theme, 'type')

    def nudge(self, *args):
        self.playNudge = int(self.config.getPluginValue(self.name, 
            'playNudge', '1'))
        self.sound_theme = self.config.getPluginValue(self.name, 
            'theme', 'default')
        if self.playNudge and self.soundsEnabled():
            self.sound.play(self.sound_theme, 'nudge')
    
    def send(self, *args):
        self.playSend = int(self.config.getPluginValue(self.name, 
            'playSend', '0'))
        self.sound_theme = self.config.getPluginValue(self.name, 
            'theme', 'default')
        if self.playSend and self.soundsEnabled():
            self.sound.play(self.sound_theme, 'send')
            
    def soundsEnabled(self):
        '''checks if sounds are enabled'''
        if not self.enabled:
            return False
        if self.disableBusy and self.controller.contacts.get_status() == 'BSY':
            return False
        return True
            
    def configure(self):
        '''display a configuration dialog'''
        l = []

        #sound theme
        themes = os.listdir(PATH.APP_PATH + os.sep + 'sound_themes')
        themes = [x for x in themes if not x.startswith('.')]

        # name, optionType, label, description, value, options
        l.append(Plugin.Option('theme', list, _('Theme'), '', 
            self.config.getPluginValue(self.name, 'theme', ''), themes))

        l.append(Plugin.Option('playOnline', bool, 
            _('Play online sound'), 
            _('Play a sound when someone gets online'), 
            (self.config.getPluginValue(self.name, 'playOnline', '1') \
                == '1')))
        
        l.append(Plugin.Option('playMessage', bool, 
            _('Play message sound'), 
            _('Play a sound when someone sends you a message'), 
            (self.config.getPluginValue(self.name,  'playMessage', '1') \
                == '1')))
        
        l.append(Plugin.Option('playNudge', bool, 
            _('Play nudge sound'), 
            _('Play a sound when someone sends you a nudge'), 
            (self.config.getPluginValue(self.name, 'playNudge', '1') \
                == '1')))
        
        l.append(Plugin.Option('playSend', bool, 
            _('Play sound when you send a message'), 
            _('Play sound when you send a message'), 
            (self.config.getPluginValue(self.name, 'playSend', '0') \
                == '1')))
        
        l.append(Plugin.Option('playInactive', bool, 
            _('Only play message sound when window is inactive'), 
            _('Play the message sound only when the window is inactive'), 
            (self.config.getPluginValue(self.name, 'playInactive', '1') \
                == '1')))
        
        l.append(Plugin.Option('disableBusy', bool, 
            _('Disable sounds when busy'), 
            _('Disable sounds when busy'), 
            (self.config.getPluginValue(self.name, 'disableBusy', '1') \
                == '1')))
        
        l.append(Plugin.Option('beep', bool, 
            _('Use system beep'), 
            _('Play the system beep instead of sound files'), 
            (self.config.getPluginValue(self.name, 'beep', '0') \
                == '1')))
        
        response = Plugin.ConfigWindow(_('Config Sound Plugin'), l).run()
        if response != None:
            if response.has_key('playOnline'):
                self.config.setPluginValue(self.name, 'playOnline', 
                    str(int(response['playOnline'].value)))
            if response.has_key('playMessage'):
                self.config.setPluginValue(self.name, 'playMessage', 
                    str(int(response['playMessage'].value)))
            if response.has_key('playNudge'):
                self.config.setPluginValue(self.name, 'playNudge', 
                    str(int(response['playNudge'].value)))
            if response.has_key('playInactive'):
                self.config.setPluginValue(self.name, 'playInactive', 
                    str(int(response['playInactive'].value)))
            if response.has_key('playSend'):
                self.config.setPluginValue(self.name, 'playSend', 
                    str(int(response['playSend'].value)))
            if response.has_key('beep'):
                self.config.setPluginValue(self.name, 'beep', 
                    str(int(response['beep'].value)))
            if response.has_key('theme'):
                self.config.setPluginValue(self.name, 'theme', 
                    response['theme'].value)
            if response.has_key('disableBusy'):
                self.config.setPluginValue(self.name, 'disableBusy', 
                    str(int(response['disableBusy'].value)))

        self.playOnline = (self.config.getPluginValue(self.name, 
            'playOnline', '1') == '1')
        self.playMessage = (self.config.getPluginValue(self.name, 
            'playMessage', '1') == '1')
        self.playNudge = (self.config.getPluginValue(self.name, 
            'playNudge', '1') == '1')
        self.playInactive = (self.config.getPluginValue(self.name, 
            'playInactive', '1') == '1')
        self.disableBusy = (self.config.getPluginValue(self.name, 
            'disableBusy', '1') == '1')
        self.sound.beep = int(self.config.getPluginValue(self.name, 
            'beep', '0'))
        
        return True
        
