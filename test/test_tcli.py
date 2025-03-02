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


def test_execue_with_empty_line():
    clear_sio()
    cli.execute("")
    assert not "invalid synatx" in sio.getvalue()


def test_execute():
    tk, _ = cli.longest_match(["set", "router-id", "1.1.1.1"])
    assert tk.__class__ == IPv4AddressToken

    clear_sio()
    cli.execute("set router-id 1.1.1.1 ")
    assert sio.getvalue() == "set router-id 1.1.1.1\n"


def test_execute_multiple_lines():
    clear_sio()
    inputbuf = """
set router-id 1.1.1.1
set router-id 2.2.2.2
show uptime
"""
    # this can happen when copy and paste commands
    cli.execute(inputbuf)
    assert "never up" in sio.getvalue()


def test_syntaxerror():
    with pytest.raises(SyntaxError):
        cli.execute("invalid syntax")


def test_longest_match_synatx_error():
    with pytest.raises(SyntaxError) as e:
        cli.longest_match(["show", "hoge", "huga"])
    assert str(e.value) == "show hoge < syntax error"


def clear_sio():
    sio.truncate(0)
    sio.seek(0)


def build_completion_output(candidates: list[tuple[str, str]]) -> str:
    o = ""
    o += "\n"
    o += "\n"
    o += "Possible completions:\n"
    for v, h in candidates:
        o += "  {:20} {}\n".format(v, h)
    o += "\n"
    o += "> "
    return o


def test_full_comlete_texttoken():

    # Full compltion test
    out = build_completion_output(
        [
            ("choice", "choice test"),
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


def test_text_has_evaluated_before_string():

    out = (build_completion_output([("<count>", "Integer")])) + "ping count "
    clear_sio()
    assert cli.complete("ping count ", "", 0) == None
    assert sio.getvalue() == out


def test_set_prefix():
    prefix = ["edit-test"]
    cli.set_prefix(prefix)

    out = (
        build_completion_output(
            [
                ("<[Enter]>", "Execute this command"),
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

    # prefix must be inserted into args passed to action
    clear_sio()
    cli.execute("set test1")
    assert "set edit-test test1" in sio.getvalue()

    clear_sio()
    cli.execute("set ")
    assert "set edit-test" in sio.getvalue()

    clear_sio()
    cli.execute("set")
    assert "set edit-test" in sio.getvalue()

    clear_sio()
    cli.execute("")
    assert not "invalid synatx" in sio.getvalue()

    cli.clear_prefix()
    test_complete_at_1st_level()
    test_complete_at_2nd_level()
