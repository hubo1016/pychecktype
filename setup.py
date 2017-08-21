#!/usr/bin/env python

from setuptools import setup

version = "1.0"

try:
    import pypandoc
    long_description = pypandoc.convert('README.md', 'rst')
except (IOError, ImportError):
    long_description = ""


setup(
    name="pychecktype",
    version=version,
    author="Hu Bo",
    author_email="hubo1016@126.com",
    long_description=long_description,
    description="asyncio wrapper for grpc.io",
    license="Apache",
    classifiers=[
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Topic :: Software Development',
    ],
    url="https://github.com/hubo1016/pychecktype",
    platforms=['any'],
    packages=[
        'pychecktype',
    ]
)
