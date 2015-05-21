import pyblish.api as pyblish


class ValidateSmurf(pyblish.Validator):
    def process(self, instance):
        assert instance.data("invalid") is False
