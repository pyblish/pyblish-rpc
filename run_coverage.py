import os
import sys

# Expose pyblish-rpc to PYTHONPATH
path = os.path.dirname(__file__)
package_path = os.path.join(path, "pyblish_rpc")
vendor = os.path.join(package_path, "vendor")
sys.path.insert(0, os.path.abspath(vendor))
sys.path.insert(0, os.path.abspath(package_path))

import nose


if __name__ == '__main__':
    argv = sys.argv[:]
    argv.extend(['-c', '.noserc'])
    nose.main(argv=argv)
