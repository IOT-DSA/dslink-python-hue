import dslink
import random
from twisted.internet import reactor

from phue import Bridge, PhueRegistrationException
from rgb_cie import Converter

converter = Converter()

'''for l in b.lights:
    print(l)


lights[1].xy = converter.hexToCIE1931('ff0000')'''


class TemplateDSLink(dslink.DSLink):
    def __init__(self, config):
        self.random = random.Random()
        self.bridges = {}
        dslink.DSLink.__init__(self, config)

    def start(self):
        self.responder.profile_manager.create_profile("add_bridge")
        self.responder.profile_manager.register_callback("add_bridge", self.create_bridge_action)

        self.responder.profile_manager.create_profile("edit_bridge")
        self.responder.profile_manager.register_callback("edit_bridge", self.edit_bridge)

        self.responder.profile_manager.create_profile("remove_bridge")
        self.responder.profile_manager.register_callback("remove_bridge", self.remove_bridge)

        self.responder.profile_manager.create_profile("set_hex")
        self.responder.profile_manager.register_callback("set_hex", self.set_hex)

        self.responder.profile_manager.create_profile("set")
        self.responder.profile_manager.register_set_callback("set", self.set_callback)

        self.responder.profile_manager.create_profile("reconnect")
        self.responder.profile_manager.register_set_callback("reconnect", self.reconnect)

        for child_name in self.responder.super_root.children:
            child = self.responder.super_root.children[child_name]
            if "@type" in child.attributes and child.attributes["@type"] == "bridge" and "@host" in child.attributes:
                try:
                    self.bridges[child_name] = Bridge(child.attributes["@host"])
                    self.bridges[child_name].connect()
                    self.create_lights(child)
                    child.get("/status").set_value("Connected")
                except PhueRegistrationException:
                    child.get("/status").set_value("Not Registered")

        reactor.callLater(0.1, self.poll)

    def get_default_nodes(self, root):
        metric = dslink.Node("updateRate", root)
        metric.set_display_name("Update Rate")
        metric.set_type("number")
        metric.set_value(1)
        root.add_child(metric)
        metric.set_profile("set_speed")
        metric.set_config("$writable", "write")

        metric = dslink.Node("add_bridge", root)
        metric.set_profile("add_bridge")
        metric.set_display_name("Add Bridge")
        metric.set_invokable(dslink.Permission.CONFIG)
        metric.set_parameters([
            {
                "name": "Bridge Name",
                "type": "string"
            },
            {
                "name": "Host",
                "type": "string"
            }
        ])
        metric.set_columns([
            {
                "name": "Success",
                "type": "bool"
            }
        ])
        root.add_child(metric)

        return root

    def create_lights(self, bridge):
        if self.bridges[bridge.name] is None:
            print("Bridge is None")
            return

        for id in self.bridges[bridge.name].get_light_objects("id"):
            l = self.bridges[bridge.name].get_light_objects("id")[id]
            node = dslink.Node("light_" + str(id), bridge)
            node.set_transient(True)
            node.set_display_name(l.name)
            bridge.add_child(node)

            set_hex = dslink.Node("set_hex", node)
            set_hex.set_display_name("Set Color")
            set_hex.set_parameters([
                {
                    "name": "value",
                    "type": "string",
                    "editor": "color",
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

        return bridge

    def create_bridge_action(self, parameters):
        name = str(parameters[1]["Bridge Name"])
        host = str(parameters[1]["Host"])
        self.create_bridge(name, host)

    def create_bridge(self, bridge_name, host):
        bridge_node = dslink.Node(bridge_name, self.responder.super_root)
        bridge_node.set_attribute("@type", "bridge")
        bridge_node.set_attribute("@host", host)

        reconnect = dslink.Node("reconnect", bridge_node)
        reconnect.set_display_name("Reconnect")
        reconnect.set_profile("reconnect")
        reconnect.set_invokable("config")

        edit_bridge = dslink.Node("editBridge", bridge_node)
        edit_bridge.set_display_name("Edit Bridge")
        edit_bridge.set_profile("edit_bridge")
        edit_bridge.set_parameters([
            {
                "name": "Bridge Name",
                "type": "string",
                "default": bridge_name
            },
            {
                "name": "Host",
                "type": "string",
                "default": host
            }
        ])
        edit_bridge.set_invokable("config")

        remove_bridge = dslink.Node("removeBridge", bridge_node)
        remove_bridge.set_display_name("Remove Bridge")
        remove_bridge.set_profile("remove_bridge")
        remove_bridge.set_invokable("config")

        status = dslink.Node("status", bridge_node)
        status.set_display_name("Status")
        status.set_type("string")
        status.set_value("Unknown")

        bridge_node.add_child(edit_bridge)
        bridge_node.add_child(remove_bridge)
        bridge_node.add_child(reconnect)
        bridge_node.add_child(status)

        self.responder.super_root.add_child(bridge_node)

        try:
            self.bridges[bridge_name] = Bridge(host)
            self.bridges[bridge_name].connect()
            self.bridges[bridge_name].get_light_objects("id")
            self.create_lights(bridge_node)
            status.set_value("Connected")
        except PhueRegistrationException:
            status.set_value("Not Registered")
            return [
                [
                    False
                ]
            ]

        return [
            [
                True
            ]
        ]

    def edit_bridge(self, parameters):
        bridge_name = parameters[0].parent.name
        self.responder.super_root.remove_child(bridge_name)
        try:
            del self.bridges[bridge_name]
        except KeyError:
            pass
        self.create_bridge_action(parameters)

        return []

    def remove_bridge(self, parameters):
        bridge_name = parameters[0].parent.name
        self.responder.super_root.remove_child(bridge_name)
        try:
            del self.bridges[bridge_name]
        except KeyError:
            # Bridge doesn't exist
            pass
        return [
            [
                True
            ]
        ]

    def reconnect(self, parameters):
        bridge_name = parameters[0].parent.name
        host = parameters[0].parent.get_attribute("@host")
        self.responder.super_root.remove_child(bridge_name)
        try:
            del self.bridges[bridge_name]
        except KeyError:
            pass
        self.create_bridge(bridge_name, host)

        return []

    def set_hex(self, parameters):
        try:
            id = int(parameters[0].parent.name.split("_")[1])
            bridge_name = parameters[0].parent.parent.name
            val = parameters[1]["value"]
            val = val.replace("#", "")
            self.bridges[bridge_name].get_light_objects("id")[id].xy = converter.hexToCIE1931(val)
        except Exception as e:
            print("Exception: %s" % e)
            return [
                [
                    False
                ]
            ]

        return [
            [
                True
            ]
        ]

    def set_callback(self, parameters):
        try:
            id = int(parameters[0].parent.name.split("_")[1])
            val = parameters[1]
            bridge_name = str(parameters[0].parent.parent.name)

            metric = parameters[0].name
            light = self.bridges[bridge_name].get_light_objects("id")[id]

            setattr(light, metric, val)
        except Exception, e:
            print("Exception: %s" % e)
            return [
                [
                    False
                ]
            ]

        return [
            [
                True
            ]
        ]

    def poll(self):
        # Poll data here and set the values
        for bridge_name in self.bridges:
            bridge = self.bridges[bridge_name]
            try:
                for l in bridge.lights:
                    id = int(l.light_id)
                    cur_node = "/%s/light_%s" % (bridge_name, str(l.light_id))
                    root = self.responder.super_root
                    lights = self.bridges[bridge_name].get_light_objects("id")
                    root.get(cur_node + "/hue").set_value(lights[id].hue)
                    root.get(cur_node + "/on").set_value(lights[id].on)
                    root.get(cur_node + "/brightness").set_value(lights[id].brightness)
                    root.get(cur_node + "/saturation").set_value(lights[id].saturation)
                    root.get(cur_node + "/transitiontime").set_value(lights[id].transitiontime)
                    root.get(cur_node + "/colormode").set_value(lights[id].colormode)
                    root.get(cur_node + "/alert").set_value(lights[id].alert)

                    '''light_xy = lights[id].xy
                    print(float(lights[id].brightness))
                    hex = converter.CIE1931ToHex(light_xy[0], light_xy[1], bri=0.5)
                    self.responder.super_root.get(cur_node+"/hex").set_value("#"+hex)'''
            except Exception, e:
                print("Poll Loop Exception: %s" % e)

        time = self.responder.super_root.get("/updateRate")
        if time.value.has_value():
            reactor.callLater(time.get_value(), self.poll)
        else:
            reactor.callLater(1, self.poll)


if __name__ == "__main__":
    TemplateDSLink(dslink.Configuration(name="PhilipsHue", responder=True))
