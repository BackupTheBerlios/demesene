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

'''module to handle p2p sessions on msn protocol'''

import os
import time
import random
import base64
import struct
import gobject

import common
import Msnobj
import msn_slp

common.debugFlag = True

def contains(string, substring):
    '''return True if string contains substring'''
    return (string.find(substring) != -1)
    
# we use the max from sys.maxint in a 32 bit machine because
# in a 64 bit machine it is bigger and can give some troubles
def random_number(minimum = 0, maximum = 2147483647):
    '''return a random number between minimum and maximum'''
    return random.randint(minimum, maximum)
 
class Base(gobject.GObject):
    '''a base class for P2P handlers
    this class has all the methods to create the different
    messages and to check if a message belong to a handler'''

    __gsignals__ = { 
        # message, session_id
        'msnp2p-message-ready':
        (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, 
            (gobject.TYPE_PYOBJECT, ) * 2),
        
        # flags, file, footer, bye (bool)
        'msnp2p-file-ready':
        (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
            (gobject.TYPE_PYOBJECT, ) * 4),

        # message
        'debug':
        (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
            (gobject.TYPE_PYOBJECT, ))
    }

    # workarounds for pylint lack of support of builtin subclassing
    # just to get cleaner output
    emit = gobject.GObject.emit
    connect = gobject.GObject.connect
    disconnect = gobject.GObject.disconnect
    
    # seconds alive until disconnecting automatically
    MAX_TIME_ALIVE = 60*3

    FOOTER = '\0\0\0\0'
    DP_FOOTER = '\0\0\0\1'
    FILE_FOOTER = '\0\0\0\2'
    INK_FOOTER = '\0\0\0\3'
    CE_FOOTER = '\0\0\0\x0c'

    # these must be replaced on subclassing
    temporary_session = None
    signals_p2p = [] # ['msnp2p-message-received']
    signals_self = [] # ['msnp2p-message-ready']
    
    def __init__(self, p2p):
        '''from_ is the sender and to the receiver email'''
        gobject.GObject.__init__(self)

        # the moment when its created
        self.time_stamp = time.time()
        
        # list of identifiers of connected signals
        self.signal_ids = []

        self.from_ = p2p.manager.msn.user
        self.to_ = p2p.mail
        
        # this values are just the most common ones
        self.via = msn_slp.random_id()
        self.cseq = '0'
        self.call_id = msn_slp.random_id()
        self.max_forwards = '0'
        self.content_type = ''
        self.content_length = ''
        self.euf_guid = ''
        self.session_id = str(random_number(50000))
        self.app_id = ''
        self.context = ''

        self.data = None

        p2p.emit('new-p2p-session', self)

    def check_time_limit(self):
        '''check if the time alive is greater than MAX_TIME_ALIVE
        if it is, return True to let the gc destroy the object'''

        if self.temporary_session and \
            time.time() > self.time_stamp + Base.MAX_TIME_ALIVE:

            self.debug('max time alive exceeded', 'p2p')
            return True

    def debug(self, message, _channel=''):
        '''Emits the debug signal and displays the message in the terminal'''
        self.emit('debug', message)
        common.debug(message, 'p2p')
        
    def is_data(self, bin):
        '''return True if the header is from a data message of
        this p2p session'''

        if bin.flag != bin.ACK_FLAG and \
           bin.session_id == int(self.session_id):
            return True

        return False

    def is_last_data(self, bin):
        '''return True if it is the last data message'''

        if self.is_data(bin) and \
            bin.data_offset + bin.message_length == bin.total_data_size:
            return True

    def connect_handler(self, p2p):
        '''connects signals, yay'''

        # the following may be confusing, but who cares? just don't touch
        # i use strings here to avoid saving a reference
        targets = ('p2p', self.signals_p2p), ('self', self.signals_self)

        for owner, signals in targets:
            if owner == 'p2p':
                src, dest = p2p, self
            else:
                src, dest = self, p2p

            for signal in signals:
                funcname = 'on_' + signal.replace("-", "_")
                identifier = src.connect(signal, getattr(dest, funcname))
                self.signal_ids.append((owner, identifier))

    def disconnect_handler(self, p2p):
        '''disconnects itself allowing garbage collection'''
        self.debug('disconnecting p2p handler', 'p2p')

        for owner, identifier in self.signal_ids:
            if owner == 'p2p':
                src = p2p
            else:
                src = self
            src.disconnect(identifier)


