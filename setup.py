"""PyPI setup script

Script includes primary Python package along with essential
non-Python files, such as json files.

Usage:
    >>> python setup.py sdist
    ...

"""

import os
import imp
from setuptools import setup, find_packages

with open("README.md") as f:
    readme = f.read()

version_file = os.path.abspath("pyblish_rpc/version.py")
version_mod = imp.load_source("version", version_file)
version = version_mod.version

classifiers = [
    "Development Status :: 5 - Production/Stable",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
    "Programming Language :: Python",
    "Programming Language :: Python :: 2",
    "Programming Language :: Python :: 2.6",
    "Programming Language :: Python :: 2.7",
    "Programming Language :: Python :: 3.3",
    "Programming Language :: Python :: 3.5",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Topic :: Utilities"
]

setup(
    name="pyblish-rpc",
    version=version,
    description="An RPC interface to Pyblish",
    long_description=readme,
    author="Abstract Factory and Contributors",
    author_email="marcus@abstractfactory.com",
    url="https://github.com/pyblish/pyblish-rpc",
    license="LGPL",
    packages=find_packages(),
    zip_safe=False,
    classifiers=classifiers,
    package_data={
        "pyblish_rpc": ["schema/*.json", "vendor/jsonschema/schemas/*.json"]
    },
    entry_points={},
)
