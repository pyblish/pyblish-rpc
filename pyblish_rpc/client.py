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
import pyblish.plugin


class Proxy(object):
    """Wrap ServerProxy with logic and object proxies

    The proxy mirrors the remote interface to provide an
    as-similar experience as possible.

    """

    _instance = None

    def __getattr__(self, attr):
        """Any call not overloaded, simply pass it on"""
        return getattr(self._proxy, attr)

    def __init__(self, port, user=None, password=None):
        transport = TimeoutTransport()

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
        return self._proxy.process(
            plugin.to_json(),
            instance.to_json() if instance else None)

    def repair(self, plugin, context, instance=None):
        return self._proxy.repair(
            plugin.to_json(),
            instance.to_json() if instance else None)

    def context(self):
        return ContextProxy.from_json(self._proxy.context())

    def discover(self):
        return [PluginProxy.from_json(plugin)
                for plugin in self._proxy.discover()]


class TimeoutTransport(xmlrpclib.Transport):
    """Some requests may take a very long time, and that is ok"""
    timeout = 60 * 60  # 1 hour

    def make_connection(self, host):
        h = HttpWithTimeout(host, timeout=self.timeout)
        return h


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


class InstanceProxy(list):
    """Instance Proxy

    Given a JSON-representation of an Instance, emulate its interface.

    """

    def __str__(self):
        return self.name

    def __repr__(self):
        return u"%s.%s(%r)" % (__name__, type(self).__name__, self.__str__())

    @classmethod
    def from_json(cls, instance):
        self = cls()
        copy = instance.copy()
        copy["_data"] = copy.pop("data")
        self.__dict__.update(copy)
        self[:] = [i for i in instance["children"]]
        return self

    def to_json(self):
        return {
            "name": self.name,
            "id": self.id,
            "data": self._data,
            "children": list(self),
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

        process = None
        repair = None

        # Emulate function
        for name in ("process", "repair"):
            args = ", ".join(plugin["process"]["args"])
            func = "def {name}({args}): pass".format(name=name,
                                                     args=args)
            exec(func)

        name = plugin["name"] + "Proxy"
        cls = type(name, (cls,), plugin)

        for member in ("order",
                       "families",
                       "optional",
                       "requires",
                       "version"):
            setattr(cls, member, cls.data[member])

        cls.process = process
        cls.repair = repair

        cls.__orig__ = plugin

        return cls

    @classmethod
    def to_json(cls):
        return cls.__orig__.copy()
