
import pytest

from nosh import *

def test_node():
    root = Node("__root__", "Root Node")
    n1 = Node("n1", "n1 desc")
    n2 = Node("n2", "n2 desc")
    m1 = Node("m1", "m1 desc")
    root.append(n1, n2, m1)
    candidates = root.compelte("", "")
    tobe = [("n1", "n1 desc"), ("n2", "n2 desc"), ("m1", "m1 desc")]
    assert candidates == tobe

def test_node_invalid_indicator():
    with pytest.raises(ValueError):
        Node("n1", "n1 desc", indicator="invalid indicator")

def test_node_complete_with_indicator():
    root = Node("__root__", "Root Node")
    n1 = Node("n1", "n1 desc", indicator="<n1-indicator>")
    n2 = Node("n2", "n2 desc")
    m1 = Node("m1", "m1 desc")
    root.append(n1, n2, m1)
    candidates = root.compelte("", "")
    tobe = [
        ("<n1-indicator>", ""), ("n1", "n1 desc"), ("n2", "n2 desc"), ("m1", "m1 desc")
    ]
    assert candidates == tobe
    

def test_node_complete_with_startwith():
    root = Node("__root__", "Root Node")
    n1 = Node("n1", "n1 desc", indicator="<n1-indicator>")
    n2 = Node("n2", "n2 desc")
    m1 = Node("m1", "m1 desc")
    root.append(n1, n2, m1)
    candidates = root.compelte("m", "m")
    tobe = [
        ("<n1-indicator>", ""), ("m1", "m1 desc"),
    ]
    assert candidates == tobe
    
def test_interface_node():
    n = InterfaceNode()
    assert ("<interface-name>", "Name of interface") in n.complete_candidates("")

def test_string_node():
    i, desc = "<test-string>", "test string"
    n = StringNode(i, desc)
    assert [(i, desc)] == n.complete_candidates("")
    
    assert n.match("asdf")
    for c in [",", ".", "+", "*", "(", ")"]:
        assert not n.match(c)

def test_ipv4addr_node():
    n = IPv4AddressNode()
    assert [("<ipv4-address>", "IPv4 Address")] == n.complete_candidates("")

    assert n.match("1.1.1.1")
    assert not n.match("1.1.1.1/24")
    assert not n.match("2001:db8::1")
    assert not n.match("2001:db8::1/64")
    assert not n.match("hoge")

    
def test_ipv6addr_node():
    n = IPv6AddressNode()
    assert [("<ipv6-address>", "IPv6 Address")] == n.complete_candidates("")

    assert n.match("2001:db8::1")
    assert not n.match("2001:db8::1/128")
    assert not n.match("1.1.1.1")
    assert not n.match("1.1.1.1/24")
    assert not n.match("hoge")

def test_interfaceaddr_node():
    n = InterfaceAddressNode()
    tobe = [("<address>", "Interface address/prefix length")]
    assert tobe == n.complete_candidates("")

    assert n.match("1.1.1.1/24")
    assert n.match("2001:db8::1/64")
    assert not n.match("2001:db8::1")
    assert not n.match("1.1.1.1")
    assert not n.match("hoge")


def test_cli():
    cli = CLI()
