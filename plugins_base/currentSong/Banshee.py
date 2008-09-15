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

VERSION = '0.02'
IFACE_NAME = 'org.gnome.Banshee'
IFACE_PATH = '/org/gnome/Banshee/Player'

import CurrentSong

class Banshee( CurrentSong.DbusBase ):

    def __init__( self ):
        CurrentSong.DbusBase.__init__( self, IFACE_NAME, self.setInterface )
        
        try: self.iface
        except: self.iface = None
        
    def setInterface( self ):
        self.iface = self.bus.get_object( IFACE_NAME, IFACE_PATH )
     
    def setCurrentSongData( self ):
        if self.iface:
            self.title = self.iface.GetPlayingTitle()
            self.artist = self.iface.GetPlayingArtist()
            self.album = self.iface.GetPlayingAlbum()
            
    def isPlaying( self ):
        if not self.iface: return False

        if not self.iface.GetPlayingTitle():
            print "nao passou teste"
            return False 
        if self.iface.GetPlayingTitle() != None:
            print "passou teste"
            return True
        return False
        
    def check( self ):
        if not self.iface or not self.isNameActive(IFACE_NAME):
            return
        
        if self.iface.GetPlayingTitle() != self.title:
            self.setCurrentSongData()
            return True
            
        return False

