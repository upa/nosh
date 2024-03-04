#!/usr/bin/env python3

from nosh import *

def act_test_ok(priv, args):
    pass

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
    ]
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
                    ]
                }
            ]
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
    ]
}

cli = CLI(debug=False)
cli.append(instantiate(show_tree))
cli.append(instantiate(set_tree))

cli.setup()
cli.cli()

















