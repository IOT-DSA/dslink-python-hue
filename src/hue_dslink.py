import dslink
import random
from twisted.internet import reactor

from phue import Bridge
from rgb_cie import Converter

import ssdp

converter = Converter()

'''for l in b.lights:
    print(l)


lights[1].xy = converter.hexToCIE1931('ff0000');'''


class TemplateDSLink(dslink.DSLink):
    def __init__(self, config):
        self.random = random.Random()
        self.bridge = None
        self.lights = None
        dslink.DSLink.__init__(self, config)

    def start(self):
        self.profile_manager.create_profile("set_bridge")
        self.profile_manager.register_set_callback("set_bridge", self.set_bridge)

        self.profile_manager.create_profile("set_hex")
        self.profile_manager.register_callback("set_hex", self.set_hex)

        self.profile_manager.create_profile("set")
        self.profile_manager.register_set_callback("set", self.set_callback)

        bridge = self.super_root.get("/bridge")
        if bridge.value.has_value():
            self.bridge = Bridge(bridge.get_value())
            self.bridge.connect()
            self.lights = self.bridge.get_light_objects('id')
            self.create_lights()

        reactor.callLater(0.1, self.poll)

    def get_default_nodes(self):
        root = self.get_root_node()

        metric = dslink.Node("updateRate", root)
        metric.set_type("number")
        metric.set_value(1)
        root.add_child(metric)
        metric.set_profile("set_speed")
        metric.set_config("$writable", "write")

        metric = dslink.Node("bridge", root)
        metric.set_type("string")
        root.add_child(metric)
        metric.set_profile("set_bridge")
        metric.set_config("$writable", "write")

        return root

    def create_lights(self):
        root = self.super_root
        if self.bridge is None:
            return

        for l in self.bridge.lights:
            node = dslink.Node("light_" + str(l.light_id), root)
            node.set_transient(True);
            node.set_display_name(l.name)
            root.add_child(node)

            set_hex = dslink.Node("set_hex", node)
            set_hex.set_display_name("Set Color");
            set_hex.set_parameters([
                {
                    "name": "value",
                    "type": "string",
                    "placeholder": "#ffffff"
                }
            ])
            set_hex.set_columns([
                {
                    "name": "Success",
                    "type": "bool",
                    "value": False
                }
            ])
            set_hex.set_profile("set_hex")
            set_hex.set_invokable("write")
            node.add_child(set_hex)

            metric = dslink.Node("hue", node)
            metric.set_type("number")
            node.add_child(metric)
            metric.set_profile("set")
            metric.set_config("$writable", "write")

            metric = dslink.Node("on", node)
            metric.set_type("bool")
            node.add_child(metric)
            metric.set_profile("set")
            metric.set_config("$writable", "write")

            metric = dslink.Node("brightness", node)
            metric.set_type("number")
            metric.set_profile("set")
            metric.set_config("$writable", "write")
            node.add_child(metric)

            metric = dslink.Node("saturation", node)
            metric.set_type("number")
            metric.set_profile("set")
            metric.set_config("$writable", "write")
            node.add_child(metric)

            metric = dslink.Node("transitiontime", node)
            metric.set_type("number")
            metric.set_profile("set")
            metric.set_config("$writable", "write")
            node.add_child(metric)

            metric = dslink.Node("colormode", node)
            metric.set_type(dslink.Value.build_enum(["hs", "xy", "ct"]))
            metric.set_profile("set")
            metric.set_config("$writable", "write")
            node.add_child(metric)

            metric = dslink.Node("alert", node)
            metric.set_type(dslink.Value.build_enum(["select", "lselect", "none"]))
            metric.set_profile("set")
            metric.set_config("$writable", "write")
            node.add_child(metric)

            metric = dslink.Node("effect", node)
            metric.set_type(dslink.Value.build_enum(["none", "colorloop"]))
            metric.set_profile("set")
            metric.set_config("$writable", "write")
            node.add_child(metric)

        return root

    def set_bridge(self, parameters):
        self.bridge = Bridge(parameters.value)
        self.bridge.connect()
        self.lights = self.bridge.get_light_objects('id')

        self.create_lights()

        return [
            [
                True
            ]
        ]

    def set_hex(self, parameters):
        try:
            id = int(parameters.node.parent.name.split("_")[1])
            val = parameters.params["value"]
            val = val.replace("#", "")
            self.lights[id].xy = converter.hexToCIE1931(val)
        except Exception, e:
            print "Exception: %s" % e

        return [
            [
                True
            ]
        ]

    def set_callback(self, parameters):
        print(parameters.node.path)
        print(parameters.value)

        try:
            id = int(parameters.node.parent.name.split("_")[1])
            val = parameters.value

            metric = parameters.node.name
            light = self.lights[id]

            setattr(light, metric, val)
        except Exception, e:
            print "Exception: %s" % e

        return [
            [
                True
            ]
        ]

    def poll(self):
        # Poll data here and set the values

        try:
            if self.bridge is not None:
                for l in self.bridge.lights:
                    id = int(l.light_id)
                    cur_node = "/light_" + str(l.light_id)
                    self.super_root.get(cur_node + "/hue").set_value(self.lights[id].hue)
                    self.super_root.get(cur_node + "/on").set_value(self.lights[id].on)
                    self.super_root.get(cur_node + "/brightness").set_value(self.lights[id].brightness)

                    self.super_root.get(cur_node + "/saturation").set_value(self.lights[id].saturation)
                    self.super_root.get(cur_node + "/transitiontime").set_value(self.lights[id].transitiontime)

                    self.super_root.get(cur_node + "/colormode").set_value(self.lights[id].colormode)
                    self.super_root.get(cur_node + "/alert").set_value(self.lights[id].alert)

                    '''light_xy = lights[id].xy
                    print(float(lights[id].brightness))
                    hex = converter.CIE1931ToHex(light_xy[0], light_xy[1], bri=0.5)
                    self.super_root.get(cur_node+"/hex").set_value("#"+hex)'''

        except Exception, e:
            print "Poll Loop Exception: %s" % e

        time = self.super_root.get("/updateRate")
        if time.value.has_value():
            reactor.callLater(time.get_value(), self.poll)
        else:
            reactor.callLater(1, self.poll)


if __name__ == "__main__":
    TemplateDSLink(dslink.Configuration(name="PhilipsHue", responder=True))
