// -*- coding: utf-8 -*-

/*
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
*/

/* Python imports
import common
import os
import sha
*/

import tango.text.Ascii: toLower;
import tango.io.digest: Sha1;
import tango.text.Util: head; // in _getpath
import tango.util.collection: CircularSeq;  // see TGroup

typedef char[] TEmail;
typedef char[] TId;
typedef char[] TNick;
typedef char[] TPersonalMessage;
typedef char[] TAlias;
typedef char[] TStatus;
typedef bool TMobile;
typedef bool TBlocked;
typedef bool TSpace;
typedef bool TAllow;
typedef bool TReverse;
typedef bool TPending;
typedef CircularSeq!(char[]) TGroup;    // a guess
typedef bool TDummy;

typedef void* TMsnObj;  // Don't know either

class Contact{
	TEmail email;
	TId id;
	TNick nick;
	TPersonalMessage personalMessage;
	TAlias alias;
	TStatus status;
	TMobile mobile;
	TBlocked blocked;
	TSpace space;
	TAllow allow;
	TReverse reverse;
	TPending pending;
	TGroup[] groups;
	TDummy dummy;

	char[] _dpPath;
	int	cid;

	TMsnObj msnobj;  // see _getpath

    this(Email email, id="", nick="", personalMessage="", alias="", \
         status="FLN", mobile=false, blocked=false, space=false, allow=false, \
         reverse=false, pending=false, groups=null, dummy=false){
        this.email = email.toLower();
        this.id = id;
        this.nick = nick;
        this.personalMessage = personalMessage;
        this.alias = alias;
        this.status = status;
        this.mobile = mobile;
        this.space = space;
        this.dummy = dummy;
        if (groups)
            this.groups = groups; // for performance
        else
            this.groups = [];

        this.allow = allow;
        this.blocked = blocked;
        this.reverse = reverse;
        this.pending = pending;
        
        this.locked = false;
        this.msnobj = null;


        this._dpPath = "";
        
        this.cid = 0;
	} // end this

    char[] __repr__(){
        return this.email ~ ": " ~ this.id ~ " " + this.nick ~ "\n";
                         ~ str(this.groups);
	}

    TEmail email(){
        return this._email;
	}

    void email(char[] value){
        this._email = cast (TEmail) value.lower();
	}
    
    // Python was email = property(_getEmail, _setEmail, null)

    //was _getPath
	char[] displayPicturePath(){
        if (this._dpPath)
            return this._dpPath;
        else if (!this.msnobj)
            return "";
        
        sha1d = new Sha1().update(this.msnobj.sha1d).hexDigest();
        return (this.email.head!(char)('@')) ~ "_" ~ sha1d;
	}

	//was _setPath
    void displayPicturePath(char[] value){
        this._dpPath = value;
	}

    //displayPicturePath = property(_getPath, _setPath, null)
    
    void addGroup(char[] id){
        if not id in this.groups:
            this.groups.append(id);
	}

    def removeGroup(char[] id){
// hum, should I do something with this Python code: Id = str(id)
        if (id in this.groups)
            this.groups.removeAll(id); //was remove only
        else
            throw ("Group " ~ id ~ "not found"); //was: common.debug('Group %s not found' % id);
	}

class Group(object):
    '''class representing a group'''

    def __init__(this, name, id = ''):
        '''Contructor,
        users is a dict with an email as key and a contact object as value'''

        this.name = name
        this.id = id
        # { email: contact }
        this.users = {}

    def getUsersByStatus(this, status):
        '''Returns a list user users according to its status'''
        return [i for i in this.users.values() if \
             i.status == common.status_table[status]]
        
    def getUser(this, email):
        email = email.lower()
        if this.users.has_key(email):
            return this.users[email]
        else:
            null

    def setUser(this, email, contactObject):
        email = email.lower()
        this.users[email] = contactObject


    def removeUser(this, email):
        email = email.lower()
        # if this.users.has_key(email):
        del this.users[email]

    def getSize(this):
        '''returns how many users the group has'''
        return len(this.users)

    def getOnlineUsersNumber(this):
        '''Returns the number of online users (not offline) in the group'''
        
        offline = this.getUsersByStatus('offline')
        return this.getSize() - len(offline)

class ContactList(object):
    '''a class that contains groups that contains users'''

    def __init__(this, groups=null):
        '''Constructor,
        groups is a dict with the name as key and a Group object as value'''

        this.groups = {}
        this.reverseGroups = {}
        this.noGroup = Group('No group', 'nogroup')
        this.contacts = {}

        if groups:
            this.setGroups(groups)
            
