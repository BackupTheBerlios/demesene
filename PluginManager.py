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
import sys
import weakref
import emesenelib.common
from emesenecommon import PATH

class PluginManager( object ):
    '''This module handles the plugins'''
    
    def __init__( self, controller ):
        '''Constructor'''

        # we do the import here because we need to wait until the
        # config creates the plugin directory on the user home
        userPlugins = {}
        if os.name == 'posix':
            sys.path.append(PATH.CONFIG_DIR)
            userPlugins = self.inspectPackage(PATH.CONFIG_DIR, 
                    PATH.PLUGINS_HOME)
            
        systemPlugins = self.inspectPackage(PATH.APP_PATH, 
                PATH.PLUGINS_SYSTEM_WIDE)
        
        # system plugins have preference over user plugins
        # unless user plug's version is greater then sys' one
        for i in userPlugins.keys():
            if not i in systemPlugins:
                # the plugin is only in user's place
                continue
            # both user and system have the plugin
            elif not userPlugins[i]:
                # user version is None, so it can't be less
                del userPlugins[i]
            elif self.comparePluginVersions(userPlugins[i], 
                                             systemPlugins[i] ):
                # user version is greater than system version
                del systemPlugins[i]
            else:
                del userPlugins[i]
        
        self.userPlugins = userPlugins.keys()
        self.systemPlugins = systemPlugins.keys()
        
        self.controller = controller
        
        # a dict that contain an instance of the object plugin (because the 
        # module can have multiple clases)
        self.plugin = {}
        
        for i in self.getModules():
            self.loadPlugin( i )
        
        self.runningPlugins = []
        
    def inspectPackage(self, path, package):
        '''Searches the given path for plugins in package.
        Returns a dict with the found plugins and their versions, if any.'''
                
        try:
            __import__(package, globals(), locals(), [])
        except:
            print 'LO QUE!!!'
        
        path = path + PATH.DIR_SEP + package
        modules = [ x.split( '.' )[ 0 ] for x in os.listdir( path ) \
                    if x.endswith( '.py' ) and not x.startswith( '_' ) \
                    and x != 'Plugin.py' ]
        plugins = {}
        plugins = plugins.fromkeys( modules )
        
        for i in modules:
            try:
                mod = __import__( package + '.' + i, globals(), \
                                  None, [ 'VERSION' ] )
                plugins[i] = getattr( mod, 'VERSION' )
            except AttributeError, error:
                pass
            except Exception, e:
                del plugins[i]
                print('Exception importing %s\n%s'
                % (i, str(e)), 'PluginManager')
        
        return plugins
    
    def comparePluginVersions( self, v1, v2 ):
        '''Compare versions of the format 'x.y.z'
        Returns True if v1 and v2 can be compared and v1 > v2, otherwise False'''
        
        v1 = v1.strip().split( '.' )
        v2 = v2.strip().split( '.' )
        
        try:
            for i in range( min( len( v1 ), len( v2 ) ) ):
                if int( v1[ i ] ) > int( v2[ i ] ):
                    return True
                if int( v1[ i ] ) < int( v2[ i ] ):
                    return False
        except:
            return False
        
        if len( v1 ) > len( v2 ):
            return True
        else:
            return False
            
    
    def getModules(self):
        '''Returns a list with the plugins full module names  on the form:
        module_name.plugin_name'''
        user = [ PATH.PLUGINS_HOME + '.' + x for x in self.userPlugins ]
        system = [ PATH.PLUGINS_SYSTEM_WIDE + '.' + x for x in self.systemPlugins ]
        user.extend( system )
        return user
    
    def getPlugins(self):
        '''Returns a list with the plugins names'''
        
        list = self.userPlugins[:]    # makes a copy of userPlugins
        list.extend( self.systemPlugins )
        return list

    def pluginToModuleName(self, plugin):
        '''Converts a plugin name into a module name with full path'''
        if plugin in self.systemPlugins:
            return PATH.PLUGINS_SYSTEM_WIDE + '.' + plugin
        elif plugin in self.userPlugins:
            return PATH.PLUGINS_HOME + '.' + plugin
        else:
            return ''
        
    def loadPlugin( self, module, doReload=False ):
        '''Instanciate an object of the plugin, the possible exceptions should
        be handled by the caller.'''

        weakmsn = weakref.ref(self.controller.msn)

        if module in self.getModules():
            try:
                mod = __import__( module, globals(), locals(), [] )
                name = module.split('.')[ 1 ]
                plugin = getattr( mod, name )
                if doReload:
                    reload(plugin)

                self.plugin[ name ] = plugin.MainClass( self.controller, \
                    weakmsn() )
            except Exception, e:
                print 'Plugin ' + module + ' could not be initialized'
                print 'Reason: ' + str( e  )

    def checkPlugin( self, name ):
        '''check if the plugin can be initialized'''
        
        if self.plugin.has_key( name ):
            return self.plugin[ name ].check()
        else:
            return [ False, 'The plugin isn\'t loaded' ]
        
    def startPlugin( self, name ):
        '''start the plugin, call check before this!'''
        
        if self.plugin.has_key( name ):
            self.plugin[ name ].start()
            self.runningPlugins.append( name )
            return True
        else:
            return False
        
    def stopPlugin( self, name ):
        '''stop the plugin'''
        
        if self.plugin.has_key( name ):
            if name in self.runningPlugins:
                self.plugin[ name ].stop()
                self.runningPlugins.remove( name )
                return True
        else:
            return False
        
    def getPlugin( self, name ):
        '''return the plugin if exist or None'''
        
        if self.plugin.has_key( name ):
            return self.plugin[ name ]
        else:
            return None
        
    def destroy( self ):
        '''Stops all the running plugins and cleans references'''
        
        for i in self.runningPlugins:
            try:
                self.plugin[ i ].stop()
            except:
                emesenelib.common.debug( 'Plugin ' + self.plugin[ i ].name + \
                    ' failed to stop' )
        
