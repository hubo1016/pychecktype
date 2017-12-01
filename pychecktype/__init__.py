#!/bin/env python
from __future__ import print_function
import re

try:
    from reprlib import recursive_repr
except Exception:
    recursive_repr = lambda: lambda x: x
    
class TypeMismatchException(Exception):
    def __init__(self, value, type_, info = None):
        Exception.__init__(self, repr(value) + " cannot match type " \
            + repr(type_) + ('' if info is None else ': ' + info))
        self.value = value
        self.type = type_


class InvalidTypeException(Exception):
    def __init__(self, type_, info = None):
        Exception.__init__(self, repr(type_) + " is not a valid type" \
            + ("" if info is None else ": " + info))

        
class NoMatch(object):
    """
    A class which never matches any value
    Usage::
    
        >>> NoMatch()
        Traceback (most recent call last):
            ...
        TypeError: Cannot create 'NoMatch' instances
        >>> check_type({"a":1, "b":2}, \
        {"?a": NoMatch}) # doctest: +ELLIPSIS
        Traceback (most recent call last):
            ...
        TypeMismatchException: 1 cannot match type <class '...NoMatch'>
        >>> check_type({"a": 1, "b": 2}, \
        {"a": int, "~": NoMatch}) # doctest: +ELLIPSIS
        Traceback (most recent call last):
            ...
        TypeMismatchException: 2 cannot match type <class '...NoMatch'>
    """
    def __new__(self, *args, **kwargs):
        raise TypeError('Cannot create ' + repr(self.__name__) + \
            ' instances')

        
class CustomizedChecker(object):
    """
    Inherit from this class to create a customized type checker
    """
    def __init__(self, *args, **kwargs):
        """
        Call bind()
        """
        if args or kwargs:
            self.bind(*args, **kwargs)
    def bind(self):
        """
        Allow delayed init
        """
        pass
    def pre_check_type(self, value):
        """
        First-step check for value. This step should not do any
        recursive check.
        
        :param value: value to be checked
        
        :return: An object if recursive creation if needed, or None
                 if not needed.
                 
                 TypeMismatchException should be raised if there is
                 something wrong.
        """
        return None
        
    def final_check_type(self, value, current_result,
            recursive_check_type):
        """
        Second-step check for value. This step can use recursive check.
        
        :param value: value to be checked
        
        :param current_result: value returned by pre_check_type.
                               If this value is not None, the return
                               value must be the same object.
        
        :param recursive_check_type: a function
                                     recursive_check_type(value, type)
                                     to be called to do recursive type
                                     check
        """
        raise NotImplementedError

        



