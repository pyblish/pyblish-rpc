import pyblish.api as pyblish
import pyblish_xmlrpc


class ExtractSmurf(pyblish.Extractor):
    def process(self, instance):
        if not hasattr(pyblish_xmlrpc, "_data"):
            pyblish_xmlrpc._data = list()
        pyblish_xmlrpc._data.append(instance.data("value"))
