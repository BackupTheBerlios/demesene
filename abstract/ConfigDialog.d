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

///base classes that represent abstract GUI elements to build configuration dialog

    /**the base class for all the items that can contain a value, it 
    contains a identifier and a value, the callback is called when the
    value changes, the callback must receive 4 arguments:
    * this object
    * the identifier
    * the value
    * a boolean that is true if the configurarion dialog is closed
    (that means that it's the last change on the element, useful if you
    dont want to update things everytime the user changes the content, and
    only when is the last change)*/

class Base{

	char[] identifier;
	void delegate(char[] identifier, Object value,  bool isClosed) callback;

    private:
    Object _value;

    this(identifier, callback=null){
        this.identifier = identifier;
        this._value = null;
        this.callback = callback;
	}

	/// read for value property
    char value(){
        return this._value;
	}

	/// write for value property
    void value(value){
        this._value = value;
        this.on_value_changed();
	}

    // Python was: value = property(fget=_get_value, fset=_set_value), not needed in D

    /** call the calback if not none with the arguments especified on the
        class doc, is_last_change will be True if it's the last change on the
        object (when the config dialog is closed
	*/
    void on_value_changed(bool is_last_change=false){
        if (callback)
            this.callback(this.identifier, this.value, is_last_change);
	}

    ///since no validations can be done on this fiels, always return true
    bool validate(out char[] result_mesg, out Object instance, Object value=null){
		result_mesg="OK";
		instance=this;
        return true;
	}
}

/// a class that contain methods to validate the content
class Validable:Base{

	bool delegate(out char[], out Object, Object)[] validators;

    this(char[] identifier, callback=null){
        super(identifier, callback);
        this.validators = [];
	}

    /** add a validator method to the validators that will be called
        on the content when the validate method is called.
         if the validator return False, the error_message will be displayed
    **/	
    void add_validator(bool delegate(out char[], out Object, Object) validator, char[] error_message){
		this.validators.append(validator, error_message);
	}

    /** validate the value with all the validators or self.value if
        value is null, the first that fails
        will return the error message, if some fails will return 
        (False, error_message, self) if none fails return (True, 'OK', self
	**/
    bool validate(out char[] result_msg, out Object instance, Object value=null){
		instance=this;
        foreach (validator, error_message; this.validators){
            if (!validator(value || this.value)){
				result_msg=error_message;
                return (false);
			}
		result_msg="OK";
        return (True);
	}
}

/// a class that represent an abstract field that contains a label and a text field with an optional text content
class Text:Validable{
	gtk.Label label;
	char[] value;

    this(char[] identifier, gtk.Label label, char[] text=null,bool delegate(char[] identifier, Object value,  bool isClosed) callback=null){
        super();
        this.label = label;
		if (text) this.value = text; else this.value = "";
	}
}

///a class that represent an abstract field that contains a label and a password field with an optional text content
class Password:Text{
	this(char[] identifier, gtk.Label label, char[] text=null, bool delegate(char[] identifier, Object value,  bool isClosed) callback=null){
        super(identifier, label, text, callback);
	}
}

///a class that represent an abstract field that contains a label and can be set to checked or not checked
class CheckBox:Base{
    this(char[] identifier, gtk.Label label, bool value=false, bool delegate(char[] identifier, Object value,  bool isClosed) callback=null){
        super(identifier, callback);
        label = label;
        value = value;
	}
}

/** a class that represent an abstract group of fields on which only one
    can be selected

	every item has a label and the group has a text that
    describe the groups, for example group_label="fruits",
    labels=("apple", "orange", "banana") selected_index=1
    the identifiers are the values that will be returned as the selecetd
    index, for example the label can be A_pple and the identidier apple,
    or the label can be translated, but identifier stay the same
**/
class RadioGroup:Base{
	gtk.Labels[] labels;
	char[][] identifiers;
	Group group_label;

	/** class constructor

		labels is a list or tuple of strings and 
        selected_index is the index of the selected index by default, if
        the index is out of range, the first item will be selected.
        identifier is the identifier of the group, identifiers is a list or
        tuple of the identifier value for each label
	**/
    this(char [] identifier, gtk.Labels[] labels, char[][] identifiers, Group group_label, 
            ushort selected_index=0, bool delegate(char[] identifier, Object value,  bool isClosed) callback=null){
        super(identifier, callback);
        if (len(labels) < 2)
            throw new Exception("labels size < 2");

        if (len(labels) != len(identifiers))
            throw new Exception("number of labels and identifiers differ");

        this.labels = labels;
        this.group_label = group_label;
        this.selected_index = selected_index;
        this.identifiers = identifiers;
        
        if (self.selected_index < 0 || self.selected_index > len(self.labels))
            self.selected_index = 0;
	}
}

/** a class that represent a logic group of elements, the way it is 
    represented can be a frame or something like that, it has a optional
    name for the group, if label is none, then no frame or label will be
    displayed on the group
**/
Label label;
Object[] items;

class Group{
    this(label=null){
        self.label = label;
        self.items = [];
	}

	///add an item to the group, the item can be any element
    void add_item(self, item){
        self.items.append(item);
	}

	/// test if obj is a subclass of T
	bool isSubclass(T)(Object obj) {
		return (cast(T) obj)?true:false;
	}

	/// call last change for all the containing items
    void on_last_change(){
        foreach (item; this.items)
            if (isSubclass!(Base)(item))
                item.on_value_changed(True);
            else if (isSubclass!(Group)(item))
                item.on_last_change();
	}

    /** validate all the containing elements and return (True, 'OK')
        if all validated and (False, error_message) of the first validation
        that failed
	**/
    void validate(out char[] errorMsg, out Object element){
		bool validated;
        foreach (item; this.items){
            validated = item.validate(errorMsg, item);
            if (!validated)
                return validated;
		}
		errorMsg=r"OK";
		element=this;
        return true;
	}

/// a class that represent a containter tab with elements
class Tab:Group{
    this(Label label){
        super(label);
	}
}

class TabGroup:Group{
    this(){
        super(null);
	}
    
    /// add an item to the group, the item can be any element
    void add_item(Object item){
        if (isSubclass!(Tab)(item))
            Group.add_item(item);
        else
            throw new Exception(r"item is not of type Tab");
	}
}

  /++ this method should be overrided by the implementation module, it should
    return a non modal window with an accept button, that will call to
    a method like this on close:
   
    (validated, message, element) = element.validate()

    # here a dialog should be displayed and the window not closed
    if not validated:
        dialog.error("field '" + element.identifier + \
        "' with value '" + element.value + "' not valid: \n" + message)
    else:
        # all fields are valid
        element.on_last_change()
        dialog_window.close() # or similar
    ++/
	void build(element){
    	throw new Exception(r"NotImplementedError");
	}

}
}