class Sender(Base):
    '''A class that sends p2p content based on msnobjs (with dpm)
    This is unbeliabely short, heh.'''

    temporary_session = True
    
    signals_p2p = []
    signals_self = ['msnp2p-message-ready', 'msnp2p-file-ready']

    def __init__(self, p2p, bin_header, slp, data):
        Base.__init__(self, p2p)

        self.data = data
        self.via = slp.via
        self.call_id = slp.call_id
        self.session_id = slp.body['SessionID']
        
        self.connect_handler(p2p)
        self.emit('msnp2p-message-ready', msn_slp.ok(self), 0)
        self.emit('msnp2p-message-ready', '\0\0\0\0', self.session_id) #dpm
        self.emit('msnp2p-file-ready', bin_header.EACH_FLAG, self.data,
            Base.DP_FOOTER, self.on_transfer_complete)

    def on_transfer_complete(self, p2p):
        self.emit('msnp2p-message-ready', msn_slp.bye(self), 0)
        self.disconnect_handler(p2p)


class Receiver(Base):
    '''a class that request data to other client and receive it'''

    temporary_session = True

    signals_p2p = ['msnp2p-message-received']
    signals_self = ['msnp2p-message-ready']

    def __init__(self, p2p, msnobj):
        '''p2p is a P2PUser, msnobj is a Msnobj'''

        if p2p.last_requested_msnobj == msnobj:
            return
        
        Base.__init__(self, p2p)
        
        p2p.last_requested_msnobj = msnobj
        self.msnobj = msnobj

        if self.msnobj.type == Msnobj.Msnobj.DISPLAY_PICTURE:
            self.app_id = '1' 
        elif self.msnobj.type == Msnobj.Msnobj.CUSTOM_EMOTICON:
            self.app_id = '12' 

        self.connect_handler(p2p)

        context = base64.b64encode(str(msnobj) + '\0')
        self.emit('msnp2p-message-ready', msn_slp.invite(self, context), 0)
    
    def on_msnp2p_message_received(self, p2p, bin, slp, message):
        '''method called when P2PManager receives a msnp2p message
        we check if it is from this session, if it is, we process it
        if we are finished or something went wrong, we disconnect the signal
        '''
        if self.check_time_limit():
            self.disconnect_handler(p2p)
        else:
            self.debug('receiver checking', 'p2p')
            if int(self.session_id) == int(bin.session_id):
                body = message[48:-4]

                if body == '\0\0\0\0':   # ignore dpm
                    return
                
                if len(body) != bin.total_data_size:
                    self.debug('corrupt data, not all pieces received')
                elif self.msnobj.type == Msnobj.Msnobj.CUSTOM_EMOTICON:
                    self.debug('custom-emoticon-data-received', 'p2p')
                    p2p.emit('custom-emoticon-data-received', 
                        self.msnobj, body, self.to_)
                elif self.msnobj.type == Msnobj.Msnobj.DISPLAY_PICTURE:
                    self.debug('display-picture-received', 'p2p')
                    p2p.emit('display-picture-received', 
                        self.msnobj, body, self.to_)
                else:
                    self.debug('no CE or DP? %s' % self.msnobj.type, 'p2p')

                self.disconnect_handler(p2p)


