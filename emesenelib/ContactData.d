// -*- coding: utf-8 -*-

//  yet another change to test if "ssl required" only in gnome-terminal

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

import tango.util.log.Log; // used in ContactList.getGroup

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

typedef short TGId;

Logger logger = Log.getLogger("ContactData");	// a new Logger instance

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
} // end Class Contact

class Group(){

	char[] name, id;
	TContact[TEmail] users;

    this(char[] name,char[] id = ""){
		/*
        '''Contructor,
        users is a dict with an email as key and a contact object as value'''
		*/

        this.name = name;
        this.id = id;
        // was a comment in Python code # { email: contact }
        this.users = [];
	}
	
	///Returns a list user users according to its status
    CircularSeq!(TContact) getUsersByStatus(char[] status){
        /* Python code was: return [i for i in this.users.values() if \
             i.status == common.status_table[status]] */
		CircularSeq!(TContact) answer;
		foreach (user; this.users)
			if (user.status == common.status_table[status]) answer.append(user); // common not implemented yet
		return answer;
	}
        
    Contact getUser(TEmail email){
        lower_email = (cast (char[]) email).toLower();
        if lower_email in this.users
            return this.users[email];
        else
            null;
	}

    void setUser(TEmail email, Contact contactObject){
        lower_email = (cast (char[]) email).toLower();
        this.users[lower_email] = contactObject;
	}

    void removeUser(email){
        lower_email = (cast (char[]) email).toLower();
        // comment in original Python code # if this.users.has_key(email):
        this.users.remove(lower_email);
	}

    /// returns how many users the group has
    short getSize(){
		return this.users.length;
	}

	/// Returns the number of online users (not offline) in the group
    short getOnlineUsersNumber(){
		Contact[] offline = this.getUsersByStatus('offline');
        return this.getSize() - len(offline);
	}
} // end of Class Group

// a class that contains groups that contains users
class ContactList(Object){

	Group[TName] groups;
	Group[TName] reverseGroups; // I suppose
	Group noGroup;
	Contact[/* heu */] contacts; 
	??? [char[]] lists;

    this(groups=null){
        this.groups = [];
        this.reverseGroups = [];
        this.noGroup = Group("No group", "nogroup");
        this.contacts = [];

        if groups
            this.setGroups(groups);
            
        this.lists = [];
        this.lists["Allow"] = [];
        this.lists["Block"] = [];
        this.lists["Reverse"] = [];
        this.lists["Pending"] = [];
        this.pendingNicks = [];
	}

	/// Returns a list with the groups' names in the contact list
    Group[TName] getGroupNames(){
        return this.reverseGroups.keys();
	}

	///set the dict
    void setGroups(??? groupDict){
        this.groups = groupDict.dup;
        this.reverseGroups = [];
		foreach (int i, Group whatever ; groups)
            this.reverseGroups[this.groups[i].name] = this.groups[i];
	}

    void addGroup(char name, TGId gid){ // short for gid ??
        group = Group(name, gid);
        this.setGroup(gid, group);
	}

    Group getGroup(TypeId id){
        if (id in this.groups)
            return this.groups[id];
        else{
            logger.warn("group not found, returning dummy group");
            return Group(id, "dummy" ~ id);
		}
	}

    void setGroup(TGId id, Group groupObject){
        this.groups[id] = groupObject;
        this.reverseGroups[groupObject.name] = this.groups[id];
        // update contained contacts
        foreach (contact; groupObject.users.dup())
            this.addUserToGroup(contact, id);
	}

    void removeGroup(Group group){
        if (group in this.groups){
            // update contained contacts
            foreach (contact ; this.groups[group].users.dup())
                this.removeUserFromGroup(contact, group);
            name = this.groups[group].name;
            // remove the group
            this.groups.removeAll(group);
            this.reverseGroups.removeAll(name);
		} //if
	} // removeGroup

    void renameGroup(TGId id,TName newName){
        if (id in this.groups){
            this.reverseGroups.removeAll(this.groups[id].name);
            this.groups[id].name = newName;
            this.reverseGroups[newName] = this.groups[id];
		}
	} 

    TGId getGroupId(TName name){
        if (name in this.reverseGroups)
            return this.reverseGroups[name].id;
        else if (name == "No group")
            return "nogroup"
        else
            return null;
	}
            
