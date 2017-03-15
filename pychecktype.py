#!/bin/env python
from __future__ import print_function
import re

class TypeMismatchException(Exception):
    def __init__(self, value, type_, info = None):
        Exception.__init__(self, repr(value) + " cannot match type " + repr(type_) + ('' if info is None else ': ' + info))
        self.value = value
        self.type = type_


class InvalidTypeException(Exception):
    def __init__(self, type_, info = None):
        Exception.__init__(self, repr(type_) + " is not a valid type" + ("" if info is None else ": " + info))

        
class NoMatch(object):
    """
    A class which never matches any value
    Usage::
    
        >>> NoMatch()
        Traceback (most recent call last):
            ...
        TypeError: Cannot create 'NoMatch' instances
        >>> check_type({"a":1, "b":2}, {"?a": NoMatch}) # doctest: +ELLIPSIS
        Traceback (most recent call last):
            ...
        TypeMismatchException: 1 cannot match type <class '...NoMatch'>
        >>> check_type({"a": 1, "b": 2}, {"a": int, "~": NoMatch}) # doctest: +ELLIPSIS
        Traceback (most recent call last):
            ...
        TypeMismatchException: 2 cannot match type <class '...NoMatch'>
    """
    def __new__(self, *args, **kwargs):
        raise TypeError('Cannot create ' + repr(self.__name__) + ' instances')


