#!/usr/bin/env python3

from subprocess import check_output
import platform
import socket
import sys
import os

import nosh
from nosh import (
    CLI,
    StaticNode,
    IPv4AddressNode,
    InterfaceAddressNode,
    InterfaceNode,
    StringNode,
    IntNode,
)


def prompt_cb() -> str:
    return "{}@{}>".format(os.getlogin(), socket.gethostname())


def fork_and_exec(args: list[str]):
    try:
        pid = os.fork()
    except OSError as e:
        print(f"failed to fork: {e}", file=sys.stderr)

    if not pid:
        try:
            os.execvp(args[0], args)
        except Exception as e:
            print(f"{' '.join(args)}: {e}", file=sys.stderr)
    else:
        try:
            os.waitpid(pid, 0)
        except KeyboardInterrupt:
            pass


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


def act_ping(args: list[str]):
    cmd = ["ping"]
    option_idx = []
    for idx, key in enumerate(args):
        if key == "count":
            cmd += ["-c", args[idx + 1]]
            option_idx += [idx, idx + 1]
        elif key == "timeout":
            cmd += ["-W", args[idx + 1]]
            option_idx += [idx, idx + 1]

    for i in sorted(option_idx, reverse=True):
        args.pop(i)  # remove ping options from args

    target = args.pop()
    if target == "ping":
        # All options removed, then the token is 'ping'. this means
        # <targe> is not specified.
        print("<target> must be specified")
        return

    cmd.append(target)

    fork_and_exec(cmd)


def act_print_args(args):
    print(f"execute command for: {args}")


def main():

    cli = CLI(prompt_cb=prompt_cb)

    show_nodes = {
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
    show_nodes = nosh.instantiate(show_nodes)
    cli.append(show_nodes)

    show_system_version = StaticNode(
        token="version", desc="Show system version", action=act_show_system_version
    )
    cli.insert(["show", "system"], show_system_version)

    set_nodes = {
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
    cli.append(nosh.instantiate(set_nodes))

    # ping command
    pn = StaticNode(token="ping", desc="Ping remote target")

    ping_count_node = {
        "token": "count",
        "desc": "Number of ping requests",
        "class": StaticNode,
        "leaves": [
            {
                "class": IntNode,
                "reference": "<Number>",
                "reference_desc": "Number of ping requests",
                "action": act_ping,
            }
        ],
    }
    cn = nosh.instantiate(ping_count_node)

    ping_wait_node = {
        "token": "wait",
        "desc": "Wait time for ping response",
        "class": StaticNode,
        "action": act_ping,
        "leaves": [
            {
                "class": IntNode,
                "reference": "<Second>",
                "reference_desc": "Seconds for waiting ping response",
                "action": act_ping,
            }
        ],
    }
    wn = nosh.instantiate(ping_wait_node)

    ping_target_node = {
        "class": StringNode,
        "reference": "<target>",
        "reference_desc": "Ping target",
        "action": act_ping,
    }
    tn = nosh.instantiate(ping_target_node)

    cli.append(pn)
    pn.append(cn, wn, tn)
    tn.append(cn, wn)

    cli.insert(["ping", "count", IntNode], wn, tn)
    cli.insert(["ping", "wait", IntNode], cn, tn)

    # exit command
    cli.append(StaticNode(token="exit", desc="Exit from CLI", action=act_cli_exit))
    cli.append(StaticNode(token="quit", desc="Exit from CLI", action=act_cli_exit))

    cli.cli()


if __name__ == "__main__":
    main()
