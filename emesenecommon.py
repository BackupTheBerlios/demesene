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
import re
import sys

from htmlentitydefs import codepoint2name

#
# Global variables for use throughout the program
#
APP_NAME = 'emesene'
APP_VERSION = '1.0.1'
OS_NAME = os.name
DIR_SEP = os.sep

class PATH(object):
    '''a namespace for paths'''

    DIR_SEP = os.sep

    if hasattr(sys, "frozen"):
        APP_PATH = os.path.dirname(sys.executable)
    else:
        APP_PATH = os.path.abspath(os.path.dirname(__file__))
    
    HOME_DIR = os.path.expanduser('~')
    CONF_DIR_NAME = '.config' + DIR_SEP + 'emesene1.0'
    CONFIG_DIR = HOME_DIR + DIR_SEP + CONF_DIR_NAME
        
    THEME_HOME_PATH = CONFIG_DIR + DIR_SEP + 'themes'
    THEME_SYSTEM_WIDE_PATH = APP_PATH + DIR_SEP + 'themes'
    DEFAULT_THEME_PATH = THEME_SYSTEM_WIDE_PATH + DIR_SEP + 'default' + DIR_SEP

    PLUGINS_HOME = 'pluginsEmesene'
    PLUGINS_SYSTEM_WIDE = 'plugins_base'
    PLUGIN_SYSTEM_WIDE_PATH = APP_PATH + DIR_SEP + PLUGINS_SYSTEM_WIDE
    PLUGIN_HOME_PATH = CONFIG_DIR + DIR_SEP + PLUGINS_HOME
    
    SMILIES_SYSTEM_WIDE_PATH = APP_PATH + DIR_SEP + 'smilies'
    SMILIES_HOME_PATH = CONFIG_DIR + DIR_SEP + 'smilies'
    DEFAULT_SMILIES_PATH = SMILIES_SYSTEM_WIDE_PATH + DIR_SEP + 'default' + DIR_SEP
    
    CONVTHEMES_SYSTEM_WIDE_PATH = APP_PATH + DIR_SEP + 'conversation_themes'
    CONVTHEMES_HOME_PATH = CONFIG_DIR + DIR_SEP + 'conversation_themes'
    DEFAULT_CONVTHEMES_PATH = CONVTHEMES_SYSTEM_WIDE_PATH + DIR_SEP + 'default' + DIR_SEP
    
    LANG_PATH = APP_PATH + DIR_SEP + 'po'
    SOUNDS_PATH = APP_PATH + DIR_SEP + 'sound_themes'

# workaround for pluginsEmesene/__init__.py
PLUGINS_HOME = PATH.PLUGINS_HOME
PLUGIN_SYSTEM_WIDE_PATH = PATH.PLUGIN_SYSTEM_WIDE_PATH

# Other constants
RESPONSE_DELETE_ALIAS = 50
RESPONSE_NO_AVATAR = -50
MAX_MESSAGE_LENGTH = 1100

#Regex
urlRe = re.compile("(^|[^A-Za-z0-9])(https?\:\/\/|ftp\:\/\/|www\.)([A-Za-z0-9\$_\.\+!\*':\(\|\)@,;\/\?&%=~#^`\\\-]+)")
reUnencode = re.compile( '=\\?([^\\?]+)\\?Q\\?([^\\?]+)\\?=' )
reChar = re.compile( '=([A-z0-9]{2})' )

#
# Global functions
#

def htmlEncode(string):
    '''this method return a string whit html tags encoded'''
    for i,j in codepoint2name.iteritems():
        if i <= 256 and str(chr(i)) in string:
            string = string.replace(chr(i), j)
    return string

def rgbToHexa( color ):
    '''take a gtk.gdk.Color end returns a string with html way color. Eg.: #FFCC00'''
    
    red = color.red >> 8
    green = color.green >> 8
    blue = color.blue >> 8
    
    return '#'+'%02X%02X%02X' % ( red , green , blue )

def sort( list ):
    '''Sorts a list in alphabetical order without regard of the capitalization'''
    
    list = list[:]
    list.sort( key= lambda x: str.lower( x ) )
    return list
    
def getLinks( text ):
    links = ()
    text = re.sub( urlRe, _searchAnchors, text.replace('%','%%') )
    return text, links

def _searchAnchors( data ):
    s, w, url = data.groups()
    href = w+url
    if w == 'www.':
        href  = 'http://'+href
    return '%s'