class DCHandler(Base):
    '''A class that handles direct connect invites
    After the automatic ack massacre, most code here was removed,
    so handling ACK MSNSLP messages'''

    temporary_session = False

    signals_p2p = ['msnp2p-message-received']
    signals_self = ['msnp2p-message-ready']

    def __init__(self, p2p, bin_header, slp):
        '''this processes the first invite, subsequent invites should '''
        Base.__init__(self, p2p)

        self.via = slp.via
        self.call_id = slp.call_id
        if 'SessionID' in slp.body:
            self.session_id = slp.body['SessionID']
        else:
            self.session_id = 0
        
        self.connect_handler(p2p)
        self.tempp2p = p2p
        
        self.handle_invite(bin_header, slp)
            
    def handle_invite(self, bin_header, slp):
        '''Handles a invite message'''

        if slp.content_type == msn_slp.SLPMessage.CONTENT_TRANS_REQ:
            # params after \r\n\r\n:
            #Bridges: TRUDPv1 TCPv1 SBBridge TURNv1
            #NetID: -1689699384
            #Conn-Type: Port-Restrict-NAT
            #TCP-Conn-Type: Port-Restrict-NAT
            #UPnPNat: false
            #ICF: false
            #Hashed-Nonce: {44C4DB18-98AC-2025-1404-1998BEE1C437}
            #SessionID: 10958830
            #SChannelState: 0
            #Capabilities-Flags: 1

            message = msn_slp.ok(self)
            message.content_type = msn_slp.SLPMessage.CONTENT_TRANS_RESP
            message.body = {
                'Bridge': 'TCPv1',
                'Listening': 'false',
                'Nonce': '{00000000-0000-0000-0000-000000000000}',
            }
            self.emit('msnp2p-message-ready', message, 0)

        elif slp.content_type == msn_slp.SLPMessage.CONTENT_TRANS_RESP:
            # the second invite is a TRANSRESP. body:
            # 
            # Bridge: TCPv1
            # Listening: true
            # Conn-Type: Direct-Connect
            # TCP-Conn-Type: Direct-Connect
            # Nonce: {A10AE850-D3DD-4A4A-A69D-C41F01D41F94}
            # IPv4Internal-Addrs: 5.127.##.## 169.254.##.### 201.255.###.##
            # IPv4Internal-Port: 3660
            #  <alt>
            # IPv4Internal-Addrs: 190.183.##.##
            # IPv4Internal-Port: 1434
            # SessionID: 278241011
            # SChannelState: 0
            # Capabilities-Flags: 1

            # this is auto acked
            pass

    def on_msnp2p_message_received(self, p2p, bin, slp, message):
        self.debug('DC Handler checking')
        if 'SessionID' in slp.body:
            session_id = slp.body['SessionID']
        else:
            session_id = bin.session_id

        if session_id == self.session_id or slp.call_id == self.call_id:
            if slp.method.startswith('ACK'):

                addrs = []
                for field in ('External', 'Internal'):
                    fieldname = 'IPv4' + field + 'AddrsAndPorts'
                    if fieldname in slp.body:
                        addrs.extend(slp.body[fieldname].strip().split())
                
                self.debug("Got ACK, i'll connect to " + repr(addrs))
                
                #p2p.get_switchboard()
                #p2p.switchboard.emit('message', 'p2p', '',
                #    'Received address list ' + repr(addrs), '', '')
                #time.sleep(10)
                
            elif slp.method.startswith('BYE'):
                self.disconnect_handler(p2p)