def check_type(value, type):
    """
    Generic type checking.
    
    :param type: could be:
                                  
                 - a Python type. Notice that `object` matches all types,
                   including None. There are a few special rules:
                   int or long type always match
                   both int and long value; str or unicode type always
                   match both str and unicode value; int type CANNOT match
                   bool value.
                 
                 - a tuple of type, means that data can match any subtype.
                   When multiple subtypes can be matched, the first matched
                   subtype is used.
                 
                 - a empty tuple () means any data type which is not None
                 
                 - None, means None. Could be used to match nullable value
                   e.g. `(str, None)`. Equal to types.NoneType
                 
                 - a list, means that data should be a list, or a single
                   item which is converted to a list of length 1. Tuples
                   are also
                   converted to lists.
                 
                 - a list with exact one valid `type`, means a list which all
                   items are in `type`, or an item in `type` which is
                   converted to a list. Tuples are also converted to lists.
                   
                 - a dict, means that data should be a dict
                 
                 - a dict with keys and values. Values should be valid `type`.
                   If a key starts with '?', it is optional and '?' is removed.
                   If a key starts with '!', it is required, and '!' is removed.
                   If a key starts with '~', the content after '~' should be
                   a regular expression, and any keys in `value` which matches
                   the regular expression (with re.search) and not matched by
                   other keys
                   must match the corresponding type. The behavior is undefined
                   when a key is matched by multiple regular expressions.
                   
                   If a key does not start with '?', '!' or '~', it is required,
                   as if '!' is prepended.
    
    :param value: the value to be checked. It is guaranteed that
                  this value is not modified.
    
    :return: the checked and converted value. An exception is
             raised (usually TypeMismatchException) when `value`
             is not in `type`. The returned
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
       >>> check_type("abc", list_([str], True)) # doctest: +ELLIPSIS
       Traceback (most recent call last):
           ...
       TypeMismatchException: 'abc' cannot match type [<... 'str'>]: \
strict mode disables auto-convert-to-list for single value
       >>> check_type(None, str) # doctest: +ELLIPSIS
       Traceback (most recent call last):
           ...
       TypeMismatchException: None cannot match type <... 'str'>
       >>> check_type(None, (str, None)) is None
       True
       >>> check_type([1,2,"abc",["def","ghi"]], [(int, [str])])
       [1, 2, ['abc'], ['def', 'ghi']]
       >>> check_type({"abc":123, "def":"ghi"}, {"abc": int, "def": str}) \\
       ... == {"abc":123, "def":"ghi"}
       True
       >>> check_type({"abc": {"def": "test", "ghi": 5}, "def": 1},
       ... {"abc": {"def": str, "ghi": int}, "def": [int]}) == \\
       ... {"abc": {"def": "test", "ghi": 5}, "def": [1]}
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
       >>> check_type(my_obj, (my_type, [(my_type, int)])) \
# doctest: +ELLIPSIS
       Traceback (most recent call last):
           ...
       TypeMismatchException: [[[...]], 1] cannot match type \
([[...]], [([[...]], <... 'int'>)])
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
       InvalidTypeException: [<... 'int'>, <... 'str'>] is not a valid type: \
list must contain 0 or 1 valid inner type
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
       >>> check_type(1, {}) # doctest: +ELLIPSIS
       Traceback (most recent call last):
           ...
       TypeMismatchException: 1 cannot match type {}...
       >>> check_type([], {}) # doctest: +ELLIPSIS
       Traceback (most recent call last):
           ...
       TypeMismatchException: [] cannot match type {}...
       >>> from collections import defaultdict
       >>> check_type({}, dict_({}, defaultdict, lambda: defaultdict(int)))\
# doctest: +ELLIPSIS
       Traceback (most recent call last):
          ...
       TypeMismatchException: {} cannot match type {}: \
allowed types are: <... 'collections.defaultdict'>
       >>> check_type(defaultdict(str), dict_({}, defaultdict,
       ... lambda: defaultdict(int))) # doctest: +ELLIPSIS
       defaultdict(<... 'int'>, {})
       >>> from collections import OrderedDict
       >>> check_type(OrderedDict((("b",1),("a",2),("def","abc"))),
       ... dict_({"a": int, "b": int, "def": str}, dict, OrderedDict))
       OrderedDict([('b', 1), ('a', 2), ('def', 'abc')])
       >>> check_type({"a":1}, {})
       {'a': 1}
       >>> check_type({"a":1}, {"b": int}) # doctest: +ELLIPSIS
       Traceback (most recent call last):
           ...
       TypeMismatchException: {'a': 1} cannot match type \
{'b': <... 'int'>}: key 'b' is required
       >>> check_type({"abc": 1, "abd": 2, "abe": "abc"}, {"~a.*": int}) # doctest: +ELLIPSIS
       Traceback (most recent call last):
           ...
       TypeMismatchException: 'abc' cannot match type <... 'int'>
       >>> check_type({"abc": 1, "abd": 2, "abe": "abc"}, \
       {"~a.*": int, "abe": str}) == {'abc': 1, 'abd': 2, 'abe': 'abc'}
       True
       >>> check_type({"abc": 1, "abd": 2, "abe": "abc"}, \
       {"~a.*": int, "?abe": str}) == {'abc': 1, 'abd': 2, 'abe': 'abc'}
       True
       >>> check_type({"abc": 1, "def": "abc"}, {"abc": int}) == \
       {'abc': 1, 'def': 'abc'}
       True
       >>> check_type({"abc": 1, "abc": 2, "bcd": "abc", "bce": "abd"},
       ... {"~a.*": int, "~b.*": str}) == \\
       ... {"abc": 1, "abc": 2, "bcd": "abc", "bce": "abd"}
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
       TypeMismatchException: [[...], 1] cannot match type \
(<... 'str'>, [(...)])
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


class ListChecker(CustomizedChecker):
    """
    Default `[]` type implementation
    
    Examples::
        
        >>> list_([])
        []
        >>> list_({})
        Traceback (most recent call last):
          ...
        InvalidTypeException: {} is not a valid type: must be a list
    """
    def bind(self, type_, strict = False,
                allowed_type = (list, tuple)):
        """
        `type_` must be a list type [] / [sub_type]
        
        :param strict: if True, auto-convert from a single value
                       to a list is disabled
        
        :param allowed_type: a tuple of allowed class of input
        """
        if not isinstance(type_, list):
            raise InvalidTypeException(type_, "must be a list")
        if len(type_) > 1:
            raise InvalidTypeException(type_,
                    "list must contain 0 or 1 valid inner type")
        self.type_ = type_
        self.strict = strict
        self.allowed_type = allowed_type

    def __repr__(self):
        return repr(self.type_)
        
    def pre_check_type(self, value):
        if isinstance(value, self.allowed_type):
            return []
        elif self.strict:
            raise TypeMismatchException(value, self.type_,
                "strict mode disables auto-convert-to-list for single value")
        else:
            return None
            
    def final_check_type(self, value, current_result, recursive_check_type):
        if not self.type_:
            # matches any list or tuple
            if current_result is None:
                return [value]
            else:
                current_result.extend(value)
                return current_result
        else:
            subtype = self.type_[0]
            if current_result is not None:
                current_result.extend(recursive_check_type(o, subtype)
                                      for o in value)
                return current_result
            else:
                return [recursive_check_type(value, subtype)]

                
list_ = ListChecker


class DictChecker(CustomizedChecker):
    """
    Default `{}` type implementation
    
    Examples::
    
        >>> dict_({})
        {}
        >>> dict_([])
        Traceback (most recent call last):
          ...
        InvalidTypeException: [] is not a valid type: must be a dict
    """
    def bind(self, type_, allowed_type = dict, created_type = dict):
        """
        :param type_: a dict describing the input format
        
        :param allowed_type: limit input type to a sub type,
                             or a tuple of sub types
        
        :param created_type: create a subtype of dict instead
                             (e.g. OrderedDict)
        """
        if not isinstance(type_, dict):
            raise InvalidTypeException(type_, "must be a dict")
        self.type_ = type_
        self.allowed_type = allowed_type
        self.created_type = created_type
        
    def pre_check_type(self, value):
        if not isinstance(value, self.allowed_type):
            raise TypeMismatchException(value, self.type_,
                    "allowed types are: " + repr(self.allowed_type))
        return self.created_type()
        
    def final_check_type(self, value, current_result, recursive_check_type):
        if not self.type_:
            current_result.update(value)
        else:
            required_keys = dict((k[1:]
                                  if isinstance(k, str)
                                      and k.startswith('!')
                                  else k, v)
                                  for k,v in self.type_.items()
                                  if not isinstance(k, str)
                                  or (not k.startswith('?')
                                    and not k.startswith('~')))
            optional_keys = dict((k[1:], v) for k, v in self.type_.items()
                             if k.startswith('?'))
            regexp_keys = [(k[1:], v) for k, v in self.type_.items()
                           if k.startswith('~')]
            # check required keys
            for k in required_keys:
                if k not in value:
                    raise TypeMismatchException(value, self.type_, 'key '
                        + repr(k) + ' is required')
            optional_keys.update(required_keys)
            for k, v in value.items():
                if k in optional_keys:
                    current_result[k] = recursive_check_type(v,
                            optional_keys[k])
                else:
                    for rk, rv in regexp_keys:
                        if re.search(rk, k):
                            current_result[k] = recursive_check_type(v, rv)
                            break
                    else:
                        current_result[k] = v
        return current_result
    
    def __repr__(self):
        return repr(self.type_)


dict_ = DictChecker


class TupleChecker(CustomizedChecker):
    """
    Check a tuple type: a fix-sized tuple/list, each element may have
    a different type
    
    Examples::
    
        >>> tuple_((str, int)) # doctest: +ELLIPSIS
        tuple_((<... 'str'>, <... 'int'>))
        >>> tuple_({})
        Traceback (most recent call last):
            ...
        InvalidTypeException: tuple_({}) is not a valid type: \
