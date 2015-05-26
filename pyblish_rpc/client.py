"""Client communication library

This library is responsible for intercepting and processing
both incoming and outgoing communication. Incoming communication
is parsed into "Object Proxys" (see below) whereas outgoing
communication is serialised back into its original JSON.

"""

import socket
import httplib
import xmlrpclib

import pyblish.api


class Proxy(object):
    """Wrap ServerProxy with logic and object proxies

    The proxy mirrors the remote interface to provide an
    as-similar experience as possible.

    ..note:: This is a singleton.

    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Proxy, cls).__new__(cls)
            cls._instance.__init(*args, **kwargs)
        return cls._instance

    def __getattr__(self, attr):
        """Any call not overloaded, simply pass it on"""
        return getattr(self._proxy, attr)

    def __init(self, port, user=None, password=None, timeout=0.5):
        transport = TimeoutTransport()
        transport.set_timeout(timeout)

        self._proxy = xmlrpclib.ServerProxy(
            "http://{auth}127.0.0.1:{port}/pyblish".format(
                port=port,
                auth=("{user}:{pwd}@".format(
                    user=user, pwd=password)
                ) if user else ""),
            allow_none=True,
            transport=transport)

    def ping(self):
        """Convert Fault to True/False"""
        try:
            self._proxy.ping()
        except (socket.timeout, socket.error):
            return False
        return True

    def process(self, plugin, context, instance=None):
        print plugin, context, instance
        result = self._proxy.process(
            plugin.to_json(),
            context.to_json(),
            instance.to_json() if instance else None)
        print "Result: %s" % result
        return {"success": True, "error": None}

    def repair(self, plugin, context, instance=None):
        return self._proxy.repair(
            plugin.to_json(),
            context.to_json(),
            instance.to_json() if instance else None)

    def context(self):
        context = ContextProxy.from_json(self._proxy.context())
        return context

    def discover(self):
        plugins = [PluginProxy.from_json(plugin)
                   for plugin in self._proxy.discover()]
        return plugins


class HttpWithTimeout(httplib.HTTP):
    def __init__(self, host="", port=None, strict=None, timeout=5.0):
        self._setup(self._connection_class(
            host,
            port if port != 0 else None,
            strict,
            timeout=timeout)
        )

    def getresponse(self, *args, **kw):
        return self._conn.getresponse(*args, **kw)


class TimeoutTransport(xmlrpclib.Transport):
    timeout = 10

    def set_timeout(self, timeout):
        self.timeout = timeout

    def make_connection(self, host):
        h = HttpWithTimeout(host, timeout=self.timeout)
        return h


# Object Proxies


class ContextProxy(list):
    """Context Proxy

    Given a JSON-representation of a Context, emulate its interface.

    """

    @classmethod
    def from_json(cls, context):
        self = cls()
        self[:] = [InstanceProxy.from_json(i) for i in context["children"]]
        self._data = context.pop("data")
        self._data["pyblishClientVersion"] = pyblish.api.version
        return self

    def to_json(self):
        return {
            "children": list(self),
            "data": self._data
        }

    def data(self, key, default=None):
        return self._data.get(key, default)

    def set_data(self, key, value):
        self._data[key] = value


class InstanceProxy(object):
    """Instance Proxy

    Given a JSON-representation of an Instance, emulate its interface.

    """

    def __str__(self):
        return self.name

    def __repr__(self):
        return u"%s.%s(%r)" % (__name__, type(self).__name__, self.__str__())

    @classmethod
    def from_json(cls, json):
        self = cls()
        copy = json.copy()
        copy["_data"] = copy.pop("data")
        self.__dict__.update(copy)
        return self

    def to_json(self):
        return {
            "name": self.name,
            "id": self.id,
            "data": self._data,
            "children": self.children,
        }

    def data(self, key, default=None):
        return self._data.get(key, default)


class PluginProxy(object):
    """Plug-in Proxy

    Given a JSON-representation of an Plug-in, emulate its interface.

    """

    def __str__(self):
        return type(self).__name__

    def __repr__(self):
        return u"%s.%s(%r)" % (__name__, type(self).__name__, self.__str__())

    @classmethod
    def from_json(cls, plugin):
        """Build PluginProxy object from incoming dictionary

        Emulate a plug-in by providing access to attributes
        in the same way they are accessed using the remote object.
        This allows for it to be used by members of :mod:`pyblish.logic`.

        """

        attributes = {
            "order": plugin["data"]["order"],
            "families": plugin["data"]["families"],
            "optional": plugin["data"]["optional"],
        }

        name = plugin["name"] + "Proxy"
        self = type(name, (cls,), attributes)()
        self.__dict__.update(plugin)

        return self

    def to_json(self):
        return self.__dict__.copy()
