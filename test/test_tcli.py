from typing import Text
import pytest

from nosh import *
from tcli import *


def test_insert():
    token = TextToken(text="version", desc="show system version", action=act_test_ok)
    cli.insert(["show", "system"], token)
    tk, _ = cli.longest_match(["show", "system", "version"])
    assert tk == token


def test_insert_under_stringtoken():
    token = TextToken(
        text="test", desc="desc set route-map <route-map> test", action=act_test_ok
    )
    cli.insert(["set", "route-map", StringToken], token)

    tk, _ = cli.longest_match(["set", "route-map", "test-map", "not-match"])
    assert tk.__class__ == StringToken

    tk, _ = cli.longest_match(["set", "route-map", "test-map", "test"])
    assert tk == token


def test_execute():
    tk, _ = cli.longest_match(["set", "router-id", "1.1.1.1"])
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
    out = build_completion_output(
        [
            ("edit", "edit test: insert edit-test"),
            ("ping", "ping to remote host"),
            ("set", "desc set"),
            ("show", "desc show"),
            ("top", "clear edit prefix"),
        ]
    )
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

    out = (
        build_completion_output(
            [
                ("<route-map>", "desc set route-map <route-map>"),
                ("text", "desc text"),
            ]
        )
        + "set route-map "
    )

    clear_sio()
    assert cli.complete("set route-map ", "", 0) == None
    assert sio.getvalue() == out


def test_set_prefix():
    prefix = ["edit-test"]
    cli.set_prefix(prefix)

    out = (
        build_completion_output(
            [
                ("test1", "test1-desc"),
                ("test2", "test2-desc"),
                ("test3", "test3-desc"),
            ]
        )
        + "set "
    )

    clear_sio()
    assert cli.complete("set ", "", 0) == None
    assert sio.getvalue() == out
    test_complete_at_1st_level()
    cli.clear_prefix()
    test_complete_at_1st_level()
    test_complete_at_2nd_level()


def test_text_has_evaluated_before_string():

    out = (build_completion_output([("<count>", "Integer")])) + "ping count "
    clear_sio()
    assert cli.complete("ping count ", "", 0) == None
    assert sio.getvalue() == out
