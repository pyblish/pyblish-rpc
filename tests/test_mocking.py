"""Test mocking plug-ins"""


import pyblish.api
import pyblish.logic
import pyblish.plugin

import pyblish_rpc.service
import pyblish_rpc.mocking

import mock


def test_plugins():
    """Trigger all plug-ins"""
    context = pyblish.api.Context()

    for plugin in pyblish_rpc.mocking.plugins:
        pyblish.plugin.process(plugin, context)


@mock.patch("pyblish.api.discover")
def test_service_discover(discover):
    """Mock service discover works well"""
    service = pyblish_rpc.service.MockRpcService(delay=1)

    # This service mocks the discovery function of Pyblish
    # to only provide mocked plug-ins.
    service.discover()
    assert not discover.called


@mock.patch("time.sleep")
def test_service_sleep(sleep):
    # Processing includes an artificial delay via time.sleep
    service = pyblish_rpc.service.MockRpcService(delay=1)
    plugins = service.discover()
    service.process(plugins[0])
    assert sleep.called
