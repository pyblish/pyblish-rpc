import pyblish.api


@pyblish.api.log
class SelectInstances(pyblish.api.Selector):
    """Select debugging instances

    These instances are part of the evil plan to destroy the world.
    Be weary, be vigilant, be sexy.

    """

    def process_context(self, context):
        self.log.info("Selecting instances..")

        for instance in instances[:-1]:
            name, data = instance["name"], instance["data"]
            self.log.info("Selecting: %s" % name)
            instance = context.create_instance(name)

            for key, value in data.iteritems():
                instance.set_data(key, value)


@pyblish.api.log
class SelectDiInstances(pyblish.api.Selector):
    """Select DI instances"""

    name = "Select Dependency Instances"

    def process(self, context):
        name, data = instances[-1]["name"], instances[-1]["data"]
        self.log.info("Selecting: %s" % name)
        instance = context.create_instance(name)

        for key, value in data.iteritems():
            instance.set_data(key, value)


@pyblish.api.log
class SelectInstancesFailure(pyblish.api.Selector):
    """Select some instances, but fail before adding anything to the context.

    That's right. I'm programmed to fail. Try me.

    """

    __fail__ = True

    def process_context(self, context):
        self.log.warning("I'm about to fail")
        assert False, "I was programmed to fail"


@pyblish.api.log
class SelectInstances2(pyblish.api.Selector):
    def process(self, context):
        self.log.warning("I'm good")


@pyblish.api.log
class ValidateNamespace(pyblish.api.Validator):
    """Namespaces must be orange

    In case a namespace is not orange, report immediately to
    your officer in charge, ask for a refund, do a backflip.

    This has been an example of:

    - A long doc-string
    - With a list
    - And plenty of newlines and tabs.

    """

    families = ["B"]

    def process(self, instance):
        self.log.info("Validating the namespace of %s" % instance.data("name"))
        self.log.info("""And here's another message, quite long, in fact it's
too long to be displayed in a single row of text.
But that's how we roll down here. It's got \nnew lines\nas well.

- And lists
- And more lists

        """)


@pyblish.api.log
class ValidateContext(pyblish.api.Validator):
    families = ["A", "B"]

    def process_context(self, context):
        self.log.info("Processing context..")


@pyblish.api.log
class ValidateContextFailure(pyblish.api.Validator):
    optional = True
    families = ["C"]
    __fail__ = True

    def process_context(self, context):
        self.log.info("About to fail..")
        assert False, """I was programmed to fail

The reason I failed was because the sun was not aligned with the tides,
and the moon is gray; not yellow. Try again when the moon is yellow."""


@pyblish.api.log
class Validator1(pyblish.api.Validator):
    """Test of the order attribute"""
    order = pyblish.api.Validator.order + 0.1
    families = ["A"]

    def process_instance(self, instance):
        pass


@pyblish.api.log
class Validator2(pyblish.api.Validator):
    order = pyblish.api.Validator.order + 0.2
    families = ["B"]

    def process_instance(self, instance):
        pass


@pyblish.api.log
class Validator3(pyblish.api.Validator):
    order = pyblish.api.Validator.order + 0.3
    families = ["B"]

    def process_instance(self, instance):
        pass


@pyblish.api.log
class ValidateFailureMock(pyblish.api.Validator):
    """Plug-in that always fails"""
    optional = True
    order = pyblish.api.Validator.order + 0.1
    families = ["C"]
    __fail__ = True

    def process_instance(self, instance):
        self.log.debug("e = mc^2")
        self.log.info("About to fail..")
        self.log.warning("Failing.. soooon..")
        self.log.critical("Ok, you're done.")
        assert False, """ValidateFailureMock was destined to fail..

Here's some extended information about what went wrong.

It has quite the long string associated with it, including
a few newlines and a list.

- Item 1
- Item 2

"""


@pyblish.api.log
class ValidateIsIncompatible(pyblish.api.Validator):
    """This plug-in should never appear.."""
    requires = False  # This is invalid


@pyblish.api.log
class ValidateWithRepair(pyblish.api.Validator):
    """A validator with repair functionality"""
    optional = True
    families = ["C"]
    __fail__ = True

    def process_instance(self, instance):
        assert False, "%s is invalid, try repairing it!" % instance.name

    def repair_instance(self, instance):
        self.log.info("Attempting to repair..")
        self.log.info("Success!")


@pyblish.api.log
class ValidateWithRepairFailure(pyblish.api.Validator):
    """A validator with repair functionality that fails"""
    optional = True
    families = ["C"]
    __fail__ = True

    def process_instance(self, instance):
        assert False, "%s is invalid, try repairing it!" % instance.name

    def repair_instance(self, instance):
        self.log.info("Attempting to repair..")
        assert False, "Could not repair due to X"


@pyblish.api.log
class ValidateWithVeryVeryVeryLongLongNaaaaame(pyblish.api.Validator):
    """A validator with repair functionality that fails"""
    families = ["A"]


