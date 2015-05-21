import pyblish.api as pyblish


class SelectSmurf(pyblish.Selector):
    def process(self, context):
        instance = context.create_instance("Smurf")
        instance.set_data("family", "smurfFamily")
