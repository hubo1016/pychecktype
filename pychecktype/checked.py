"""
Python 3 annotation based type-check
"""
from pychecktype import check_type
from functools import wraps
import inspect
import warnings
import sys
if sys.version_info >= (3,5):
    PY35 = True
    import pychecktype._checked_35 as _checked_35


def _get_inner_function(f):
    while hasattr(f, '__wrapped__'):
        f = f.__wrapped__
    return f


def checked(f):
    """
    Check input types with annotations
    
    Examples::
    
        >>> @checked
        ... def test(a: (str,int), b: (str,int))->str:
        ...     return a + b
        ...
        >>> test('a','b')
        'ab'
        >>> test(1,2)
        Traceback (most recent call last):
          ...
        pychecktype.TypeMismatchException: 3 cannot match type <class 'str'>
        >>> test(1.0,2.0)
        Traceback (most recent call last):
          ...
        pychecktype.TypeMismatchException: 1.0 cannot match type (<class 'str'>, <class 'int'>)
        >>> import asyncio
        >>> @checked
        ... async def test2(a: (str,int), b: (str,int))->str:
        ...     return a + b
        ...
        >>> asyncio.get_event_loop().run_until_complete(test2(1,2))
        Traceback (most recent call last):
          ...
        pychecktype.TypeMismatchException: 3 cannot match type <class 'str'>
        >>> @checked
        ... def test3(a: str, *args: [int], **kwargs: {'?join': bool}):
        ...     if kwargs.get('join'):
        ...         return a.join(str(v) for v in args)
        ...     else:
        ...         return a + str(sum(args))
        ...
        >>> test3('a',2,3)
        'a5'
        >>> test3('a','b',2)
        Traceback (most recent call last):
          ...
        pychecktype.TypeMismatchException: 'b' cannot match type <class 'int'>
        >>> test3('a',5,join=True)
        '5'
        >>> test3('a',5,join=1)
        Traceback (most recent call last):
          ...
        pychecktype.TypeMismatchException: 1 cannot match type <class 'bool'>
        >>> @checked
        ... async def test3(a: str, *args: [int], **kwargs: {'?join': bool}):
        ...     if kwargs.get('join'):
        ...         return a.join(str(v) for v in args)
        ...     else:
        ...         return a + str(sum(args))
        ...
        >>> asyncio.get_event_loop().run_until_complete(test3('a',2,3))
        'a5'
        >>> asyncio.get_event_loop().run_until_complete(test3('a','b',2))
        Traceback (most recent call last):
          ...
        pychecktype.TypeMismatchException: 'b' cannot match type <class 'int'>
        >>> asyncio.get_event_loop().run_until_complete(test3('a',5,join=True))
        '5'
        >>> asyncio.get_event_loop().run_until_complete(test3('a',5,join=1))
        Traceback (most recent call last):
          ...
        pychecktype.TypeMismatchException: 1 cannot match type <class 'bool'>
        >>> @checked
        ... def f(a, b: int):
        ...     return a + b
        ...
        >>> f('a','b')
        Traceback (most recent call last):
          ...
        pychecktype.TypeMismatchException: 'b' cannot match type <class 'int'>
        >>> f(1,2)
        3
        >>> from functools import wraps
        >>> def testdecorator(f):
        ...     @wraps(f)
        ...     def _f(*args, **kwargs):
        ...         print("Wrapped")
        ...         return f(*args, **kwargs)
        ...     return _f
        ...
        >>> @checked
        ... @testdecorator
        ... def f2(a: int):
        ...     return a
        ...
        >>> f2(1)
        Wrapped
        1
        >>> f2('a')
        Traceback (most recent call last):
          ...
        pychecktype.TypeMismatchException: 'a' cannot match type <class 'int'>
    """
    _inner_f = _get_inner_function(f)
    check_type_args = inspect.getfullargspec(_inner_f)
    check_type_annotations = check_type_args.annotations
    if not check_type_annotations:
        warnings.warn(UserWarning("Function " + repr(f) + " does not have annotations, checktype ignored."))
        return f
    if PY35 and hasattr(inspect, 'iscoroutinefunction') and inspect.iscoroutinefunction(f):
        _f = _checked_35.wrap_async(f, _inner_f, check_type_args, check_type_annotations)
    else:
        # Notice: async generators are treated as normal functions
        @wraps(f)
        def _f(*args, **kwargs):
            call_args = inspect.getcallargs(_inner_f, *args, **kwargs)
            for k, v in list(call_args.items()):
                if k in check_type_annotations:
                    call_args[k] = check_type(v, check_type_annotations[k])
            # Create arguments
            args = [call_args.pop(a) for a in check_type_args.args]
            if check_type_args.varargs is not None:
                args.extend(call_args.pop(check_type_args.varargs))
            if check_type_args.varkw is not None:
                kwargs = call_args.pop(check_type_args.varkw)
            else:
                kwargs = {}
            kwargs.update(call_args)
            _return = f(*args, **kwargs)
            if 'return' in check_type_annotations:
                return check_type(_return, check_type_annotations['return'])
            else:
                return _return        
    return _f


if __name__ == '__main__':
    import doctest
    doctest.testmod()