    TName getGroupName(TGId id){
        if (id in this.groups)
            return this.groups[id].name;
        else if (id == "nogroup")
            return "No group";
        else
            return "dummy" ~ cast (char[]) id);
	}

    void addContact(Contact contact){

        this.contacts[contact.email] = contact;

        foreach (id ; contact.groups)
            if (id in this.groups.keys)
                this.groups[id].setUser(contact.email, contact);

        if (contact.groups == [])
            this.noGroup.setUser(contact.email, contact);
	}
            
    void addNewContact(TEmail email, Group[] groups=null){
        lower_email = email.toLower()        ;
        if (lower_email in this.lists['Block'])
            contact = Contact(email, blocked=True);
        else
            contact = Contact(email, allow=True);
        this.addContact(contact);
	}
             
	///Sets a contact's id from the add user soap response xml
    void setContactIdXml(TEmail email, char[] xml){
        auto lower_email = cast(char[])(email).toLower();
        if (email in this.contacts){
// euh!?
            guid = xml.split("<guid>")[1].split("</guid>")[0];
            this.contacts[email].id = guid;
		} else
            logger.warn("Contact %s not in list" ~ email);
	}

    Contact getContact(TEmail email){
        auto lowerEmail = email.toLower()
        if (lowerEmail in this.contacts.keys)
            return this.contacts[email];
        else{
            logger.warn("user " ~ lowerEmail ~ "not found, returning dummy user");
            return this.getDummyContact(email);
	}
        
    /**  build a dummy contact with some data to be allowed to show data about
        contacts that we dont have i.e when someone add in a group chat someone that we dont have. **/
    Contact getDummyContact(TEmail email){
        lowerEmail = email.toLower();
        return Contact(email, "", lowerEmail, "", "", "NLN", false, false, false, 
            true, true, false, dummy=True);
	}
    
    bool contact_exists(TEmail email){  // comment in Python code # breaking name conventions wdeaah
        return (email.toLower) in this.contacts.keys;
	}

    TStatus getContactStatus(TEmail email){
        lowerEmail = email.toLower();
        if (lowerEmail in this.contacts.keys)
            return this.contacts[lowerEmail].status;
        else
            return "FLN";
	}

    void setContactStatus(TEmail email, TStatus status){
        emailLower = email.toLower();
        if this.contacts.has_key(emailLower)
            this.contacts[emailLower].status = status;
	}

    bool getContactHasSpace(TEmail email){
        auto emailLower = email.toLower();
        if (emailLower in this.contacts.keys)
            return this.contacts[emailLower].space;
        else
            return false;
	}

    bool getContactHasMobile(TEmail email){
        auto emailLower = email.toLower();
        if (emailLower in this.contacts.keys)
            return this.contacts[email].mobile;
        else
            return false;
	}
    
    bool getContactIsBlocked(TEmail email){
        auto emailLower = email.toLower();
        if (emailLower in this.contacts.keys)
            return this.contacts[email].blocked
        else
            return false;
	}

    bool setContactIsBlocked(TEmail email, bool value):
        emailLower = email.toLower();
        if (emailLower in this.contacts.keys)
            this.contacts[email].blocked = value;
        else
            // pass
	}

    bool getContactIsAllowed(TEmail email){
        emailLower = email.toLower();
        if (emailLower in this.contacts.keys)
            return this.contacts[email].allow;
        else
            return true;
	}
        
    void setContactIsAllowed(TEmail email, bool value){
        emailLower = email.toLower();
        if (emailLower in this.contacts.keys)
            this.contacts[email].allow = value;
	}

    TNick getContactNick(TEmail email, escaped=false){
        auto emailLower = email.lower();
        
        if (emailLower in this.contacts.keys)
            nick = this.contacts[email].nick;
        else if (emailLower in this.pendingNicks.keys)
            nick = this.pendingNicks[emailLower];
        else
            nick = emailLower;

        if (escaped)
            return common.escape(nick);
        else
            return nick;
	}

    void setContactNick(TEmail email, value){
        auto emailLower = email.lower();
        if (emailLower in this.contacts.keys)
            this.contacts[emailLower].nick = value;
	}

    TPersonalMessage getContactPersonalMessage(TEmail email, bool escaped=false){
        auto emailLower = email.toLower();
        if (emailLower in this.contacts.keys)
            if (escaped)
                return common.escape(this.contacts[emailLower].personalMessage);
            else
                return this.contacts[emailLower].personalMessage;
	}

    void setContactPersonalMessage(TEmail email, TPersonalMessage value){
        auto email = email.toLower();
        if (emailLower in this.contacts.keys)
            this.contacts[emailLower].personalMessage = value;
	}

    TAlias getContactAlias(TEmail email, bool escaped=false){
        auto TEmail email = email.toLower();
        if (email in this.contacts.keys)
            if (escaped)
                return common.escape(this.contacts[emailLower].alias);
            else
                return this.contacts[emailLower].alias;
        else
            return "";
	}

    void setContactAlias(TEmail email,Contact value){
        auto emailLower = email.toLower();
        if (emailLower) in this.contacts.keys)
            this.contacts[emailLower].alias = value;
	}

    char[] getContactNameToDisplay(TEmail email){
        auto emailLower = email.toLower();
        char[] displayName = this.getContactAlias(email, true);
        if (displayName == "")
            displayName = this.getContactNick(email, true);
        return displayName;
	}

    TCId getContactId(TEmail email){
        auto emailLower = email.toLower();
        if (emailLower in this.contacts.keys)
            return this.contacts[emailLower].id;
        else
            return "";
	}

	///return a list with the group ids or an empty list
    TGId getContactGroupIds(TEmail email){

        auto email = email.toLower();

        if (emailLower in this.contacts.keys && len(this.contacts[email].groups) > 0)
            return this.contacts[email].groups;
        return [];
	}

    void unblockContact(TEmail email){
        auto emailLower = email.toLower();
        if (emailLower in this.contacts.keys){
            this.contacts[email].blocked = false;
            this.contacts[email].allow = true;
		}
	}

    void blockContact(TEmail email){
        auto emailLower = email.toLower();
        if (emailLowre in this.contacts.keys){
            this.contacts[emailLower].blocked = true;
            this.contacts[emailLower].allow = false;
		}
	}

    void removeUserFromGroup(TUser user, Group group)
        auto userLower = (cast (char[]) user).toLower();
        Group group = cast (Group) group;
        if (group in this.groups.keys)
            contact = this.groups[group].getUser(user);
            if (contact != null)
                //Python comment: remove group from user's list of belongings
                contact.removeGroup(group);
                
                //Python comment: add the contact to no group if applicable
                if (contact.groups == [])
                    this.noGroup.setUser(user, contact);
                    
                //Python comment: remove user from group
                this.groups[group].removeUser(user);
            else
                logger.warn("Contact " ~ user ~ "not in group" ~ group);
        else
            logger.warn("Group " ~ group ~ "not found");
	}

    void removeContact(TEmail contactMail){
        auto contactMailLower = (cast (char[]) contactMail).toLower();
        if (contacMailLower in this.contacts.keys)
            //Python comment: remove user from groups to which he belongs
            contact = this.contacts[contactMailLower];
            foreach (Group group ; contact.groups)
                this.groups[group].removeUser(contactMailLower);
            
            //Python comment: remove user from the no group, if applicable
            if (len(contact.groups) == 0)
                this.noGroup.removeUser(contactMailLower);
            
            // remove user
            this.contacts.remove(contactMailLower);
        else
            logger.warn("Contact " ~ contactMailLower ~ "not in list");
	}

    void addUserToGroup(TUser user_arg, Group group_arg){
        char[] user = (cast (char[]) user_arg).toLower();
        char[] group = (cast (char[]) group_arg);
        if (group in this.groups.keys && user in this.contacts.keys){
            contact = this.contacts[user];
            //Python comment: remove from nogroup if applicable
            if (len(contact.groups) == 0)
                this.noGroup.removeUser(user);
            
            groupObj = this.groups[group];
            contact.addGroup(group);
            
            groupObj.setUser(user, contact);
		} else if (! user in this.contacts.keys)
            logger.warn("Contact " ~ user ~ "not in list");
        else if (! group in this.groups)
            logger.warn("Group " ~ group ~ " not found");
	}

    /// Updates contact membership info according to this.lists
    void updateMemberships(){
        foreach (TEmail email ; this.contacts){
            this.contacts[email.toLower()].reverse = (email in this.lists['Reverse']);
            this.contacts[email.toLower()].allow = (email in this.lists['Allow']);
            this.contacts[email.toLower()].blocked = (email in this.lists['Block']);
		}
	}

    /** Create a XML String with all the contacts we have for
        the initial ADL Command **/

