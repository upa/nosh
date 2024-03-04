#!/usr/bin/env python3

from subprocess import check_output
import platform
import socket
import sys
import os

import nosh
from nosh import (
    CLI,
    TextToken,
    IPv4AddressToken,
    InterfaceAddressToken,
    InterfaceToken,
    StringToken,
    IntToken,
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
    print()


def act_cli_exit(priv, args):
    raise EOFError


def act_show_interfaces(priv, args):
    print(check_output(["ifconfig"], text=True))


def act_show_interfaces_interface(priv, args):
    print(check_output(["ifconfig", args.pop()], text=True))


def act_show_system(priv, args):
    print(check_output(["uname", "-a"], text=True))


def act_show_system_version(priv, args):
    os = platform.system()
    if os == "Darwin":
        print(check_output(["sw_vers"], text=True))
    elif os == "Linux":
        print(check_output(["lsb_release", "-a"], text=True))


def act_show_ip_route(priv, args):
    os = platform.system()
    if os == "Darwin":
        print(check_output(["netstat", "-rnfinet"], text=True))
    elif os == "Linux":
        print(check_output(["ip", "route", "show"], text=True))


def act_ping(priv, args: list[str]):
    cmd = ["ping"]
    option_idx = []
    for idx, key in enumerate(args):
        if key == "count":
            cmd += ["-c", args[idx + 1]]
            option_idx += [idx, idx + 1]
        elif key == "wait":
            cmd += ["-W", args[idx + 1]]
            option_idx += [idx, idx + 1]

    for i in sorted(option_idx, reverse=True):
        args.pop(i)  # remove ping options from args

    target = args.pop()
    if target == "ping":
        # All options removed, then the text is 'ping'. this means
        # <targe> is not specified.
        print("<target> must be specified")
        return

    cmd.append(target)

    fork_and_exec(cmd)


def act_print_args(priv, args):
    print(f"execute command for: {args}")


def main():

    cli = CLI(prompt_cb=prompt_cb)

    show_tokens = {
        "class": TextToken,
        "text": "show",
        "desc": "Show information",
        "leaves": [
            {
                "class": TextToken,
                "text": "interface",
                "desc": "Show interface information",
                "action": act_show_interfaces,
                "leaves": [
                    {
                        "class": InterfaceToken,
                        "action": act_show_interfaces_interface,
                    }
                ],
            },
            {
                "class": TextToken,
                "text": "system",
                "desc": "Show system information",
                "action": act_show_system,
            },
            {
                "class": TextToken,
                "text": "ip",
                "desc": "Show ip information",
                "leaves": [
                    {
                        "text": "route",
                        "desc": "Show ip route information",
                        "class": TextToken,
                        "action": act_show_ip_route,
                    },
                ],
            },
        ],
    }

    show_tokens = nosh.instantiate(show_tokens)
    cli.append(show_tokens)

    show_system_version = TextToken(
        text="version", desc="Show system version", action=act_show_system_version
    )
    cli.insert(["show", "system"], show_system_version)

    set_tokens = {
        "class": TextToken,
        "text": "set",
        "desc": "Set parameters",
        "leaves": [
            {
                "class": TextToken,
                "text": "interfaces",
                "desc": "Set interface parameters",
                "leaves": [
                    {
                        "class": InterfaceToken,
                        "leaves": [
                            {
                                "class": TextToken,
                                "text": "address",
                                "desc": "IP address for this interface",
                                "leaves": [
                                    {
                                        "class": InterfaceAddressToken,
                                        "action": act_print_args,
                                    }
                                ],
                            },
                            {
                                "class": TextToken,
                                "text": "mtu",
                                "desc": "MTU for this interface",
                                "leaves": [
                                    {
                                        "class": IntToken,
                                        "mark": "<mtu>",
                                        "desc": "MTU value",
                                        "action": act_print_args,
                                    }
                                ],
                            },
                        ],
                    }
                ],
            },
            {
                "class": TextToken,
                "text": "route-map",
                "desc": "Set a route-map",
                "leaves": [
                    {
                        "class": StringToken,
                        "mark": "<route-map>",
                        "desc": "Name to identify a route-map",
                        "action": act_print_args,
                    }
                ],
            },
            {
                "class": TextToken,
                "text": "router-id",
                "desc": "Set router-id",
                "leaves": [
                    {
                        "class": IPv4AddressToken,
                        "mark": "<router-id>",
                        "desc": "Router Identifier",
                        "action": act_print_args,
                    }
                ],
            },
        ],
    }
    cli.append(nosh.instantiate(set_tokens))

    # ping command
    pn = TextToken(text="ping", desc="Ping remote target")

    ping_count_token = {
        "class": TextToken,
        "text": "count",
        "desc": "Number of ping requests",
        "leaves": [
            {
                "class": IntToken,
                "mark": "<Number>",
                "desc": "Number of ping requests",
                "action": act_ping,
            }
        ],
    }
    cn = nosh.instantiate(ping_count_token)

    ping_wait_token = {
        "class": TextToken,
        "text": "wait",
        "desc": "Wait time for ping response",
        "action": act_ping,
        "leaves": [
            {
                "class": IntToken,
                "mark": "<Second>",
                "desc": "Seconds for waiting ping response",
                "action": act_ping,
            }
        ],
    }
    wn = nosh.instantiate(ping_wait_token)

    ping_target_token = {
        "class": StringToken,
        "mark": "<target>",
        "desc": "Ping target",
        "action": act_ping,
    }
    tn = nosh.instantiate(ping_target_token)

    cli.append(pn)
    pn.append(cn, wn, tn)
    tn.append(cn, wn)

    cli.insert(["ping", "count", IntToken], wn, tn)
    cli.insert(["ping", "wait", IntToken], cn, tn)

    # exit command
    cli.append(TextToken(text="exit", desc="Exit from CLI", action=act_cli_exit))
    cli.append(TextToken(text="quit", desc="Exit from CLI", action=act_cli_exit))

    cli.cli()


if __name__ == "__main__":
    main()
