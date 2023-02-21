#!/usr/bin/python3

import sys
from dasbus.typing import get_native
import dasbus.connection
bus = dasbus.connection.SessionMessageBus()

if len(sys.argv) != 5:
    print("No node name, unit, interface and property supplied")
    sys.exit(1)

node_name = sys.argv[1]
unit_name = sys.argv[2]
iface_name = sys.argv[3]
property_name = sys.argv[4]

manager = bus.get_proxy("org.containers.hirte",  "/org/containers/hirte")
node_path = manager.GetNode(node_name)
node = bus.get_proxy("org.containers.hirte",  node_path)

val = node.GetUnitProperty(unit_name, iface_name, property_name)
print(f"{property_name}: {get_native(val)}")