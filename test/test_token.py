import pytest

from nosh.cli import CLI
from nosh.token import (
    IntToken,
    StaticToken,
    StringToken,
    InterfaceToken,
    IPv4AddressToken,
    IPv6AddressToken,
    InterfaceAddressToken,
)


def test_token():

    root = StaticToken(tokenstr="__root__", desc="Root Token")
    n1 = StaticToken(tokenstr="n1", desc="n1 desc")
    n2 = StaticToken(tokenstr="n2", desc="n2 desc")
    m1 = StaticToken(tokenstr="m1", desc="m1 desc")
    root.append(n1, n2, m1)
    candidates = root.complete("", "")
    tobe = [("n1", "n1 desc"), ("n2", "n2 desc"), ("m1", "m1 desc")]
    assert candidates == tobe


def test_token_invalid_reference():
    with pytest.raises(ValueError):
        StaticToken("n1", "n1 desc", reference="invalid reference")


def test_token_complete_with_reference():
    root = StaticToken("__root__", "Root StaticToken")
    n1 = StaticToken("n1", "n1 desc", reference="<n1-reference>")
    n2 = StaticToken("n2", "n2 desc")
    m1 = StaticToken("m1", "m1 desc")
    root.append(n1, n2, m1)
    candidates = root.complete("", "")
    tobe = [
        ("<n1-reference>", ""),
        ("n1", "n1 desc"),
        ("n2", "n2 desc"),
        ("m1", "m1 desc"),
    ]
    assert candidates == tobe


def test_token_complete_with_startwith():
    root = StaticToken("__root__", "Root StaticToken")
    n1 = StaticToken("n1", "n1 desc", reference="<n1-reference>")
    n2 = StaticToken("n2", "n2 desc")
    m1 = StaticToken("m1", "m1 desc")
    root.append(n1, n2, m1)
    candidates = root.complete("m", "m")
    tobe = [
        ("<n1-reference>", ""),
        ("m1", "m1 desc"),
    ]
    assert candidates == tobe


def test_interface_token():
    n = InterfaceToken()
    assert ("<interface-name>", "Name of interface") in n.completion_candidates("")


def test_string_token():
    i, desc = "<test-string>", "test string"
    n = StringToken(i, desc)
    assert [(i, desc)] == n.completion_candidates("")

    assert n.match("asdf")
    for c in [",", ".", "+", "*", "(", ")"]:
        assert not n.match(c)


def test_int_token():
    n = IntToken()
    assert [("<int>", "Integer")] == n.completion_candidates("")

    assert n.match("10")
    assert not n.match("test")


def test_ipv4addr_token():
    n = IPv4AddressToken()
    assert [("<ipv4-address>", "IPv4 Address")] == n.completion_candidates("")

    assert n.match("1.1.1.1")
    assert not n.match("1.1.1.1/24")
    assert not n.match("2001:db8::1")
    assert not n.match("2001:db8::1/64")
    assert not n.match("hoge")


def test_ipv6addr_token():
    n = IPv6AddressToken()
    assert [("<ipv6-address>", "IPv6 Address")] == n.completion_candidates("")

    assert n.match("2001:db8::1")
    assert not n.match("2001:db8::1/128")
    assert not n.match("1.1.1.1")
    assert not n.match("1.1.1.1/24")
    assert not n.match("hoge")


def test_interfaceaddr_token():
    n = InterfaceAddressToken()
    tobe = [("<address>", "Interface address/prefix length")]
    assert tobe == n.completion_candidates("")

    assert n.match("1.1.1.1/24")
    assert n.match("2001:db8::1/64")
    assert not n.match("2001:db8::1")
    assert not n.match("1.1.1.1")
    assert not n.match("hoge")


def test_cli():
    cli = CLI()