must use a tuple/list of types
        >>> check_type((1,2), tuple_((1,2), allowed_type=int)) \
# doctest: +ELLIPSIS
        Traceback (most recent call last):
            ...
        TypeMismatchException: (1, 2) cannot match type tuple_((1, 2)): \
allowed types are: <... 'int'>
        >>> check_type(("abc", 123), tuple_(()))
        Traceback (most recent call last):
            ...
        TypeMismatchException: ('abc', 123) cannot match type tuple_(()): \
length mismatch
        >>> check_type(("abc", 123), tuple_((str, int)))
        ('abc', 123)
        >>> check_type(["abc", 123], tuple_((str, int)))
        ('abc', 123)
        >>> t = []
        >>> tuple_type = tuple_()
        >>> t.append(tuple_type)
        >>> tuple_type.bind(t)
        >>> l = []
        >>> l.append(l)
        >>> check_type(l, tuple_type) \\
        ... # By default, a direct recursive is not allowed # doctest: +ELLIPSIS
        Traceback (most recent call last):
            ...
        TypeMismatchException: [[...]] cannot match type \
tuple_([...])
        >>> t = []
        >>> tuple_type = tuple_()
        >>> t.append([tuple_type])
        >>> tuple_type.bind(t)
        >>> check_type(l, tuple_type) # An indirect recursive is allowed
        ([([...],)],)
        >>> t = []
        >>> tuple_type = tuple_()
        >>> t.append(tuple_type)
        >>> t.append(int)
        >>> tuple_type.bind(t, allow_recursive = True)
        >>> l = []
        >>> l.append(l)
        >>> l.append(123)
        >>> check_type(l, tuple_type) \\
        ... # allow_recursive allows a direct recursive \
