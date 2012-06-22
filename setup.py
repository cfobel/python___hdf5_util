#!/usr/bin/env python

import distutils.core

try:
    from distutils.command.build_py import build_py_2to3 as build_py
except ImportError:
    from distutils.command.build_py import build_py

# Setup script for path

kw = {
    'name': "hdf5_util",
    'version': "{{ ___VERSION___ }}",
    'description': "A set of utilities for use with HDF5/PyTables",
    'author': "Christian Fobel",
    'author_email': "christian@fobel.net",
    'url': "https://github.com/cfobel/python___hdf5_util",
    'license': "MIT License",
    'packages': ['hdf5_util'],
    'cmdclass': dict(build_py=build_py),
}


# If we're running Python 2.3, add extra information
if hasattr(distutils.core, 'setup_keywords'):
    if 'classifiers' in distutils.core.setup_keywords:
        kw['classifiers'] = [
            'Development Status :: 3 - Alpha',
            'License :: OSI Approved :: MIT License',
            'Intended Audience :: Developers',
            'Operating System :: OS Independent',
            'Programming Language :: Python',
            'Topic :: Software Development :: Libraries :: Python Modules'
          ]
    if 'download_url' in distutils.core.setup_keywords:
        kw['download_url'] = 'https://github.com/cfobel/python___hdf5_util/'\
                'tarball/master'

distutils.core.setup(**kw)
