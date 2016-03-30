"""Test mocking plug-ins"""

import pyblish.api
import pyblish.logic
import pyblish.plugin

import pyblish_rpc.service
import pyblish_rpc.mocking

import mock


@mock.patch("time.sleep")
def test_plugins(sleep):
    """Trigger all plug-ins"""
    context = pyblish.api.Context()

    for plugin, instance in pyblish.logic.Iterator(
            pyblish_rpc.mocking.plugins, context):
        print("Running %s" % plugin)
        pyblish.plugin.process(plugin, context, instance)


@mock.patch("time.sleep")
def test_service_sleep(sleep):
    # Processing includes an artificial delay via time.sleep
    service = pyblish_rpc.service.MockRpcService(delay=1)
    plugins = service.discover()
    service.process(plugins[0])
    assert sleep.called