and return list instead of tuple
        [[...], 123]
    """
    def bind(self, tuple_of_types, allowed_type = (list, tuple),
            allow_recursive = False):
        """
        :param tuple_of_types: a tuple or list, each of its element is
                               a valid type
        
        :param allowed_type: allowed input types
        
        :param allow_recursive: if False, directly recursive struct
                                (a tuple contains itself) is not accepted,
                                and the result
                                is a tuple.
                                
                                if True, recursive struct is accepted and
                                returned as a list.
        """
        self.type_ = tuple_of_types
        if not isinstance(tuple_of_types, (list, tuple)):
            raise InvalidTypeException(self,
                        "must use a tuple/list of types")
        self.allowed_type = allowed_type
        self.allow_recursive = allow_recursive
        
    @recursive_repr()
    def __repr__(self):
        return "tuple_(" + repr(self.type_) + ")"

    def pre_check_type(self, value):
        if not isinstance(value, self.allowed_type):
            raise TypeMismatchException(value, self,
                    "allowed types are: " + repr(self.allowed_type))
        if len(value) != len(self.type_):
            raise TypeMismatchException(value, self, "length mismatch")
        if self.allow_recursive:
            return []
        else:
            return None
    
    def final_check_type(self, value, current_result, recursive_check_type):
        if current_result is None:
            return tuple(recursive_check_type(v, t)
                         for v, t in zip(value, self.type_))
        else:
            current_result.extend(recursive_check_type(v, t)
                                  for v, t in zip(value, self.type_))
            return current_result


tuple_ = TupleChecker


class MapChecker(CustomizedChecker):
    """
    Check dict type, where every key is in key_type and every value is
    in value_type
    
    Examples::
        >>> check_type([], map_(int, str)) # doctest: +ELLIPSIS
        Traceback (most recent call last):
            ...
        TypeMismatchException: [] cannot match type \
