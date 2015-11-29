import dslink
import random
from twisted.internet import reactor

from phue import Bridge
from rgb_cie import Converter


b = Bridge('192.168.86.188')
b.connect()
lights = b.get_light_objects('id')
for l in b.lights:
    print(l)

converter = Converter()
lights[1].xy = converter.hexToCIE1931('ff0000');

class TemplateDSLink(dslink.DSLink):
    def __init__(self, config):
        self.random = random.Random()
        self.speed = 0.1
        dslink.DSLink.__init__(self, config)

    def start(self):
        self.profile_manager.create_profile("set_speed")
        self.profile_manager.register_callback("set_speed", self.set_speed)

        self.profile_manager.create_profile("set_on")
        self.profile_manager.register_callback("set_on", self.set_on)

        self.profile_manager.create_profile("set_hex")
        self.profile_manager.register_callback("set_hex", self.set_hex)

        reactor.callLater(0.1, self.poll)

    def get_default_nodes(self):
        root = self.get_root_node()

        set_speed = dslink.Node("set_speed", root)
        set_speed.set_display_name("Set Poll Rate");
        set_speed.set_parameters([
            {
                "name": "Speed",
                "type": "number",
                "value": 1
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

        for l in b.lights:
            node = dslink.Node("light_" + str(l.light_id), root)
            node.set_display_name(l.name);
            root.add_child(node)

            set_on = dslink.Node("set_on", root)
            set_on.set_display_name("@set");
            set_on.set_parameters([
                {
                    "name": "value",
                    "type": "boolean",
                    "value": False
                }
            ])
            set_on.set_columns([
                {
                    "name": "Success",
                    "type": "bool",
                    "value": False
                }
            ])
            set_on.set_profile("set_on")
            set_on.set_invokable("write")

            node.add_child(set_on)

        return root

    def set_speed(self, parameters):
        #self.speed = int(parameters.params["Speed"])
        try:
            lights[1].hue = parameters.params["Speed"]
        except Exception, e:
            print "Exception: %s" % e

        return [
            [
                True
            ]
        ]

    def set_on(self, parameters):
        try:
            lights[1].hue = parameters.params["Speed"]
        except Exception, e:
            print "Exception: %s" % e

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
