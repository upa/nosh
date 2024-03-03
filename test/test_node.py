import pytest

from nosh.cli import CLI
from nosh.node import (
    IntNode,
    StaticNode,
    StringNode,
    InterfaceNode,
    IPv4AddressNode,
    IPv6AddressNode,
    InterfaceAddressNode,
)


def test_node():

    root = StaticNode("__root__", "Root Node")
    n1 = StaticNode("n1", "n1 desc")
    n2 = StaticNode("n2", "n2 desc")
    m1 = StaticNode("m1", "m1 desc")
    root.append(n1, n2, m1)
    candidates = root.complete("", "")
    tobe = [("n1", "n1 desc"), ("n2", "n2 desc"), ("m1", "m1 desc")]
    assert candidates == tobe


def test_node_invalid_reference():
    with pytest.raises(ValueError):
        StaticNode("n1", "n1 desc", reference="invalid reference")


def test_node_complete_with_reference():
    root = StaticNode("__root__", "Root StaticNode")
    n1 = StaticNode("n1", "n1 desc", reference="<n1-reference>")
    n2 = StaticNode("n2", "n2 desc")
    m1 = StaticNode("m1", "m1 desc")
    root.append(n1, n2, m1)
    candidates = root.complete("", "")
    tobe = [
        ("<n1-reference>", ""),
        ("n1", "n1 desc"),
        ("n2", "n2 desc"),
        ("m1", "m1 desc"),
    ]
    assert candidates == tobe


def test_node_complete_with_startwith():
    root = StaticNode("__root__", "Root StaticNode")
    n1 = StaticNode("n1", "n1 desc", reference="<n1-reference>")
    n2 = StaticNode("n2", "n2 desc")
    m1 = StaticNode("m1", "m1 desc")
    root.append(n1, n2, m1)
    candidates = root.complete("m", "m")
    tobe = [
        ("<n1-reference>", ""),
        ("m1", "m1 desc"),
    ]
    assert candidates == tobe


def test_interface_node():
    n = InterfaceNode()
    assert ("<interface-name>", "Name of interface") in n.completion_candidates("")


def test_string_node():
    i, desc = "<test-string>", "test string"
    n = StringNode(i, desc)
    assert [(i, desc)] == n.completion_candidates("")

    assert n.match("asdf")
    for c in [",", ".", "+", "*", "(", ")"]:
        assert not n.match(c)


def test_int_node():
    n = IntNode()
    assert [("<int>", "Integer")] == n.completion_candidates("")

    assert n.match("10")
    assert not n.match("test")


def test_ipv4addr_node():
    n = IPv4AddressNode()
    assert [("<ipv4-address>", "IPv4 Address")] == n.completion_candidates("")

    assert n.match("1.1.1.1")
    assert not n.match("1.1.1.1/24")
    assert not n.match("2001:db8::1")
    assert not n.match("2001:db8::1/64")
    assert not n.match("hoge")


def test_ipv6addr_node():
    n = IPv6AddressNode()
    assert [("<ipv6-address>", "IPv6 Address")] == n.completion_candidates("")

    assert n.match("2001:db8::1")
    assert not n.match("2001:db8::1/128")
    assert not n.match("1.1.1.1")
    assert not n.match("1.1.1.1/24")
    assert not n.match("hoge")


def test_interfaceaddr_node():
    n = InterfaceAddressNode()
    tobe = [("<address>", "Interface address/prefix length")]
    assert tobe == n.completion_candidates("")

    assert n.match("1.1.1.1/24")
    assert n.match("2001:db8::1/64")
    assert not n.match("2001:db8::1")
    assert not n.match("1.1.1.1")
    assert not n.match("hoge")


def test_cli():
    cli = CLI()
