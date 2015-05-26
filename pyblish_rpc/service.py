
# Standard library
import os
import sys
import json
import time
import Queue
import getpass
import logging
import traceback

# Pyblish Library
import pyblish.api
import pyblish.util

# Local Library
import version
import mocking
import formatting

_request_queue = Queue.Queue()
_log = logging.getLogger("pyblish-rpc")


class RpcService(object):
    _count = 0
    _instances = property(
        lambda self: pyblish.lib.ItemList("name", self._context))

    def __init__(self):
        self._context = None
        self._plugins = None
        self._provider = None

        self.reset()

    def ping(self):
        """Used to check connectivity"""
        return {
            "message": "Hello, whomever you are"
        }

    def stats(self):
        """Return statistics about the API"""
        return {
            "totalRequestCount": self._count,
        }

    def push(self):
        """An incoming push request"""
        try:
            message = _request_queue.get(timeout=1)
        except Queue.Empty:
            return "heartbeat"

        try:
            json.dumps(message)
        except:
            _log.warning("Could not send request; %s is not JSON-serialisable"
                         % message)
            return None

        return message

    def reset(self):
        self._context = pyblish.api.Context()
        self._plugins = list()
        self._provider = pyblish.plugin.Provider()

    def context(self):
        # Append additional metadata to context
        executable = sys.executable
        basename = os.path.basename(executable)
        name, _ = os.path.splitext(basename)
        port = os.environ.get("PYBLISH_CLIENT_PORT", -1)

        for key, value in {"host": name,
                           "port": int(port),
                           "user": getpass.getuser(),
                           "connectTime": pyblish.util.time(),
                           "pyblishServerVersion": pyblish.version,
                           "clientVersion": version.version,
                           "pythonVersion": sys.version}.iteritems():

            self._context.set_data(key, value)

        return formatting.format_context(self._context)

    def discover(self):
        return formatting.format_plugins(pyblish.api.discover())

    def process(self, plugin, context, instance=None):
        """Given JSON objects from client, perform actual processing

        Arguments:
            plugin (dict): JSON representation of plug-in to process
            context (dict): JSON representation of Context to be processed
            instance (dict, optional): JSON representation of Instance to
                be processed.

        """

        plugin_obj = plugin_from_name(plugin["name"])
        instance_obj = (self._instances[instance["name"]]
                        if instance is not None else None)

        result = pyblish.util.process(
            plugin=plugin_obj,
            context=self._context,
            instance=instance_obj)

        print "Returning: %s" % result.keys()

        return formatting.format_result(result)

    def repair(self, plugin, context, instance=None):
        plugin_obj = plugin_from_name(plugin["name"])
        instance_obj = (self._instances[instance["name"]]
                        if instance is not None else None)

        result = pyblish.util.repair(
            plugin=plugin_obj,
            context=self._context,
            instance=instance_obj)

        return formatting.format_result(result)

    def _dispatch(self, method, params):
        """Customise exception handling"""
        self._count += 1

        func = getattr(self, method)
        try:
            return func(*params)
        except Exception as e:
            traceback.print_exc()
            raise e


class MockRpcService(RpcService):
    def __init__(self, *args, **kwargs):
        super(MockRpcService, self).__init__(*args, **kwargs)

        for plugin in mocking.plugins:
            pyblish.api.register_plugin(plugin)

    def process(self, *args, **kwargs):
        time.sleep(0.1)
        super(MockRpcService, self).process(*args, **kwargs)


def plugin_from_name(name):
    """Parse plug-in id to object"""
    plugins = pyblish.api.discover()
    plugins = pyblish.lib.ItemList("__name__", plugins)
    return plugins[name]
