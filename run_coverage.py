import os
import sys

# Set PYBLISH_SAFE to enable verbose checks
os.environ['PYBLISH_SAFE'] = "1"

# Expose pyblish-rpc to PYTHONPATH
path = os.path.dirname(__file__)
package_path = os.path.join(path, "pyblish_rpc")
sys.path.insert(0, os.path.abspath(package_path))

import pyblish_rpc
pyblish_rpc.register_vendor_packages()

import nose


if __name__ == "__main__":
    argv = sys.argv[:]
    argv.extend(["pyblish_rpc",
                 "tests",
                 "-c",
                 ".noserc"])
    nose.main(argv=argv)
