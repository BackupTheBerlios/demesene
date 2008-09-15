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
import tempfile
import threading
import time

import Plugin

class MainClass(Plugin.Plugin):
    '''Main plugin class'''

    def __init__( self, controller, msn ):
        '''Constructor'''

        Plugin.Plugin.__init__( self, controller, msn )
        self.description = _( 'Take screenshots and send them with ' +
                    '/screenshot [save] [<seconds>]' )
        self.authors = { 'Dx' : 'dx@dxzone.com.ar' }
        self.website = 'http://www.dxzone.com.ar'
        self.displayName = 'Screenshots'
        self.name = 'Screenshots'
        
        self.config = controller.config
        self.config.readPluginConfig(self.name)

        self.controller = controller
        self.slash = controller.Slash
        self.msn = msn
        
        if os.name == 'posix':
            self.root = controller.mainWindow.get_root_window()
        else:
            self.root = None

    def start( self ):
        '''start the plugin'''
        self.slash.register('screenshot', self.screenshot, \
            _('Takes screenshots') )

        self.enabled = True

    def screenshot( self, slashAction ):
        params = slashAction.getParams().split()
        
        save = False
        delay = 0
        
        # parse parameters
        for param in params:
            if param == 'save':
                save = True
            elif param.isdigit():
                delay = int(param)
        
        if delay > 0:
            slashAction.outputText(_('Taking screenshot in %s seconds') % delay)
        
        if not save:
            if self.config.getPluginValue(self.name, 'tip', '0') == '0':
                slashAction.outputText( \
                    _('Tip: Use "/screenshot save <seconds>" to skip the upload '))
                self.config.setPluginValue(self.name, 'tip', '1')
        
        ScreenThread( slashAction, self, save=save, delay=delay ).start()

    def stop( self ):    
        '''stop the plugin'''
        self.slash.unregister('screenshot')
        self.enabled = False

    def check( self ):
        return ( True, 'Ok' )

class ScreenThread(threading.Thread):

    def __init__(self, action, plugin, save=False, delay=0):
        threading.Thread.__init__( self )
        self.slashAction = action
        self.plugin = plugin
        self.save = save
        self.sleepTime = int(delay)

    def run(self):
        print "sleeping: " + str(self.sleepTime)
        time.sleep(self.sleepTime)
        if os.name == 'nt':
            print 'screenshot on windows never tested, check source!'

            # yes, i had to break this link.. 80 cols :P
            ## mail.python.org/pipermail/python-win32/
            ## .../2003-January/000709.html

            # import win32api, win32clipboard
            # win32api.keybd_event(win32con.VK_PRINT, 0)
            # win32clipboard.OpenClipboard(0)
            # data = win32clipboard.GetClipboardData(win32clipboard.CF_DIB)
            # win32clipboard.CloseClipboard()
        elif os.name == 'posix':
            temp = tempfile.mkstemp(prefix='screenshot', suffix='.png')
            os.close(temp[0])
            
            # überfast screenshots! 1.9secs in my pentium II 350mhz
            # er.. yes, that's fast.. try running import
            root = self.plugin.root
            size = root.get_size()
            colormap = root.get_colormap()
            pixmap = gtk.gdk.pixmap_foreign_new(root.xid)
            pixbuf = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, 0, 8, *size)
            pixbuf.get_from_drawable(pixmap, colormap, 0, 0, 0, 0, *size)
            pixbuf.save(temp[1], 'png')
            
        if not self.save:
            self.slashAction.conversation.sendFile(temp[1])
        else:
            self.slashAction.outputText( _('Temporary file:') + ' ' + \
                temp[1] )

