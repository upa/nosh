#!/usr/bin/env python3

from subprocess import check_output
import platform
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
from nosh.node import IntNode


def prompt_cb() -> str:
    return "{}@{}>".format(os.getlogin(), socket.gethostname())


def act_cli_exit(args):
    raise EOFError


def act_show_interfaces(args):
    print(check_output(["ifconfig"], text=True))


def act_show_interfaces_interface(args):
    print(check_output(["ifconfig", args.pop()], text=True))


def act_show_system(args):
    print(check_output(["uname", "-a"], text=True))


def act_show_ip_route(args):
    os = platform.system()
    if os == "Darwin":
        print(check_output(["netstat", "-rnfinet"], text=True))
    elif os == "linux":
        print(check_output(["ip", "route", "show"], text=True))


def act_print_args(args):
    print(f"execute command: {args}")


def main():

    cli = CLI(prompt_cb=prompt_cb)

    cli.insert([], StaticNode("show", "Show system information"))

    cli.insert(
        ["show"],
        StaticNode("system", "Show System information", action=act_show_system),
    )

    cli.insert(
        ["show"],
        StaticNode(
            "interfaces", "Show interface information", action=act_show_interfaces
        ),
    )
    cli.insert(
        ["show", "interfaces"], InterfaceNode(action=act_show_interfaces_interface)
    )

    cli.insert(["show"], StaticNode("ip", "Show ip information"))
    cli.insert(
        ["show", "ip"],
        StaticNode("route", "Show ip route information", action=act_show_ip_route),
    )

    cli.insert([], StaticNode("set", "Set configuration parameters"))
    cli.insert(["set"], StaticNode("route-map", "Set route-map"))
    cli.insert(
        ["set", "route-map"],
        StringNode(
            reference="<route-map>",
            reference_desc="Name to identify a route-map",
            action=act_print_args
        ),
    )

    cli.insert(["set"], StaticNode("router-id", "Set router-id"))
    cli.insert(["set", "router-id"], IPv4AddressNode(action=act_print_args))

    cli.insert(["set"], StaticNode("interface", "Set interface parameters"))
    cli.insert(["set", "interface"], InterfaceNode())
    cli.insert(
        ["set", "interface", InterfaceNode],
        StaticNode("address", "IP address for this interface"),
    )
    cli.insert(
        ["set", "interface", InterfaceNode, "address"],
        InterfaceAddressNode(action=act_show_ip_route),
    )
    cli.insert(["set", "interface", InterfaceNode], StaticNode("mtu", "Set MTU"))
    cli.insert(
        ["set", "interface", InterfaceNode, "mtu"], IntNode(action=act_print_args)
    )

    cli.append(StaticNode("exit", "Exit from CLI", action=act_cli_exit))

    cli.start()


if __name__ == "__main__":
    main()
