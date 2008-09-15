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

import common

import sys
import Queue
import threading
import httplib

requestQueue = Queue.Queue( 0 )
responseQueue = Queue.Queue( 0 )

def put(request):
    global requestQueue
    #common.debug("SoapManager.put(%s%s)" % (request.host, request.path), "soap")
    requestQueue.put(request)
    
def get():
    global responseQueue
    retval = responseQueue.get()
    common.debug("SoapManager.get() --> %s%s" % (retval.host, retval.path),
        "soap")
    return retval

def getNoBlock():
    global responseQueue
    
    return responseQueue.get(True, 0.01)

def process():
    '''run the callbacks if some response is in responseQueue'''
    global responseQueue
    
    while True:
        try:
            response = getNoBlock()
            common.debug("SoapManager.process: %s%s" %
                (response.host, response.path), "soap")
                        
            if response.callback != None:
                response.callback( response, *response.args )
        except Queue.Empty:
            break

    return True

class SoapRequest( object ):
    '''This class represent a soapRequest'''
    
    def __init__( self, action, host, port, path, body, \
                  callback=None, args=() ):
        '''Constructor'''
        
        self.action = action
        self.host = host
        self.port = port
        self.path = path
        self.body = body
        self.callback = callback
        self.args = args
        self.extraCookie = ''
        self.errorCount = 0
        self.status = ( 0 , '' )

class SoapManager( threading.Thread ):
    '''This class is a thread that wait for soapRequest in the requestQueue
    and make the request, then add the response to the responseQueue'''
       
    def __init__( self, msn ):
        threading.Thread.__init__( self )
        
        self.msn = msn

    def process( self ):
        try:
            return process()
        except:
            self.msn.emit('exception', sys.exc_info())

    def destroy( self ):
        global requestQueue, responseQueue
        try:
            while True:
                tmp = responseQueue.get(True, 0.01)
                for i in dir(tmp):
                    if not i.startswith('_'):
                        setattr(tmp, i, None)
        except Queue.Empty:
            pass

        try:
            while True:
                tmp = requestQueue.get(True, 0.01)
                for i in dir(tmp):
                    if not i.startswith('_'):
                        setattr(tmp, i, None)
        except Queue.Empty:
            pass
        
        put('quit')
        self.msn = None

    def run( self ):
        global requestQueue, responseQueue
        
        while True:
            req = requestQueue.get()
            
            if req == 'quit' or self.msn == None:
                break
            else:
                try:
                    responseQueue.put( self.makeSoapRequest( req ) )
                except Exception, e:
                    print e
                    if req.errorCount < 2:
                        req.errorCount += 1
                        requestQueue.put( req )
                
        return False
        
    def makeSoapRequest( self, soapRequest, retry=True ):
    
        headers = { \
            "SOAPAction": soapRequest.action, \
            "Content-Type": "text/xml; charset=utf-8", \
            "Cookie": "MSPAuth=" + self.msn.MSPAuth + ";MSPProf=" + \
                self.msn.MSPProf + soapRequest.extraCookie, \
            "Host": soapRequest.host, \
            "Content-Length": str( len(soapRequest.body) ), \
            "User-Agent": "MSN Explorer/9.0 (MSN 8.0; TmstmpExt)", \
            "Connection": "Keep-Alive", \
            "Cache-Control": "no-cache", \
        }
        
        conn = None
        response = None
        
        if soapRequest.port == 443:
            conn = httplib.HTTPSConnection( soapRequest.host + ':' + \
                str(soapRequest.port) )  
        else:
            conn = httplib.HTTPConnection( soapRequest.host + ':' + \
                str(soapRequest.port) ) 
             
        conn.request( "POST", soapRequest.path, soapRequest.body, headers )
        response = conn.getresponse()

        soapResponse = SoapRequest( soapRequest.action, soapRequest.host, \
            soapRequest.port, soapRequest.path, response.read(), \
            soapRequest.callback, soapRequest.args )            
        soapResponse.status = ( response.status, response.reason )
        
        if soapResponse.body.count('TweenerChallenge') or \
                          soapResponse.body.count('LockKeyChallenge'):
            retry = False

        if retry and soapResponse.body.count('AuthenticationFailure') or \
                                 soapResponse.body.count('PassportAuthFail'):
            self.msn.passportReAuth()
            soapResponse = self.makeSoapRequest( soapRequest, False )
        
        return soapResponse 
