from demogrid.common.utils import enum

import json

class ObjectValidationException(Exception):
    """A simple exception class used for validation exceptions"""
    pass

PropertyTypes = enum("STRING",
                     "INTEGER",
                     "NUMBER",
                     "BOOLEAN",
                     "OBJECT",
                     "ARRAY",
                     "NULL",
                     "ANY")

def pt_to_str(pt, items_type = None):
    if pt == PropertyTypes.STRING:
        return "string"
    elif pt == PropertyTypes.INTEGER:
        return "integer"
    elif pt == PropertyTypes.NUMBER:
        return "number"
    elif pt == PropertyTypes.BOOLEAN:
        return "boolean"
    elif pt == PropertyTypes.OBJECT:
        return "object"
    elif pt == PropertyTypes.ARRAY:
        return "list of %s" % pt_to_str(items_type)
    elif pt == PropertyTypes.NULL:
        return "null"
    elif pt == PropertyTypes.ANY:
        return "any"
    elif issubclass(pt, PersistentObject):
        return pt.__name__
    else:
        return "unknown"

def validate_property_type(value, expected_type, items_type = None):
    if expected_type == PropertyTypes.STRING:
        valid = isinstance(value, basestring)
    elif expected_type == PropertyTypes.INTEGER:
        valid = isinstance(value, int)
    elif expected_type == PropertyTypes.NUMBER:
        valid = isinstance(value, int) or isinstance(value, float)
    elif expected_type == PropertyTypes.BOOLEAN:
        valid = isinstance(value, bool)
    elif expected_type == PropertyTypes.OBJECT:
        valid = isinstance(value, dict)
    elif expected_type == PropertyTypes.ARRAY:
        if isinstance(value, list):
            valid = True
            for elem in value:
                valid &= validate_property_type(elem, items_type)
        else:
            valid = False    
    elif expected_type == PropertyTypes.NULL:
        valid = value is None
    elif expected_type == PropertyTypes.ANY:
        valid = True
    elif issubclass(expected_type, PersistentObject):
        # Further validation is done when we convert
        # this object
        valid = isinstance(value, dict)
    else:
        valid = False    
    
    return valid

class Property(object):    
    def __init__(self, name, proptype, required, description, indexable = False, unique = False, editable = False, items = None):
        self.name = name
        self.type = proptype
        self.required = required
        self.editable = editable
        self.indexable = indexable
        self.unique = unique
        self.description = description
        self.items = items
        
class PropertyChange(object):
    pass

class PrimitivePropertyChange(object):
    def __init__(self, old_value, new_value):
        self.old_value = old_value
        self.new_value = new_value
        
    def to_dict(self):
        d = {}        
        d["old"] = self.old_value
        d["new"] = self.new_value
        return d
        
class ArrayPropertyChange(object):
    def __init__(self, add, remove, edit):
        self.add = add
        self.remove = remove
        self.edit = edit
        
    def to_dict(self):
        d = {}
        
        if len(self.add) > 0:
            d["ADD"] = self.add
            
        if len(self.remove) > 0:
            d["REMOVE"] = self.remove
        
        if len(self.edit) > 0:
            editd = {}
            for property in self.edit:
                editd[property] = self.edit[property].to_dict()
            d["EDIT"] = editd
            
        return d
        
        
        
class ObjectPropertyChange(object):
    def __init__(self, changes):
        self.changes = changes
        
    def to_dict(self):
        d = {}
        for property in self.changes:
            d[property] = self.changes[property].to_dict()
        return d
        