map_(<... 'int'>, <... 'str'>): allowed types are: <... 'dict'>
        >>> check_type({}, map_(int, str))
        {}
        >>> check_type({1: "abc"}, map_(int, str))
        {1: 'abc'}
        >>> m = map_()
        >>> m.bind(int, m)
        >>> d = {}
        >>> d[1] = d
        >>> check_type(d, m)
        {1: {...}}
    """
    def bind(self, key_type, value_type, allowed_type = dict,
                created_type = dict):
        """
        :param key_type: a valid type for dict key
        
        :param value_type: a valid type for dict value
        
        :param allowed_type: allowed class of the input
        
        :param created_type: class of the return value
        """
        self.key_type = key_type
        self.value_type = value_type
        self.allowed_type = allowed_type
        self.created_type = created_type
    
    def pre_check_type(self, value):
        if not isinstance(value, self.allowed_type):
            raise TypeMismatchException(value, self,
                    "allowed types are: " + repr(self.allowed_type))
        return {}
        
    def final_check_type(self, value, current_result, recursive_check_type):
        current_result.update(
                (recursive_check_type(k, self.key_type),
                    recursive_check_type(v, self.value_type))
                for k, v in list(value.items())
        )
        return current_result
    
    @recursive_repr()
    def __repr__(self):
        return "map_(" + repr(self.key_type) + ", " + \
                repr(self.value_type) + ")"
        

map_ = MapChecker


class ExtraChecker(CustomizedChecker):
    """
    Do extra checks around a basic type
    
    Examples::
    
        >>> extra([])
        extra([])
        >>> check_type({"age": 15}, extra({"age": int}))
        {'age': 15}
        >>> check_type({"age": 15}, extra({"age": int},
        ... check = lambda x: 14 < x['age'] < 18))
        {'age': 15}
        >>> check_type({"age": 19}, extra({"age": int},
        ... check = lambda x: 14 < x['age'] < 18)) # doctest: +ELLIPSIS
        Traceback (most recent call last):
            ...
        TypeMismatchException: {'age': 19} cannot match type \
extra({'age': <... 'int'>}): check returns False
        >>> e_t = extra(None, precreate = lambda x: {})
        Traceback (most recent call last):
            ...
        InvalidTypeException: extra(None) is not a valid type: \
precreate and merge must be used together
        >>> e_t = extra()
        >>> e_t.bind(tuple_((str, [e_t])),
        ...          check_before = lambda x: len(x) >= 2,
        ...          check = lambda x: len(x[1]) <= 3,
        ...          convert_before = lambda x: x[:2],
        ...          convert = lambda x: (x[0], x[1], len(x[1])),
        ...          precreate = lambda x: {},
        ...          merge = lambda c, r:
        ...                     c.update((
        ...                         ("name", r[0]),
        ...                         ("children", r[1]),
        ...                         ("childcount", r[2])
        ...                     ))
        ...          )
        >>> check_type(("a",), e_t) # doctest: +ELLIPSIS
        Traceback (most recent call last):
            ...
        TypeMismatchException: ('a',) cannot match type \
