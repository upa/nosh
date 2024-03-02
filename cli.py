#!/usr/bin/env python3

import subprocess
import socket
import os

from nosh import (
    CLI,
    StaticNode,
    IPv4AddressNode,
    IPv6AddressNode,
    InterfaceAddressNode,
    InterfaceNode,
    StringNode,
)


def prompt_cb() -> str:
    return "{}@{}>".format(os.getlogin(), socket.gethostname())


def act_cli_exit(args):
    raise EOFError


def act_show_interfaces(args):
    out = subprocess.check_output(["ifconfig"], text=True)
    print(out)


def act_show_interfaces_interface(args):
    ifname = args.pop()
    out = subprocess.check_output(["ifconfig", ifname], text=True)
    print(out)


def act_show_system(args):
    out = subprocess.check_output(["uname", "-a"], text=True)
    print(out)


def act_print_args(args):
    print(args)


def main():

    cli = CLI(prompt_cb=prompt_cb)

    show = StaticNode("show", "Show system information")
    show_interfaces = StaticNode(
        "interfaces", "Show interface information", action=act_show_interfaces
    )
    show.append(show_interfaces)
    show_interfaces_ifname = InterfaceNode(action=act_show_interfaces_interface)
    show_interfaces.append(show_interfaces_ifname)

    cli.root.append(show)

    show.append(StaticNode("ip", "Show ip information"))
    show.append(StaticNode("system", "Show system information", action=act_show_system))

    cli.append(StaticNode("set", "Set configuration parameters"))

    cli.find(["set"]).append(StaticNode("route-map", "Set route-map"))
    cli.find(["set", "route-map"]).append(
        StringNode("<route-map>", "Name to identify a route-map", action=act_print_args)
    )

    cli.find(["set"]).append(StaticNode("router-id", "Set router-id"))
    cli.find(["set", "router-id"]).append(IPv4AddressNode(action=act_print_args))

    node_addr = StaticNode("address", "Set address")
    node_addr.append(IPv4AddressNode(action=act_print_args))
    node_addr.append(IPv6AddressNode(action=act_print_args))
    cli.find(["set"]).append(node_addr)

    cli.find(["set"]).append(StaticNode("interface", "Set inteface parameters"))

    cli.find(["set", "interface"]).append(InterfaceNode())
    cli.find(["set", "interface", InterfaceNode]).append(
        InterfaceAddressNode(action=act_print_args)
    )

    cli.append(StaticNode("exit", "Exit from CLI", action=act_cli_exit))

    cli.start()


if __name__ == "__main__":
    main()