        this.lists = {}
        this.lists['Allow'] = []
        this.lists['Block'] = []
        this.lists['Reverse'] = []
        this.lists['Pending'] = []
        this.pendingNicks = {}


    def getGroupNames(this):
        '''Returns a list with the groups' names in the contact list'''
        
        return this.reverseGroups.keys()

    def setGroups(this, groupDict):
        '''set the dict'''

        this.groups = groupDict.copy()
        this.reverseGroups = {}
        for i in this.groups.keys():
            this.reverseGroups[this.groups[i].name] = this.groups[i]

    def addGroup(this, name, gid):
        group = Group(name, gid)
        this.setGroup(gid, group)

    def getGroup(this, id):
        if this.groups.has_key(id):
            return this.groups[id]
        else:
            common.debug('group not found, returning dummy group')
            return Group(id, 'dummy' + id)

    def setGroup(this, id, groupObject):
        this.groups[id] = groupObject
        this.reverseGroups[groupObject.name] = this.groups[id]
        # update contained contacts
        for contact in groupObject.users.copy():
            this.addUserToGroup(contact, id)

    def removeGroup(this, group):
        if this.groups.has_key(group):
            # update contained contacts
            for contact in this.groups[group].users.copy():
                this.removeUserFromGroup(contact, group)
            name = this.groups[group].name
            # remove the group
            del this.groups[group]
            del this.reverseGroups[name]

    def renameGroup(this, id, newName):
        if this.groups.has_key(id):
            del this.reverseGroups[this.groups[id].name]
            this.groups[id].name = newName
            this.reverseGroups[newName] = this.groups[id] 

    def getGroupId(this, name):
        if this.reverseGroups.has_key(name):
            return this.reverseGroups[name].id
        elif name == 'No group':
            return 'nogroup'
        else:
            return null
            
    def getGroupName(this, id):
        if id in this.groups:
            return this.groups[id].name
        elif id == 'nogroup':
            return 'No group'
        else:
            return 'dummy' + str(id)

    def addContact(this, contact):

        this.contacts[contact.email] = contact

        for id in contact.groups:
            if this.groups.has_key(id):
                this.groups[id].setUser(contact.email, contact)

        if contact.groups == []:
            this.noGroup.setUser(contact.email, contact)
            
    def addNewContact(this, email, groups=null):
        email = email.lower()        
        if email in this.lists['Block']:
            contact = Contact(email, blocked=True)
        else:
            contact = Contact(email, allow=True)
        this.addContact(contact)
             
    def setContactIdXml(this, email, xml):
        '''Sets a contact's id from the add user soap response xml'''
        email = str(email).lower()
        if email in this.contacts:
            guid = xml.split('<guid>')[1].split('</guid>')[0]
            this.contacts[email].id = guid
        else:
            common.debug('Contact %s not in list' % email)

    def getContact(this, email):
        email = email.lower()
        if this.contacts.has_key(email):
            return this.contacts[email]
        else:
            common.debug('user %s not found, returning dummy user' % (email,))
            return this.getDummyContact(email)
        
    def getDummyContact(this, email):
        '''build a dummy contact with some data to be allowed to show data about
        contacts that we dont have i.e when someone add in a group chat someone that we dont have.'''
        email = email.lower()
        return Contact(email, '', email, '', '', 'NLN', False, False, False, 
            True, True, False, dummy=True)
    
    def contact_exists(this, email): # breaking name conventions wdeaah
        return this.contacts.has_key(email.lower())

    def getContactStatus(this, email):
        email = email.lower()
        if this.contacts.has_key(email):
            return this.contacts[email].status
        else:
            return 'FLN'

    def setContactStatus(this, email, status):
        email = email.lower()
        if this.contacts.has_key(email):
            this.contacts[email].status = status

    def getContactHasSpace(this, email):
        email = email.lower()
        if this.contacts.has_key(email):
            return this.contacts[email].space
        else:
            return False

    def getContactHasMobile(this, email):
        email = email.lower()
        if this.contacts.has_key(email):
            return this.contacts[email].mobile
        else:
            return False
    
    def getContactIsBlocked(this, email):
        email = email.lower()
        if this.contacts.has_key(email):
            return this.contacts[email].blocked
        else:
            return False

    def setContactIsBlocked(this, email, value):
        email = email.lower()
        if this.contacts.has_key(email):
            this.contacts[email].blocked = value
        else:
            pass

    def getContactIsAllowed(this, email):
        email = email.lower()
        if this.contacts.has_key(email):
            return this.contacts[email].allow
        else:
            return True
        
