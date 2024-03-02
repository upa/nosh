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
    show.append_leaf(show_interfaces)
    show_interfaces_ifname = InterfaceNode(action=act_show_interfaces_interface)
    show_interfaces.append_leaf(show_interfaces_ifname)

    cli.root.append_leaf(show)

    show.append_leaf(Node("ip", "Show ip information"))
    show.append_leaf(Node("system", "Show system information", action=act_show_system))

    node_set = Node("set", "Set configuration parameters")
    node_rm = Node("route-map", "Set route-map")
    node_rm_name = StringNode(
        "<route-map>", "Name to identify a route-map", action=act_print_args
    )
    node_rm.append_leaf(node_rm_name)
    node_set.append_leaf(node_rm)

    node_router_id = Node("router-id", "Set router-id")
    node_set.append_leaf(node_router_id)
    node_router_id.append_leaf(IPv4AddressNode(action=act_print_args))

    node_addr = Node("address", "Set address")
    node_addr.append_leaf(IPv4AddressNode(action=act_print_args))
    node_addr.append_leaf(IPv6AddressNode(action=act_print_args))
    node_set.append_leaf(node_addr)

    node_if = Node("interface", "Set interface parameters")
    node_if_port = InterfaceNode()
    node_if.append_leaf(node_if_port)
    node_ifa = Node("address", "Set interface address")
    node_if_port.append_leaf(node_ifa)
    node_ifa.append_leaf(InterfaceAddressNode(action=act_print_args))
    node_set.append_leaf(node_if)

    cli.root.append_leaf(node_set)
    cli.root.append_leaf(Node("exit", "Exit from CLI", action=act_cli_exit))

    cli.start_cli()


if __name__ == "__main__":
    main()