def check_type(value, type):
    """
    Generic type checking.
    
    :param type: could be:
                                  
                 - a Python type. Notice that `object` matches all types, including None. There are a few special rules: int or long type always match
                   both int and long value; str or unicode type always match both str and unicode value; int type CANNOT match bool value.
                 
                 - a tuple of type, means that data can match any subtype. When multiple subtypes can be matched, the first matched subtype is used.
                 
                 - a empty tuple () means any data type which is not None
                 
                 - None, means None. Could be used to match nullable value e.g. `(str, None)`. Equal to types.NoneType
                 
                 - a list, means that data should be a list, or a single item which is converted to a list of length 1. Tuples are also
                   converted to lists.
                 
                 - a list with exact one valid `type`, means a list which all items are in `type`, or an item in `type` which is
                   converted to a list. Tuples are also converted to lists.
                   
                 - a dict, means that data should be a dict
                 
                 - a dict with keys and values. Values should be valid `type`. If a key starts with '?', it is optional and '?' is removed.
                   If a key starts with '!', it is required, and '!' is removed. If a key starts with '~', the content after '~' should be
                   a regular expression, and any keys in `value` which matches the regular expression (with re.search) and not matched by other keys
                   must match the corresponding type. The behavior is undefined when a key is matched by multiple regular expressions.
                   
                   If a key does not start with '?', '!' or '~', it is required, as if '!' is prepended.
    
    :param value: the value to be checked. It is guaranteed that this value is not modified.
    
    :return: the checked and converted value. An exception is raised (usually TypeMismatchException) when `value` is not in `type`. The returned
             result may contain objects from `value`.
             
    Some examples::
    
       >>> check_type("abc", str)
       'abc'
       >>> check_type([1,2,3], [int])
       [1, 2, 3]
       >>> check_type((1,2,3), [int])
       [1, 2, 3]
       >>> check_type(1, ())
       1
       >>> check_type([[]], ())
       [[]]
       >>> check_type(None, ())
       Traceback (most recent call last):
           ...
       TypeMismatchException: None cannot match type ()
       >>> check_type([1,2,"abc"], [int]) # doctest: +ELLIPSIS
       Traceback (most recent call last):
           ...
       TypeMismatchException: 'abc' cannot match type <... 'int'>
       >>> check_type("abc", [str])
       ['abc']
       >>> check_type(None, str) # doctest: +ELLIPSIS
       Traceback (most recent call last):
           ...
       TypeMismatchException: None cannot match type <... 'str'>
       >>> check_type(None, (str, None)) is None
       True
       >>> check_type([1,2,"abc",["def","ghi"]], [(int, [str])])
       [1, 2, ['abc'], ['def', 'ghi']]
       >>> check_type({"abc":123, "def":"ghi"}, {"abc": int, "def": str}) == {"abc":123, "def":"ghi"}
       True
       >>> check_type({"abc": {"def": "test", "ghi": 5}, "def": 1}, {"abc": {"def": str, "ghi": int}, "def": [int]}) == {"abc": {"def": "test", "ghi": 5}, "def": [1]}
       True
       >>> a = []
       >>> a.append(a)
       >>> check_type(a, a)
       [[...]]
       >>> r = _
       >>> r[0] is r
       True
       >>> check_type(1, None)
       Traceback (most recent call last):
           ...
       TypeMismatchException: 1 cannot match type None
       >>> check_type(a, ())
       [[...]]
       >>> check_type(True, int) # doctest: +ELLIPSIS
       Traceback (most recent call last):
           ...
       TypeMismatchException: True cannot match type <... 'int'>
       >>> check_type(1, bool) # doctest: +ELLIPSIS
       Traceback (most recent call last):
           ...
       TypeMismatchException: 1 cannot match type <... 'bool'>
       >>> check_type([1], [list]) # doctest: +ELLIPSIS
       Traceback (most recent call last):
           ...
       TypeMismatchException: 1 cannot match type <... 'list'>
       >>> check_type(1, 1)
       Traceback (most recent call last):
           ...
       InvalidTypeException: 1 is not a valid type: Unrecognized type
       >>> my_type = []
       >>> my_type.append(([str], my_type))
       >>>
       >>> my_data = ["abc"]
       >>> my_data.append(my_data)
       >>>
       >>> check_type(my_data, my_type)
       [['abc'], [...]]
       >>> r = _
       >>> r[1] is r
       True
       >>> my_type = {}
       >>> my_type["abc"] = my_type
       >>> my_type["def"] = [my_type]
       >>> my_data = {}
       >>> my_data["abc"] = my_data
       >>> my_data["def"] = my_data
       >>> r = check_type(my_data, my_type)
       >>> r['abc'] is r
       True
       >>> r['def'][0] is r
       True
       >>> my_obj = []
       >>> my_obj2 = [my_obj]
       >>> my_obj.append(my_obj2)
       >>> my_obj.append(1)
       >>> my_type = []
       >>> my_type.append(my_type)
       >>> check_type(my_obj, (my_type, [(my_type, int)])) # doctest: +ELLIPSIS
       Traceback (most recent call last):
           ...
       TypeMismatchException: [[[...]], 1] cannot match type ([[...]], [([[...]], <... 'int'>)])
       >>> my_type = []
       >>> my_type.append(my_type)
       >>> check_type(1, my_type)
       Traceback (most recent call last):
           ...
       TypeMismatchException: 1 cannot match type [[...]]
       >>> check_type(True, bool)
       True
       >>> check_type(1, [[[[[[[[[[int]]]]]]]]]])
       [[[[[[[[[[1]]]]]]]]]]
       >>> check_type([], [int, str]) # doctest: +ELLIPSIS
       Traceback (most recent call last):
           ...
       InvalidTypeException: [<... 'int'>, <... 'str'>] is not a valid type: list must contain 0 or 1 valid inner type
       >>> check_type([], [])
       []
       >>> check_type([1,2,3], [])
       [1, 2, 3]
       >>> check_type([1,"abc"], [])
       [1, 'abc']
       >>> check_type((1, "abc"), [])
       [1, 'abc']
       >>> check_type({"a": 1}, [])
       [{'a': 1}]
       >>> check_type(1, {})
       Traceback (most recent call last):
           ...
       TypeMismatchException: 1 cannot match type {}
       >>> check_type([], {})
       Traceback (most recent call last):
           ...
       TypeMismatchException: [] cannot match type {}
       >>> check_type({"a":1}, {})
       {'a': 1}
       >>> check_type({"a":1}, {"b": int}) # doctest: +ELLIPSIS
       Traceback (most recent call last):
           ...
       TypeMismatchException: {'a': 1} cannot match type {'b': <... 'int'>}: key 'b' is required
       >>> check_type({"abc": 1, "abd": 2, "abe": "abc"}, {"~a.*": int}) # doctest: +ELLIPSIS
       Traceback (most recent call last):
           ...
       TypeMismatchException: 'abc' cannot match type <... 'int'>
       >>> check_type({"abc": 1, "abd": 2, "abe": "abc"}, {"~a.*": int, "abe": str}) == {'abc': 1, 'abd': 2, 'abe': 'abc'}
       True
       >>> check_type({"abc": 1, "abd": 2, "abe": "abc"}, {"~a.*": int, "?abe": str}) == {'abc': 1, 'abd': 2, 'abe': 'abc'}
       True
       >>> check_type({"abc": 1, "def": "abc"}, {"abc": int}) == {'abc': 1, 'def': 'abc'}
       True
       >>> check_type({"abc": 1, "abc": 2, "bcd": "abc", "bce": "abd"}, {"~a.*": int, "~b.*": str}) == {"abc": 1, "abc": 2, "bcd": "abc", "bce": "abd"}
       True
       >>> my_type = (str, [])
       >>> my_type[1].append(my_type)
       >>> check_type(1, my_type) # doctest: +ELLIPSIS
       Traceback (most recent call last):
           ...
       TypeMismatchException: 1 cannot match type (<... 'str'>, [(...)])
       >>> my_obj = []
       >>> my_obj.append(my_obj)
       >>> my_obj.append(1)
       >>> check_type(my_obj, my_type) # doctest: +ELLIPSIS
       Traceback (most recent call last):
           ...
       TypeMismatchException: [[...], 1] cannot match type (<... 'str'>, [(...)])
       >>> my_obj = []
       >>> my_obj.append(my_obj)
       >>> my_obj.append("abc")
       >>> check_type(my_obj, my_type)
       [[...], 'abc']
       >>> my_type = []
       >>> my_type2 = {"a": my_type, "b": my_type}
       >>> my_type.append(my_type2)
       >>> my_obj = {}
       >>> my_obj['a'] = my_obj
       >>> my_obj['b'] = my_obj
       >>> r = check_type(my_obj, my_type)
       >>> r[0]['a'][0] is r[0]['b'][0]
       True
       >>> r[0]['a'][0] is r[0]
       True
       >>> r = check_type(my_obj, my_type2)
       >>> r['a'][0] is r['b'][0]
       True
       >>> r['a'][0] is r
       True
       >>> my_obj2 = []
       >>> my_obj2.append(my_obj2)
       >>> my_obj2.append(1)
       >>> my_obj = [my_obj2, my_obj2]
       >>> my_type = []
       >>> my_type.append((int, my_type))
       >>> check_type(my_obj, my_type)
       [[[...], 1], [[...], 1]]
       >>> r = _
       >>> r[0] is r[1]
       True
       >>> my_type = []
       >>> my_type.append(([int], my_type))
       >>> check_type(my_obj, my_type)
       [[[...], [1]], [[...], [1]]]
       >>> r = _
       >>> r[0] is r[1]
       True
    """
    return _check_type_inner(value, type)


