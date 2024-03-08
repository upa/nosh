#!/usr/bin/env python3

"""test cli"""

import argparse
import io
import sys

sys.path.insert(0, ".")

from nosh import *


def act_test_ok(priv: Any, args: list[str]):
    c: CLI = priv
    c.file.write(" ".join(args))


def act_test_ng(priv: Any, args: list[str]):
    raise RuntimeError("act_test_ng is called: {}".format(" ".join(args)))


def act_edit_test(priv: Any, args: list[str]):
    c: CLI = priv
    c.set_prefix(["edit-test"])


def act_top(priv: Any, args: list[str]):
    c: CLI = priv
    c.clear_prefix()


show_tree = {
    "class": TextToken,
    "text": "show",
    "desc": "desc show",
    "leaves": [
        {
            "class": TextToken,
            "text": "system",
            "desc": "desc show system",
            "action": act_test_ok,
        },
        {
            "class": TextToken,
            "text": "sysmet",
            "desc": "desc show sysmet",
            "action": act_test_ok,
        },
    ],
}

set_tree = {
    "class": TextToken,
    "text": "set",
    "desc": "desc set",
    "action": act_test_ok,
    "leaves": [
        {
            "class": TextToken,
            "text": "route-map",
            "desc": "desc set route-map",
            "leaves": [
                {
                    "class": TextToken,
                    "text": "text",
                    "desc": "desc text",
                },
                {
                    "class": StringToken,
                    "mark": "<route-map>",
                    "desc": "desc set route-map <route-map>",
                    "action": act_test_ok,
                    "leaves": [
                        {
                            "class": TextToken,
                            "text": "permit",
                            "desc": "desc set route-map <route-map> permit",
                            "action": act_test_ok,
                        },
                    ],
                },
            ],
        },
        {
            "class": TextToken,
            "text": "router-id",
            "desc": "desc set router-id",
            "leaves": [
                {
                    "class": IPv4AddressToken,
                    "mark": "<router-id>",
                    "action": act_test_ok,
                },
            ],
        },
        {
            "class": TextToken,
            "text": "edit-test",
            "action": act_test_ok,
            "leaves": [
                {
                    "class": TextToken,
                    "text": "test1",
                    "desc": "test1-desc",
                    "action": act_test_ok,
                },
                {
                    "class": TextToken,
                    "text": "test2",
                    "desc": "test2-desc",
                    "action": act_test_ok,
                },
                {
                    "class": TextToken,
                    "text": "test3",
                    "desc": "test3-desc",
                    "action": act_test_ok,
                },
            ],
        },
    ],
}

edit_tree = {
    "class": TextToken,
    "text": "edit",
    "desc": "edit test: insert edit-test",
    "action": act_edit_test,
}

top_tree = {
    "class": TextToken,
    "text": "top",
    "desc": "clear edit prefix",
    "action": act_top,
}

ping = instantiate(
    {
        "class": TextToken,
        "text": "ping",
        "desc": "ping to remote host",
        "leaves": [
            {
                "class": StringToken,
                "mark": "<remote>",
                "desc": "Ping target",
                "action": act_test_ok,
            },
        ],
    }
)

count = instantiate(
    {
        "class": TextToken,
        "text": "count",
        "desc": "Number of ping requests to be sent",
        "leaves": [
            {
                "class": IntToken,
                "mark": "<count>",
                "action": act_test_ok,
            }
        ],
    }
)

wait = instantiate(
    {
        "class": TextToken,
        "text": "wait",
        "desc": "Wait time (seconds)",
        "leaves": [
            {
                "class": IntToken,
                "mark": "<secounds>",
                "action": act_test_ok,
            },
        ],
    }
)


ping.append(count, wait)
target = ping.find([StringToken])
count.insert([IntToken], target, wait)
wait.insert([IntToken], target, count)

sio = io.StringIO()
cli = CLI(file=sio)
cli.append(
    instantiate(show_tree),
    instantiate(set_tree),
    instantiate(edit_tree),
    instantiate(top_tree),
    ping,
)
cli.private = cli


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--debug", action="store_true", help="enable debug")
    args = parser.parse_args()

    cli.file = sys.stdout
    cli.debug = args.debug
    cli.cli()