@pyblish.api.log
class ValidateWithRepairContext(pyblish.api.Validator):
    """A validator with repair functionality that fails"""
    optional = True
    families = ["C"]
    __fail__ = True

    def process_context(self, context):
        assert False, "Could not validate context, try repairing it"

    def repair_context(self, context):
        self.log.info("Attempting to repair..")
        assert False, "Could not repair"


@pyblish.api.log
class ExtractAsMa(pyblish.api.Extractor):
    """Extract contents of each instance into .ma

    Serialise scene using Maya's own facilities and then put
    it on the hard-disk. Once complete, this plug-in relies
    on a Conformer to put it in it's final location, as this
    extractor merely positions it in the users local temp-
    directory.

    """

    optional = True
    __expected__ = {
        "logCount": ">=4"
    }

    def process_instance(self, instance):
        self.log.info("About to extract scene to .ma..")
        self.log.info("Extraction went well, now verifying the data..")

        if instance.name == "Richard05":
            self.log.warning("You're almost running out of disk space!")

        self.log.info("About to finish up")
        self.log.info("Finished successfully")


@pyblish.api.log
class ConformAsset(pyblish.api.Conformer):
    """Conform the world

    Step 1: Conform all humans and Step 2: Conform all non-humans.
    Once conforming has completed, rinse and repeat.

    """

    optional = True

    def process_instance(self, instance):
        self.log.info("About to conform all humans..")

        if instance.name == "Richard05":
            self.log.warning("Richard05 is a conformist!")

        self.log.info("About to conform all non-humans..")
        self.log.info("Conformed Successfully")


@pyblish.api.log
class ValidateInstancesDI(pyblish.api.Validator):
    """Validate using the DI interface"""
    families = ["diFamily"]

    def process(self, instance):
        self.log.info("Validating %s.." % instance.data("name"))


@pyblish.api.log
class ValidateDIWithRepair(pyblish.api.Validator):
    families = ["diFamily"]
    optional = True
    __fail__ = True

    def process(self, instance):
        assert False, "I was programmed to fail, for repair"

    def repair(self, instance):
        self.log.info("Repairing %s" % instance.data("name"))


@pyblish.api.log
class ExtractInstancesDI(pyblish.api.Extractor):
    """Extract using the DI interface"""
    families = ["diFamily"]

    def process(self, instance):
        self.log.info("Extracting %s.." % instance.data("name"))


@pyblish.api.log
class ValidateWithLabel(pyblish.api.Validator):
    """Validate using the DI interface"""
    label = "Validate with Label"


@pyblish.api.log
class ValidateWithLongLabel(pyblish.api.Validator):
    """Validate using the DI interface"""
    label = "Validate with Loooooooooooooooooooooong Label"


@pyblish.api.log
class SimplePlugin1(pyblish.api.Plugin):
    """Validate using the simple-plugin interface"""

    def process(self):
        self.log.info("I'm a simple plug-in, only processed once")


@pyblish.api.log
class SimplePlugin2(pyblish.api.Plugin):
    """Validate using the simple-plugin interface

    It doesn't have an order, and will likely end up *before* all
    other plug-ins. (due to how sorted([1, 2, 3, None]) works)

    """

    def process(self, context):
        self.log.info("Processing the context, simply: %s" % context)


@pyblish.api.log
class SimplePlugin3(pyblish.api.Plugin):
    """Simply process every instance"""

    def process(self, instance):
        self.log.info("Processing the instance, simply: %s" % instance)



instances = [
    {
        "name": "Peter01",
        "data": {
            "family": "A",
            "publish": False
        }
    },
    {
        "name": "Richard05",
        "data": {
            "family": "A",
        }
    },
    {
        "name": "Steven11",
        "data": {
            "family": "B",
        }
    },
    {
        "name": "Piraya12",
        "data": {
            "family": "B",
        }
    },
    {
        "name": "Marcus",
        "data": {
            "family": "C",
        }
    },
    {
        "name": "Extra1",
        "data": {
            "family": "C",
        }
    },
    {
        "name": "DependencyInstance",
        "data": {
            "family": "diFamily"
        }
    },
    {
        "name": "NoFamily",
        "data": {}
    }
]

plugins = [
    SelectInstances,
    SelectInstances2,
    SelectDiInstances,
    SelectInstancesFailure,
    ValidateFailureMock,
    ValidateNamespace,
    ValidateIsIncompatible,
    ValidateWithVeryVeryVeryLongLongNaaaaame,
    ValidateContext,
    ValidateContextFailure,
    Validator1,
    Validator2,
    Validator3,
    ValidateWithRepair,
    ValidateWithRepairFailure,
    ValidateWithRepairContext,
    ValidateWithLabel,
    ValidateWithLongLabel,
    ExtractAsMa,
    ConformAsset,

    SimplePlugin1,
    SimplePlugin2,
    SimplePlugin3,

    ValidateInstancesDI,
    ExtractInstancesDI,
    ValidateDIWithRepair,
]

pyblish.api.sort_plugins(plugins)