extra(tuple_((<... 'str'>, [...]))): \
check_before returns False
        >>> check_type(("a",[],123), e_t) == \\
        ... {'name': 'a', 'children': [], 'childcount': 0}
        True
        >>> d = ("a",[])
        >>> d[1].append(d)
        >>> d[1].append(d)
        >>> r = check_type(d, e_t)
        >>> r['name']
        'a'
        >>> r['childcount']
        2
        >>> len(r['children'])
        2
        >>> r['children'][0] is r
        True
        >>> r['children'][1] is r
        True
                            
    """
    def bind(self, basictype = object, check = None,
                                       check_before = None,
                                       convert = None,
                                       convert_before = None,
                                       precreate = None,
                                       merge = None):
        """
        Do extra check/convert around a basic type check.
        Added steps are:
        
        1. if check_before is not None, call check_before(value),
           raises Exception if it returns False
        
        2. if precreate is not None, create result_obj = precreate(value)

        3. if convert_before is not None, value = convert_before(value)
                
        4. do the basic type check against basictype, get result
        
        5. if check is not None, call check(result), raises Exception
           if it returns False
        
        6. if convert is not None, result = convert(result)
        
        7. if merge is not None, call merge(result_obj, result),
           then result = result_obj
        
        Use precreate and merge to create a recursive object
        (e.g. an instance referencing itself): first create an empty object,
        do check type, and merge the result to the pre-created object.
        
        Use bind() to delay the initialize of this type to
        create recursive types::
        
            new_type = extra()
            new_type.bind([new_type])
            
        Take care of convert_before / convert: do not break the
        recursive structure.
        """
        self.basictype = basictype
        self._check = check
        self._check_before = check_before
        self._convert = convert
        self._convert_before = convert_before
        self._precreate = precreate
        self._merge = merge
        if (self._precreate is None and self._merge is not None) or \
                (self._precreate is not None and self._merge is None):
            raise InvalidTypeException(self,
                    "precreate and merge must be used together")
        if self._precreate is not None:
            self._recursive = True
        else:
            self._recursive = False
    
    def pre_check_type(self, value):
        if self._check_before is not None:
            if not self._check_before(value):
                raise TypeMismatchException(value, self,
                        "check_before returns False")
        if self._precreate is not None:
            return self._precreate(value)
        else:
            return None
    
    def final_check_type(self, value, current_result, recursive_check_type):
        origin_value = value
        if self._convert_before is not None:
            value = self._convert_before(value)
        r = recursive_check_type(value, self.basictype)
        if self._check is not None:
            if not self._check(r):
                raise TypeMismatchException(origin_value, self,
                        "check returns False")
        if self._convert is not None:
            r = self._convert(r)
        if current_result is not None:
            self._merge(current_result, r)
            return current_result
        else:
            return r
    
    @recursive_repr()
    def __repr__(self):
        return "extra(" + repr(self.basictype) + ")"

        
extra = ExtraChecker


def default_object_merger(o, new_dict):
    o.__dict__.update(new_dict)
    return o


class ObjectChecker(CustomizedChecker):
    """
    Check a customized object and its properties. This checker directly
    operate on __dict__, so magic attributes e.g. __getattr__ does not
    have effects.
    
    Examples::
    
        >>> class SingleLinked(object):
        ...     def __init__(self, name, next = None):
        ...         self.name = name
        ...         self.next = next
        ...
        >>> class DoubleLinked(object):
        ...     def __init__(self, name, next = None, prev = None):
        ...         self.name = name
        ...         self.next = next
        ...         self.prev = prev
        ...
        >>> single = class_()
        >>> single.bind(SingleLinked, {"next": (single, None)})
        >>> s1 = SingleLinked("A", SingleLinked("B", SingleLinked("C")))
        >>> s2 = SingleLinked("C", SingleLinked("B", SingleLinked("A")))
        >>> s2.next.next.next = s2
        >>> r = check_type(s1, single)
        >>> (r.name, r.next.name, r.next.next.name, r.next.next.next) == \\
        ... ("A", "B", "C", None)
        True
        >>> r = check_type(s2, single)
        >>> (r.name, r.next.name, r.next.next.name, r.next.next.next.name) \\
        ... == ("C", "B", "A", "C")
        True
        >>> r.next.next.next is r
        True
        >>> r is not s2
        True
        >>>
        >>> single2 = class_()
        >>> single2.bind(SingleLinked, {"next": (single2, None)},
        ... recreate_object = False)
        >>> r = check_type(s1, single2)
        >>> r is s1
        True
        >>> r = check_type(s2, single2)
        >>> r is s2
        True
        >>>
        >>> single_to_double = class_()
        >>>
        >>> def _modify_node(o):
        ...     if o.next:
        ...         o.next.prev = o
        ...     if not hasattr(o, 'prev'):
        ...         o.prev = None
        ...
        >>> def _check(x):
        ...     if hasattr(x, 'prev'):
        ...         if x.prev.name == "C" and x.name == "A":
        ...             return False
        ...     if x.name == "C" and x.next is not None and \\
        ...             hasattr(x.next, 'name') and x.next.name == 'A':
        ...         return False
        ...     return True
        ...
        >>> single_to_double.bind(SingleLinked,
        ...                       {"next": (single_to_double, None)},
        ...                       check_before = lambda x: x.name != "",
        ...                       check = _check,
        ...                       recreate_object =
        ...                         lambda: DoubleLinked.__new__(
        ...                             DoubleLinked),
        ...                       modify = _modify_node)
        >>>
        >>> check_type(SingleLinked(""), single_to_double) \
# doctest: +ELLIPSIS
        Traceback (most recent call last):
          ...
        TypeMismatchException: ... cannot match type class_(...): \
