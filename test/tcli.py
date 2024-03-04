#!/usr/bin/env python3

"""test cli"""

import argparse
import io

from nosh import *


def act_test_ok(priv: Any, args: list[str]):
    out: TextIO = priv
    out.write(" ".join(args))


def act_test_ng(priv: Any, args: list[str]):
    raise RuntimeError("act_test_ng is called: {}".format(" ".join(args)))


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
            "text" :"edit-test",
            "leaves": [
                {"class": TextToken, "text": "test1", "desc": "test1-desc" },
                {"class": TextToken, "text": "test2", "desc": "test2-desc" },
                {"class": TextToken, "text": "test3", "desc": "test3-desc" },
            ]
        },
    ],
}

sio = io.StringIO()
cli = CLI(file=sio, private=sio)
cli.append(instantiate(show_tree))
cli.append(instantiate(set_tree))

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--debug", action="store_true", help="enable debug")
    args = parser.parse_args()

    cli.file = sys.stdout
    cli.debug = args.debug
    cli.cli()
