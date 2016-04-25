import os
import sys

# Set PYBLISH_SAFE to enable verbose checks
os.environ['PYBLISH_SAFE'] = "1"

# Expose pyblish-rpc to PYTHONPATH
test_path = os.path.realpath(__file__)
repo_dir = os.path.dirname(test_path)
package_path = os.path.join(repo_dir, "pyblish_rpc")
sys.path.insert(0, package_path)

import pyblish_rpc
pyblish_rpc.register_vendor_packages()

import nose


if __name__ == "__main__":
    argv = sys.argv[:]
    argv.extend([
        "tests",
        "pyblish_rpc",
        "--exclude=vendor",
        "--with-doctest",
        "--verbose"])
    nose.main(argv=argv)