class PersistentObject(object):
    def __init__(self):
        self._json_file = None

    def save(self, filename = None):
        if self._json_file == None and filename == None:
            raise Exception("Don't know where to save this topology")
        if filename != None:
            self._json_file = filename
        f = open (self._json_file, "w")
        json_string = self.to_json_string()
        f.write(json_string)
        f.close()
        
    def set_property(self, p_name, p_value):
        # TODO: Validation
        setattr(self, p_name, p_value)
        
    def has_property(self, p_name):
        return hasattr(self, p_name)       
    
    def get_property(self, p_name):
        # TODO: Validation
        return getattr(self, p_name)        
    
    def validate_update(self, pobj):
        if type(self) != type(pobj):
            raise ObjectValidationException("Cannot update a %s object with a %s object" % (type(self).__name__, type(pobj).__name__))
        
        changes = {}
        for name, property in self.properties.items():
            if hasattr(self, name) and hasattr(pobj, name):
                # Both objects have the same property.
                self_value = getattr(self, name)
                pobj_value = getattr(pobj, name)
                
                if property.type in (PropertyTypes.STRING, PropertyTypes.INTEGER, PropertyTypes.NUMBER, PropertyTypes.BOOLEAN, PropertyTypes.NULL):
                    # If this is a primitive type, check if the value has changed and, if so,
                    # whether the change is allowed.
                    if self_value != pobj_value:
                        if not property.editable:
                            raise ObjectValidationException("Tried to change the value of non-editable property '%s' (from %s to %s)""" % (name, self_value, pobj_value))
                        else:
                            changes[name] = PrimitivePropertyChange(self_value, pobj_value)
                elif property.type == PropertyTypes.ARRAY:
                    if property.items in (PropertyTypes.STRING, PropertyTypes.INTEGER, PropertyTypes.NUMBER, PropertyTypes.BOOLEAN, PropertyTypes.NULL):
                        self_set = set(self_value)
                        pobj_set = set(pobj_value)
                        
                        add = list(pobj_set - self_set)
                        remove = list(self_set - pobj_set)
                        
                        if len(add) + len(remove) > 0:
                            if property.editable: 
                                changes[name] = ArrayPropertyChange(add, remove, {})
                            else:                        
                                raise ObjectValidationException("Tried to add/remove items from non-editable array '%s' (Add: %s  Remove: %s)""" % (name, add, remove))
                    elif issubclass(property.items, PersistentObject):
                        if property.indexable:
                            self_set = set([x.id for x in self_value])
                            pobj_set = set([x.id for x in pobj_value])
                            
                            add = list(pobj_set - self_set)
                            remove = list(self_set - pobj_set)
                            
                            if len(add) + len(remove) > 0 and not property.editable:
                                raise ObjectValidationException("Tried to add/remove items from non-editable array '%s' (Add: %s  Remove: %s)""" % (name, add, remove))                            
                            
                            common = list(self_set & pobj_set)
                            
                            self_items_value = dict([(n.id, n) for n in self_value if n.id in common])
                            pobj_items_value = dict([(n.id, n) for n in pobj_value if n.id in common])
                            
                            edit = {}
                            for s in self_items_value.values():
                                p = pobj_items_value[s.id]
                                item_changes = s.validate_update(p)
                                if len(item_changes.changes) > 0:
                                    if not property.editable:
                                        raise ObjectValidationException("Tried to edit an item in an non-editable array '%s' (Item with id '%s')""" % (name, s.id))
                                    else:
                                        edit[s.id] = item_changes

                            if len(add) + len(remove) + len(edit) > 0:
                                changes[name] = ArrayPropertyChange(add, remove, edit)
                        else:
                            # We have no way of telling if individual entries have been edited,
                            # or even if entries have been added/removed, since we don't have
                            # object equality implemented yet.
                            pass
                    elif property.items in (PropertyTypes.ARRAY):
                        raise ObjectValidationException("ARRAYs of ARRAYs not supported.")                            
                    elif property.items in (PropertyTypes.OBJECT, PropertyTypes.ANY):
                        raise ObjectValidationException("Arbitrary types (OBJECT, ANY) not supported.")                                                
                elif issubclass(property.type, PersistentObject):
                    property_changes = self_value.validate_update(pobj_value)
                    if len(property_changes.changes) > 0:
                        if not property.editable:
                            raise ObjectValidationException("Tried to to change the value of non-editable property '%s' (Changes: '%s')""" % (name, property_changes.to_dict()))
                        else:
                            changes[name] = property_changes
                elif property.type in (PropertyTypes.OBJECT, PropertyTypes.ANY):
                    raise ObjectValidationException("Arbitrary types (OBJECT, ANY) not supported.") 
                
        return ObjectPropertyChange(changes)               

    def to_json_dict(self):
        json = {}
        for name, property in self.properties.items():
            if hasattr(self, name):
                if property.type in (PropertyTypes.STRING, PropertyTypes.INTEGER, PropertyTypes.NUMBER, PropertyTypes.BOOLEAN, PropertyTypes.NULL):
                    value = getattr(self, name)
                elif property.type == PropertyTypes.ARRAY:
                    value = []
                    l = getattr(self, name)
                    for elem in l:
                        if property.items in (PropertyTypes.STRING, PropertyTypes.INTEGER, PropertyTypes.NUMBER, PropertyTypes.BOOLEAN, PropertyTypes.NULL):
                            value.append(elem)
                        elif issubclass(property.items, PersistentObject):
                            elem_obj = elem.to_json_dict()
                            value.append(elem_obj)
                        elif property.items in (PropertyTypes.ARRAY):
                            raise ObjectValidationException("ARRAYs of ARRAYs not supported.")                            
                        elif property.items in (PropertyTypes.OBJECT, PropertyTypes.ANY):
                            raise ObjectValidationException("Arbitrary types (OBJECT, ANY) not supported.")
                elif issubclass(property.type, PersistentObject):
                    value = getattr(self, name).to_json_dict()              
                elif property.type in (PropertyTypes.OBJECT, PropertyTypes.ANY):
                    raise ObjectValidationException("Arbitrary types (OBJECT, ANY) not supported.")
                json[name] = value
                
        return json

    def to_json_string(self):
        return json.dumps(self.to_json_dict(), indent=2)

    def __primitive_to_ruby(self, value, p_type):
        if p_type == PropertyTypes.STRING:
            return "\"%s\"" % value
        elif p_type == PropertyTypes.INTEGER:
            return "%i" % value
        elif p_type == PropertyTypes.NUMBER:
            return "%f" % value
        elif p_type == PropertyTypes.BOOLEAN:
            if value == True:
                return "true"
            else:
                return "false" 
        elif p_type == PropertyTypes.NULL:
            return "nil"        

    def to_ruby_hash_string(self, indexable_array_as_dicts = False):
        hash_str = "{"
        
        obj_items = {}
        for name, property in self.properties.items():
            if hasattr(self, name):
                value = getattr(self, name)
                if property.type in (PropertyTypes.STRING, PropertyTypes.INTEGER, PropertyTypes.NUMBER, PropertyTypes.BOOLEAN, PropertyTypes.NULL):
                    value_str = self.__primitive_to_ruby(value, property.type)
                elif property.type == PropertyTypes.ARRAY and property.indexable and issubclass(property.items, PersistentObject) and indexable_array_as_dicts:
                    value_str = "{"
                        
                    items = {}
                    for elem in value:
                        items[elem.id] = elem.to_ruby_hash_string(indexable_array_as_dicts)
                        
                    value_str += ", ".join([" \"%s\" => %s" % (k,v) for k,v in items.items()])
                    value_str += "}"
                elif property.type == PropertyTypes.ARRAY:
                    value_str = "["
                        
                    items = []
                    for elem in value:
                        if property.items in (PropertyTypes.STRING, PropertyTypes.INTEGER, PropertyTypes.NUMBER, PropertyTypes.BOOLEAN, PropertyTypes.NULL):
                            items.append( self.__primitive_to_ruby(elem, property.items) )
                        elif issubclass(property.items, PersistentObject):
                            items.append( elem.to_ruby_hash_string(indexable_array_as_dicts) )
                        elif property.items in (PropertyTypes.ARRAY):
                            raise ObjectValidationException("ARRAYs of ARRAYs not supported.")                            
                        elif property.items in (PropertyTypes.OBJECT, PropertyTypes.ANY):
                            raise ObjectValidationException("Arbitrary types (OBJECT, ANY) not supported.")

                    value_str += ", ".join(items)
                    value_str += "]"
                elif issubclass(property.type, PersistentObject):
                    value_str = value.to_ruby_hash_string(indexable_array_as_dicts) 
                elif property.type in (PropertyTypes.OBJECT, PropertyTypes.ANY):
                    raise ObjectValidationException("Arbitrary types (OBJECT, ANY) not supported.")
                obj_items[name] = value_str        

        hash_str += ", ".join([" :%s => %s" % (k,v) for k,v in obj_items.items()])

        hash_str += "}"
        
        return hash_str

    @classmethod
    def from_json_string(cls, json_string):
        try:
            json_dict = json.loads(json_string)
            return cls.from_json_dict(json_dict)
        except ValueError, ve:
            raise ObjectValidationException("Error parsing JSON. %s" % ve)

    @classmethod
    def from_json_dict(cls, obj_dict):
        obj = cls()
        if not isinstance(obj_dict, dict):
            raise ObjectValidationException("JSON provided for %s is not a dictionary" % cls.__name__)
        
        given_names = set(obj_dict.keys())
        required_names = set([p.name for p in cls.properties.values() if p.required])
        valid_names = set(cls.properties.keys())
        
        # Check whether required fields are present
        missing = required_names - given_names
        if len(missing) > 0:
            raise ObjectValidationException("JSON provided for %s is missing required properties: %s" % (cls.__name__, ", ".join(missing)))
        
        # Check whether there are any unexpected fields
        unexpected = given_names - valid_names
        if len(unexpected) > 0:
            raise ObjectValidationException("Encountered unexpected properties in JSON provided for %s: %s" % (cls.__name__, ", ".join(unexpected)))
        
        for p_name, p_value in obj_dict.items():
            property = cls.properties[p_name]
            if not validate_property_type(p_value, property.type, property.items):
                raise ObjectValidationException("'%s' is not a valid value for %s.%s. Expected a %s." % (p_value, cls.__name__, p_name, pt_to_str(property.type, property.items)))
            else:
                if property.type in (PropertyTypes.STRING, PropertyTypes.INTEGER, PropertyTypes.NUMBER, PropertyTypes.BOOLEAN, PropertyTypes.NULL):
                    setattr(obj, p_name, p_value)
                elif property.type == PropertyTypes.ARRAY:
                    l = []
                    for elem in p_value:
                        if property.items in (PropertyTypes.STRING, PropertyTypes.INTEGER, PropertyTypes.NUMBER, PropertyTypes.BOOLEAN, PropertyTypes.NULL):
                            l.append(elem)
                        elif issubclass(property.items, PersistentObject):
                            elem_obj = property.items.from_json_dict(elem)
                            l.append(elem_obj)
                        elif property.items in (PropertyTypes.ARRAY):
                            raise ObjectValidationException("ARRAYs of ARRAYs not supported.")                            
                        elif property.items in (PropertyTypes.OBJECT, PropertyTypes.ANY):
                            raise ObjectValidationException("Arbitrary types (OBJECT, ANY) not supported.")
                    obj.set_property(p_name, l)
                elif issubclass(property.type, PersistentObject):
                    p_value_obj = property.type.from_json_dict(p_value)
                    obj.set_property(p_name, p_value_obj)               
                elif property.type in (PropertyTypes.OBJECT, PropertyTypes.ANY):
                    raise ObjectValidationException("Arbitrary types (OBJECT, ANY) not supported.")
                
        return obj