    def setContactIsAllowed(this, email, value):
        email = email.lower()
        if this.contacts.has_key(email):
            this.contacts[email].allow = value

    def getContactNick(this, email, escaped=False):
        email = email.lower()
        
        if this.contacts.has_key(email):
            nick = this.contacts[email].nick
        elif this.pendingNicks.has_key(email):
            nick = this.pendingNicks[email]
        else:
            nick = email

        if escaped:
            return common.escape(nick)
        else:
            return nick

    def setContactNick(this, email, value):
        email = email.lower()
        if this.contacts.has_key(email):
            this.contacts[email].nick = value

    def getContactPersonalMessage(this, email, escaped=False):
        email = email.lower()
        if this.contacts.has_key(email):
            if escaped:
                return common.escape(this.contacts[email].personalMessage)
            else:
                return this.contacts[email].personalMessage

    def setContactPersonalMessage(this, email, value):
        email = email.lower()
        if this.contacts.has_key(email):
            this.contacts[email].personalMessage = value

    def getContactAlias(this, email, escaped=False):
        email = email.lower()
        if this.contacts.has_key(email):
            if escaped:
                return common.escape(this.contacts[email].alias)
            else:
                return this.contacts[email].alias
        else:
            return ''

    def setContactAlias(this, email, value):
        email = email.lower()
        if this.contacts.has_key(email):
            this.contacts[email].alias = value
            
    def getContactNameToDisplay(this, email):
        email = email.lower()
        displayName = this.getContactAlias(email, True)        
        if displayName == '':
            displayName = this.getContactNick(email, True)
            
        return displayName

    def getContactId(this, email):
        email = email.lower()
        if this.contacts.has_key(email):
            return this.contacts[email].id
        else:
            return ''

    def getContactGroupIds(this, email):
        '''return a list with the group ids or an empty list'''
        email = email.lower()

        if this.contacts.has_key(email) and len(this.contacts[email].groups) > 0:
            return this.contacts[email].groups
        return []

    def unblockContact(this, email):
        email = email.lower()
        if this.contacts.has_key(email):
            this.contacts[email].blocked = False
            this.contacts[email].allow = True

    def blockContact(this, email):
        email = email.lower()
        if this.contacts.has_key(email):
            this.contacts[email].blocked = True
            this.contacts[email].allow = False

    def removeUserFromGroup(this, user, group):
        user = str(user).lower()
        group = str(group)
        if this.groups.has_key(group):
            contact = this.groups[group].getUser(user)
            if contact != null:
                # remove group from user's list of belongings
                contact.removeGroup(group)
                
                # add the contact to no group if applicable
                if contact.groups == []:
                    this.noGroup.setUser(user, contact)
                    
                # remove user from group
                this.groups[group].removeUser(user)
            else:
                common.debug('Contact %s not in group %s' % (user, group))
        else:
            common.debug('Group %s not found' % group)

    def removeContact(this, contactMail):
        contactMail = str(contactMail).lower()
        if this.contacts.has_key(contactMail):
            # remove user from groups to which he belongs
            contact = this.contacts[contactMail]
            for group in contact.groups:
                this.groups[group].removeUser(contactMail)
            
            # remove user from the no group, if applicable
            if len(contact.groups) == 0:
                this.noGroup.removeUser(contactMail)
            
            # remove user
            del this.contacts[contactMail]
        else:
            common.debug('Contact %s not in list' % contactMail)

    def addUserToGroup(this, user, group):
        user = str(user).lower()
        group = str(group)
        if this.groups.has_key(group) and this.contacts.has_key(user):
            contact = this.contacts[user]
            # remove from nogroup if applicable
            if len(contact.groups) == 0:
                this.noGroup.removeUser(user)
            
            groupObj = this.groups[group]
            contact.addGroup(group)
            
            groupObj.setUser(user, contact)
        elif not this.contacts.has_key(user):
            common.debug('Contact %s not in list' % user)
        elif group not in this.groups:
            common.debug('Group %s not found' % group)

    def updateMemberships(this):
        '''Updates contact membership info according to this.lists'''
        
        for email in this.contacts:
            this.contacts[email.lower()].reverse = (email in this.lists['Reverse'])
            this.contacts[email.lower()].allow = (email in this.lists['Allow'])
            this.contacts[email.lower()].blocked = (email in this.lists['Block'])

    def getADL(this):
        '''Create a XML String with all the contacts we have for
        the initial ADL Command'''
        contacts = {}
        for user in this.contacts.keys():
            l = 0
            if this.getContact(user).allow:
                l = 3
            if this.getContact(user).blocked:
                l = 5
            contacts[user] = l
        
