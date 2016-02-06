"""Assume behaviour on part of the core Pyblish library"""

import sys
import subprocess

import pyblish_rpc.client
import pyblish_rpc.server

server = None
thread = None
process = None
client = None

self = sys.modules[__name__]


def setup():
    """Subprocessed RPC server

    The benefit of a processed server, as opposed to threaded
    is that it accurately reflects the production server, at
    the cost of not allowing plug-ins to be registered during
    a test.

    """

    self.process = subprocess.Popen(
        ["python", "-m", "pyblish_rpc", "--port", str(7001)])
    self.client = pyblish_rpc.client.Proxy(7001)


def teardown():
    """Shutdown module-level server"""
    self.client.kill()
    print "Killed"
    self.process.wait()
    assert not process.poll()