check_before returns False
        >>> r = check_type(s1, single_to_double)
        >>> (r.prev, r.name, r.next.name, r.next.next.name, r.next.next.next) \\
        ... == (None, "A", "B", "C", None)
        True
        >>> r.next.prev is r
        True
        >>>
        >>> r = check_type(s2, single_to_double)
        >>> (r.prev.name, r.name, r.next.name, r.next.next.name,
        ... r.next.next.next.name) == \\
        ... ("A", "C", "B", "A", "C")
        True
        >>> r.next.next.next is r
        True
        >>> r.prev.prev.prev is r
        True
        >>>
        >>> def _check2(x):
        ...     if hasattr(x, 'prev'):
        ...         if x.prev.name == "A" and x.name == "C":
        ...             return False
        ...     if x.name == "A" and x.next is not None and \\
        ...             hasattr(x.next, 'name') and x.next.name == 'C':
        ...         return False
        ...     return True
        ...
        >>> single_to_double2 = class_()
        >>> single_to_double2.bind(SingleLinked,
        ...                        {"next": (single_to_double2, None)},
        ...                        check_before = lambda x: x.name != "",
        ...                        check = _check2,
        ...                        recreate_object =
        ...                            lambda: DoubleLinked.__new__(
        ...                                         DoubleLinked),
        ...                        modify = _modify_node)
        >>> check_type(s2, single_to_double2) # doctest: +ELLIPSIS
        Traceback (most recent call last):
          ...
        TypeMismatchException: ... cannot match type ...: \
