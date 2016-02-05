import logging

import pyblish.api
from pyblish_rpc import schema
from pyblish_rpc import formatting


def test_instance():
    """Formatting of instances works fine"""
    instance = pyblish.api.Instance("MyInstance")
    instance.set_data("family", "MyFamily")

    instance = formatting.format_instance(instance)
    schema.validate(instance, "instance")


def test_context():
    """Formatting of instances works fine"""
    context = pyblish.api.Context()
    instance = context.create_instance("MyInstance")
    instance.set_data("family", "MyFamily")
    context.set_data("some", "data")

    context = formatting.format_context(context)
    schema.validate(context, "context")


def test_record():
    """Formatting of records works well"""
    import logging
    record = logging.LogRecord(
        name="MyRecord",
        level=logging.DEBUG,
        pathname="",
        lineno=0,
        msg="My log message",
        args=["args1"],
        exc_info=None,
        func=None)

    record = formatting.format_record(record)
    schema.validate(record, "record")


def test_error():
    """Formatting of exceptions works well"""
    error = Exception("My message")

    error = formatting.format_error(error)
    schema.validate(error, "error")


def test_result():
    """Formatting of composite result works well"""
    class MyPlugin(pyblish.api.Selector):
        """Some docstring"""
        def process(self):
            assert False, "I was programmed to fail"

    record = logging.LogRecord(
        name="MyRecord",
        level=logging.DEBUG,
        pathname="",
        lineno=0,
        msg="My log message",
        args=["args1"],
        exc_info=None,
        func=None)

    instance = pyblish.api.Instance("MyInstance")
    instance.set_data("family", "MyFamily")
    error = Exception("My message")

    result = {
        "success": True,
        "instance": instance,
        "plugin": MyPlugin,
        "records": [record],
        "error": error,
        "duration": 0.0
    }

    result = formatting.format_result(result)
    schema.validate(result, "result")


def test_plugin():
    """Formatting of plug-ins works well"""
    class MyPlugin(pyblish.api.Selector):
        """Some docstring"""
        def process(self):
            assert False, "I was programmed to fail"

    plugin = formatting.format_plugin(MyPlugin)
    schema.validate(plugin, "plugin")

    plugin = MyPlugin()
    plugin = formatting.format_plugin(MyPlugin)
    schema.validate(plugin, "plugin")
