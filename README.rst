pychecktype
===========

.. image:: https://readthedocs.org/projects/pychecktype/badge/?version=latest
   :target: http://pychecktype.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status
.. image:: https://img.shields.io/pypi/v/pychecktype.svg
   :target: https://pypi.python.org/pypi/pychecktype
   :alt: PyPI

A type-checker which can process recursive types and data

Documents: http://pychecktype.readthedocs.io/en/latest/

Install
-------

::

    pip install pychecktype

Basic Usage
-----------

.. code:: python

    from pychecktype import check_type

    check_type({"abc": [1,2,3], "def": {"test": "abc"}}, {"abc": [int], "def": {"test": [str]}})

    # Returns: {"abc": [1,2,3], "def": {"test": ["abc"]}}

Highlight
---------

The most intersting thing of this implementation is that it fully
support recursive types and data, for example:

.. code:: python

    from pychecktype import check_type


    my_type = []
    my_type.append((int, my_type))

    # my_type accepts: recursive lists with only sub-list and integers with any depth - even infinite

    check_type([], my_type) # []

    check_type([1,2,3,[1,2],[1,2,[3,4]]], my_type) # [1,2,3,[1,2],[1,2,[3,4]]]

    check_type([1,2,3,[1,2],[1,2,["3",4]]], my_type) # failed

    my_obj = []
    my_obj.append(my_obj)
    my_obj.append(2)
    check_type(my_obj, my_type) # [[...], 2]

Rules
-----

This type-checker has some specialized rules suitable for YAML. For
example, this type-checker accepts a single value against a list type,
and convert the value to ``[value]``.

This type-checker uses a slightly simpler and more readable DSL rules
than other libraries like ``typing`` and ``trafaret``, most of them are
Python builtin objects.

The ``check_type`` method not only checks that the value is matched with
the given type; it returns a *corrected* version of that object.

Generally:

1. A Python type matches any object in that type (e.g str, int) except:

a. ``str`` and ``unicode`` always match both str and unicode objects
   both in Python 2 and Python 3

b. ``int`` and ``long`` always match both int and long objects both in
   Python 2 and Python 3

c. bool objects are never matched with ``int`` or ``long``, they are
   only matched with ``bool`` (though ``bool`` is a subclass of ``int``)

Specially, ``object`` matches any value including ``None``. A helper
class ``NoMatch`` is provided to do not match any instances, it can be
embedded in other types to create assertions.

2. ``None`` matches ``None`` only (equivalent to ``NoneType``)

3. Tuple as a type:

a. ``()`` matches any object *EXCEPT* ``None``

b. A tuple of multiple valid types ``(type1, type2, ...)`` tries to
   match the object with each sub-type from left to right. For example,
   ``(str, int)`` matches a str object or an int object; ``(str, None)``
   matches a str object or None

4. List as a type:

a. ``[]`` matches any list, or convert the object to a list contains the
   object

b. ``[type]`` matches a list of items which all match the inner type, or
   convert an object which matches with the inner type to a list
   contains it

c. By default, list types matches both *list* objects and *tuple*
   objects, and convert them to lists. For example, ``[int]`` matches
   ``(1,2,3)`` and returns ``[1,2,3]``. Use ``list_`` factory method to
   create a customized list type which accepts only types that are
   specified. You may also use it to accept more iterable types e.g.
   ``set``

d. By default, list types can convert non-list objects to a list
   contains only that object, e.g. ``1`` to ``[1]``, ``{"a":1}`` to
   ``[{"a":1}]``. This conversion cannot happen when the object itself
   is a list/tuple, e.g. ``[list]`` cannot match ``[1]``, because it is
   not allowed to be converted to ``[[1]]``.

   You may disable the conversion by creating a customized list type
   with ``list_`` factory method with ``strict=True``

e. List types return a shallow copy of the input list.

5. Dist as a type:

a. ``{}`` matches any dict

b. When dict contains key-value pairs, they become restricts to the
   input dict:

   1). Keys start with '!' are required keys, and the corresponding
   value is a type. The value of the specified key in the input dict
   must match the specified type in the type dict.

   2). Keys start with '?' are optional keys, they are not needed to
   appear in the input dict, but if they appear they must be matched
   with the value in the type dict.

   3). Keys start with '~' are regular expressions. For all keys in the
   input dict that are matched by the regular expression followed by the
   '~', the corresponding value must match with the specified type.
   Regular expressions only match the keys that are not required or
   optional keys.

   4). Other keys are regarded as required keys (as if they are
   prepended by '!')

   5). Extra keys in the input dict do not affect the match. You may use
   ``'~': NoMatch`` to disable extra keys.

   Examples:

   ::

       `{"abc": int}` matches `{"abc": 1}` and `{"abc": 1, "d": 2}` but not `{"d": 2}`

       `{"!abc": int}` matches `{"abc": 1}` and `{"abc": 1, "d": 2}` but not `{"d": 2}`

       `{"?abc": int}` matches `{"abc": 1}`, `{"abc": 1, "d": 2}` and `{"d": 1}`, but not `{"abc": "a"}`

       `{"~a.b": int}` matches `{"acb": 1}` but not `{"facbg": "a"}` because "facbg" is matched by 'a.b'

       `{"~a.b": int, "adb": str}` matches `{"adb": "abc"}` but not `{"adb": 1}`

6. ``tuple_((type1, type2, type3, ...))`` creates a customized type
   (tuple type) which matches any tuple/list that contains exactly the
   same number of items, each matches the corresponding sub type.

7. ``map_(key_type, value_type)`` creates a customized type (map type)
   which matches any dict, in which each key matches the *key\_type*,
   and each value matches the *value\_type*

8. ``extra_`` and ``class_`` are advanced customized types, they do
   customized additional checks for the input object e.g. check against
   a regular expression etc.

See docstring in pychecktype.py for details.

Python 3 Annotation Checks
--------------------------

You may use `pychecktype.checked.checked` decorator to check input parameters and return values of a function

.. code:: python

    from pychecktype.checked import checked
    @checked
    def f(a: str, b: int)->str:
        """
        check `a` is str, `b` is int, and returns str
        """
        return a + str(b)
    
    @checked
    def f2(a, b: int):
        """
        You may check only part of the parameters.
        """
        return str(a) + str(b)
    
    @checked
    async def f3(a: str, *args: [int], **kwargs: {'?join': bool})->str:
        """
        Async functions are decorated to async functions
        
        *args , keyword-only arguments and **kwargs can also be checked
        """
        if kwargs.get('join'):
            return a.join(str(v) for v in args)
        else:
            return a + str(sum(args))

    from functools import wraps
    def testdecorator(f):
        @wraps
        def _f(*args, **kwargs):
            print("Wrapped")
            return f(*args, **kwargs)
    
    @checked
    @testdecorator
    def f4(a: int):
        """
        Works well with decorators that are correctly using `functools.wraps`
        and not modifying the argument list
        """
        return a + 1
