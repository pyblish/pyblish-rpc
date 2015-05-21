
import os
import sys
import time
import json
import copy
import logging
import getpass
import traceback
import SocketServer

from SimpleXMLRPCServer import (
    SimpleXMLRPCServer,
    list_public_methods,
)

import pyblish.api as pyblish
import pyblish.lib

import service
import version

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger("pyblish-xmlrpc")


class Api(object):
    def __init__(self):
        self._context = service.Context()
        self._plugins = service.Plugins()
        self._provider = pyblish.plugin.Provider()

    def sleep(self, duration=1):
        time.sleep(duration)

    def reset(self):
        self._context = service.Context()
        self._plugins[:] = pyblish.api.discover()
        self._provider = pyblish.plugin.Provider()

        # Append additional metadata to context
        executable = sys.executable
        basename = os.path.basename(executable)
        name, _ = os.path.splitext(basename)

        for key, value in {"host": name,
                           "port": int(os.environ.get("ENDPOINT_PORT", -1)),
                           "user": getpass.getuser(),
                           "connectTime": time.time(),
                           "pyblishVersion": pyblish.version,
                           "xmlrpcVersion": version.version,
                           "pythonVersion": sys.version}.iteritems():

            self._context.set_data(key, value)

        return {
            "status": True
        }

    def process(self, plugin_id, instance_id=None):
        """Process `instance_id` with `plugin_id`

        Arguments:
            plugin_id (str): Id of plug-in to process
            instance_id (str, optional): Id of instance_id to process,
                if not passed Context is processed.

        """

        try:
            Plugin = self._plugins[plugin_id]
        except KeyError as e:
            extract_traceback(e)

            result = {
                "success": False,
                "plugin": plugin_id,
                "instance": instance_id or "Context",
                "error": format_error(e),
                "records": list(),
                "duration": 0
            }

            self.store_results_in_context(result)

            return result

        records = list()
        handler = MessageHandler(records)

        root_logger = logging.getLogger()
        root_logger.addHandler(handler)

        success = True
        formatted_error = None

        plugin = Plugin()
        self._provider.inject("context", self._context)

        if instance_id is not None:
            self._provider.inject("instance", self._context[instance_id])

        __start = time.time()

        try:
            self._provider.invoke(plugin.process)
        except Exception as error:
            success = False
            extract_traceback(error)
            formatted_error = format_error(error)

        __end = time.time()

        formatted_records = list()
        for record in records:
            formatted_records.append(format_record(record))

        # Restore balance to the world
        root_logger.removeHandler(handler)

        result = {
            "success": success,
            "plugin": plugin_id,
            "instance": instance_id or "Context",
            "error": formatted_error,
            "records": formatted_records,
            "duration": (__end - __start) * 1000  # ms
        }

        self.store_results_in_context(result)

        return result

    def context(self):
        return format_context(self._context)

    def plugins(self):
        return format_plugins(self._plugins)

    def store_results_in_context(self, result):
        results = self._context.data("results")
        if results is None:
            results = list()
            self._context.set_data("results", results)

        result = copy.deepcopy(result)
        results.append(result)

    def _listMethods(self):
        return list_public_methods(self)

    def _methodHelp(self, method):
        return getattr(self, method).__doc__


class MessageHandler(logging.Handler):
    def __init__(self, records, *args, **kwargs):
        # Not using super(), for compatibility with Python 2.6
        logging.Handler.__init__(self, *args, **kwargs)
        self.records = records

    def emit(self, record):
        self.records.append(record)


def extract_traceback(exception):
    try:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        exception.traceback = traceback.extract_tb(exc_traceback)[-1]

    except:
        pass

    finally:
        del(exc_type, exc_value, exc_traceback)


def format_record(record):
    """Serialise LogRecord instance

    Data:
        threadName
        name
        thread
        created
        process
        processName
        args
        module
        filename
        levelno
        exc_text
        pathname
        lineno
        msg
        exc_info
        funcName
        relativeCreated
        levelname
        msecs

    """

    record = record.__dict__

    # Humanise output and conform to Exceptions
    record["message"] = record.pop("msg")

    return record


def format_error(error):
    """Serialise exception"""
    formatted = {"message": str(error)}

    if hasattr(error, "traceback"):
        fname, line_no, func, exc = error.traceback
        formatted.update({
            "fname": fname,
            "line_number": line_no,
            "func": func,
            "exc": exc
        })

    return formatted


def format_state(state):
    """Bridge context with plug-ins

    Attribute:
        - compatibleInstances
        - compatiblePlugins

    """

    formatted = {
        "context": format_context(state["context"]),
        "plugins": format_plugins(state["plugins"])
    }

    return formatted


def format_data(data):
    """Serialise instance/context data

    Given an arbitrary dictionary of Python object,
    return a JSON-compatible dictionary.

    Note that all keys are cast to string and that values
    not compatible with JSON are replaced with "Not supported".

    Arguments:
        data (dict): Data to serialise

    Returns:
        data (dict): Serialised data

    """

    formatted = dict()

    for key, value in data.iteritems():
        try:
            key = str(key)
        except:
            continue

        try:
            json.dumps(value)
        except:
            value = "Not supported"

        formatted[key] = value

    return formatted


