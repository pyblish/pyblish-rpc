import pyblish.api


@pyblish.api.log
class SelectInstances(pyblish.api.Selector):
    """Select debugging instances

    These instances are part of the evil plan to destroy the world.
    Be weary, be vigilant, be sexy.

    """

    hosts = ["python"]

    def process_context(self, context):
        self.log.info("Selecting instances..")

        for name in instances:
            instance = context.create_instance(name=name)

            self.log.info("Selecting: %s" % name)

            instance._data = {
                "publish": True,
                "family": "napoleon.animation.cache",
                "identifier": "napoleon.instance",
                "minWidth": 800,
                "assetSource": "/server/assets/Peter",
                "destination": "/server/published/assets",
            }

            if name == "Peter01":
                instance.set_data("publish", False)
                instance.set_data("family", "napoleon.asset.rig")

            for node in ["node1", "node2", "node3"]:
                instance.append(node)


@pyblish.api.log
class SelectInstancesFailure(pyblish.api.Selector):
    """Select some instances, but fail before adding anything to the context.

    That's right. I'm programmed to fail. Try me.

    """

    hosts = ["python"]

    def process_context(self, context):
        self.log.warning("I'm about to fail")
        raise pyblish.api.SelectionError("I was programmed to fail")


@pyblish.api.log
class SelectInstanceAndProcess(pyblish.api.Selector):
    """Select an instance, and also process it.

    Not sure why this would be necessary, but I'd imagine the need
    coming up eventually.

    If this plug-in isn't logging information about which instance
    it processes, something's wrong.

    """

    hosts = ["python"]
    families = ["napoleon.asset.rig"]

    def process_context(self, context):
        self.log.info("Selecting additional instance \"Extra1\"")
        instance = context.create_instance("Extra1")
        instance.set_data("family", "napoleon.asset.rig")

    def process_instance(self, instance):
        self.log.info("Processing my own instance: %s" % instance)


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

    families = ["napoleon.animation.cache"]
    hosts = ["*"]
    version = (0, 0, 1)

    def process_instance(self, instance):
        self.log.info("Validating the namespace of %s" % instance.data("name"))
        self.log.info("""And here's another message, quite long, in fact it's
too long to be displayed in a single row of text.
But that's how we roll down here. It's got \nnew lines\nas well.

- And lists
- And more lists

        """)


@pyblish.api.log
class ValidateContext(pyblish.api.Validator):
    def process_context(self, context):
        self.log.info("Processing context..")


@pyblish.api.log
class ValidateContextFailure(pyblish.api.Validator):
    optional = True

    def process_context(self, context):
        self.log.info("About to fail..")
        raise pyblish.api.ValidationError("""I was programmed to fail

The reason I failed was because the sun was not aligned with the tides,
and the moon is gray; not yellow. Try again when the moon is yellow.""")


@pyblish.api.log
class Validator1(pyblish.api.Validator):
    """Test of the order attribute"""
    order = pyblish.api.Validator.order + 0.1

    def process_instance(self, instance):
        pass


@pyblish.api.log
class Validator2(pyblish.api.Validator):
    order = pyblish.api.Validator.order + 0.2

    def process_instance(self, instance):
        pass


@pyblish.api.log
class Validator3(pyblish.api.Validator):
    order = pyblish.api.Validator.order + 0.3

    def process_instance(self, instance):
        pass


@pyblish.api.log
class ValidateFailureMock(pyblish.api.Validator):
    """Plug-in that always fails"""
    families = ["*"]
    hosts = ["*"]
    version = (0, 0, 1)
    optional = True
    order = pyblish.api.Validator.order + 0.1

    def process_instance(self, instance):
        if instance.name == "Richard05":
            self.log.debug("e = mc^2")
            self.log.info("About to fail..")
            self.log.warning("Failing.. soooon..")
            self.log.critical("Ok, you're done.")
            raise ValueError("""ValidateFailureMock was destined to fail..

Here's some extended information about what went wrong.

It has quite the long string associated with it, including
a few newlines and a list.

- Item 1
- Item 2

""")


@pyblish.api.log
class ValidateIsIncompatible(pyblish.api.Validator):
    """This plug-in should never appear.."""
    hosts = ["*"]
    version = (0, 0, 1)
    optional = True


@pyblish.api.log
class ValidateWithRepair(pyblish.api.Validator):
    """A validator with repair functionality"""
    hosts = ["*"]
    version = (0, 0, 1)
    optional = True

    def process_instance(self, instance):
        if instance.name == "Richard05":
            raise pyblish.api.ValidationError(
                "%s is invalid, try repairing it!" % instance.name)

    def repair_instance(self, instance):
        self.log.info("Attempting to repair..")
        self.log.info("Success!")


@pyblish.api.log
class ValidateWithRepairFailure(pyblish.api.Validator):
    """A validator with repair functionality that fails"""
    hosts = ["*"]
    version = (0, 0, 1)
    optional = True

    def process_instance(self, instance):
        if instance.name == "Richard05":
            raise pyblish.api.ValidationError(
                "%s is invalid, try repairing it!" % instance.name)

    def repair_instance(self, instance):
        self.log.info("Attempting to repair..")

        if instance.name == "Richard05":
            raise pyblish.api.ValidationError("Could not repair due to X")


@pyblish.api.log
class ValidateWithRepairContext(pyblish.api.Validator):
    """A validator with repair functionality that fails"""
    hosts = ["*"]
    version = (0, 0, 1)
    optional = True

    def process_context(self, context):
        raise pyblish.api.ValidationError(
            "Could not validate context, try repairing it")

    def repair_context(self, context):
        self.log.info("Attempting to repair..")
        raise pyblish.api.ValidationError("Could not repair")


@pyblish.api.log
class ExtractAsMa(pyblish.api.Extractor):
    """Extract contents of each instance into .ma

    Serialise scene using Maya's own facilities and then put
    it on the hard-disk. Once complete, this plug-in relies
    on a Conformer to put it in it's final location, as this
    extractor merely positions it in the users local temp-
    directory.

    """

    hosts = ["*"]
    version = (0, 0, 1)
    optional = True

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


instances = [
    "Peter01",
    "Richard05",
    "Steven11",
    "Piraya12",
    "Marcus",
    "Extra1"
]

plugins = [
    SelectInstances,
    SelectInstancesFailure,
    SelectInstanceAndProcess,
    ValidateFailureMock,
    ValidateNamespace,
    ValidateIsIncompatible,
    ValidateContext,
    ValidateContextFailure,
    Validator1,
    Validator2,
    Validator3,
    ValidateWithRepair,
    ValidateWithRepairFailure,
    ValidateWithRepairContext,
    ExtractAsMa,
    ConformAsset,
]
