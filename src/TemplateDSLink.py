import dslink
import random
from twisted.internet import reactor


class TemplateDSLink(dslink.DSLink):
    def __init__(self, config):
        self.random = random.Random()
        self.speed = 0.1
        dslink.DSLink.__init__(self, config)

    def start(self):
        self.profile_manager.create_profile("set_speed")
        self.profile_manager.register_callback("set_speed", self.set_speed)

        reactor.callLater(0.1, self.poll)

    def get_default_nodes(self):
        root = self.get_root_node()

        set_speed = dslink.Node("set_speed", root)
        set_speed.set_parameters([
            {
                "name": "Speed",
                "type": "number",
                "value": 0.1
            }
        ])
        set_speed.set_columns([
            {
                "name": "Success",
                "type": "bool",
                "value": False
            }
        ])
        set_speed.set_profile("set_speed")
        set_speed.set_invokable("config")

        test_one = dslink.Node("test_one", root)
        test_one.set_type("number")
        test_one.set_value(0)

        test_two = dslink.Node("test_two", root)
        test_two.set_type("number")
        test_two.set_value(0)

        root.add_child(test_one)
        root.add_child(test_two)
        root.add_child(set_speed)

        return root

    def set_speed(self, parameters):
        self.speed = int(parameters.params["Speed"])

        return [
            [
                True
            ]
        ]

    def poll(self):
        # Poll data here and set the values
        self.super_root.get("/test_one").set_value(self.random.random())
        self.super_root.get("/test_two").set_value(self.random.random())

        reactor.callLater(self.speed, self.poll)

if __name__ == "__main__":
    TemplateDSLink(dslink.Configuration(name="template", responder=True))
