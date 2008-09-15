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

VERSION = '0.2'
IFACE_NAME = 'org.exaile.DBusInterface'
IFACE_PATH = '/DBusInterfaceObject'
    
import CurrentSong

class Exaile( CurrentSong.DbusBase ):
    '''Exaile Interface'''
    
    def __init__( self ):
        CurrentSong.DbusBase.__init__( self, IFACE_NAME, self.setInterface )
        
        try: self.iface
        except: self.iface = None
       
    def setInterface( self ):
        proxy_obj = self.bus.get_object( IFACE_NAME, IFACE_PATH )
        self.iface = self.module.Interface( proxy_obj, IFACE_NAME )
        
    def getCoverPath( self ):
        if self.iface:
            return self.iface.get_cover_path()
        else:
            return None
     
    def setCurrentSongData( self ):
        if self.iface:
            self.artist = self.iface.get_artist()
            self.title = self.iface.get_title()
            self.album = self.iface.get_album()

    def getVersion( self ):
        try:
            self.iface.get_version()
        except:
            return False
        
        return True
    
    def isPlaying( self ):
        if not self.getVersion():
            return False
            
        if self.iface.get_artist() != None and \
           self.iface.get_title() != None and \
           self.iface.get_album() != None:
            return True
        
        return False
        
    def check( self ):
        if not self.iface or not self.isNameActive(IFACE_NAME):
            return
        
        if self.artist != self.iface.get_artist() or \
           self.title != self.iface.get_title() or \
           self.album != self.iface.get_album():
            self.setCurrentSongData()
            return True
            
        return False

