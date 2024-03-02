#!/usr/bin/env python3

import subprocess
import socket
import os

import nosh
from nosh.node import InterfaceNode
from nosh.nosh import Node


def prompt_cb() -> str:
    return "{}@{}>".format(os.getlogin(), socket.gethostname())

def prompt_cb_configure() -> str:
    return "{}@{}#".format(os.getlogin(), socket.gethostname())


conf = nosh.Nosh(prompt_cb=prompt_cb_configure)
cli = nosh.Nosh(prompt_cb=prompt_cb)


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

def act_configure_mode(args):
    conf.start_cli()

def main():

    node_set = Node("set", "Set a parameter")
    node_set.append_leaf(Node("pppoe", "PPPoE"))
    node_set.append_leaf(Node("wlan", "Wireless interface"))
    
    conf.root.append_leaf(node_set)
    conf.root.append_leaf(Node("exit", "Exit from Configure mode",
                               action = act_cli_exit))

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

    cli.root.append_leaf(Node("exit", "Exit from CLI", action=act_cli_exit))

    cli.root.append_leaf(Node("configure", "Enter configuration mode",
                              action = act_configure_mode))

    cli.start_cli()


if __name__ == "__main__":
    main()