class FTSender(Base):
    '''a class that request data to other client and receive it'''
    
    temporary_session = False
    
    signals_p2p = ['msnp2p-message-received', 'file-transfer-canceled']
    signals_self = ['msnp2p-message-ready', 'msnp2p-file-ready']

    def __init__(self, p2p, filename):
        Base.__init__(self, p2p)
        
        self.app_id = '2' 
        
        self.context = FTContext()
        self.context.filename = filename
        #self.context.preview = base64.b64encode( self.data )
        self.context.file_size = os.stat(filename).st_size
        self.data = open(filename, "rb")

        self.connect_handler(p2p)
        self.current_transfer = 0

        message = msn_slp.invite(self, base64.b64encode(str(self.context)),
            msn_slp.SLPMessage.EUFGUID_FILE)

        self.emit('msnp2p-message-ready', message, 0)
        
    def on_msnp2p_message_received(self, p2p, bin, slp, message):
        '''method called when P2PManager receives a msnp2p message
        we check if it is from this session, if it is, we process it
        if we are finished or something went wrong, we disconnect the signal
        '''
        
        if 'SessionID' in slp.body:
            session_id = int(slp.body['SessionID'])
        else:
            session_id = int(bin.session_id)

        self.debug("FTSender checking")

        if session_id == int(self.session_id):
            self.debug("Mine!")
            if slp.method == msn_slp.SLPMessage.OK_STATUS:
                self.debug("Accepted")
                common.debug('sending data', 'p2p')
                p2p.emit('file-transfer-accepted', int(self.session_id),
                    self.context, 'Me')
                self.emit('msnp2p-file-ready', bin.FILE_FLAG | \
                    bin.EACH_FLAG | bin.STORAGE_FLAG, self.data,
                    Base.FILE_FOOTER, self.on_transfer_complete)
                
            elif slp.method == msn_slp.SLPMessage.DECLINE_STATUS or \
                 slp.method.startswith('BYE'):
                
                self.debug("Cancelled")
                # notify the user
                p2p.emit('transfer-failed', int(self.session_id), 'cancelled')
                self.disconnect_handler(p2p)
            else:
                self.debug("wtf is " + str(slp.method))
        elif slp.call_id == self.call_id and slp.method.startswith("BYE"):
            self.debug("file transfer canceled", 'p2p')
            p2p.emit('transfer-failed', int(self.session_id), 'cancelled')
            self.disconnect_handler(p2p)
            
    def on_transfer_complete(self, p2p):
        p2p.emit('file-transfer-complete', int(self.session_id),
            self.context, None, 'Me')
        self.emit('msnp2p-message-ready', msn_slp.bye(self), 0)
        self.disconnect_handler(p2p)

    def on_file_transfer_canceled(self, p2p, session, context, sender):
        '''callback for P2PUser file-transfer-canceled, sends a decline
        message canceling the transfer'''
        if int(session) == int(self.session_id):
            self.debug('canceling FT')
            self.emit('msnp2p-message-ready', msn_slp.bye(self), 0)
            self.disconnect_handler(p2p)
    
    def disconnect_handler(self, p2p):
        Base.disconnect_handler(self, p2p)
        if self.current_transfer and \
           self.current_transfer in p2p.outgoing_pending_messages:
            # this stops the send data callback
            del p2p.outgoing_pending_messages[self.current_transfer]
            self.current_transfer = 0

class FTReceiver(Base):
    '''a class to accept and handle an incoming file transfer'''

    temporary_session = False

    signals_p2p = ['msnp2p-message-received', 'msnp2p-file-received',
        'file-transfer-accepted', 'file-transfer-canceled']
    signals_self = ['msnp2p-message-ready']

    def __init__(self, p2p, context, slp, bin_header):
        '''context, slp and bin_header are from the INVITE message'''
        Base.__init__(self, p2p)

        self.context = context

        self.via = slp.via
        self.call_id = slp.call_id
        self.session_id = int(slp.body['SessionID'])
        
        self.connect_handler(p2p)

        p2p.start_new_conv()
        p2p.emit('file-transfer-invite', int(self.session_id), \
            self.context, self.from_)
        
    def on_file_transfer_accepted(self, p2p, session, context, sender):
        '''callback for P2PUser file-transfer-accepted, sends a 200ok
        message starting the transfer'''
        if int(session) == int(self.session_id) and \
           context == self.context and \
           sender == self.from_:

            # accept the file
            self.debug('accepting FT')
            self.emit('msnp2p-message-ready', msn_slp.ok(self), 0)

    def on_file_transfer_canceled(self, p2p, session, context, sender):
        '''callback for P2PUser file-transfer-canceled, sends a decline
        message canceling the transfer'''
        if int(session) == int(self.session_id):
            self.debug('canceling FT')
            self.emit('msnp2p-message-ready', msn_slp.bye(self), 0)
            self.disconnect_handler(p2p)

    def on_msnp2p_message_received(self, p2p, bin, slp, message):
        '''method called when P2PManager receives a msnp2p message
        we check if it is from this session, if it is, we process it
        if we are finished or something went wrong, we disconnect the signal
        '''
        
        self.debug('FT Receiver checking', 'p2p')
        if 'SessionID' in slp.body:
            session_id = int(slp.body['SessionID'])
        else:
            session_id = int(bin.session_id)

        if session_id == int(self.session_id):
            if slp.method == msn_slp.SLPMessage.DECLINE_STATUS or \
               slp.method.startswith('BYE'):
                
                self.debug("file transfer canceled", 'p2p')
                p2p.emit('transfer-failed', int(self.session_id), 'cancelled')
                self.disconnect_handler(p2p)

            if bin.flag == bin.CANCEL_FLAG:
                self.debug('cancelled on TLP')
                p2p.emit('transfer-failed', int(self.session_id), 'error')
                self.disconnect_handler(p2p)

        elif slp.call_id == self.call_id and slp.method.startswith("BYE"):
            self.debug("file transfer canceled", 'p2p')
            p2p.emit('transfer-failed', int(self.session_id), 'cancelled')
            self.disconnect_handler(p2p)
            
    def on_msnp2p_file_received(self, p2p, bin, rc):
        '''Method called when the file is received succesfully'''
        self.debug('FTReceiver checking file')
        if self.is_data(bin) and bin.flag & bin.FILE_FLAG:
            self.debug('file received')
            
            # file received successfully
            self.debug('file-transfer-complete')
            p2p.emit('file-transfer-complete', int(self.session_id),
                self.context, rc, self.from_)
            self.disconnect_handler(p2p)



