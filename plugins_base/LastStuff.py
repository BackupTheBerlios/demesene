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

VERSION = '0.1'

import time

import emesenelib.common
import Plugin

class MainClass(Plugin.Plugin):
    '''Main plugin class'''
    
    def __init__(self, controller, msn):
        '''Contructor'''
        
        Plugin.Plugin.__init__(self, controller, msn)
        
        self.description = _('Get Last something from the logs')
        self.authors = { 'Luis Mariano Guerra' : 
            'luismarianoguerra at gmail dot com' }
        self.website = 'http://emesene.org'
        self.displayName = 'LastStuff'
        self.name = 'LastStuff'
        self.controller = controller
        self.Slash = controller.Slash

    def start(self):
        '''start the plugin'''
        self.Slash.register('last', self.get_last, 'Get last stuff')
        self.enabled = True

    def get_last(self, slash_action):
        params = slash_action.getParams()
        if params:
            data = params.split(' ')
        else:
            data = ''

        logger = self.controller.pluginManager.getPlugin("Logger")

        if not logger or not logger.enabled:
            slash_action.outputText('Logger plugin not available', False)
            return

        if len(data) != 3:
            slash_action.outputText('Usage: /last # stuff account', False)
            return
        
        (stamp, stuff, account) = data
        
        try:
            num = int(data[0])
        except:
            slash_action.outputText(_('invalid number as first parameter'), 
                False)
            return
        
        if data[1] == "nick":
            results = logger.get_last_nick(account, num)
            results.reverse()
            for (stamp, result) in results:
                slash_action.outputText(result, False)
            
            if len(results) == 0:
                slash_action.outputText(_('Empty result'), False)
                
        elif data[1] == "pm":
            results = logger.get_last_personal_message(account, num)
            results.reverse()
            for (stamp, result) in results:
                slash_action.outputText(result, False)
            
            if len(results) == 0:
                slash_action.outputText(_('Empty result'), False)
                
        elif data[1] == "ce":
            results = logger.get_last_custom_emoticon(account, num)
            results.reverse()
            for (stamp, result) in results:
                slash_action.outputText(result, False)
            
            if len(results) == 0:
                slash_action.outputText(_('Empty result'), False)
                
        elif data[1] == "dp":
            results = logger.get_last_display_picture(account, num)
            results.reverse()
            for (stamp, result) in results:
                slash_action.outputText(result, False)
            
            if len(results) == 0:
                slash_action.outputText(_('Empty result'), False)
                
        elif data[1] == "message":
            results = logger.get_last_message(account, num)
            results.reverse()
            for (stamp, result) in results:
                try:
                    slash_action.outputText(result.split("\r\n")[2], False)
                except IndexError:
                    print 'malformed message on LastStuff'
            
            if len(results) == 0:
                slash_action.outputText('Empty result', False)
                
        elif data[1] == "conversation":
            results = logger.get_last_conversation(account, num)
            results.reverse()
            for (stamp, account, result) in results:
                try:
                    slash_action.outputText(
                        account + ': ' + result.split("\r\n")[2], False)
                except IndexError:
                    print 'malformed message on LastStuff'

            if len(results) == 0:
                slash_action.outputText(_('Empty result'), False)
                
        elif data[1] == "status":
            results = logger.get_last_status(account, num)
            results.reverse()
            for (stamp, result) in results:
                slash_action.outputText('%s since %s' % (
                    emesenelib.common.reverse_status[result], 
                    time.ctime(float(stamp)))
                    , False)
            
            if len(results) == 0:
                slash_action.outputText(_('Empty result'), False)
                
    def stop(self):    
        '''stop the plugin'''
        self.Slash.unregister('last')
        self.enabled = False
        
    def check(self):
        plugin = self.controller.pluginManager.getPlugin("Logger")
        if plugin is None or not plugin.enabled:
            return (False, _('Enable the logger plugin'))

        return (True, 'Ok')

