import os
import sys
import json
import logging
import inspect
import traceback

import schema

log = logging.getLogger("pyblish")


def extract_traceback(exception):
    try:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        exception.traceback = traceback.extract_tb(exc_traceback)[-1]

    except:
        pass

    finally:
        del(exc_type, exc_value, exc_traceback)


def format_result(result):
    """Serialise Result"""
    instance = None
    error = None

    if result["instance"] is not None:
        instance = format_instance(result["instance"])

    if result["error"] is not None:
        error = format_error(result["error"])

    result = {
        "success": result["success"],
        "plugin": format_plugin(result["plugin"]),
        "instance": instance,
        "error": error,
        "records": format_records(result["records"]),
        "duration": result["duration"]
    }

    schema.validate(result, "result")

    return result


def format_records(records):
    """Serialise multiple records"""
    formatted = list()
    for record_ in records:
        formatted.append(format_record(record_))
    return formatted


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

    schema.validate(record, "record")

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


def format_instance(instance):
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

    instance = {
        "name": instance.name,
        "id": instance.id,
        "children": children,
        "data": format_data(instance._data)
    }

    schema.validate(instance, "instance")

    return instance


def format_context(context):
    formatted = []

    for instance_ in context:
        formatted_instance = format_instance(instance_)
        formatted.append(formatted_instance)

    return {
        "data": format_data(context._data),
        "children": formatted
    }


def format_plugins(plugins):
    """Serialise multiple plug-in

    Returns:
        List of JSON-compatible plug-ins

    """

    formatted = []
    for plugin_ in plugins:
        formatted_plugin = format_plugin(plugin_)
        formatted.append(formatted_plugin)

    return formatted


def format_plugin(plugin):
    """Serialise `plugin`

    Attributes:
        name: Name of Python class
        id: Unique identifier
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

    # docstring = getattr(plugin, "doc", plugin.__doc__)
    docstring = inspect.getdoc(plugin)

    formatted = {
        "name": plugin.__name__,
        "id": plugin.id,
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
        },
        "process": {
            "args": inspect.getargspec(plugin.process).args,
        },
        "repair": {
            "args": inspect.getargspec(plugin.repair).args,
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

    if any(a in ("context", "instance")
           for a in inspect.getargspec(plugin.repair).args):
        formatted["data"]["hasRepair"] = True

    # Legacy abilities
    if any(func in ("repair_context", "repair_instance")
            for func in dir(plugin)):
        formatted["data"]["hasRepair"] = True

    schema.validate(formatted, "plugin")

    return formatted