try:
    _long = long
except Exception:
    _long = int

try:
    _unicode = unicode
except Exception:
    _unicode = str


def _check_type_inner(value, type_, _recursive_check = None):
    # print('Check type:', value, id(value), type_, id(type_))
    if _recursive_check is None:
        # current, succeeded, failed, listloop
        _recursive_check = ({}, {}, {}, set())
    current_check, succeded_check, failed_check, list_loop = _recursive_check
    # Use (id(value), id(type)) to store matches that are done before
    check_id = (id(value), id(type_))
    if check_id in succeded_check:
        # This match is already done, return the result
        # print('Hit succedded cache:', succeded_check[check_id], id(succeeded_check[check_id]))
        return succeded_check[check_id]
    elif check_id in failed_check:
        # This match is already failed, raise the exception
        raise failed_check[check_id]
    elif check_id in current_check:
        # print('Hit succedded cache:', current_check[check_id], id(current_check[check_id]))
        # This match is in-operation. The final result is depended by itself. Return the object itself to form a recursive structure.
        return current_check[check_id]
    return_value = None
    try:
        if type_ == None:
            # Match None only
            if value is not None:
                raise TypeMismatchException(value, type_)
            else:
                return_value = value
        elif type_ == ():
            if value is None:
                raise TypeMismatchException(value, type_)
            else:
                return_value = value
        elif type_ is int or type_ is _long:
            # Enhanced behavior when matching int type: long is also matched; bool is NOT matched
            if not isinstance(value, bool) and (isinstance(value, int) or isinstance(value, _long)):
                return_value = value
            else:
                raise TypeMismatchException(value, type_)
        elif type_ is str or type_ is _unicode:
            # Enhanced behavior when matching str: unicode is always matched (even in Python2)
            if isinstance(value, str) or isinstance(value, _unicode):
                return_value = value
            else:
                raise TypeMismatchException(value, type_)
        elif isinstance(type_, type):
            if isinstance(value, type_):
                return_value = value
            else:
                raise TypeMismatchException(value, type_)
        elif isinstance(type_, tuple):
            for subtype in type_:
                try:
                    return_value = _check_type_inner(value, subtype, _recursive_check)
                except TypeMismatchException:
                    continue
                else:
                    break
            else:
                raise TypeMismatchException(value, type_)
        elif isinstance(type_, list):
            if len(type_) > 1:
                raise InvalidTypeException(type_, "list must contain 0 or 1 valid inner type")
            if not type_:
                # matches any list or tuple
                if isinstance(value, list) or isinstance(value, tuple):
                    return_value = list(value)
                else:
                    return_value = [value]
            else:
                subtype = type_[0]
                if isinstance(value, list) or isinstance(value, tuple):
                    # matches a list or tuple with all inner objects matching subtype
                    current_result = []
                    # save the reference to the list
                    current_check[check_id] = current_result
                    # backup succedded check: it may depends on current result. If the type match fails, revert all succeeded check
                    _new_recursive_check = (current_check, dict(succeded_check), failed_check, set())
                    current_result.extend(_check_type_inner(o, subtype, _new_recursive_check) for o in value)
                    # copy succeeded checks
                    succeded_check.clear()
                    succeded_check.update(_new_recursive_check[1])
                else:
                    # a non-list value like "abc" cannot match an infinite looped [[...]]
                    # when a non-list value is replaced to a list, we must prevent it from forming an infinite loop
                    if check_id in list_loop:
                        raise TypeMismatchException(value, type_)
                    list_loop.add(check_id)
                    try:
                        current_result = [_check_type_inner(value, subtype, _recursive_check)]
                    finally:
                        list_loop.discard(check_id)
                return_value = current_result
        elif isinstance(type_, dict):
            if not isinstance(value, dict):
                raise TypeMismatchException(value, type_)
            if not type_:
                return_value = dict(value)
            else:
                required_keys = dict((k[1:] if isinstance(k, str) and k.startswith('!') else k, v)
                                 for k,v in type_.items()
                                 if not isinstance(k, str) or (not k.startswith('?') and not k.startswith('~')))
                optional_keys = dict((k[1:], v) for k, v in type_.items()
                                 if k.startswith('?'))
                regexp_keys = [(k[1:], v) for k, v in type_.items()
                               if k.startswith('~')]
                # check required keys
                for k in required_keys:
                    if k not in value:
                        raise TypeMismatchException(value, type_, 'key ' + repr(k) + ' is required')
                optional_keys.update(required_keys)
                current_result = {}
                # save the reference to the dict
                current_check[check_id] = current_result
                # backup succedded check: it may depends on current result. If the type match fails, revert all succeeded check
                _new_recursive_check = (current_check, dict(succeded_check), failed_check, set())
                for k, v in value.items():
                    if k in optional_keys:
                        current_result[k] = _check_type_inner(v, optional_keys[k], _new_recursive_check)
                    else:
                        for rk, rv in regexp_keys:
                            if re.search(rk, k):
                                current_result[k] = _check_type_inner(v, rv, _new_recursive_check)
                                break
                        else:
                            current_result[k] = v
                # copy succeeded checks
                succeded_check.clear()
                succeded_check.update(_new_recursive_check[1])
                return_value = current_result
        else:
            raise InvalidTypeException(type_, "Unrecognized type")
    except Exception as exc:
        # This match fails, store the exception
        failed_check[check_id] = exc
        if check_id in current_check:
            del current_check[check_id]
        raise
    else:
        # This match succeeded
        if check_id in current_check:
            del current_check[check_id]
            # Only store the succeded_check if necessary. 
            succeded_check[check_id] = return_value
        return return_value

if __name__ == '__main__':
    import doctest
    doctest.testmod()