/+  Sorry this code is too weird for me to translate right now
    char[] getADL(){
        contacts = {}
        for user in this.contacts.keys():
            l = 0
            if this.getContact(user).allow:
                l = 3
            if this.getContact(user).blocked:
                l = 5
            contacts[user] = l
        
        return this.buildDL(contacts, initial=True)
+/


    /** return a list of XML for the DL command, is a list because each DL
        should be less than 7500 bytes
        contacts is a dict {user: type} **/
    void buildDL(Contact[] contacts, initial=false){

        CircularSeq!(char []) domains = [];

        foreach (char[] i) in contacts.keys{
            auto user = i.split('@') [0];
			auto domain = i.split("@") [1];

            if (domain in domains.keys)
                domains[domain].append(user);
            else
                domains[domain] = [user];
		}

        CircularSeq!(char []) xmlDomains = [];

        foreach ( i in domains.keys ){
            users = "";
            foreach ( j in domains[i]){
                
                l = contacts[j ~ "@" ~ i];
                
                if (l > 0)
                    users ~= "\"<c n=\"" ~ j ~ "\" l=\"" ~ cast (char []) (l) ~ "\" t=\"1\" />";

                if (len(users) + len("<d n=\"" ~ i ~ "\"></d>") > 7200){
                    xmlDomains.append("<d n=\"" ~ i ~ "\">" ~ users ~ "</d>");
                    users = "";
				}

            if (len(users) > 0)
                xmlDomains.append("<d n=\"" ~ i ~ "\">" ~ users ~ "</d>");


        CircularSeq!(char []) adls = [];
        full = false;

        while (xmlDomains){
            if (initial)
                xml = `<ml l="1">`; 
            else
                xml = "<ml>";

            foreach (int i in range(len(xmlDomains)){
                char[] domain = xmlDomains.pop();
                
                //Python comment: TODO: consider domains > 7500
                //Python comment: here that's an infinite loop
                if ((len(xml) + len(domain)) < 7400)
                    xml ~= domain;
                else{
                    xml ~= "</ml>";
                    adls.append(xml);
                    xmlDomains.append(domain);
                    full = true;
                    break;
				}
			}

            if (!full){
                xml ~= "</ml>";
                adls.append(xml);
				}
            else
                full = false;
        
        return adls;
	}

    ///return a list of online users
    char[][char[]] getOnlineUsers(){
        char[][char[]] ret = [];
        foreach (char[] i ; this.contacts.keys)
            if (this.getContactStatus(i) != 'FLN')
                ret.append([i, this.getContactStatus(i)]);
        return ret
	}
    
    char[][char[]] getOnlineUsersDict(){
        dictionary = [];
        
        foreach ( char[] i ; this.contacts.keys)
            if (this.getContactStatus(i) != "FLN")
                dictionary[i] = this.getContact(i);

        return dictionary;
	}

// hum, looks too hard to translate for now... I pass
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

    ///return a dictionarie with the contact list sorted acording the parameters
    char[][char[]] getContactList(showOffline = true, showEmptyGroups = false, \
            orderByStatus = false){

        char[][char[]] cl = [];

        if (orderByStatus){
            cl['offline'] = []; // empty dict
            cl['online'] = []; // empty dict
            for (TEmail email ; this.contacts){
                status = this.getContactStatus(email);
                if (status == 'FLN' && !showOffline)
                    continue;
                else if (status == "FLN")
                    cl["offline"][email] = this.contacts[email];
                else
                    cl["online"][email] = this.contacts[email];
			}
		} else{
            // Python comment:  Initialize return dict and build id2group_name dict
            foreach (char[] i ; this.reverseGroups)
                cl[i] = []; // empty dict
            cl["No group"] = []; //empty dict
                
            //Python comment: classify contacts into their group/s
            foreach (TEMail email ; this.contacts){
                contactGroups = [];
                foreach (char[] id ; this.getContactGroupIds(email))
euh                    contactGroups += [this.groups[id].name]    
                if (len(contactGroups) == 0)  //Python: email doesn't belong to any group
                    contactGroups = ["No group"];
                // the actual classification:
                foreach (Group group ; contactGroups)
                    if (showOffline)
                            cl[group][email] = this.contacts[email];
                    else if (this.getContactStatus(email) != "FLN")
                            cl[group][email] = this.contacts[email];

        if (!showEmptyGroups){
            foreach (char[] i; cl.keys)
                if (len(cl[i]) == 0)
                    cl.removeAll(i);

        return cl;
	}

class ContactNotInListError:Exception){
    this( char[] value){
        super(value);
	}
         
    char[] toString(){
        return "Contact " ~ value ~ " is not in the list";
	}
}
    
class ContactNotInGroupError:Exception{
	Group group;

    this (char[] value, Group group){
        super(value);
        this.group = group;
	}
        
    char[] toString(){
        return "Contact " ~ (cast(char[]) this.value) ~ " is not in this group: " \
                        ~ (cast (char[]) this.group);
	}
}
                        
class GroupNotFoundError:Exception{
    this(char[] value){
        super(value);
	}
        
    char[] toString(){
        return "Group " ~ this.value ~ " does not exist";
	}
}