class FTContext(object):
    '''this class represents a File Transfer Context'''

    #FORMAT = '<LLQL520s30sL64s'  # perl?
    FORMAT = '<LLQL520s30sL'
    PORTABLE_FORMAT = '<LQL520s'  # note: without header
    HEADER_FORMAT = '<L'

    UNKNOWN_FT = 0xffffffff
    UNKNOWN_BG = 0xfffffffe
    RUBBISH = base64.b64encode("rubbish")

    TYPE_NO_PREVIEW = 0
    TYPE_PREVIEW = 1
    TYPE_BACKGROUND = 4
    
    def __init__(self, data=None):
        '''Constructor'''
        
        self.header_length = struct.calcsize(FTContext.FORMAT)
                                     # ..dw
        self.msnc = 2                # dw (3 == msn7)
        self.file_size = 0           # qw
        self.__data_type = 0         # dw
        self.__filename = ''         # 520 byte string, utf-16-le
        self.rubbish = ''            # 30 byte string, optional base64
        self.unknown1 = 0            # dw (see UNKNOWN_(BG|FT))

        # set properties
        self.data_type = FTContext.TYPE_NO_PREVIEW
        self.filename = ''

        self.preview = ''

        if data != None:
            self.fill(data)
            
    def __str__(self):
        '''return the representation of this object'''

        return struct.pack(FTContext.FORMAT,
            self.header_length,
            self.msnc,
            self.file_size,
            self.data_type,
            self.__filename,
            self.rubbish,
            self.unknown1) + self.preview
    
    def set_data_type(self, dword):
        '''property setter for data_type
        when it's set as background, the rubbish and unknown1 fields
        are set to the corresponding values'''

        self.__data_type = dword
        if dword == FTContext.TYPE_BACKGROUND:
            self.rubbish = FTContext.RUBBISH
            self.unknown1 = FTContext.UNKNOWN_BG
        else:
            self.rubbish = ''
            self.unknown1 = FTContext.UNKNOWN_FT

    def get_data_type(self):
        '''property getter for data_type'''
        return self.__data_type

    data_type = property(fset=set_data_type, fget=get_data_type)

    def set_filename(self, data):
        '''set the value of filename'''
        data = os.path.basename(data)
        self.__filename = data.encode('utf-16-le', 'replace').ljust(520, '\0')
        
    def get_filename(self):
        '''get the value of filename'''
        return self.__filename.decode('utf-16-le', 'replace').replace('\0', '')

    filename = property(fset=set_filename, fget=get_filename)
    
    def print_fields(self):
        '''print the binary fields'''
        print
        print 'Header length:   ' + str(self.header_length)
        print 'msnc:            ' + str(self.msnc)
        print 'File size:       ' + str(self.file_size)
        print 'Type:            ' + str(self.data_type)
        print 'Filename:        ' + str(self.filename)
        print
        
    def fill(self, data):
        '''fill the object with the data provided'''
        self.header_length = struct.unpack(FTContext.HEADER_FORMAT, data[:4])[0]
        portable_size = struct.calcsize(FTContext.PORTABLE_FORMAT)
        header = data[4:portable_size + 4]
        
        # from __future__ import braces
        (   
            self.msnc,
            self.file_size,
            self.data_type,
            self.__filename,
        ) = struct.unpack(FTContext.PORTABLE_FORMAT, header)

        self.preview = data[self.header_length:]
