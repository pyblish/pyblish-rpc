import os

import pyblish.logic
import pyblish_rpc.client

os.environ["USERNAME"] = "marcus"
os.environ["PASSWORD"] = "pass"


class Controller(object):
    def __init__(self, port):
        self.api = pyblish_rpc.client.Proxy(port)
        self._errors = list()

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
            results.append(result)
        return results


if __name__ == '__main__':
    import pyblish_rpc.server
    # import threading

    # thread = threading.Thread(
    #     target=pyblish_rpc.server.start_debug_server,
    #     kwargs={"port": 6000})
    # thread.daemon = True
    # thread.start()

    c = Controller(6000)
    # c.api.process({}, c.api.process, {})
    c.reset()
    # c.publish()

    print c.api.context()
    print c.api.stats()
