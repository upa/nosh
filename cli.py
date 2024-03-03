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
from nosh.node import IntNode, instantiate


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


def act_show_system_version(args):
    os = platform.system()
    if os == "Darwin":
        print(check_output(["sw_vers"], text=True))
    elif os == "Linux":
        print(check_output(["lsb_release", "-a"], text=True))


def act_show_ip_route(args):
    os = platform.system()
    if os == "Darwin":
        print(check_output(["netstat", "-rnfinet"], text=True))
    elif os == "Linux":
        print(check_output(["ip", "route", "show"], text=True))


def act_print_args(args):
    print(f"execute command for: {args}")


def main():

    cli = CLI(prompt_cb=prompt_cb)

    show_cmds = {
        "token": "show",
        "desc": "Show information",
        "class": StaticNode,
        "leaves": [
            {
                "token": "interface",
                "desc": "Show interface information",
                "class": StaticNode,
                "action": act_show_interfaces,
                "leaves": [
                    {
                        "class": InterfaceNode,
                        "action": act_show_interfaces_interface,
                    }
                ],
            },
            {
                "token": "system",
                "desc": "Show system information",
                "class": StaticNode,
                "action": act_show_system,
            },
            {
                "token": "ip",
                "desc": "Show ip information",
                "class": StaticNode,
                "leaves": [
                    {
                        "token": "route",
                        "desc": "Show ip route information",
                        "class": StaticNode,
                        "action": act_show_ip_route,
                    },
                ],
            },
        ],
    }
    show_cmds = instantiate(show_cmds)
    cli.append(show_cmds)

    show_system_version = StaticNode(
        token="version", desc="Show system version", action=act_show_system_version
    )
    cli.insert(["show", "system"], show_system_version)

    set_cmds = {
        "token": "set",
        "desc": "Set parameters",
        "class": StaticNode,
        "leaves": [
            {
                "token": "interfaces",
                "desc": "Set interface parameters",
                "class": StaticNode,
                "leaves": [
                    {
                        "class": InterfaceNode,
                        "leaves": [
                            {
                                "token": "address",
                                "desc": "IP address for this interface",
                                "class": StaticNode,
                                "leaves": [
                                    {
                                        "class": InterfaceAddressNode,
                                        "action": act_print_args,
                                    }
                                ],
                            },
                            {
                                "token": "mtu",
                                "desc": "MTU for this interface",
                                "class": StaticNode,
                                "leaves": [
                                    {
                                        "class": IntNode,
                                        "reference": "<mtu>",
                                        "reference_desc": "MTU value",
                                        "action": act_print_args,
                                    }
                                ],
                            },
                        ],
                    }
                ],
            },
            {
                "token": "route-map",
                "desc": "Set a route-map",
                "class": StaticNode,
                "leaves": [
                    {
                        "class": StringNode,
                        "reference": "<route-map>",
                        "reference_desc": "Name to identify a route-map",
                        "action": act_print_args,
                    }
                ],
            },
            {
                "token": "router-id",
                "desc": "Set router-id",
                "class": StaticNode,
                "leaves": [
                    {
                        "class": IPv4AddressNode,
                        "reference": "<router-id>",
                        "reference_desc": "Router Identifier",
                        "action": act_print_args,
                    }
                ],
            },
        ],
    }

    cli.append(instantiate(set_cmds))

    cli.append(StaticNode("exit", "Exit from CLI", action=act_cli_exit))

    cli.start()


if __name__ == "__main__":
    main()
