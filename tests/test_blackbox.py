"""Assume behaviour on part of the core Pyblish library"""

import sys
import threading

import pyblish_rpc.server
import pyblish_rpc.client
import pyblish.logic

import pyblish.api

from nose.tools import *

thread = None
server = None
client = None
port = 6000

self = sys.modules[__name__]


def setup():
    import pyblish_rpc.server
    import pyblish_rpc.service

    service = pyblish_rpc.service.MockRpcService(delay=0.001)
    self.server = pyblish_rpc.server._server(self.port, service)

    self.thread = threading.Thread(target=self.server.serve_forever)

    self.thread.daemon = True
    self.thread.start()

    self.client = pyblish_rpc.client.Proxy(port)


def teardown():
    self.server.shutdown()
    self.thread.join(timeout=10)
    assert not thread.isAlive()


def setup_empty():
    pyblish.api.config["paths"][:] = []
    pyblish.api.deregister_all_paths()
    pyblish.api.deregister_all_plugins()
    pyblish.api.deregister_all_services()

    self.client.reset()


class Controller(object):
    def __init__(self, port):
        self.api = pyblish_rpc.client.Proxy(port)

    def reset(self):
        results = list()
        plugins = [p for p in self.api.discover()
                   if p.order < 1]

        for result in pyblish.logic.process(
                plugins=plugins,
                process=self.api.process,
                context=self.api.context()):
            results.append(result)
        return results

    def publish(self):
        results = list()
        plugins = [p for p in self.api.discover()
                   if p.order >= 1]

        for result in pyblish.logic.process(
                plugins=plugins,
                process=self.api.process,
                context=self.api.context()):

            if isinstance(result, pyblish.logic.TestFailed):
                print("Stopped due to: %s" % result)
                break

            if isinstance(result, Exception):
                print("Got an exception: %s" % result)
                break

            results.append(result)
        return results


@with_setup(setup_empty)
def test_mock_client():
    """A mock client works fine"""
    count = {"#": 0}

    assert_equals(pyblish.api.registered_plugins(), [])

    class SelectInstances(pyblish.api.Selector):
        def process(self, context):
            instance = context.create_instance("MyInstance")
            instance.set_data("family", "myFamily")
            count["#"] += 1

    class ValidateInstances(pyblish.api.Validator):
        families = ["myFamily"]

        def process(self, instance):
            count["#"] += 1
            assert False

    pyblish.api.register_plugin(SelectInstances)
    pyblish.api.register_plugin(ValidateInstances)

    c = Controller(port)
    c.reset()

    plugins = c.api.discover()
    assert "SelectInstances" in [p.name for p in plugins]
    assert "ValidateInstances" in [p.name for p in plugins]

    c.publish()

    instance = c.api.context()[0]
    assert_equals(instance.name, "MyInstance")
    assert_equals(count["#"], 2)


@with_setup(setup_empty)
def test_logic():
    """Logic works well"""
    count = {"#": 0}

    assert_equals(pyblish.api.registered_plugins(), [])

    class RunOnce(pyblish.api.Selector):
        def process(self, context):
            print("Processing: %s" % type(self).__name__)

            for name in ("A", "B"):
                instance = context.create_instance(name)
                instance.set_data("family", "myFamily")

            count["#"] += 1

    class RunTwice(pyblish.api.Validator):
        families = ["myFamily"]

        def process(self, instance):
            print("Processing: %s" % type(self).__name__)
            count["#"] += 1
            assert False, "I was programmed to fail"

    class DontRun1(pyblish.api.Validator):
        families = ["unsupportedFamily"]

        def process(self, instance):
            print("Processing: %s" % type(self).__name__)
            count["#"] += 1

    class DontRun2(pyblish.api.Extractor):
        def process(self, context):
            print("Processing: %s" % type(self).__name__)
            count["#"] += 10

    class DontRun3(pyblish.api.Extractor):
        families = ["myFamily"]

        def process(self, instance):
            print("Processing: %s" % type(self).__name__)
            count["#"] += 100

    pyblish.api.register_plugin(RunOnce)
    pyblish.api.register_plugin(RunTwice)
    pyblish.api.register_plugin(DontRun1)
    pyblish.api.register_plugin(DontRun2)
    pyblish.api.register_plugin(DontRun3)

    proxy = pyblish_rpc.client.Proxy(port)

    test_failed = False

    for result in pyblish.logic.process(
            plugins=proxy.discover,
            process=proxy.process,
            context=proxy.context):

        if isinstance(result, pyblish.logic.TestFailed):
            print("Stopped due to: %s" % result)
            test_failed = True
            break

        if isinstance(result, Exception):
            print("Got an exception: %s" % result)
            break

    context = proxy.context()
    assert context[0].name in ["A", "B"]
    assert context[1].name in ["A", "B"]
    assert_equals(count["#"], 3)
    assert_true(test_failed)
