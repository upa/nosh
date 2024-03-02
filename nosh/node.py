
from __future__ import annotations
from typing import Callable

import ifaddr

class Node():
    """Basic Node representing cli node"""

    def __init__(self, text: str, helpstr: str,
                 action: Callable[[list[str]]] | None = None):
        self.text = text
        self.helpstr = helpstr
        self.leafs: list[Node]= []
        self.action = action

    def __str__(self):
        return self.text

    def append_leaf(self, node: Node):
        """This method just appends the Node to as a leaf of this Node"""
        self.leafs.append(node)

    def compelte(self, linebuffer: str, text: str) -> list[tuple[str, str]]:
        """This method returns list of candidate values of `LEAF
        Nodes` and their help strings.

        For example, consider a case where linebuffer is "set vlans
        vlan-a v". Nosh.longest_prefix_match() returns Node(["set",
        "vlans", NodeString]), and the complete_help() of the Node is
        called with linebuffer "set vlans vlan-a v" and text
        "v". Then, complete_help() returns [("vlan", "VLAN Identifier
        (1..4096)"), ("vxlan", "VXLAN configuration")].

        """

        if self.match(text):
            """ called with "prefix... text", not with "prefix... text ".
            so, returns this node as the candidate.
            """
            return [(text, self.helpstr)]

        candidates : list[tuple[str, str]]= []
        for leaf in self.leafs:
            candidates += leaf.candidates(text)
        return candidates


    def candidates(self, text: str) -> list[tuple[str, str]]:
        """This method returns list of candidate values of `THIS Node`
        and their help strings. This is the basic Node, so it retrurns
        just [(text, helpstr)] if matches. If the node is
        InterfaceNode, it returns [(ifname, ""), ...] matching text.

        """
        if self.text.startswith(text):
            return [(self.text, self.helpstr)]
        return []

    def match(self, text: str) -> bool:
        """returns True if `text` extactly matches this Node. """
        return self.text == text

    def find_leaf(self, text) -> Node | None:
        for leaf in self.leafs:
            if leaf.match(text):
                return leaf
        return None

class InterfaceNode(Node):
    """ Node representing interfaces """
    def __init__(self, action: Callable[[list[str]]] | None = None):
        super().__init__("", "", action = action)

    def __str__(self):
        return "<[INTERFACE]>"

    def candidates(self, text: str) -> list[tuple[str, str]]:
        matched = []
        for adapter in ifaddr.get_adapters():
            if adapter.name.startswith(text):
                matched.append((adapter.name, ""))
        return matched

    def match(self, text: str) -> bool:
        for adapter in ifaddr.get_adapters():
            if adapter.name == text:
                return True
        return False
