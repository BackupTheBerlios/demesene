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

import Plugin

class MainClass( Plugin.Plugin ):
    '''Main plugin class'''
    
    def __init__( self, controller, msn ):
        '''Contructor'''
        
        Plugin.Plugin.__init__( self, controller, msn )
        
        self.description = _('Save the personal message between sessions.')
        self.authors = { 'Mariano Guerra' : 'luismarianoguerra at gmail dot com' }
        self.website = 'http://emesene-msn.blogspot.com'
        self.displayName = _('Personal Message')
        self.name = 'PersonalMessage'
        
        self.config = controller.config
        self.config.readPluginConfig(self.name)
        
        self.enabled = False
        
    def start( self ):
        '''start the plugin'''

        self.enabled = True
        self.msn.changePersonalMessage(self.config.getPluginValue(self.name, 'pm', ''))
        self.msn.connect( 'self-personal-message-changed', self.action )
        
    def stop( self ):    
        '''stop the plugin'''
        
        self.enabled = False
        
    def action( self, msnp, user, pm ):
        if self.enabled:
            self.config.setPluginValue(self.name, 'pm', pm)
    
    def check( self ):
        '''
        check if everything is OK to start the plugin
        return a tuple whith a boolean and a message
        if OK -> ( True , 'some message' )
        else -> ( False , 'error message' )
        '''
        
        return ( True, 'Ok' )