def format_instance(instance, data=None):
    """Serialise `instance`

    For children to be visualised and modified,
    they must provide an appropriate implementation
    of __str__.

    Data that isn't JSON compatible cannot be
    visualised nor modified.

    Attributes:
        name (str): Name of instance
        niceName (str, optional): Nice name of instance
        family (str): Name of compatible family
        children (list, optional): Associated children
        data (dict, optional): Associated data
        publish (bool): Whether or not instance should be published

    Returns:
        Dictionary of JSON-compatible instance

    """

    children = list()
    for child in instance:
        try:
            json.dumps(child)
        except:
            child = "Invalid"
        children.append(child)

    data = format_data(instance._data)

    return {
        "name": instance.name,
        "children": children,
        "data": data
    }


def format_context(context, data=None):
    formatted = []

    for instance in context:
        formatted_instance = format_instance(instance, data)
        formatted.append(formatted_instance)

    return {
        "data": format_data(context._data),
        "children": formatted
    }


def format_plugins(plugins, data=None):
    """Serialise multiple plug-in

    Returns:
        List of JSON-compatible plug-ins

    """

    formatted = []
    for plugin in plugins:
        formatted_plugin = format_plugin(plugin, data=data)
        formatted.append(formatted_plugin)

    return formatted


def format_plugin(plugin, data=None):
    """Serialise `plugin`

    Attributes:
        name: Name of Python class
        version: Plug-in version
        category: Optional category
        requires: Plug-in requirements
        order: Plug-in order
        optional: Is the plug-in optional?
        doc: The plug-in documentation
        hasRepair: Can the plug-in perform a repair?
        hasCompatible: Does the plug-in have any compatible instances?
        type: Which baseclass does the plug-in stem from? E.g. Validator
        module: File in which plug-in was defined
        canProcessContext: Does it process the Context?
        canProcessInstance: Does it process the Instance(s)?

    """

    assert issubclass(plugin, pyblish.plugin.Plugin)

    docstring = getattr(plugin, "doc", plugin.__doc__)

    formatted = {
        "name": plugin.__name__,
        "data": {
            "version": plugin.version,
            "category": getattr(plugin, "category", None),
            "requires": plugin.requires,
            "order": plugin.order,
            "optional": plugin.optional,
            "doc": docstring,
            "hasRepair": False,
            "hasCompatible": False,
            "hosts": [],
            "families": [],
            "type": None,
            "module": None,
            "canProcessContext": False,
            "canProcessInstance": False,
            "canRepairInstance": False,
            "canRepairContext": False
        }
    }

    try:
        # The MRO is as follows: (-1)object, (-2)Plugin, (-3)Selector..
        formatted["data"]["type"] = plugin.__mro__[-3].__name__
    except IndexError:
        # Plug-in was not subclasses from any of the
        # provided superclasses of pyblish.api. This
        # is either a bug or some (very) custom behavior
        # on the users part.
        log.critical("This is a bug")

    try:
        if plugin.__module__ == "__main__":
            # Support for in-memory plug-ins.
            path = "mem:%s" % plugin.__name__
        else:
            module = sys.modules[plugin.__module__]
            path = os.path.abspath(module.__file__)

        formatted["data"]["module"] = path

    except IndexError:
        pass

    for attr in ("hosts", "families"):
        if hasattr(plugin, attr):
            formatted["data"][attr] = getattr(plugin, attr)

    Superclass = pyblish.plugin.Plugin

    if Superclass.process_context != plugin.process_context:
        formatted["data"]["canProcessContext"] = True

    if Superclass.process_instance != plugin.process_instance:
        formatted["data"]["canProcessInstance"] = True

    # TODO(marcus): As of Pyblish 1.0.15, this try/except block
    # is no longer necessary.
    try:
        if Superclass.repair_instance != plugin.repair_instance:
            formatted["data"]["canRepairInstance"] = True
            formatted["data"]["hasRepair"] = True
    except AttributeError:
        pass

    try:
        if Superclass.repair_context != plugin.repair_context:
            formatted["data"]["canRepairContext"] = True
            formatted["data"]["hasRepair"] = True
    except AttributeError:
        pass

    return formatted


class ThreadedServer(SocketServer.ThreadingMixIn, SimpleXMLRPCServer):
    """Support multiple requests simultaneously

    This is important, as we will still want to emit heartbeats
    during a potentially long process.

    """


def serve():
    modulepath = sys.modules[__name__].__file__
    dirname = os.path.dirname(modulepath)
    pluginpath = os.path.join(dirname, "plugins")
    pyblish.api.register_plugin_path(pluginpath)

    server = ThreadedServer(
        ("127.0.0.1", 8000),
        allow_none=True,
        logRequests=True)

    server.register_introspection_functions()
    server.register_instance(Api(), allow_dotted_names=True)

    print("Listening on %s:%s" % server.server_address)
    server.serve_forever()


if __name__ == '__main__':
    serve()
