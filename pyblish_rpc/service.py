# *-* coding:utf-8*-*
"""Endpoint Service

In order to protect Endpoint from the internals or both Pyblish
and each host application, the service acts as a layer inbetween
the two.

Users are meant to subclass :class:`EndpointService` in order to
implement support for clients; such as wrapping non-threadsafe calls
in a host-specific wrapper, such as maya.utils.executeInMainThreadWithResults

"""

import os
import sys
import time
import json
import copy
import getpass
import logging
import traceback

import pyblish
import pyblish.api
import pyblish.plugin

from version import version

log = logging.getLogger("endpoint")


class State(dict):
    """Hold on to information about host state

    State does not modify or interact with host and
    is therefore thread-safe.

    """

    def __init__(self, service):
        self.service = service

    def compute(self):
        """Format current state of Service into JSON-compatible dictionary

        Given that the Service contains an up-to-date view of the host,
        format this information into a dictionary capable of being passed
        on to the client.

        Returns:
            state: JSON-compatible dictionary of current state

        """

        self.clear()

        plugins = self.service.plugins
        context = self.service.context

        state = format_state({"plugins": plugins,
                              "context": context})

        # Bridge instances and plug-ins
        for plugin in state["plugins"]:
            compatible = pyblish.api.instances_by_plugin(
                instances=context,
                plugin=plugins[plugin["name"]])

            compatible = [str(i) for i in compatible]
            plugin["data"]["compatibleInstances"] = compatible

        for instance in state["context"]["children"]:
            compatible = list()
            family = instance["data"].get("family")

            if family:
                compatible = pyblish.api.plugins_by_family(
                    plugins=plugins,
                    family=family)
                compatible = [getattr(i, "id") for i in compatible]

            instance["data"]["compatiblePlugins"] = compatible

        super(State, self).update(state)

    def update(self, changes):
        """Parse changes from `changes` and apply to Service

        Given a dictionary of changes, apply changes to
        corresponding instances and plug-ins.

        Arguments:
            changes (dict): Dictionary of changes.

        """

        context_changes = changes["context"]

        for name, changes in context_changes.iteritems():

            try:
                instance = self.service.context[name]
            except KeyError:
                log.error(
                    "Instance from client does "
                    "not exist on server: %s "
                    "(available instances: %s)"
                    % (name, [i.name for i in self.service.context]))
                continue

            for key, change in changes.iteritems():
                current_value = instance.data(key)

                if current_value == change["new"]:
                    continue

                print(
                    "Changing \"{instance}.{data}\" from "
                    "\"{from_}\" to \"{to}\"".format(
                        instance=name,
                        data=key,
                        from_=instance.data(key),
                        to=change["new"]))

                instance.set_data(key, change["new"])


class Plugins(list):
    def __getitem__(self, index):
        if isinstance(index, int):
            return super(Plugins, self).__getitem__(index)

        for item in self:
            if item.__name__ == index:
                return item

        raise KeyError("%s not in list" % index)


class Context(pyblish.api.Context):
    def __getitem__(self, index):
        if isinstance(index, int):
            return super(Context, self).__getitem__(index)

        for item in self:
            if item.name == index:
                return item

        raise KeyError("%s not in list" % index)


class EndpointService(object):
    """Abstract baseclass for host interfaces towards endpoint

    The Service is responsible for computing and fetching data
    from a host and is thus *not* thread-safe.

    """

    _current = None

    def __init__(self):
        self.provider = pyblish.plugin.Provider()
        self.context = Context()
        self.plugins = Plugins()

        self.state = State(self)

    def init(self):
        """Create context and discover plug-ins and instances"""
        self.reset()
        self.plugins[:] = pyblish.api.discover()

    def reset(self):
        self.provider = pyblish.plugin.Provider()
        self.context = Context()
        self.plugins = Plugins()
        self.state.clear()

        # Append additional metadata to context
        executable = sys.executable
        basename = os.path.basename(executable)
        name, _ = os.path.splitext(basename)

        for key, value in {"host": name,
                           "port": int(os.environ.get("ENDPOINT_PORT", -1)),
                           "user": getpass.getuser(),
                           "connectTime": time.time(),
                           "pyblishVersion": pyblish.version,
                           "endpointVersion": version,
                           "pythonVersion": sys.version}.iteritems():

            self.context.set_data(key, value)

    def process(self, plugin_id, instance_id=None):
        return self._process_pair("process", plugin_id, instance_id)

    def repair(self, plugin_id, instance_id):
        return self._process_pair("repair", plugin_id, instance_id)

    def _process_services(self, params):
        print("Processing %s" % (params))

    def _process_pair(self, mode, plugin_id, instance_id=None):
        """Process `instance_id` with `plugin_id`

        Arguments:
            plugin_id (str): Id of plug-in to process
            instance_id (str, optional): Id of instance_id to process,
                if not passed Context is processed.

        """

        try:
            Plugin = self.plugins[plugin_id]
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

        if hasattr(Plugin, "process"):
            # New-style
            plugin = Plugin()
            self.provider.inject("context", self.context)

            if instance_id is not None:
                self.provider.inject("instance", self.context[instance_id])

            processor = self.provider.invoke
            item = plugin.process

        else:
            # Old-style
            if instance_id is None:
                item = self.context
                processor = getattr(Plugin(), "%s_context" % mode)
            else:
                item = self.context[instance_id]
                processor = getattr(Plugin(), "%s_instance" % mode)

        __start = time.time()

        try:
            processor(item)
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

    def store_results_in_context(self, result):
        results = self.context.data("results")
        if results is None:
            results = list()
            self.context.set_data("results", results)

        result = copy.deepcopy(result)
        results.append(result)


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


def current():
    """Return currently active service"""
    return EndpointService._current


def register_service(service, force=True):
    """Register service

    The service will be used by the endpoint for host communication
    and represents a host-specific layer inbetween Pyblish and Endpoint.

    Arguments:
        service (EndpointService): Service to register
        force (bool): Overwrite any existing service

    """

    if EndpointService._current is not None and force is False:
        raise ValueError("An existing service was found: %s, "
                         "use deregister_service to remove it"
                         % type(EndpointService._current).__name__)
    EndpointService._current = service()
    log.info("Registering: %s" % service)


def deregister_service(service=None):
    if service is None or service is EndpointService._current:
        EndpointService._current = None
    else:
        raise ValueError("Could not deregister service")
