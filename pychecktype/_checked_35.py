"""
Wrap an async function
"""
from pychecktype import check_type
from functools import wraps
import inspect


def wrap_async(f, _inner_f, check_type_args, check_type_annotations):
    @wraps(f)
    async def _f(*args, **kwargs):
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
        _return = await f(*args, **kwargs)
        if 'return' in check_type_annotations:
            return check_type(_return, check_type_annotations['return'])
        else:
            return _return        
    return _f
