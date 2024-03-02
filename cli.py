#!/usr/bin/env python3

import subprocess
import socket
import os

import nosh
from nosh.node import (
    IPv4AddressNode,
    IPv6AddressNode,
    InterfaceAddressNode,
    InterfaceNode,
    StringNode,
)
from nosh.nosh import Node


def prompt_cb() -> str:
    return "{}@{}>".format(os.getlogin(), socket.gethostname())


def act_cli_exit(args: list[str]):
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

    cli = nosh.Nosh(prompt_cb=prompt_cb)

    show = Node("show", "Show system information")
    show_interfaces = Node(
        "interfaces", "Show interface information", action=act_show_interfaces
    )
    show.append(show_interfaces)
    show_interfaces_ifname = InterfaceNode(action=act_show_interfaces_interface)
    show_interfaces.append(show_interfaces_ifname)

    cli.root.append(show)

    show.append(Node("ip", "Show ip information"))
    show.append(Node("system", "Show system information", action=act_show_system))

    cli.append(Node("set", "Set configuration parameters"))

    cli.find(["set"]).append(Node("route-map", "Set route-map"))
    cli.find(["set", "route-map"]).append(StringNode(
        "<route-map>", "Name to identify a route-map", action=act_print_args
    ))

    cli.find(["set"]).append(Node("router-id", "Set router-id"))
    cli.find(["set", "router-id"]).append(IPv4AddressNode(action=act_print_args))


    node_addr = Node("address", "Set address")
    node_addr.append(IPv4AddressNode(action=act_print_args))
    node_addr.append(IPv6AddressNode(action=act_print_args))
    cli.find(["set"]).append(node_addr)

    cli.find(["set"]).append(Node("interface", "Set inteface parameters"))

    cli.find(["set", "interface"]).append(InterfaceNode())
    cli.find(["set", "interface", InterfaceNode]).append(InterfaceAddressNode(action=act_print_args))

    cli.append(Node("exit", "Exit from CLI", action=act_cli_exit))

    cli.start_cli()


if __name__ == "__main__":
    main()
