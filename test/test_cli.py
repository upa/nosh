from typing import Text
import pytest
import io

from nosh import *

def act_test_ok(priv: Any, args: list[str]):
    out : TextIO = priv
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


sio = io.StringIO()
cli = CLI(file = sio, private=sio)
cli.append(instantiate(show_tree))
cli.append(instantiate(set_tree))

def test_insert():
    token = TextToken(text="version", desc="show system version", action=act_test_ok)
    cli.insert(["show", "system"], token)
    tk, _ = cli.longest_match(["show", "system", "version"])
    assert tk == token

def test_insert_under_stringtoken():
    token = TextToken(text="test", desc="desc set route-map <route-map> test",
                      action=act_test_ok)
    cli.insert(["set", "route-map", StringToken], token)

    tk, _ = cli.longest_match(["set", "route-map", "test-map", "not-match"])
    assert tk.__class__ == StringToken

    tk, _ = cli.longest_match(["set", "route-map", "test-map", "test"])
    assert tk == token
    
def test_execute():
    tk, _  = cli.longest_match(["set", "router-id", "1.1.1.1"])
    assert tk.__class__ == IPv4AddressToken

    clear_sio()
    cli.execute("set router-id 1.1.1.1 ")
    assert sio.getvalue() == "set router-id 1.1.1.1"

def clear_sio():
    sio.truncate(0)
    sio.seek(0)

def build_completion_output(candidates: list[tuple[str, str]]) -> str:
    o = ""
    o += "\n"
    o += "\n"
    o += "Completions:\n"
    for v, h in candidates:
        o += "  {:16} {}\n".format(v, h)
    o += "\n"
    o += "> "
    return o

def test_full_comlete_texttoken():

    # Full compltion test
    out = build_completion_output([("set", "desc set"), ("show", "desc show")])
    clear_sio()
    assert cli.complete("", "", 0) == None
    assert sio.getvalue() == out

def test_complete_at_1st_level():
    # 's' matches show and set
    assert cli.complete("s", "s", 0) == "show "
    assert cli.complete("s", "s", 1) == "set "

def test_complete_at_2nd_level():
    # 'show sys' matches show system and sysmet
    assert cli.complete("show sys", "sys", 0) == "system "
    assert cli.complete("show sys", "sys", 1) == "sysmet "
    
def test_string_and_text_at_same_level():
    
    out = build_completion_output([
        ("<route-map>", "desc set route-map <route-map>"),
        ("text", "desc text"),
    ])
    out += "set route-map "

    clear_sio()
    assert cli.complete("set route-map ", "", 0) == None
    assert sio.getvalue() == out

