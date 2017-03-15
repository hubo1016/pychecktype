# pychecktype
A type-checker which can process recursive types and data

## Basic Usage

```python
from pychecktype import check_type

check_type({"abc": [1,2,3], "def": {"test": "abc"}}, {"abc": [int], "def": {"test": [str]}})

# Returns: {"abc": [1,2,3], "def": {"test": ["abc"]}}
```

## Rules

This type-checker has some specialized rules designed for YAML. For example, this type-checker accepts a single value against a
list type, and convert the value to [value].

See docstring in pychecktype.py for details.

## Highlight

The most intersting thing of this implementation is that it fully support recursive types and data, for example:

```python
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
```

## Try & Use

This small script is never meant to be a standard libaray, so it is not published to PyPI. If you want to use it
or modify it, simply copy it into your source directory. The code is published under Apache 2.0 license.