check returns False
    """
    def bind(self, object_type, property_check = {},
                                recreate_object = True,
                                check = None,
                                check_before = None,
                                modify = None,
                                merge = default_object_merger):
        """
        :param object_type: a user-defined class
        
        :param property_check: type check for object __dict__.
                               The checked result will be updated to
                               object __dict__.
        
        :param recreate_object: if a callable is passed in, use it to
                                create a new object; use
                                `object_type.__new__(object_type)`
                                to create a new object if True;
                                use the original object else
                                (**WARNING: this may modify the
                                original object**)
        
        :param check: run an additional check for created object
        
        :param check_before: run a check before property checking
        
        :param modify: modify the object after type check
        
        :param merge: customize property merge process
        
        Sequence: check object_type -> check_before -> recreate_object ->
        check property -> merge -> check -> modify
        """
        self.object_type = object_type
        self.property_check = property_check
        if callable(recreate_object):
            self._recreate_object = recreate_object
        elif recreate_object:
            self._recreate_object = lambda: object_type.__new__(object_type)
        else:
            self._recreate_object = None
        self._check = check
        self._check_before = check_before
        self._modify = modify
        self._merge = merge
    
    def pre_check_type(self, value):
        if not isinstance(value, self.object_type):
            raise TypeMismatchException(value, self, "class type mismatch")
        if self._check_before is not None:
            if not self._check_before(value):
                raise TypeMismatchException(value, self,
                        "check_before returns False")
        if self._recreate_object is not None:
            return self._recreate_object()
        else:
            return value
    
    def final_check_type(self, value, current_result, recursive_check_type):
        d = recursive_check_type(value.__dict__, self.property_check)
        if self._merge is not None:
            self._merge(current_result, d)
        if self._check is not None:
            if not self._check(current_result):
                raise TypeMismatchException(value, self,
                        "check returns False")
        if self._modify is not None:
            self._modify(current_result)
        return current_result
        
    @recursive_repr()
    def __repr__(self):
        return 'class_(' + repr(self.object_type) + ', ' + \
                repr(self.property_check) + ')'

        
class_ = ObjectChecker


class TypeChecker(ExtraChecker):
    """
    Check an input variable is a class, and (optionally)
    a subclass of `baseclass`, and (optionally) has a metaclass
    of `metaclass`.
    
    Examples::
        
        >>> t = type_(int)
        >>> t # doctest: +ELLIPSIS
        type_(<... 'int'>)
        >>> check_type(bool, t) # doctest: +ELLIPSIS
        <... 'bool'>
        >>> check_type(str, t) # doctest: +ELLIPSIS
        Traceback (most recent call last):
          ...
        TypeMismatchException: <... 'str'> cannot match type type_(<... 'int'>): must be a subclass of <... 'int'>
    """
    def _check(self, value):
        if not issubclass(value, self._baseclass):
            raise TypeMismatchException(value, self, "must be a subclass of " + repr(self._baseclass))
        return True

    def bind(self, baseclass=None, metaclass=type):
        """
        :param baseclass: if not None, check the input is a subclass of `baseclass`
        
        :param metaclass: if not None, check the input is an instance of `metaclass`
        """
        self._metaclass = metaclass
        self._baseclass = baseclass
        if not isinstance(metaclass, type):
            raise InvalidTypeException(self, repr(metaclass) + " is not a metaclass")
        if baseclass is None:
            ExtraChecker.bind(self, metaclass)
        else:
            if not isinstance(baseclass, type):
                raise InvalidTypeException(self, repr(metaclass) + " is not a baseclass")
            ExtraChecker.bind(self, metaclass, check=self._check)

    def __repr__(self):
        return "type_(" +  ("" if self._baseclass is None else repr(self._baseclass)) + \
                 ("" if self._metaclass is type else "metaclass=" + repr(self._metaclass)) + ")"


def type_(baseclass=None, metaclass=type):
    """
    Create a TypeChecker
    """
    return TypeChecker(baseclass, metaclass)


def _check_type_inner(value, type_, _recursive_check = None):
    # print('Check type:', value, id(value), type_, id(type_))
    if _recursive_check is None:
        # current, succeeded, failed, listloop
        # each has id-tuple as their key, and (result, value, type_) as the value.
        # we must store the used value ans types to prevent them from being collected,
        # or the ids may be reused
        _recursive_check = ({}, {}, {}, {})
    current_check, succeded_check, failed_check, list_loop = \
            _recursive_check
    # Use (id(value), id(type)) to store matches that are done before
    check_id = (id(value), id(type_))
    if check_id in succeded_check:
        # This match is already done, return the result
        # print('Hit succedded cache:', succeded_check[check_id],
        #    id(succeeded_check[check_id]))
        return succeded_check[check_id][0]
    elif check_id in failed_check:
        # This match is already failed, raise the exception
        raise failed_check[check_id][0]
    elif check_id in current_check:
        # print('Hit succedded cache:', current_check[check_id],
        #    id(current_check[check_id]))
        # This match is in-operation. The final result is depended by
        # itself. Return the object itself to form a recursive structure.
        return current_check[check_id][0]
    return_value = None
    def _customized_check(checker):
        if check_id in list_loop:
            raise TypeMismatchException(value, type_)
        current_result = checker.pre_check_type(value)
        if current_result is None:
            # Prevent an infinite loop
            list_loop[check_id] = (value, type_)
            try:
                current_result = checker.final_check_type(
                                    value,
                                    None,
                                    lambda value, type:
                                        _check_type_inner(
                                            value, type, _recursive_check)
                                 )
            finally:
                del list_loop[check_id]
        else:
            current_check[check_id] = (current_result, value, type_)
            # backup succedded check: it may depends on current result.
            # If the type match fails, revert all succeeded check
            _new_recursive_check = (current_check, dict(succeded_check),
                failed_check, {})
            checker.final_check_type(
                value,
                current_result,
                lambda value, type:
                    _check_type_inner(value, type, _new_recursive_check)
            )
            # copy succeeded checks
            succeded_check.clear()
            succeded_check.update(_new_recursive_check[1])
        return current_result
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
            # Enhanced behavior when matching int type:
            # long is also matched; bool is NOT matched
            if not isinstance(value, bool) and (isinstance(value, int) \
                    or isinstance(value, _long)):
                return_value = value
            else:
                raise TypeMismatchException(value, type_)
        elif type_ is str or type_ is _unicode:
            # Enhanced behavior when matching str:
            # unicode is always matched (even in Python2)
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
                    return_value = _check_type_inner(
                                        value,
                                        subtype,
                                        _recursive_check
                                    )
                except TypeMismatchException:
                    continue
                else:
                    break
            else:
                raise TypeMismatchException(value, type_)
        elif isinstance(type_, list):
            return_value = _customized_check(ListChecker(type_))
        elif isinstance(type_, dict):
            return_value = _customized_check(DictChecker(type_))
        elif isinstance(type_, CustomizedChecker):
            return_value = _customized_check(type_)
        else:
            raise InvalidTypeException(type_, "Unrecognized type")
    except Exception as exc:
        # This match fails, store the exception
        failed_check[check_id] = (exc, value, type_)
        if check_id in current_check:
            del current_check[check_id]
        raise
    else:
        # This match succeeded
        if check_id in current_check:
            del current_check[check_id]
            # Only store the succeded_check if necessary. 
            succeded_check[check_id] = (return_value, value, type_)
        return return_value

if __name__ == '__main__':
    import doctest
    doctest.testmod()