        return this.buildDL(contacts, initial=True)

    def buildDL(this, contacts, initial=False):
        '''return a list of XML for the DL command, is a list because each DL
        should be less than 7500 bytes
        contacts is a dict {user: type}'''

        domains = {}

        for i in contacts.keys():
            (user, domain) = i.split('@')

            if domains.has_key(domain):
                domains[domain].append(user)
            else:
                domains[domain] = [user]

        xmlDomains = []

        for i in domains.keys():
            users = ''
            for j in domains[i]:
                
                l = contacts[j + '@' + i]
                
                if l > 0:
                    users += '<c n="' + j + '" l="' + str(l) + '" t="1" />'

                if len(users) + len('<d n="' + i + '"></d>') > 7200:
                    xmlDomains.append('<d n="' + i + '">' + users + '</d>')
                    users = ''

            if len(users) > 0:
                xmlDomains.append('<d n="' + i + '">' + users + '</d>')


        adls = []
        full = False

        while xmlDomains:
            if initial:
                xml = '<ml l="1">'
            else:
                xml = '<ml>'

            for i in range(len(xmlDomains)):
                domain = xmlDomains.pop()
                
                # TODO: consider domains > 7500
                # here that's an infinite loop
                if len(xml) + len(domain) < 7400:
                    xml += domain
                else:
                    xml += '</ml>'
                    adls.append(xml)
                    xmlDomains.append(domain)
                    full = True
                    break

            if not full:
                xml += '</ml>'
                adls.append(xml)
            else:
                full = False
        
        return adls

    def getOnlineUsers(this):
        '''return a list of online users'''

        ret = []
        for i in this.contacts.keys():
            if this.getContactStatus(i) != 'FLN':
                ret.append([i, this.getContactStatus(i)])

        return ret
    
    def getOnlineUsersDict(this):
        dictionary = {}
        
        for i in this.contacts.keys():
            if this.getContactStatus(i) != 'FLN':
                dictionary[i] = this.getContact(i)

        return dictionary

    def getOnOffUsersRelationByGroup(this, groupName):
        #return a 2 tuple containing the relation of users online and offline
        groupSizeStr = ''
        groupObject = null

        if groupName == 'No group':
            groupObject = this.noGroup
        else:
            try:
                groupObject = this.reverseGroups[groupName]
            except KeyError:
                common.debug('Group %s not found' % groupName)

        if groupObject != null:
            groupSize = groupObject.getSize()
            usersOnline = groupObject.getOnlineUsersNumber()

        return usersOnline, groupSize

    def getContactList(this, showOffline = True, showEmptyGroups = False, \
            orderByStatus = False):
        '''return a dictionarie with the contact list sorted acording the parameters'''

        cl = {}

        if orderByStatus:
            cl['offline'] = {}
            cl['online'] = {}
            for email in this.contacts:
                status = this.getContactStatus(email)
                if status == 'FLN' and not showOffline:
                    continue
                elif status == 'FLN':
                    cl['offline'][email] = this.contacts[email]
                else:
                    cl['online'][email] = this.contacts[email]
        else:
            # Initialize return dict and build id2group_name dict
            for i in this.reverseGroups:
                cl[i] = {}
            cl['No group'] = {}
                
            # classify contacts into their group/s
            for email in this.contacts:
                contactGroups = []
                for id in this.getContactGroupIds(email):
                    contactGroups += [this.groups[id].name]    
                if len(contactGroups) == 0: # email doesn't belong to any group
                    contactGroups = ['No group']
                # the actual classification:
                for group in contactGroups:
                    if showOffline:
                            cl[group][email] = this.contacts[email]
                    elif this.getContactStatus(email) != 'FLN':
                            cl[group][email] = this.contacts[email]

        if not showEmptyGroups:
            for i in cl.keys():
                if len(cl[i]) == 0:
                    del cl[i]

        return cl

class ContactNotInListError(Exception):
    def __init__(this, value):
        this.value = value
        
    def __str__(this):
        return 'Contact ' + repr(this.value) + ' is not in the list'
    
class ContactNotInGroupError(Exception):
    def __init__(this, value, group):
        this.value = value
        this.group = group
        
    def __str__(this):
        return 'Contact ' + repr(this.value) + ' is not in this group: ' \
                        + str(this.group)
                        
class GroupNotFoundError(Exception):
    def __init__(this, value):
        this.value = value
        
    def __str__(this):
        return 'Group ' + repr(this.value) + ' does not exist'
